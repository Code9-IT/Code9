"""Deterministic Grafana dashboard builder for multi-vessel incidents."""

from __future__ import annotations

from typing import Any


DYNAMIC_FLEET_DASHBOARD_UID = "maritime_dynamic_fleet_incident"
DYNAMIC_FLEET_DASHBOARD_TITLE = "Dynamic Fleet Incident Dashboard"
DATASOURCE_UID = "timescaledb"
DEFAULT_LOOKBACK_HOURS = 24


def build_fleet_dashboard_payload(context: dict[str, Any]) -> dict[str, Any]:
    """Build one Grafana dashboard dict for the current fleet incident context."""
    lookback_hours = int(context.get("lookback_hours") or DEFAULT_LOOKBACK_HOURS)
    summary = context.get("summary") or "No summary generated."
    generated_at = context["generated_at"]
    trigger_mode = context["trigger_mode"]
    focus_app_id = context.get("focus_app_id") or "-"
    focus_app_name = context.get("focus_app_name") or focus_app_id
    focus_alert_name = context.get("focus_alert_name") or "-"
    focus_alert_type = context.get("focus_alert_type") or "-"
    focus_severity = context.get("focus_severity") or "-"
    scenario_key = context.get("scenario_key") or "multi_vessel_incident"

    summary_markdown = (
        f"## Fleet Incident Summary\n"
        f"- Scenario: `{scenario_key}`\n"
        f"- Focus application: `{focus_app_name}`\n"
        f"- Focus alert: `{focus_alert_name}`\n"
        f"- Alert type: `{focus_alert_type}`\n"
        f"- Severity: `{focus_severity}`\n"
        f"- Trigger mode: `{trigger_mode}`\n"
        f"- Generated at: `{generated_at}`\n\n"
        f"{summary}"
    )

    panels = [
        _row_panel(100, "Dynamic Fleet Incident", y=0),
        _text_panel(1, "Fleet Incident Summary", summary_markdown, x=0, y=1, w=12, h=8),
        _table_panel(2, "Fleet Incident Context", _fleet_context_sql(context), x=12, y=1, w=12, h=8),
        _table_panel(3, "Fleet Status", _fleet_status_sql(lookback_hours), x=0, y=9, w=12, h=10),
        _table_panel(
            4,
            "Correlated Applications",
            _correlated_apps_sql(lookback_hours, context.get("focus_app_id")),
            x=12,
            y=9,
            w=12,
            h=10,
        ),
        _table_panel(
            5,
            "Correlated Alert Types",
            _correlated_alert_types_sql(lookback_hours, context.get("focus_alert_name")),
            x=0,
            y=19,
            w=12,
            h=10,
        ),
        _table_panel(
            6,
            "Fleet Active Alerts",
            _fleet_alerts_sql(
                lookback_hours,
                context.get("focus_app_id"),
                context.get("focus_alert_name"),
            ),
            x=12,
            y=19,
            w=12,
            h=10,
        ),
        _table_panel(
            7,
            "Vessel Impact By Application",
            _vessel_app_impact_sql(lookback_hours, context.get("focus_app_id")),
            x=0,
            y=29,
            w=24,
            h=10,
        ),
        _table_panel(
            8,
            "Fleet Alert Timeline",
            _fleet_timeline_sql(lookback_hours, context.get("focus_app_id"), context.get("focus_alert_name")),
            x=0,
            y=39,
            w=24,
            h=8,
        ),
    ]

    return {
        "annotations": {"list": []},
        "description": (
            "Generated fleet-focused dashboard built from MCP-backed correlation and "
            "fleet alert context, then written through the Grafana HTTP API."
        ),
        "editable": True,
        "graphTooltip": 1,
        "id": None,
        "links": _dashboard_links(),
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 39,
        "tags": ["dynamic", "fleet", "incident", scenario_key],
        "templating": {"list": []},
        "time": {"from": f"now-{lookback_hours}h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": DYNAMIC_FLEET_DASHBOARD_TITLE,
        "uid": DYNAMIC_FLEET_DASHBOARD_UID,
        "version": 1,
        "fiscalYearStartMonth": 0,
        "liveNow": False,
    }


def _dashboard_links() -> list[dict[str, Any]]:
    return [
        {
            "asDropdown": False,
            "icon": "dashboard",
            "includeVars": False,
            "keepTime": True,
            "tags": [],
            "targetBlank": False,
            "title": "Fleet Overview",
            "tooltip": "Open the static fleet-wide UDS dashboard",
            "type": "link",
            "url": "/d/maritime_fleet_overview/fleet-overview",
        },
        {
            "asDropdown": False,
            "icon": "dashboard",
            "includeVars": False,
            "keepTime": True,
            "tags": [],
            "targetBlank": False,
            "title": "Alert Trends",
            "tooltip": "Open the predictive alert trend dashboard",
            "type": "link",
            "url": "/d/maritime_alert_trends/alert-trends",
        },
        {
            "asDropdown": False,
            "icon": "dashboard",
            "includeVars": False,
            "keepTime": False,
            "tags": [],
            "targetBlank": True,
            "title": "Single Incident Dashboard",
            "tooltip": "Open the single-vessel dynamic dashboard",
            "type": "link",
            "url": "http://localhost:3000/d/maritime_dynamic_incident/dynamic-incident-dashboard",
        },
        {
            "asDropdown": False,
            "icon": "external link",
            "includeVars": False,
            "keepTime": False,
            "tags": [],
            "targetBlank": True,
            "title": "Presentation Monitor",
            "tooltip": "Open the external presentation shell for the staged critical event demo",
            "type": "link",
            "url": "http://localhost:8000/api/v1/dynamic/monitor?presentation=1",
        },
        {
            "asDropdown": False,
            "icon": "external link",
            "includeVars": False,
            "keepTime": False,
            "tags": [],
            "targetBlank": True,
            "title": "AI Chat",
            "tooltip": "Ask the chat assistant about the fleet incident context",
            "type": "link",
            "url": "http://localhost:8000/api/v1/chat",
        },
    ]


def _row_panel(panel_id: int, title: str, *, y: int) -> dict[str, Any]:
    return {
        "collapsed": False,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "id": panel_id,
        "title": title,
        "type": "row",
    }


def _text_panel(panel_id: int, title: str, content: str, *, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    return {
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {"content": content, "mode": "markdown"},
        "title": title,
        "type": "text",
    }


def _table_panel(panel_id: int, title: str, raw_sql: str, *, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    return {
        "datasource": {"type": "postgres", "uid": DATASOURCE_UID},
        "fieldConfig": {"defaults": {}, "overrides": []},
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {
            "cellHeight": "sm",
            "footer": {"countRows": False, "fields": "", "reducer": ["sum"], "show": False},
            "showHeader": True,
        },
        "targets": [{"format": "table", "rawSql": raw_sql, "refId": "A"}],
        "title": title,
        "type": "table",
    }


def _fleet_context_sql(context: dict[str, Any]) -> str:
    values = [
        ("Generated At", context["generated_at"]),
        ("Trigger Mode", context["trigger_mode"]),
        ("Scenario", context.get("scenario_key") or "multi_vessel_incident"),
        ("Focus App", context.get("focus_app_name") or context.get("focus_app_id") or "-"),
        ("Focus App ID", context.get("focus_app_id") or "-"),
        ("Focus Alert", context.get("focus_alert_name") or "-"),
        ("Alert Type", context.get("focus_alert_type") or "-"),
        ("Severity", context.get("focus_severity") or "-"),
        ("Affected Vessels", context.get("affected_vessels_count") or 0),
        ("Fleet Alerts", context.get("fleet_alert_count") or 0),
        ("Used Tools", ", ".join(context.get("used_tools") or [])),
    ]
    rows = ", ".join(f"({_sql_literal(label)}, {_sql_literal(value)})" for label, value in values)
    return 'SELECT * FROM (VALUES ' + rows + ') AS fleet_context("Field", "Value")'


def _fleet_status_sql(lookback_hours: int) -> str:
    return f"""
WITH active_alerts AS (
    SELECT
        u.id AS vessel_id,
        u.name AS vessel_name,
        u.imo_nr,
        COUNT(*)::int AS active_alert_count,
        COUNT(DISTINCT al.application_id)::int AS affected_app_count,
        COUNT(*) FILTER (WHERE LOWER(COALESCE(al.severity, 'info')) = 'critical')::int AS critical_alert_count,
        MAX(COALESCE(al.received_at, al.starts_at)) AS latest_alert_at
    FROM udslocations u
    LEFT JOIN alerts al
      ON al.uds_location_id = u.id
     AND COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
     AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
     AND (al.ends_at IS NULL OR al.ends_at > NOW())
    GROUP BY u.id, u.name, u.imo_nr
)
SELECT
    vessel_name AS "Vessel",
    imo_nr AS "IMO",
    CASE
        WHEN critical_alert_count > 0 THEN 'critical'
        WHEN active_alert_count > 0 THEN 'degraded'
        ELSE 'healthy'
    END AS "Status",
    active_alert_count AS "Active Alerts",
    affected_app_count AS "Affected Apps",
    latest_alert_at AS "Latest Alert"
FROM active_alerts
ORDER BY
    CASE
        WHEN critical_alert_count > 0 THEN 0
        WHEN active_alert_count > 0 THEN 1
        ELSE 2
    END,
    active_alert_count DESC,
    vessel_name ASC;
""".strip()


def _correlated_apps_sql(lookback_hours: int, focus_app_id: str | None) -> str:
    return f"""
SELECT
    CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(focus_app_id or '')}) THEN 'focus' ELSE '' END AS "Focus",
    a.name AS "Application",
    a.external_id AS "App ID",
    COUNT(DISTINCT u.imo_nr)::int AS "Affected Vessels",
    STRING_AGG(DISTINCT u.name || ' (' || u.imo_nr || ')', ', ' ORDER BY u.name || ' (' || u.imo_nr || ')') AS "Vessels",
    STRING_AGG(DISTINCT al.alert_name, ', ' ORDER BY al.alert_name) AS "Alert Names"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
JOIN applications a ON a.id = al.application_id
WHERE COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW())
GROUP BY a.external_id, a.name
HAVING COUNT(DISTINCT u.imo_nr) > 1
ORDER BY
    CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(focus_app_id or '')}) THEN 0 ELSE 1 END,
    COUNT(DISTINCT u.imo_nr) DESC,
    a.name ASC;
""".strip()


def _correlated_alert_types_sql(lookback_hours: int, focus_alert_name: str | None) -> str:
    return f"""
SELECT
    CASE WHEN LOWER(al.alert_name) = LOWER({_sql_literal(focus_alert_name or '')}) THEN 'focus' ELSE '' END AS "Focus",
    al.alert_name AS "Alert",
    COALESCE(al.alert_type, '-') AS "Alert Type",
    COUNT(DISTINCT u.imo_nr)::int AS "Affected Vessels",
    STRING_AGG(DISTINCT u.name || ' (' || u.imo_nr || ')', ', ' ORDER BY u.name || ' (' || u.imo_nr || ')') AS "Vessels",
    STRING_AGG(DISTINCT COALESCE(a.name, '-'), ', ' ORDER BY COALESCE(a.name, '-')) AS "Affected Apps"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW())
GROUP BY al.alert_name, al.alert_type
HAVING COUNT(DISTINCT u.imo_nr) > 1
ORDER BY
    CASE WHEN LOWER(al.alert_name) = LOWER({_sql_literal(focus_alert_name or '')}) THEN 0 ELSE 1 END,
    COUNT(DISTINCT u.imo_nr) DESC,
    al.alert_name ASC;
""".strip()


def _fleet_alerts_sql(lookback_hours: int, focus_app_id: str | None, focus_alert_name: str | None) -> str:
    return f"""
SELECT
    CASE
        WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or '')})
          OR LOWER(al.alert_name) = LOWER({_sql_literal(focus_alert_name or '')}) THEN 'focus'
        ELSE ''
    END AS "Focus",
    u.name AS "Vessel",
    u.imo_nr AS "IMO",
    COALESCE(a.name, 'unknown') AS "Application",
    COALESCE(a.external_id, '-') AS "App ID",
    al.alert_name AS "Alert",
    COALESCE(al.alert_type, '-') AS "Type",
    COALESCE(al.severity, '-') AS "Severity",
    COALESCE(al.status, 'firing') AS "Status",
    COALESCE(al.received_at, al.starts_at) AS "Received"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW())
ORDER BY
    CASE
        WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or '')})
          OR LOWER(al.alert_name) = LOWER({_sql_literal(focus_alert_name or '')}) THEN 0
        ELSE 1
    END,
    CASE LOWER(COALESCE(al.severity, 'info'))
        WHEN 'critical' THEN 0
        WHEN 'high' THEN 1
        WHEN 'warning' THEN 2
        ELSE 3
    END,
    COALESCE(al.received_at, al.starts_at) DESC
LIMIT 100;
""".strip()


def _vessel_app_impact_sql(lookback_hours: int, focus_app_id: str | None) -> str:
    return f"""
SELECT
    CASE WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or '')}) THEN 'focus' ELSE '' END AS "Focus",
    u.name AS "Vessel",
    u.imo_nr AS "IMO",
    COALESCE(a.name, 'unknown') AS "Application",
    COALESCE(a.external_id, '-') AS "App ID",
    COUNT(*)::int AS "Active Alerts",
    STRING_AGG(DISTINCT al.alert_name, ', ' ORDER BY al.alert_name) AS "Alert Names",
    MAX(COALESCE(al.received_at, al.starts_at)) AS "Latest Alert"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW())
GROUP BY u.name, u.imo_nr, a.name, a.external_id
ORDER BY
    CASE WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or '')}) THEN 0 ELSE 1 END,
    COUNT(*) DESC,
    u.name ASC,
    COALESCE(a.name, 'unknown') ASC;
""".strip()


def _fleet_timeline_sql(lookback_hours: int, focus_app_id: str | None, focus_alert_name: str | None) -> str:
    return f"""
SELECT
    COALESCE(al.received_at, al.starts_at) AS "Time",
    u.name AS "Vessel",
    u.imo_nr AS "IMO",
    COALESCE(a.name, 'unknown') AS "Application",
    COALESCE(a.external_id, '-') AS "App ID",
    al.alert_name AS "Alert",
    COALESCE(al.severity, '-') AS "Severity",
    CASE
        WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or '')})
          OR LOWER(al.alert_name) = LOWER({_sql_literal(focus_alert_name or '')}) THEN 'focus'
        ELSE ''
    END AS "Focus"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
ORDER BY COALESCE(al.received_at, al.starts_at) DESC
LIMIT 120;
""".strip()


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    text = str(value).replace("'", "''")
    return f"'{text}'"
