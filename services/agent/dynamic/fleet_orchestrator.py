"""Orchestration flow for the dynamic fleet incident dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from db import get_pool
from dynamic.fleet_dashboard_builder import (
    DYNAMIC_FLEET_DASHBOARD_UID,
    build_fleet_dashboard_payload,
)
from dynamic.grafana_client import GrafanaClient
from dynamic.mcp_client import MCPClient


LOOKBACK_HOURS = 24
FLEET_DASHBOARD_SLUG = "dynamic-fleet-incident-dashboard"


@dataclass
class FleetTriggerRequest:
    mode: str
    dry_run: bool
    app_external_id: str | None = None
    alert_name: str | None = None


class DynamicFleetDashboardOrchestrator:
    """Glue code between fleet correlation, alert context, and Grafana upsert."""

    def __init__(
        self,
        *,
        mcp_client: MCPClient | None = None,
        grafana_client: GrafanaClient | None = None,
    ) -> None:
        self.mcp_client = mcp_client or MCPClient()
        self.grafana_client = grafana_client or GrafanaClient()

    async def trigger(self, request: FleetTriggerRequest) -> dict[str, Any]:
        hints = self._resolve_request(request)
        fleet_status = await self.mcp_client.get_fleet_status()
        fleet_alerts = await self.mcp_client.get_fleet_alerts(hours=LOOKBACK_HOURS)
        correlation = await self.mcp_client.get_cross_vessel_correlation(hours=LOOKBACK_HOURS)
        used_tools = [
            "get_fleet_status",
            "get_fleet_alerts",
            "get_cross_vessel_correlation",
        ]

        focus = _select_fleet_focus(
            hints=hints,
            fleet_alerts=list(fleet_alerts.get("alerts") or []),
            correlation=correlation,
        )

        generated_at = datetime.now(timezone.utc).isoformat()
        summary = _build_fleet_summary(
            focus=focus,
            fleet_status=fleet_status,
            fleet_alerts=fleet_alerts,
            correlation=correlation,
        )
        dashboard_context = {
            "generated_at": generated_at,
            "trigger_mode": request.mode,
            "scenario_key": "multi_vessel_incident",
            "focus_app_id": focus.get("focus_app_id"),
            "focus_app_name": focus.get("focus_app_name"),
            "focus_alert_name": focus.get("focus_alert_name"),
            "focus_alert_type": focus.get("focus_alert_type"),
            "focus_severity": focus.get("focus_severity"),
            "affected_vessels_count": focus.get("affected_vessels_count", 0),
            "fleet_alert_count": int(fleet_alerts.get("count") or 0),
            "used_tools": used_tools,
            "lookback_hours": LOOKBACK_HOURS,
            "summary": summary,
        }
        dashboard_payload = build_fleet_dashboard_payload(dashboard_context)

        grafana_result: dict[str, Any] | None = None
        if not request.dry_run:
            grafana_result = await self.grafana_client.upsert_dashboard(
                dashboard_payload,
                message=(
                    "Dynamic fleet incident update: "
                    f"{focus.get('focus_app_id') or focus.get('focus_alert_name') or 'fleet'}"
                ),
            )

        await self._log_run(
            trigger_mode=request.mode,
            app_external_id=focus.get("focus_app_id"),
            alert_name=focus.get("focus_alert_name"),
            severity=focus.get("focus_severity"),
            dashboard_uid=DYNAMIC_FLEET_DASHBOARD_UID,
            summary=summary,
            used_tools=used_tools,
            dashboard_json=dashboard_payload,
            dry_run=request.dry_run,
        )

        response: dict[str, Any] = {
            "dashboard_uid": DYNAMIC_FLEET_DASHBOARD_UID,
            "dashboard_url": self.grafana_client.dashboard_url(
                DYNAMIC_FLEET_DASHBOARD_UID,
                slug=FLEET_DASHBOARD_SLUG,
            ),
            "scenario_key": "multi_vessel_incident",
            "trigger_mode": request.mode,
            "generated_at": generated_at,
            "summary": summary,
            "used_tools": used_tools,
            "dry_run": request.dry_run,
            "grafana_result": grafana_result,
        }
        if request.dry_run:
            response["dashboard_json"] = dashboard_payload
        return response

    def _resolve_request(self, request: FleetTriggerRequest) -> dict[str, Any]:
        if request.mode == "latest_correlated_incident":
            return {
                "app_external_id": request.app_external_id,
                "alert_name": request.alert_name,
            }
        if request.mode == "explicit_context":
            if not request.app_external_id and not request.alert_name:
                raise ValueError("app_external_id or alert_name is required for explicit_context mode")
            return {
                "app_external_id": request.app_external_id,
                "alert_name": request.alert_name,
            }
        raise ValueError(f"Unsupported fleet trigger mode: {request.mode}")

    async def _log_run(
        self,
        *,
        trigger_mode: str,
        app_external_id: str | None,
        alert_name: str | None,
        severity: str | None,
        dashboard_uid: str,
        summary: str,
        used_tools: list[str],
        dashboard_json: dict[str, Any],
        dry_run: bool,
    ) -> None:
        pool = get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO dynamic_dashboard_runs (
                    trigger_mode,
                    source_alert_fingerprint,
                    vessel_imo,
                    app_external_id,
                    alert_name,
                    severity,
                    scenario_key,
                    dashboard_uid,
                    summary,
                    used_tools_json,
                    dashboard_json,
                    dry_run
                )
                VALUES ($1, NULL, 'FLEET', $2, $3, $4, $5, $6, $7, $8::jsonb, $9::jsonb, $10)
                """,
                trigger_mode,
                app_external_id,
                alert_name,
                severity,
                "multi_vessel_incident",
                dashboard_uid,
                summary,
                json.dumps(used_tools),
                json.dumps(dashboard_json),
                dry_run,
            )


