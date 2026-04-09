"""Orchestration flow for the dynamic incident dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from db import get_pool
from dynamic.dashboard_builder import DYNAMIC_DASHBOARD_UID, build_dashboard_payload
from dynamic.grafana_client import GrafanaClient
from dynamic.mcp_client import MCPClient
from dynamic.scenario_selector import metric_names_for_scenario, select_scenario


LOOKBACK_HOURS = 24


@dataclass
class TriggerRequest:
    mode: str
    dry_run: bool
    vessel_imo: str | None = None
    app_external_id: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    source_alert_fingerprint: str | None = None


class DynamicDashboardOrchestrator:
    """Glue code between MCP context, scenario selection, and Grafana upsert."""

    def __init__(
        self,
        *,
        mcp_client: MCPClient | None = None,
        grafana_client: GrafanaClient | None = None,
    ) -> None:
        self.mcp_client = mcp_client or MCPClient()
        self.grafana_client = grafana_client or GrafanaClient()

    async def trigger(self, request: TriggerRequest) -> dict[str, Any]:
        resolved, used_tools = await self._resolve_request(request)
        context_bundle, context_tools = await self._collect_context(resolved)
        for tool_name in context_tools:
            _mark_tool(used_tools, tool_name)
        scenario_key = select_scenario(
            alert=context_bundle["selected_alert"],
            app_status=context_bundle["selected_app_status"],
        )
        metric_names = metric_names_for_scenario(scenario_key)
        await self._load_metric_history(
            resolved["vessel_imo"],
            resolved["app_external_id"],
            metric_names,
            used_tools,
        )

        generated_at = datetime.now(timezone.utc).isoformat()
        summary = _build_summary(
            vessel=context_bundle["vessel"],
            app_status=context_bundle["selected_app_status"],
            selected_alert=context_bundle["selected_alert"],
            logs=context_bundle["logs"],
            scenario_key=scenario_key,
        )
        dashboard_context = {
            "generated_at": generated_at,
            "trigger_mode": request.mode,
            "vessel_imo": resolved["vessel_imo"],
            "app_external_id": resolved["app_external_id"],
            "app_name": _app_display_name(context_bundle["selected_app_status"]),
            "alert_name": resolved["alert_name"],
            "severity": resolved["severity"],
            "source_alert_fingerprint": resolved.get("source_alert_fingerprint"),
            "scenario_key": scenario_key,
            "summary": summary,
            "used_tools": used_tools,
            "lookback_hours": LOOKBACK_HOURS,
            "metric_names": metric_names,
        }
        dashboard_payload = build_dashboard_payload(dashboard_context)

        grafana_result: dict[str, Any] | None = None
        if not request.dry_run:
            grafana_result = await self.grafana_client.upsert_dashboard(
                dashboard_payload,
                message=f"Dynamic incident update: {scenario_key} / {resolved['vessel_imo']}",
            )

        await self._log_run(
            trigger_mode=request.mode,
            source_alert_fingerprint=resolved.get("source_alert_fingerprint"),
            vessel_imo=resolved["vessel_imo"],
            app_external_id=resolved.get("app_external_id"),
            alert_name=resolved.get("alert_name"),
            severity=resolved.get("severity"),
            scenario_key=scenario_key,
            dashboard_uid=DYNAMIC_DASHBOARD_UID,
            summary=summary,
            used_tools=used_tools,
            dashboard_json=dashboard_payload,
            dry_run=request.dry_run,
        )

        response: dict[str, Any] = {
            "dashboard_uid": DYNAMIC_DASHBOARD_UID,
            "dashboard_url": self.grafana_client.dashboard_url(DYNAMIC_DASHBOARD_UID),
            "scenario_key": scenario_key,
            "trigger_mode": request.mode,
            "generated_at": generated_at,
            "summary": summary,
            "used_tools": used_tools,
            "dry_run": request.dry_run,
            "grafana_result": grafana_result,
        }
        # In dry-run mode the caller never sees a Grafana write, so return
        # the generated payload inline. This is the fallback Codex asked for:
        # if Grafana is unreachable on demo day we can still show the JSON
        # the orchestrator produced.
        if request.dry_run:
            response["dashboard_json"] = dashboard_payload
        return response

    async def status(self) -> dict[str, Any]:
        pool = get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT created_at, trigger_mode, vessel_imo, app_external_id, alert_name,
                       severity, scenario_key, dashboard_uid, dry_run
                FROM dynamic_dashboard_runs
                ORDER BY created_at DESC
                LIMIT 10
                """
            )

        grafana_ok = False
        mcp_ok = False
        try:
            await self.grafana_client.health()
            grafana_ok = True
        except Exception as exc:  # pragma: no cover
            print(f"[agent] Dynamic status Grafana health failed: {exc}")
        try:
            await self.mcp_client.health()
            mcp_ok = True
        except Exception as exc:  # pragma: no cover
            print(f"[agent] Dynamic status MCP health failed: {exc}")

        recent_runs = []
        for row in rows:
            item = dict(row)
            item["created_at"] = row["created_at"].isoformat()
            recent_runs.append(item)

        return {
            "status": "ok" if grafana_ok and mcp_ok else "degraded",
            "dashboard_uid": DYNAMIC_DASHBOARD_UID,
            "dashboard_url": self.grafana_client.dashboard_url(DYNAMIC_DASHBOARD_UID),
            "grafana_reachable": grafana_ok,
            "mcp_reachable": mcp_ok,
            "recent_runs": recent_runs,
        }

    async def _resolve_request(self, request: TriggerRequest) -> tuple[dict[str, Any], list[str]]:
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

        if request.mode != "latest_firing_alert":
            raise ValueError(f"Unsupported trigger mode: {request.mode}")

        fleet_alerts = await self.mcp_client.get_fleet_alerts(hours=LOOKBACK_HOURS)
        alerts = list(fleet_alerts.get("alerts") or [])
        if not alerts:
            raise LookupError("No active fleet alerts found for latest_firing_alert mode")

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
                # Preserve the alert's fingerprint so _select_alert can use the
                # fast-path lookup and the audit row records which alert this
                # run was bound to.
                "source_alert_fingerprint": latest.get("fingerprint"),
            },
            ["get_fleet_alerts"],
        )

    async def _collect_context(
        self,
        resolved: dict[str, Any],
    ) -> tuple[dict[str, Any], list[str]]:
        used_tools: list[str] = []
        vessel_status = await self.mcp_client.get_vessel_app_status(resolved["vessel_imo"])
        _mark_tool(used_tools, "get_vessel_app_status")
        vessel_alerts = await self.mcp_client.get_vessel_alerts(resolved["vessel_imo"], hours=LOOKBACK_HOURS)
        _mark_tool(used_tools, "get_vessel_alerts")
        operational_snapshot = await self.mcp_client.get_operational_snapshot(resolved["vessel_imo"])
        _mark_tool(used_tools, "get_operational_snapshot")

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

        timeline = await self.mcp_client.get_incident_timeline(
            resolved["vessel_imo"],
            hours=LOOKBACK_HOURS,
            app=resolved.get("app_external_id"),
        )
        _mark_tool(used_tools, "get_incident_timeline")

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
                "selected_alert": selected_alert,
                "selected_app_status": selected_app_status,
                "timeline": timeline,
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
        scenario_key: str,
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
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::jsonb, $11::jsonb, $12)
                """,
                trigger_mode,
                source_alert_fingerprint,
                vessel_imo,
                app_external_id,
                alert_name,
                severity,
                scenario_key,
                dashboard_uid,
                summary,
                json.dumps(used_tools),
                json.dumps(dashboard_json),
                dry_run,
            )


def _mark_tool(used_tools: list[str], name: str) -> None:
    if name not in used_tools:
        used_tools.append(name)


def _pick_focus_app(vessel_status: dict[str, Any], operational_snapshot: dict[str, Any]) -> str | None:
    applications = list(vessel_status.get("applications") or operational_snapshot.get("applications") or [])
    ranked = sorted(
        applications,
        key=lambda item: _app_rank(str(item.get("status") or "")),
    )
    if not ranked:
        return None
    return ranked[0].get("external_id")


def _app_rank(status: str) -> int:
    status_norm = status.strip().lower()
    if status_norm == "down":
        return 0
    if status_norm in {"critical", "degraded"}:
        return 1
    if status_norm in {"stale", "connectivity"}:
        return 2
    if status_norm == "unknown":
        return 3
    return 4


def _select_alert(
    *,
    alerts: list[dict[str, Any]],
    app_external_id: str | None,
    alert_name: str | None,
    source_alert_fingerprint: str | None,
) -> dict[str, Any] | None:
    if source_alert_fingerprint:
        for alert in alerts:
            if str(alert.get("fingerprint") or "") == source_alert_fingerprint:
                return alert

    def matches(alert: dict[str, Any]) -> bool:
        if app_external_id and str(alert.get("app_external_id") or "").lower() != app_external_id.lower():
            return False
        if alert_name and str(alert.get("alert_name") or "").lower() != alert_name.lower():
            return False
        return True

    filtered = [alert for alert in alerts if matches(alert)]
    if filtered:
        return filtered[0]

    # If the caller specified app_external_id or alert_name and nothing
    # matched, do NOT silently substitute a different alert -- that caused
    # the runtime_pressure / HighLatency mismatch where the request said
    # ResourcePressure but the summary described an unrelated alert that
    # happened to be at index 0. Only fall back to alerts[0] when the
    # caller gave no selection criteria at all.
    if app_external_id or alert_name:
        return None
    return alerts[0] if alerts else None


def _select_app_status(*, applications: list[dict[str, Any]], app_external_id: str | None) -> dict[str, Any] | None:
    if not app_external_id:
        return applications[0] if applications else None
    for application in applications:
        if str(application.get("external_id") or "").lower() == app_external_id.lower():
            return application
    return applications[0] if applications else None


def _app_display_name(app_status: dict[str, Any] | None) -> str | None:
    if not app_status:
        return None
    return str(app_status.get("name") or app_status.get("external_id") or "").strip() or None


def _build_summary(
    *,
    vessel: dict[str, Any],
    app_status: dict[str, Any] | None,
    selected_alert: dict[str, Any] | None,
    logs: dict[str, Any],
    scenario_key: str,
) -> str:
    vessel_name = str(vessel.get("name") or vessel.get("imo_nr") or "Unknown vessel")
    app_name = _app_display_name(app_status) or "unknown application"
    app_status_label = str((app_status or {}).get("status") or "unknown").lower()
    active_alerts = int((app_status or {}).get("active_alert_count") or 0)
    latest_log = next(iter(logs.get("logs") or []), None)
    latest_log_text = ""
    if latest_log:
        latest_log_text = (
            f" Latest log signal: {latest_log.get('level', 'info')} from "
            f"{latest_log.get('source', 'unknown source')} saying "
            f"'{latest_log.get('message', '')}'."
        )

    alert_fragment = ""
    if selected_alert:
        alert_fragment = (
            f" The current alert is {selected_alert.get('alert_name', 'unknown alert')}"
            f" with severity {selected_alert.get('severity', 'unknown')}."
        )

    return (
        f"{scenario_key.replace('_', ' ').title()} was selected for {app_name} on {vessel_name}. "
        f"The current application status is {app_status_label}, with {active_alerts} active alert(s)."
        f"{alert_fragment}{latest_log_text}"
    )
