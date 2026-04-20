"""Deterministic Grafana dashboard builder for dynamic NOC support cases."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote


DYNAMIC_NOC_DASHBOARD_UID = "maritime_dynamic_noc_support"
DYNAMIC_NOC_DASHBOARD_TITLE = "Dynamic NOC Support Dashboard"
DATASOURCE_UID = "timescaledb"
DEFAULT_LOOKBACK_HOURS = 72


def build_noc_dashboard_payload(context: dict[str, Any]) -> dict[str, Any]:
    vessel_imo = context["vessel_imo"]
    vessel_name = context.get("vessel_name") or vessel_imo
    focus_app_id = context.get("focus_app_id")
    focus_app_name = context.get("focus_app_name") or focus_app_id or "No focused application"
    focus_alert_name = context.get("focus_alert_name") or "-"
    focus_severity = context.get("focus_severity") or "-"
    generated_at = context["generated_at"]
    trigger_mode = context["trigger_mode"]
    lookback_hours = int(context.get("lookback_hours") or DEFAULT_LOOKBACK_HOURS)
    metric_names = list(context.get("metric_names") or [])
    summary = context.get("summary") or "No summary generated."

    summary_markdown = (
        f"## NOC Support Summary\n"
        f"- Vessel: `{vessel_name}`\n"
        f"- IMO: `{vessel_imo}`\n"
        f"- Focus application: `{focus_app_name}`\n"
        f"- Focus alert: `{focus_alert_name}`\n"
        f"- Severity: `{focus_severity}`\n"
        f"- Trigger mode: `{trigger_mode}`\n"
        f"- Generated at: `{generated_at}`\n\n"
        f"{summary}"
    )

    panels = [
        _row_panel(100, "Dynamic NOC Support", y=0),
        _text_panel(1, "NOC Case Summary", summary_markdown, x=0, y=1, w=12, h=8),
        _table_panel(2, "NOC Case Context", _noc_context_sql(context), x=12, y=1, w=12, h=8),
        _table_panel(3, "Vessel Operational State", _app_status_sql(vessel_imo, focus_app_id), x=0, y=9, w=12, h=10),
        _table_panel(4, "Connectivity And Freshness", _freshness_sql(vessel_imo, focus_app_id, lookback_hours), x=12, y=9, w=12, h=10),
        _table_panel(5, "Recent Alerts", _recent_alerts_sql(vessel_imo, focus_app_id, lookback_hours), x=0, y=19, w=12, h=10),
        _table_panel(6, "Recent Logs", _recent_logs_sql(vessel_imo, focus_app_id, lookback_hours), x=12, y=19, w=12, h=10),
        _table_panel(7, "Support Timeline", _timeline_sql(vessel_imo, focus_app_id, lookback_hours), x=0, y=29, w=12, h=10),
        _table_panel(8, "Historical Alert Summary", _alert_summary_sql(vessel_imo, lookback_hours), x=12, y=29, w=12, h=10),
        _timeseries_panel(9, f"Focus Application Signals ({lookback_hours}h)", _focus_metrics_sql(vessel_imo, focus_app_id, metric_names, lookback_hours), x=0, y=39, w=24, h=10),
    ]

    return {
        "annotations": {"list": []},
        "description": "Generated NOC support dashboard built from vessel-wide operational context.",
        "editable": True,
        "graphTooltip": 1,
        "id": None,
        "links": _dashboard_links(vessel_imo, focus_app_id),
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 39,
        "tags": ["dynamic", "noc", "support", "user_story_3"],
        "templating": {"list": []},
        "time": {"from": f"now-{lookback_hours}h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": DYNAMIC_NOC_DASHBOARD_TITLE,
        "uid": DYNAMIC_NOC_DASHBOARD_UID,
        "version": 1,
        "fiscalYearStartMonth": 0,
        "liveNow": False,
    }


def _dashboard_links(vessel_imo: str, focus_app_id: str | None) -> list[dict[str, Any]]:
    vessel_value = quote(vessel_imo, safe="")
    app_value = quote(focus_app_id or "", safe="")
    noc_url = f"/d/maritime_noc_support/noc-support?var-vessel={vessel_value}"
    uds_url = f"/d/maritime_uds_monitoring/uds-incident-workbench?var-vessel={vessel_value}"
    if app_value:
        noc_url += f"&var-app_filter={app_value}"
        uds_url += f"&var-app={app_value}"
    return [
        {"asDropdown": False, "icon": "dashboard", "includeVars": False, "keepTime": True, "tags": [], "targetBlank": False, "title": "NOC Support", "tooltip": "Open the static NOC support dashboard", "type": "link", "url": noc_url},
        {"asDropdown": False, "icon": "dashboard", "includeVars": False, "keepTime": True, "tags": [], "targetBlank": False, "title": "UDS Incident Workbench", "tooltip": "Open the static incident dashboard", "type": "link", "url": uds_url},
        {"asDropdown": False, "icon": "dashboard", "includeVars": False, "keepTime": False, "tags": [], "targetBlank": True, "title": "Dynamic Fleet Dashboard", "tooltip": "Open the fleet-focused dynamic dashboard", "type": "link", "url": "http://localhost:3000/d/maritime_dynamic_fleet_incident/dynamic-fleet-incident-dashboard"},
        {"asDropdown": False, "icon": "external link", "includeVars": False, "keepTime": False, "tags": [], "targetBlank": True, "title": "Presentation Monitor", "tooltip": "Open the external presentation shell for the staged critical event demo", "type": "link", "url": "http://localhost:8000/api/v1/dynamic/monitor?presentation=1"},
        {"asDropdown": False, "icon": "external link", "includeVars": False, "keepTime": False, "tags": [], "targetBlank": True, "title": "AI Chat", "tooltip": "Ask the chat assistant about this support case", "type": "link", "url": "http://localhost:8000/api/v1/chat"},
    ]


def _row_panel(panel_id: int, title: str, *, y: int) -> dict[str, Any]:
    return {"collapsed": False, "gridPos": {"h": 1, "w": 24, "x": 0, "y": y}, "id": panel_id, "title": title, "type": "row"}


def _text_panel(panel_id: int, title: str, content: str, *, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    return {"gridPos": {"h": h, "w": w, "x": x, "y": y}, "id": panel_id, "options": {"content": content, "mode": "markdown"}, "title": title, "type": "text"}


def _table_panel(panel_id: int, title: str, raw_sql: str, *, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    return {
        "datasource": {"type": "postgres", "uid": DATASOURCE_UID},
        "fieldConfig": {"defaults": {}, "overrides": []},
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {"cellHeight": "sm", "footer": {"countRows": False, "fields": "", "reducer": ["sum"], "show": False}, "showHeader": True},
        "targets": [{"format": "table", "rawSql": raw_sql, "refId": "A"}],
        "title": title,
        "type": "table",
    }


def _timeseries_panel(panel_id: int, title: str, raw_sql: str, *, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    return {
        "datasource": {"type": "postgres", "uid": DATASOURCE_UID},
        "fieldConfig": {"defaults": {"color": {"mode": "palette-classic"}}, "overrides": []},
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {"legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True}, "tooltip": {"mode": "multi", "sort": "none"}},
        "targets": [{"format": "time_series", "rawSql": raw_sql, "refId": "A"}],
        "title": title,
        "type": "timeseries",
    }


def _noc_context_sql(context: dict[str, Any]) -> str:
    values = [
        ("Generated At", context["generated_at"]),
        ("Trigger Mode", context["trigger_mode"]),
        ("Scenario", context.get("scenario_key") or "noc_support_case"),
        ("Vessel", context.get("vessel_name") or context["vessel_imo"]),
        ("Vessel IMO", context["vessel_imo"]),
        ("Focus App", context.get("focus_app_name") or context.get("focus_app_id") or "-"),
        ("Focus App ID", context.get("focus_app_id") or "-"),
        ("Focus Alert", context.get("focus_alert_name") or "-"),
        ("Severity", context.get("focus_severity") or "-"),
        ("Used Tools", ", ".join(context.get("used_tools") or [])),
    ]
    rows = ", ".join(f"({_sql_literal(label)}, {_sql_literal(value)})" for label, value in values)
    return 'SELECT * FROM (VALUES ' + rows + ') AS noc_context("Field", "Value")'


def _app_status_sql(vessel_imo: str, focus_app_id: str | None) -> str:
    return f"""
