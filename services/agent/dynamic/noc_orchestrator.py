"""Orchestration flow for the dynamic NOC support dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from db import get_pool
from dynamic.grafana_client import GrafanaClient
from dynamic.mcp_client import MCPClient
from dynamic.noc_dashboard_builder import (
    DYNAMIC_NOC_DASHBOARD_UID,
    build_noc_dashboard_payload,
)
from dynamic.orchestrator import (
    _app_display_name,
    _mark_tool,
    _pick_focus_app,
    _select_alert,
    _select_app_status,
)


LOOKBACK_HOURS = 72
NOC_DASHBOARD_SLUG = "dynamic-noc-support-dashboard"
DYNAMIC_FOLDER_UID = "maritime-dynamic-dashboards"
DYNAMIC_FOLDER_TITLE = "Dynamic Dashboards"
NOC_SUPPORT_METRICS = [
    "service_up",
    "health_check_status",
    "reporting_stale",
    "sync_delayed",
    "last_sync_age_seconds",
    "process_cpu_usage",
    "http_error_rate_5xx",
    "http_request_duration_p95",
]


@dataclass
class NOCTriggerRequest:
    mode: str
    dry_run: bool
    vessel_imo: str | None = None
    app_external_id: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    source_alert_fingerprint: str | None = None


class DynamicNOCDashboardOrchestrator:
    """Glue code between vessel support context and Grafana upsert."""

    def __init__(
        self,
        *,
        mcp_client: MCPClient | None = None,
        grafana_client: GrafanaClient | None = None,
    ) -> None:
        self.mcp_client = mcp_client or MCPClient()
        self.grafana_client = grafana_client or GrafanaClient()

    async def trigger(self, request: NOCTriggerRequest) -> dict[str, Any]:
        resolved, used_tools = await self._resolve_request(request)
        context_bundle, context_tools = await self._collect_context(resolved)
        for tool_name in context_tools:
            _mark_tool(used_tools, tool_name)

        await self._load_metric_history(
            resolved["vessel_imo"],
            resolved.get("app_external_id"),
            NOC_SUPPORT_METRICS,
            used_tools,
        )

        generated_at = datetime.now(timezone.utc).isoformat()
        summary = _build_noc_summary(
            vessel=context_bundle["vessel"],
            applications=list(context_bundle["applications"] or []),
            selected_app_status=context_bundle["selected_app_status"],
            selected_alert=context_bundle["selected_alert"],
            logs=context_bundle["logs"],
        )
        dashboard_context = {
            "generated_at": generated_at,
            "trigger_mode": request.mode,
            "scenario_key": "noc_support_case",
            "vessel_imo": resolved["vessel_imo"],
            "vessel_name": _vessel_display_name(context_bundle["vessel"]),
            "focus_app_id": resolved.get("app_external_id"),
            "focus_app_name": _app_display_name(context_bundle["selected_app_status"]),
            "focus_alert_name": resolved.get("alert_name"),
            "focus_severity": resolved.get("severity"),
            "metric_names": list(NOC_SUPPORT_METRICS),
            "used_tools": used_tools,
            "lookback_hours": LOOKBACK_HOURS,
            "summary": summary,
        }
        dashboard_payload = build_noc_dashboard_payload(dashboard_context)

        grafana_result: dict[str, Any] | None = None
        if not request.dry_run:
            await self.grafana_client.ensure_folder(
                title=DYNAMIC_FOLDER_TITLE,
                uid=DYNAMIC_FOLDER_UID,
            )
            grafana_result = await self.grafana_client.upsert_dashboard(
                dashboard_payload,
                folder_uid=DYNAMIC_FOLDER_UID,
                message=(
                    "Dynamic NOC support update: "
                    f"{resolved['vessel_imo']} / {resolved.get('app_external_id') or 'vessel'}"
                ),
            )

        await self._log_run(
            trigger_mode=request.mode,
            source_alert_fingerprint=resolved.get("source_alert_fingerprint"),
            vessel_imo=resolved["vessel_imo"],
            app_external_id=resolved.get("app_external_id"),
            alert_name=resolved.get("alert_name"),
            severity=resolved.get("severity"),
            summary=summary,
            used_tools=used_tools,
            dashboard_json=dashboard_payload,
            dry_run=request.dry_run,
        )

        response: dict[str, Any] = {
            "dashboard_uid": DYNAMIC_NOC_DASHBOARD_UID,
            "dashboard_url": self.grafana_client.dashboard_url(
                DYNAMIC_NOC_DASHBOARD_UID,
                slug=NOC_DASHBOARD_SLUG,
            ),
            "scenario_key": "noc_support_case",
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

    async def _resolve_request(self, request: NOCTriggerRequest) -> tuple[dict[str, Any], list[str]]:
        if request.mode == "explicit_context":
            if not request.vessel_imo:
                raise ValueError("vessel_imo is required for explicit_context mode")
            return (
                {
                    "vessel_imo": request.vessel_imo,
                    "app_external_id": request.app_external_id,
                    "alert_name": request.alert_name,
                    "severity": request.severity,
                    "source_alert_fingerprint": request.source_alert_fingerprint,
                },
                [],
            )

        if request.mode != "latest_alerted_vessel":
            raise ValueError(f"Unsupported NOC trigger mode: {request.mode}")

        fleet_alerts = await self.mcp_client.get_fleet_alerts(hours=LOOKBACK_HOURS)
        alerts = list(fleet_alerts.get("alerts") or [])
        if not alerts:
            raise LookupError("No active fleet alerts found for latest_alerted_vessel mode")

        latest = max(
            alerts,
            key=lambda item: (
                str(item.get("received_at") or item.get("starts_at") or ""),
                str(item.get("starts_at") or ""),
            ),
        )
        return (
            {
                "vessel_imo": latest.get("imo_nr"),
                "app_external_id": latest.get("app_external_id"),
                "alert_name": latest.get("alert_name"),
                "severity": latest.get("severity"),
                "source_alert_fingerprint": latest.get("fingerprint"),
            },
            ["get_fleet_alerts"],
        )

    async def _collect_context(self, resolved: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        used_tools: list[str] = []
        vessel_status = await self.mcp_client.get_vessel_app_status(resolved["vessel_imo"])
        _mark_tool(used_tools, "get_vessel_app_status")
        vessel_alerts = await self.mcp_client.get_vessel_alerts(resolved["vessel_imo"], hours=LOOKBACK_HOURS)
        _mark_tool(used_tools, "get_vessel_alerts")
        operational_snapshot = await self.mcp_client.get_operational_snapshot(resolved["vessel_imo"])
        _mark_tool(used_tools, "get_operational_snapshot")
        await self.mcp_client.get_incident_timeline(resolved["vessel_imo"], hours=LOOKBACK_HOURS)
        _mark_tool(used_tools, "get_incident_timeline")

        selected_alert = _select_alert(
            alerts=list(vessel_alerts.get("alerts") or []),
            app_external_id=resolved.get("app_external_id"),
            alert_name=resolved.get("alert_name"),
            source_alert_fingerprint=resolved.get("source_alert_fingerprint"),
        )

        if not resolved.get("app_external_id"):
            resolved["app_external_id"] = (
                (selected_alert or {}).get("app_external_id")
                or _pick_focus_app(vessel_status, operational_snapshot)
            )
        if not resolved.get("alert_name"):
            resolved["alert_name"] = (selected_alert or {}).get("alert_name")
        if not resolved.get("severity"):
            resolved["severity"] = (selected_alert or {}).get("severity")
        if not resolved.get("source_alert_fingerprint"):
            resolved["source_alert_fingerprint"] = (selected_alert or {}).get("fingerprint")

        selected_app_status = _select_app_status(
            applications=list(vessel_status.get("applications") or []),
            app_external_id=resolved.get("app_external_id"),
        )

        if resolved.get("app_external_id"):
            logs = await self.mcp_client.get_app_logs(
                resolved["vessel_imo"],
                resolved["app_external_id"],
                hours=LOOKBACK_HOURS,
                limit=100,
            )
            _mark_tool(used_tools, "get_app_logs")
        else:
            logs = {"logs": []}

        return (
            {
                "vessel": vessel_status.get("vessel") or operational_snapshot.get("vessel") or {},
                "applications": list(vessel_status.get("applications") or []),
                "selected_alert": selected_alert,
                "selected_app_status": selected_app_status,
                "logs": logs,
            },
            used_tools,
        )

    async def _load_metric_history(
        self,
        vessel_imo: str,
        app_external_id: str | None,
        metric_names: list[str],
        used_tools: list[str],
    ) -> None:
        if not app_external_id:
            return
        for metric_name in metric_names:
            await self.mcp_client.get_app_metric_history(
                vessel_imo,
                app_external_id,
                metric_name,
                hours=LOOKBACK_HOURS,
            )
            _mark_tool(used_tools, "get_app_metric_history")

    async def _log_run(
        self,
        *,
        trigger_mode: str,
        source_alert_fingerprint: str | None,
        vessel_imo: str,
        app_external_id: str | None,
        alert_name: str | None,
        severity: str | None,
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
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb, $12)
                """,
                trigger_mode,
                source_alert_fingerprint,
                vessel_imo,
                app_external_id,
                alert_name,
                severity,
                "noc_support_case",
                DYNAMIC_NOC_DASHBOARD_UID,
                summary,
                json.dumps(used_tools),
                json.dumps(dashboard_json),
                dry_run,
            )


