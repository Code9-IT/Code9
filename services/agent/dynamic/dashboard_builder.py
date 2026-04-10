"""Deterministic Grafana dashboard builder for dynamic incidents."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote


DYNAMIC_DASHBOARD_UID = "maritime_dynamic_incident"
DYNAMIC_DASHBOARD_TITLE = "Dynamic Incident Dashboard"
DATASOURCE_UID = "timescaledb"
DEFAULT_LOOKBACK_HOURS = 24


def build_dashboard_payload(context: dict[str, Any]) -> dict[str, Any]:
    """Build one Grafana dashboard dict for the current incident context."""
    vessel_imo = context["vessel_imo"]
    app_external_id = context.get("app_external_id")
    app_name = context.get("app_name") or app_external_id or "Unknown application"
    scenario_key = context["scenario_key"]
    lookback_hours = int(context.get("lookback_hours") or DEFAULT_LOOKBACK_HOURS)
    summary = context.get("summary") or "No summary generated."
    generated_at = context["generated_at"]
    trigger_mode = context["trigger_mode"]
    alert_name = context.get("alert_name") or "-"
    severity = context.get("severity") or "-"
    metric_names = list(context.get("metric_names") or [])

    incident_markdown = (
        f"## Incident Summary\n"
        f"- Scenario: `{scenario_key}`\n"
        f"- Vessel: `{vessel_imo}`\n"
        f"- Application: `{app_name}`\n"
        f"- Alert: `{alert_name}`\n"
        f"- Severity: `{severity}`\n"
        f"- Trigger mode: `{trigger_mode}`\n"
        f"- Generated at: `{generated_at}`\n\n"
        f"{summary}"
    )

    panels = [
        _row_panel(100, "Dynamic Incident", y=0),
        _text_panel(1, "Incident Summary", incident_markdown, x=0, y=1, w=12, h=8),
        _table_panel(2, "Incident Context", _incident_context_sql(context), x=12, y=1, w=12, h=8),
        _table_panel(3, "Operational State By App", _app_status_board_sql(vessel_imo, app_external_id), x=0, y=9, w=12, h=10),
        _table_panel(4, "Recent Alerts", _recent_alerts_sql(vessel_imo, app_external_id, lookback_hours), x=12, y=9, w=12, h=10),
        _table_panel(5, "Incident Timeline", _incident_timeline_sql(vessel_imo, app_external_id, lookback_hours), x=0, y=19, w=12, h=10),
        _table_panel(6, "Recent Logs", _recent_logs_sql(vessel_imo, app_external_id, lookback_hours), x=12, y=19, w=12, h=10),
        _timeseries_panel(7, f"Scenario Trends ({lookback_hours}h)", _scenario_metrics_sql(vessel_imo, app_external_id, metric_names, lookback_hours), x=0, y=29, w=24, h=10),
        _table_panel(8, f"Signal Summary ({lookback_hours}h)", _metric_summary_sql(vessel_imo, app_external_id, metric_names, lookback_hours), x=0, y=39, w=24, h=8),
    ]

    return {
        "annotations": {"list": []},
        "description": (
            "Generated incident-focused dashboard built from MCP-backed context and "
            "written through the Grafana HTTP API."
        ),
        "editable": True,
        "graphTooltip": 1,
        "id": None,
        "links": _dashboard_links(vessel_imo, app_external_id),
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": 39,
        "tags": ["dynamic", "incident", scenario_key],
        "templating": {"list": []},
        "time": {"from": f"now-{lookback_hours}h", "to": "now"},
        "timepicker": {},
        "timezone": "browser",
        "title": DYNAMIC_DASHBOARD_TITLE,
        "uid": DYNAMIC_DASHBOARD_UID,
        "version": 1,
        "fiscalYearStartMonth": 0,
        "liveNow": False,
    }


def _dashboard_links(vessel_imo: str, app_external_id: str | None) -> list[dict[str, Any]]:
    app_value = quote(app_external_id or "", safe="")
    vessel_value = quote(vessel_imo, safe="")
    uds_url = f"/d/maritime_uds_monitoring/uds-incident-workbench?var-vessel={vessel_value}"
    noc_url = f"/d/maritime_noc_support/noc-support?var-vessel={vessel_value}"
    selector_url = f"http://localhost:8000/api/v1/dynamic/select?vessel_imo={vessel_value}"
    if app_value:
        uds_url += f"&var-app={app_value}"
        noc_url += f"&var-app_filter={app_value}"
        selector_url += f"&app_external_id={app_value}"
    return [
        {
            "asDropdown": False,
            "icon": "dashboard",
            "includeVars": False,
            "keepTime": True,
            "tags": [],
            "targetBlank": False,
            "title": "UDS Incident Workbench",
            "tooltip": "Open the static UDS dashboard for the same vessel/application context",
            "type": "link",
            "url": uds_url,
        },
        {
            "asDropdown": False,
            "icon": "dashboard",
            "includeVars": False,
            "keepTime": True,
            "tags": [],
            "targetBlank": False,
            "title": "NOC Support",
            "tooltip": "Open the broader troubleshooting dashboard for the same vessel",
            "type": "link",
            "url": noc_url,
        },
        {
            "asDropdown": False,
            "icon": "link",
            "includeVars": False,
            "keepTime": False,
            "tags": [],
            "targetBlank": True,
            "title": "Incident Selector",
            "tooltip": "Choose another vessel, app, or alert for the dynamic dashboard",
            "type": "link",
            "url": selector_url,
        },
        {
            "asDropdown": False,
            "icon": "external link",
            "includeVars": False,
            "keepTime": False,
            "tags": [],
            "targetBlank": True,
            "title": "AI Chat",
            "tooltip": "Ask the chat assistant about this incident context",
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


def _timeseries_panel(panel_id: int, title: str, raw_sql: str, *, x: int, y: int, w: int, h: int) -> dict[str, Any]:
    return {
        "datasource": {"type": "postgres", "uid": DATASOURCE_UID},
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {
                    "axisBorderShow": False,
                    "axisCenteredZero": False,
                    "axisColorMode": "text",
                    "axisLabel": "",
                    "axisPlacement": "auto",
                    "barAlignment": 0,
                    "drawStyle": "line",
                    "fillOpacity": 10,
                    "gradientMode": "none",
                    "hideFrom": {"legend": False, "tooltip": False, "viz": False},
                    "lineInterpolation": "linear",
                    "lineWidth": 2,
                    "pointSize": 3,
                    "scaleDistribution": {"type": "linear"},
                    "showPoints": "auto",
                    "spanNulls": False,
                    "stacking": {"group": "A", "mode": "none"},
                    "thresholdsStyle": {"mode": "off"},
                },
                "mappings": [],
                "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": None}]},
            },
            "overrides": [],
        },
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "id": panel_id,
        "options": {
            "legend": {"calcs": [], "displayMode": "list", "placement": "bottom", "showLegend": True},
            "tooltip": {"mode": "multi", "sort": "none"},
        },
        "targets": [{"format": "time_series", "rawSql": raw_sql, "refId": "A"}],
        "title": title,
        "type": "timeseries",
    }


def _incident_context_sql(context: dict[str, Any]) -> str:
    values = [
        ("Generated At", context["generated_at"]),
        ("Trigger Mode", context["trigger_mode"]),
        ("Scenario", context["scenario_key"]),
        ("Vessel IMO", context["vessel_imo"]),
        ("Application", context.get("app_name") or context.get("app_external_id") or "-"),
        ("App ID", context.get("app_external_id") or "-"),
        ("Alert", context.get("alert_name") or "-"),
        ("Severity", context.get("severity") or "-"),
        ("Source Fingerprint", context.get("source_alert_fingerprint") or "-"),
        ("Used Tools", ", ".join(context.get("used_tools") or [])),
    ]
    rows = ", ".join(f"({_sql_literal(label)}, {_sql_literal(value)})" for label, value in values)
    return 'SELECT * FROM (VALUES ' + rows + ') AS incident_context("Field", "Value")'


def _app_status_board_sql(vessel_imo: str, selected_app: str | None) -> str:
    return f"""
