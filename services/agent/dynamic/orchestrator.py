"""Dynamic dashboard orchestrator.

Two-agent pipeline:
  Agent 1 — Context gathering via MCP tools (get_vessel_app_status,
             get_vessel_alerts, get_app_metric_history, get_app_logs).
  Agent 2 — Dashboard generation: classify scenario → build JSON → push to
             Grafana.

Both agents are deterministic (no LLM calls) — they follow fixed logic so
the result is fast, predictable, and demo-stable.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field

import asyncpg

from .dashboard_builder import DASHBOARD_UID, build_dashboard
from .grafana_client import upsert_dashboard
from .mcp_client import call_tool
from .scenario_selector import SCENARIO_TITLES, classify_scenario


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

@dataclass
class DynamicDashboardResult:
    run_id: str
    vessel_imo: str
    app_external_id: str
    alert_name: str
    scenario_key: str
    scenario_title: str
    dashboard_uid: str
    grafana_url: str
    summary: str
    used_tools: list[str] = field(default_factory=list)
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Agent 1 — context gathering
# ---------------------------------------------------------------------------

async def _gather_context(vessel_imo: str, app_external_id: str, alert_name: str) -> tuple[str, list[str]]:
    """Call MCP tools to collect incident context.

    Returns:
        A tuple of (summary_markdown, used_tool_names).
    """
    used: list[str] = []
    parts: list[str] = []

    # Tool 1: vessel-wide app status
    try:
        status = await call_tool("get_vessel_app_status", {"vessel_id": vessel_imo})
        used.append("get_vessel_app_status")
        apps = status.get("applications", [])
        affected = next(
            (a for a in apps if a.get("app_external_id") == app_external_id),
            None,
        )
        if affected:
            app_status = affected.get("status", "unknown")
            alert_count = affected.get("active_alert_count", "?")
            parts.append(
                f"**App status:** {app_external_id} is `{app_status}` "
                f"with {alert_count} active alert(s)."
            )
    except Exception as exc:
        parts.append(f"*App status unavailable: {exc}*")

    # Tool 2: active alerts
    try:
        alerts_resp = await call_tool(
            "get_vessel_alerts",
            {"vessel_id": vessel_imo, "hours": 6},
        )
        used.append("get_vessel_alerts")
        alerts = alerts_resp.get("alerts", [])
        related = [a for a in alerts if a.get("app_external_id") == app_external_id]
        if related:
            lines = []
            for a in related[:5]:
                lines.append(
                    f"- **{a.get('alert_name', '?')}** [{a.get('severity', '?')}] "
                    f"since {a.get('starts_at', '?')}"
                )
            parts.append("**Related alerts (last 6 h):**\n" + "\n".join(lines))
    except Exception as exc:
        parts.append(f"*Alerts unavailable: {exc}*")

    # Tool 3: metric history — requires vessel_id, app, metric
    try:
        metrics_resp = await call_tool(
            "get_app_metric_history",
            {"vessel_id": vessel_imo, "app": app_external_id, "metric": "service_up", "hours": 1},
        )
        used.append("get_app_metric_history")
        series = metrics_resp.get("series", [])
        if series:
            sample = series[0]
            parts.append(
                f"**Latest metric:** {metrics_resp.get('metric', '?')} = "
                f"{sample.get('value', '?')} at {sample.get('time', '?')}"
            )
    except Exception as exc:
        parts.append(f"*Metrics unavailable: {exc}*")

    # Tool 4: recent logs — requires vessel_id, app
    try:
        logs_resp = await call_tool(
            "get_app_logs",
            {"vessel_id": vessel_imo, "app": app_external_id, "limit": 5},
        )
        used.append("get_app_logs")
        logs = logs_resp.get("logs", [])
        if logs:
            lines = []
            for lg in logs[:3]:
                lines.append(
                    f"- `[{lg.get('level', '?')}]` {lg.get('message', '')} "
                    f"({lg.get('logged_at', '?')})"
                )
            parts.append("**Recent log entries:**\n" + "\n".join(lines))
    except Exception as exc:
        parts.append(f"*Logs unavailable: {exc}*")

    summary = "\n\n".join(parts) if parts else f"Alert `{alert_name}` triggered on `{app_external_id}`."
    return summary, used


# ---------------------------------------------------------------------------
# Agent 2 — dashboard generation
# ---------------------------------------------------------------------------

async def _log_run(
    pool: asyncpg.Pool,
    *,
    run_id: str,
    trigger_mode: str,
    vessel_imo: str,
    app_external_id: str,
    alert_name: str | None,
    severity: str | None,
    scenario_key: str,
    dashboard_uid: str,
    summary: str,
    used_tools: list[str],
    dashboard_json: dict,
    dry_run: bool,
    fingerprint: str | None = None,
) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO dynamic_dashboard_runs (
                id, trigger_mode, source_alert_fingerprint,
                vessel_imo, app_external_id, alert_name, severity,
                scenario_key, dashboard_uid, summary,
                used_tools_json, dashboard_json, dry_run
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13
            )
            """,
            uuid.UUID(run_id),
            trigger_mode,
            fingerprint,
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


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def run(
    pool: asyncpg.Pool,
    *,
    vessel_imo: str,
    app_external_id: str,
    alert_name: str = "",
    alert_type: str = "",
    severity: str = "",
    trigger_mode: str = "api",
    dry_run: bool = False,
    fingerprint: str | None = None,
) -> DynamicDashboardResult:
    """Full two-agent pipeline.

    Args:
        pool: asyncpg connection pool (from the agent service DB).
        vessel_imo: IMO number, e.g. ``IMO9300001``.
        app_external_id: Application external ID, e.g. ``data-quality-processor``.
        alert_name: Name of the triggering alert.
        alert_type: Alert type string (used for scenario classification).
        severity: Alert severity string.
        trigger_mode: Free-form tag stored in the run log.
        dry_run: If True, build the dashboard but do NOT push to Grafana.
        fingerprint: Optional alert fingerprint for deduplication tracking.

    Returns:
        :class:`DynamicDashboardResult` with all outcome metadata.
    """
    run_id = str(uuid.uuid4())

    # --- Agent 1: gather context ---
    summary, used_tools = await _gather_context(vessel_imo, app_external_id, alert_name)

    # --- Agent 2: classify + build + push ---
    scenario_key = classify_scenario(alert_name, alert_type)
    scenario_title = SCENARIO_TITLES.get(scenario_key, "Incident")

    dashboard_json = build_dashboard(
        scenario_key=scenario_key,
        vessel_imo=vessel_imo,
        app_external_id=app_external_id,
        summary=summary,
        alert_name=alert_name,
        severity=severity,
    )

    grafana_url = ""
    if not dry_run:
        try:
            resp = await upsert_dashboard(dashboard_json)
            grafana_url = resp.get("url", f"/d/{DASHBOARD_UID}")
        except Exception as exc:
            grafana_url = f"/d/{DASHBOARD_UID}"
            summary += f"\n\n*Grafana push failed: {exc}*"

    # --- Log run to DB ---
    try:
        await _log_run(
            pool,
            run_id=run_id,
            trigger_mode=trigger_mode,
            vessel_imo=vessel_imo,
            app_external_id=app_external_id,
            alert_name=alert_name or None,
            severity=severity or None,
            scenario_key=scenario_key,
            dashboard_uid=DASHBOARD_UID,
            summary=summary,
            used_tools=used_tools,
            dashboard_json=dashboard_json,
            dry_run=dry_run,
            fingerprint=fingerprint,
        )
    except Exception as exc:
        print(f"[dynamic] WARNING: failed to log run {run_id}: {exc}")

    return DynamicDashboardResult(
        run_id=run_id,
        vessel_imo=vessel_imo,
        app_external_id=app_external_id,
        alert_name=alert_name,
        scenario_key=scenario_key,
        scenario_title=scenario_title,
        dashboard_uid=DASHBOARD_UID,
        grafana_url=grafana_url,
        summary=summary,
        used_tools=used_tools,
        dry_run=dry_run,
    )