WITH latest_metrics AS (
    SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
           ms.application_instance_id, ms.metric_name, ms.time, ms.value
    FROM metric_samples ms
    WHERE ms.imo_nr = {_sql_literal(vessel_imo)}
    ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
),
active_alerts AS (
    SELECT al.application_id, COUNT(*)::int AS active_alert_count
    FROM alerts al
    JOIN udslocations u ON u.id = al.uds_location_id
    WHERE u.imo_nr = {_sql_literal(vessel_imo)}
      AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
      AND (al.ends_at IS NULL OR al.ends_at > NOW())
    GROUP BY al.application_id
)
SELECT
    CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(focus_app_id or "")}) THEN 'focus' ELSE '' END AS "Focus",
    a.name AS "Application",
    a.external_id AS "App ID",
    CASE
        WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
          OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0 THEN 'down'
        WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'reporting_stale' THEN lm.value END), 0) >= 1
          OR COALESCE(MAX(CASE WHEN lm.metric_name = 'sync_delayed' THEN lm.value END), 0) >= 1 THEN 'connectivity'
        WHEN COALESCE(aa.active_alert_count, 0) > 0 THEN 'degraded'
        WHEN MAX(lm.time) IS NULL THEN 'unknown'
        ELSE 'healthy'
    END AS "Status",
    COALESCE(aa.active_alert_count, 0) AS "Active Alerts",
    MAX(lm.time) AS "Latest Metric"