WITH latest_metrics AS (
    SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
           ms.application_instance_id,
           ms.metric_name,
           ms.time,
           ms.value
    FROM metric_samples ms
    WHERE ms.imo_nr = {_sql_literal(vessel_imo)}
    ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
),
active_alerts AS (
    SELECT al.application_id,
           COUNT(*)::int AS active_alert_count
    FROM alerts al
    JOIN udslocations u ON u.id = al.uds_location_id
    WHERE u.imo_nr = {_sql_literal(vessel_imo)}
      AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
      AND (al.ends_at IS NULL OR al.ends_at > NOW())
    GROUP BY al.application_id
)
SELECT
    CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(selected_app or "")}) THEN 'selected' ELSE '' END AS "Focus",
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
ORDER BY
    CASE WHEN LOWER(a.external_id) = LOWER({_sql_literal(selected_app or "")}) THEN 0 ELSE 1 END,
    CASE
        WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
          OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0 THEN 0
        WHEN COALESCE(aa.active_alert_count, 0) > 0 THEN 1
        ELSE 2
    END,
    a.name ASC;
""".strip()


def _recent_alerts_sql(vessel_imo: str, app_external_id: str | None, lookback_hours: int) -> str:
    app_filter = _optional_lower_eq("a.external_id", app_external_id)
    return f"""
SELECT
    COALESCE(a.name, 'unknown') AS "Application",
    COALESCE(a.external_id, '-') AS "App ID",
    al.alert_name AS "Alert",
    COALESCE(al.severity, '-') AS "Severity",
    COALESCE(al.status, 'firing') AS "Status",
    COALESCE(al.alert_type, '-') AS "Type",
    COALESCE(al.received_at, al.starts_at) AS "Received",
    al.starts_at AS "Started"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE u.imo_nr = {_sql_literal(vessel_imo)}
  AND COALESCE(al.received_at, al.starts_at) >= NOW() - INTERVAL '{lookback_hours} hours'
  AND {app_filter}