def _vessel_display_name(vessel: dict[str, Any]) -> str:
    return str(vessel.get("name") or vessel.get("imo_nr") or "Unknown vessel")


def _build_noc_summary(
    *,
    vessel: dict[str, Any],
    applications: list[dict[str, Any]],
    selected_app_status: dict[str, Any] | None,
    selected_alert: dict[str, Any] | None,
    logs: dict[str, Any],
) -> str:
    vessel_name = _vessel_display_name(vessel)
    focus_app_name = _app_display_name(selected_app_status) or "no focused application"
    app_status_label = str((selected_app_status or {}).get("status") or "unknown").lower()
    affected_apps = len(
        [
            app
            for app in applications
            if str(app.get("status") or "").strip().lower() not in {"healthy", ""}
            or int(app.get("active_alert_count") or 0) > 0
        ]
    )
    connectivity_apps = len(
        [
            app
            for app in applications
            if str(app.get("status") or "").strip().lower() in {"connectivity", "stale"}
        ]
    )
    active_alerts = sum(int(app.get("active_alert_count") or 0) for app in applications)

    latest_log = next(iter(logs.get("logs") or []), None)
    latest_log_text = ""
    if latest_log:
        latest_log_text = (
            f" Latest support signal: {latest_log.get('level', 'info')} from "
            f"{latest_log.get('source', 'unknown source')} saying "
            f"'{latest_log.get('message', '')}'."
        )

    alert_fragment = ""
    if selected_alert:
        alert_fragment = (
            f" Focus alert is {selected_alert.get('alert_name', 'unknown alert')}"
            f" with severity {selected_alert.get('severity', 'unknown')}."
        )

    return (
        f"NOC support case was generated for {vessel_name}. "
        f"The vessel currently has {affected_apps} affected application(s), "
        f"{active_alerts} active alert(s), and {connectivity_apps} application(s) "
        f"with connectivity-related symptoms. "
        f"Current focus is {focus_app_name} with status {app_status_label}."
        f"{alert_fragment}{latest_log_text}"
    )