FROM udslocations u
JOIN uds_location_application_instances uai ON uai.uds_location_id = u.id
JOIN applications a ON a.id = uai.application_instance_id
LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
LEFT JOIN active_alerts aa ON aa.application_id = a.id
WHERE u.imo_nr = {_sql_literal(vessel_imo)}
GROUP BY a.id, a.name, a.external_id, aa.active_alert_count
ORDER BY CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(focus_app_id or "")}) THEN 0 ELSE 1 END, "Status", a.name ASC;
""".strip()


def _freshness_sql(vessel_imo: str, focus_app_id: str | None, lookback_hours: int) -> str:
    return f"""
WITH latest_metrics AS (
    SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
           ms.application_instance_id, ms.metric_name, ms.time, ms.value
    FROM metric_samples ms
    WHERE ms.imo_nr = {_sql_literal(vessel_imo)}
    ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
),
latest_logs AS (
    SELECT COALESCE(a.external_id, l.app_external_id) AS app_id, MAX(l.logged_at) AS latest_log_at
    FROM app_logs l
    JOIN udslocations u ON u.id = l.uds_location_id
    LEFT JOIN applications a ON a.id = l.application_id
    WHERE u.imo_nr = {_sql_literal(vessel_imo)}
      AND l.logged_at >= NOW() - INTERVAL '{lookback_hours} hours'
    GROUP BY COALESCE(a.external_id, l.app_external_id)
)
SELECT
    CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(focus_app_id or "")}) THEN 'focus' ELSE '' END AS "Focus",
    a.name AS "Application",
    a.external_id AS "App ID",
    ROUND((COALESCE(MAX(CASE WHEN lm.metric_name = 'last_sync_age_seconds' THEN lm.value END), 0) / 60.0)::numeric, 2) AS "Last Sync Age Min",
    MAX(lm.time) AS "Latest Metric",
    ll.latest_log_at AS "Latest Log",
    CASE
        WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'reporting_stale' THEN lm.value END), 0) >= 1 THEN 'stale'
        WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'sync_delayed' THEN lm.value END), 0) >= 1 THEN 'delayed'
        WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'last_sync_age_seconds' THEN lm.value END), 0) >= 900 THEN 'aging'
        ELSE 'ok'
    END AS "Connectivity"
FROM udslocations u
JOIN uds_location_application_instances uai ON uai.uds_location_id = u.id
JOIN applications a ON a.id = uai.application_instance_id
LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
LEFT JOIN latest_logs ll ON LOWER(ll.app_id) = LOWER(a.external_id)
WHERE u.imo_nr = {_sql_literal(vessel_imo)}
GROUP BY a.id, a.name, a.external_id, ll.latest_log_at
ORDER BY CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(focus_app_id or "")}) THEN 0 ELSE 1 END, "Connectivity", a.name ASC;
""".strip()


def _recent_alerts_sql(vessel_imo: str, focus_app_id: str | None, lookback_hours: int) -> str:
    return f"""
SELECT
    CASE WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or "")}) THEN 'focus' ELSE '' END AS "Focus",
    COALESCE(a.name, 'unknown') AS "Application",
    al.alert_name AS "Alert",
    COALESCE(al.severity, '-') AS "Severity",
    COALESCE(al.status, 'firing') AS "Status",
    COALESCE(al.received_at, al.starts_at) AS "Received"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE u.imo_nr = {_sql_literal(vessel_imo)}
  AND COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
ORDER BY CASE WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or "")}) THEN 0 ELSE 1 END, COALESCE(al.received_at, al.starts_at) DESC
LIMIT 75;
""".strip()


def _recent_logs_sql(vessel_imo: str, focus_app_id: str | None, lookback_hours: int) -> str:
    return f"""