def _select_fleet_focus(
    *,
    hints: dict[str, Any],
    fleet_alerts: list[dict[str, Any]],
    correlation: dict[str, Any],
) -> dict[str, Any]:
    correlated_apps = list(correlation.get("correlated_apps") or [])
    correlated_alert_types = list(correlation.get("correlated_alert_types") or [])
    hinted_app = str(hints.get("app_external_id") or "").strip().lower()
    hinted_alert = str(hints.get("alert_name") or "").strip().lower()

    if correlated_apps:
        ranked_apps = sorted(
            correlated_apps,
            key=lambda item: (
                0 if hinted_app and str(item.get("app_id") or "").lower() == hinted_app else 1,
                -int(item.get("affected_vessels") or 0),
                str(item.get("app_name") or "").lower(),
            ),
        )
        top_app = ranked_apps[0]
        app_alerts = [
            alert
            for alert in fleet_alerts
            if str(alert.get("app_external_id") or "").lower() == str(top_app.get("app_id") or "").lower()
        ]
        top_alert = _pick_top_alert(app_alerts, hinted_alert)
        top_correlation_alert = _pick_correlated_alert_type(correlated_alert_types, top_alert)
        return {
            "focus_app_id": top_app.get("app_id"),
            "focus_app_name": top_app.get("app_name"),
            "focus_alert_name": (
                (top_alert or {}).get("alert_name")
                or (top_correlation_alert or {}).get("alert_name")
            ),
            "focus_alert_type": (
                (top_alert or {}).get("alert_type")
                or (top_correlation_alert or {}).get("alert_type")
            ),
            "focus_severity": (top_alert or {}).get("severity"),
            "affected_vessels_count": int(top_app.get("affected_vessels") or 0),
        }

    grouped_apps = _group_alerts_by_app(fleet_alerts)
    if grouped_apps:
        ranked_groups = sorted(
            grouped_apps,
            key=lambda item: (
                0 if hinted_app and item["app_id"].lower() == hinted_app else 1,
                -item["affected_vessels_count"],
                -item["critical_alert_count"],
                -item["alert_count"],
                item["latest_received"],
            ),
        )
        top_group = ranked_groups[0]
        top_alert = _pick_top_alert(top_group["alerts"], hinted_alert)
        return {
            "focus_app_id": top_group["app_id"],
            "focus_app_name": top_group["app_name"],
            "focus_alert_name": (top_alert or {}).get("alert_name"),
            "focus_alert_type": (top_alert or {}).get("alert_type"),
            "focus_severity": (top_alert or {}).get("severity"),
            "affected_vessels_count": top_group["affected_vessels_count"],
        }

    top_alert = _pick_top_alert(fleet_alerts, hinted_alert)
    return {
        "focus_app_id": (top_alert or {}).get("app_external_id"),
        "focus_app_name": (top_alert or {}).get("app_name"),
        "focus_alert_name": (top_alert or {}).get("alert_name"),
        "focus_alert_type": (top_alert or {}).get("alert_type"),
        "focus_severity": (top_alert or {}).get("severity"),
        "affected_vessels_count": 1 if top_alert else 0,
    }