ORDER BY COALESCE(al.received_at, al.starts_at) DESC
LIMIT 50;
""".strip()


def _incident_timeline_sql(vessel_imo: str, app_external_id: str | None, lookback_hours: int) -> str:
    app_alert_filter = _optional_lower_eq("a.external_id", app_external_id)
    app_log_filter = _optional_lower_eq("COALESCE(a.external_id, l.app_external_id)", app_external_id)
    return f"""
SELECT *
FROM (
    SELECT
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
      AND {app_alert_filter}
    UNION ALL
    SELECT
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
      AND {app_log_filter}
) timeline
ORDER BY "Time" DESC
LIMIT 100;
""".strip()


def _recent_logs_sql(vessel_imo: str, app_external_id: str | None, lookback_hours: int) -> str:
    app_filter = _optional_lower_eq("COALESCE(a.external_id, l.app_external_id)", app_external_id)
    return f"""
SELECT
    l.logged_at AS "Logged At",
    COALESCE(a.name, l.app_external_id, 'unknown') AS "Application",
    COALESCE(a.external_id, l.app_external_id, '-') AS "App ID",
    l.level AS "Level",
    l.source AS "Source",
    l.message AS "Message",
    COALESCE(l.correlation_key, '-') AS "Correlation",
    COALESCE(l.context::text, '{{}}') AS "Context"
FROM app_logs l
JOIN udslocations u ON u.id = l.uds_location_id
LEFT JOIN applications a ON a.id = l.application_id
WHERE u.imo_nr = {_sql_literal(vessel_imo)}
  AND l.logged_at >= NOW() - INTERVAL '{lookback_hours} hours'
  AND {app_filter}
ORDER BY l.logged_at DESC
LIMIT 100;
""".strip()


def _scenario_metrics_sql(
    vessel_imo: str,
    app_external_id: str | None,
    metric_names: list[str],
    lookback_hours: int,
) -> str:
    if not app_external_id or not metric_names:
        return (
            'SELECT NOW() AS "time", \'no_metrics\' AS metric, 0::double precision AS value '
            'WHERE FALSE'
        )
    metric_list = ", ".join(_sql_literal(metric) for metric in metric_names)
    return f"""
SELECT
    ms.time AS "time",
    CASE
        WHEN ms.metric_name = 'last_sync_age_seconds' THEN 'last_sync_age_minutes'
        ELSE ms.metric_name
    END AS metric,
    CASE
        WHEN ms.metric_name = 'last_sync_age_seconds' THEN ms.value / 60.0
        ELSE ms.value
    END AS value
FROM metric_samples ms
WHERE ms.imo_nr = {_sql_literal(vessel_imo)}
  AND LOWER(ms.app_id) = LOWER({_sql_literal(app_external_id)})
  AND ms.metric_name IN ({metric_list})
  AND ms.time >= NOW() - INTERVAL '{lookback_hours} hours'
ORDER BY ms.time ASC;
""".strip()


def _metric_summary_sql(
    vessel_imo: str,
    app_external_id: str | None,
    metric_names: list[str],
    lookback_hours: int,
) -> str:
    if not app_external_id or not metric_names:
        return (
            'SELECT * FROM (VALUES (\'No metrics\', \'No application context\')) '
            'AS metric_summary("Metric", "Value")'
        )
    metric_list = ", ".join(_sql_literal(metric) for metric in metric_names)
    return f"""
WITH filtered_metrics AS (
    SELECT
        CASE
            WHEN ms.metric_name = 'last_sync_age_seconds' THEN 'last_sync_age_minutes'
            ELSE ms.metric_name
        END AS metric_name,
        CASE
            WHEN ms.metric_name = 'last_sync_age_seconds' THEN ms.value / 60.0
            ELSE ms.value
        END AS value,
        ms.time,
        CASE
            WHEN ms.metric_name = 'last_sync_age_seconds' THEN 'Minutes'
            ELSE ms.metric_unit
        END AS metric_unit
    FROM metric_samples ms
    WHERE ms.imo_nr = {_sql_literal(vessel_imo)}
      AND LOWER(ms.app_id) = LOWER({_sql_literal(app_external_id)})
      AND ms.metric_name IN ({metric_list})
      AND ms.time >= NOW() - INTERVAL '{lookback_hours} hours'
)
SELECT
    fm.metric_name AS "Metric",
    ROUND(MIN(fm.value)::numeric, 4) AS "Min",
    ROUND(AVG(fm.value)::numeric, 4) AS "Avg",
    ROUND(MAX(fm.value)::numeric, 4) AS "Max",
    ROUND(((ARRAY_AGG(fm.value ORDER BY fm.time DESC))[1])::numeric, 4) AS "Latest",
    MAX(fm.metric_unit) AS "Unit",
    MAX(fm.time) AS "Latest Sample"
FROM filtered_metrics fm
GROUP BY fm.metric_name
ORDER BY fm.metric_name ASC;
""".strip()


def _optional_lower_eq(field_sql: str, value: str | None) -> str:
    if not value:
        return "TRUE"
    return f"LOWER(COALESCE({field_sql}, '')) = LOWER({_sql_literal(value)})"


def _sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    text = str(value).replace("'", "''")
    return f"'{text}'"