SELECT
    CASE WHEN LOWER(COALESCE(a.external_id, l.app_external_id, '')) = LOWER({_sql_literal(focus_app_id or "")}) THEN 'focus' ELSE '' END AS "Focus",
    l.logged_at AS "Logged At",
    COALESCE(a.name, l.app_external_id, 'unknown') AS "Application",
    l.level AS "Level",
    l.source AS "Source",
    l.message AS "Message"
FROM app_logs l
JOIN udslocations u ON u.id = l.uds_location_id
LEFT JOIN applications a ON a.id = l.application_id
WHERE u.imo_nr = {_sql_literal(vessel_imo)}
  AND l.logged_at >= NOW() - INTERVAL '{lookback_hours} hours'
ORDER BY CASE WHEN LOWER(COALESCE(a.external_id, l.app_external_id, '')) = LOWER({_sql_literal(focus_app_id or "")}) THEN 0 ELSE 1 END, l.logged_at DESC
LIMIT 100;
""".strip()


def _timeline_sql(vessel_imo: str, focus_app_id: str | None, lookback_hours: int) -> str:
    return f"""
SELECT *
FROM (
    SELECT
        CASE WHEN LOWER(COALESCE(a.external_id, '')) = LOWER({_sql_literal(focus_app_id or "")}) THEN 'focus' ELSE '' END AS "Focus",
        COALESCE(al.received_at, al.starts_at) AS "Time",
        'alert' AS "Type",
        COALESCE(a.name, 'unknown') AS "Application",
        COALESCE(al.severity, '-') AS "Severity",
        al.alert_name AS "Message"
    FROM alerts al
    JOIN udslocations u ON u.id = al.uds_location_id
    LEFT JOIN applications a ON a.id = al.application_id
    WHERE u.imo_nr = {_sql_literal(vessel_imo)}
      AND COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
    UNION ALL
    SELECT
        CASE WHEN LOWER(COALESCE(a.external_id, l.app_external_id, '')) = LOWER({_sql_literal(focus_app_id or "")}) THEN 'focus' ELSE '' END AS "Focus",
        l.logged_at AS "Time",
        'log' AS "Type",
        COALESCE(a.name, l.app_external_id, 'unknown') AS "Application",
        COALESCE(l.level, '-') AS "Severity",
        l.message AS "Message"
    FROM app_logs l
    JOIN udslocations u ON u.id = l.uds_location_id
    LEFT JOIN applications a ON a.id = l.application_id
    WHERE u.imo_nr = {_sql_literal(vessel_imo)}
      AND l.logged_at >= NOW() - INTERVAL '{lookback_hours} hours'
) timeline
ORDER BY CASE WHEN "Focus" = 'focus' THEN 0 ELSE 1 END, "Time" DESC
LIMIT 120;
""".strip()


def _alert_summary_sql(vessel_imo: str, lookback_hours: int) -> str:
    return f"""
SELECT
    COALESCE(a.name, 'unknown') AS "Application",
    al.alert_name AS "Alert",
    COALESCE(al.severity, '-') AS "Severity",
    COUNT(*)::int AS "Count",
    MAX(COALESCE(al.received_at, al.starts_at)) AS "Last Seen"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE u.imo_nr = {_sql_literal(vessel_imo)}
  AND COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
GROUP BY a.name, al.alert_name, al.severity
ORDER BY "Count" DESC, "Last Seen" DESC
LIMIT 75;
""".strip()


def _focus_metrics_sql(vessel_imo: str, focus_app_id: str | None, metric_names: list[str], lookback_hours: int) -> str:
    if not focus_app_id or not metric_names:
        return 'SELECT NOW() AS "time", \'no_metrics\' AS metric, 0::double precision AS value WHERE FALSE'
    metric_list = ", ".join(_sql_literal(metric) for metric in metric_names)
    return f"""
SELECT
    ms.time AS "time",
    CASE WHEN ms.metric_name = 'last_sync_age_seconds' THEN 'last_sync_age_minutes' ELSE ms.metric_name END AS metric,
    CASE WHEN ms.metric_name = 'last_sync_age_seconds' THEN ms.value / 60.0 ELSE ms.value END AS value
FROM metric_samples ms
WHERE ms.imo_nr = {_sql_literal(vessel_imo)}
  AND LOWER(ms.app_id) = LOWER({_sql_literal(focus_app_id)})
  AND ms.metric_name IN ({metric_list})
  AND ms.time >= NOW() - INTERVAL '{lookback_hours} hours'
ORDER BY ms.time ASC;
""".strip()


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"