def _pick_correlated_alert_type(
    correlated_alert_types: list[dict[str, Any]],
    top_alert: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not correlated_alert_types:
        return None
    top_alert_name = str((top_alert or {}).get("alert_name") or "").strip().lower()
    for item in correlated_alert_types:
        if top_alert_name and str(item.get("alert_name") or "").strip().lower() == top_alert_name:
            return item
    return correlated_alert_types[0]


def _group_alerts_by_app(fleet_alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for alert in fleet_alerts:
        app_id = str(alert.get("app_external_id") or "").strip()
        app_name = str(alert.get("app_name") or app_id or "Unknown application")
        if not app_id:
            continue
        bucket = groups.setdefault(
            app_id.lower(),
            {
                "app_id": app_id,
                "app_name": app_name,
                "alerts": [],
                "affected_vessels": set(),
                "critical_alert_count": 0,
                "alert_count": 0,
                "latest_received": "",
            },
        )
        bucket["alerts"].append(alert)
        bucket["affected_vessels"].add(str(alert.get("imo_nr") or ""))
        bucket["alert_count"] += 1
        if _severity_rank(str(alert.get("severity") or "")) == 0:
            bucket["critical_alert_count"] += 1
        received = str(alert.get("received_at") or alert.get("starts_at") or "")
        if received > bucket["latest_received"]:
            bucket["latest_received"] = received
    result = []
    for item in groups.values():
        item["affected_vessels_count"] = len([imo for imo in item["affected_vessels"] if imo])
        result.append(item)
    return result


def _pick_top_alert(alerts: list[dict[str, Any]], hinted_alert: str) -> dict[str, Any] | None:
    if not alerts:
        return None
    return sorted(
        alerts,
        key=lambda item: (
            0 if hinted_alert and str(item.get("alert_name") or "").strip().lower() == hinted_alert else 1,
            _severity_rank(str(item.get("severity") or "")),
            -_timestamp_rank(str(item.get("received_at") or item.get("starts_at") or "")),
        ),
    )[0]


def _severity_rank(severity: str) -> int:
    severity_norm = severity.strip().lower()
    if severity_norm == "critical":
        return 0
    if severity_norm == "high":
        return 1
    if severity_norm == "warning":
        return 2
    if severity_norm == "info":
        return 3
    return 4


def _timestamp_rank(value: str) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def _build_fleet_summary(
    *,
    focus: dict[str, Any],
    fleet_status: dict[str, Any],
    fleet_alerts: dict[str, Any],
    correlation: dict[str, Any],
) -> str:
    focus_app_name = str(focus.get("focus_app_name") or focus.get("focus_app_id") or "unknown application")
    focus_alert_name = str(focus.get("focus_alert_name") or "unknown alert")
    focus_alert_type = str(focus.get("focus_alert_type") or "unknown alert type")
    affected_vessels = int(focus.get("affected_vessels_count") or 0)
    fleet_alert_count = int(fleet_alerts.get("count") or 0)
    vessels = list(fleet_status.get("vessels") or [])
    degraded_vessels = len([item for item in vessels if str(item.get("status") or "") != "healthy"])
    correlated_apps = list(correlation.get("correlated_apps") or [])
    correlated_alert_types = list(correlation.get("correlated_alert_types") or [])

    top_alert_family = correlated_alert_types[0] if correlated_alert_types else None
    top_alert_fragment = ""
    if top_alert_family:
        top_alert_fragment = (
            f" Strongest correlated alert family is "
            f"{top_alert_family.get('alert_name', 'unknown')} "
            f"affecting {top_alert_family.get('affected_vessels', 0)} vessel(s)."
        )

    return (
        f"Multi-vessel incident was selected around {focus_app_name}. "
        f"The current fleet has {fleet_alert_count} active alert(s) across "
        f"{degraded_vessels} affected vessel(s). "
        f"The focus case is {focus_alert_name} ({focus_alert_type}) spanning "
        f"{affected_vessels} vessel(s). "
        f"Cross-vessel correlation currently shows {len(correlated_apps)} app-level "
        f"pattern(s) and {len(correlated_alert_types)} alert-family pattern(s)."
        f"{top_alert_fragment}"
    )
