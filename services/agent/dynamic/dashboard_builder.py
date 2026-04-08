"""Deterministic Grafana dashboard builder for dynamic incidents."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from itertools import count
from typing import Any, Literal
from urllib.parse import urlencode


DYNAMIC_DASHBOARD_UID = "maritime_dynamic_incident"
DYNAMIC_DASHBOARD_TITLE = "Dynamic Incident Dashboard"
DEFAULT_DATASOURCE_UID = "timescaledb"
DEFAULT_GRAFANA_SCHEMA_VERSION = 39
DEFAULT_INCIDENT_WINDOW = "6 hours"
DEFAULT_TIME_FROM = "now-24h"
DEFAULT_TIME_TO = "now"
ALL_APPS_VALUE = "__all"

ScenarioKey = Literal[
    "service_down",
    "runtime_pressure",
    "connectivity",
    "generic_incident",
]
GridPos = dict[str, int]

SCENARIO_LABELS: dict[ScenarioKey, str] = {
    "service_down": "Service Down",
    "runtime_pressure": "Runtime Pressure",
    "connectivity": "Connectivity",
    "generic_incident": "Generic Incident",
}
SCENARIO_DESCRIPTIONS: dict[ScenarioKey, str] = {
    "service_down": "Focus on availability loss, error spikes, and recovery indicators.",
    "runtime_pressure": "Focus on CPU, memory, and database latency around runtime degradation.",
    "connectivity": "Focus on freshness, sync delay, and degraded reporting signals.",
    "generic_incident": "Focus on the core application state, recent activity, and supporting context.",
}
INCIDENT_WINDOW_OPTIONS: dict[str, str] = {
    "1 hour": "Last 1h",
    "6 hours": "Last 6h",
    "24 hours": "Last 24h",
}
SCENARIO_PANEL_GROUPS: dict[ScenarioKey, tuple[str, ...]] = {
    "service_down": (
        "availability",
        "http_exceptions",
        "cpu_handles",
    ),
    "runtime_pressure": (
        "cpu_handles",
        "memory",
        "database_latency",
        "database_errors",
    ),
    "connectivity": (
        "connectivity",
        "availability",
        "http_exceptions",
    ),
    "generic_incident": (
        "availability",
        "connectivity",
        "cpu_handles",
    ),
}


@dataclass(slots=True)
class DynamicDashboardContext:
    """Inputs required to build the generated incident dashboard."""

    vessel_imo: str
    scenario_key: ScenarioKey | str
    app_external_id: str | None = None
    vessel_name: str | None = None
    app_name: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    summary: str | None = None
    source_alert_fingerprint: str | None = None
    incident_started_at: str | None = None
    generated_at: str | None = None
    incident_window: str = DEFAULT_INCIDENT_WINDOW


def build_dashboard_payload(
    context: DynamicDashboardContext | Mapping[str, Any],
) -> dict[str, Any]:
    """Build one deterministic Grafana 11 dashboard payload."""
    resolved_context = _coerce_context(context)
    panel_ids = count(1)

    panels: list[dict[str, Any]] = [
        _text_panel(
            next(panel_ids),
            "Incident Summary",
            _grid(0, 0, 12, 6),
            _build_summary_markdown(resolved_context),
        ),
        _incident_context_table_panel(next(panel_ids), _grid(12, 0, 12, 6)),
        _application_status_table_panel(next(panel_ids), _grid(0, 6, 24, 8)),
        _recent_alerts_table_panel(next(panel_ids), _grid(0, 14, 12, 8)),
        _incident_timeline_table_panel(next(panel_ids), _grid(12, 14, 12, 8)),
        _recent_logs_table_panel(next(panel_ids), _grid(0, 22, 12, 8)),
        _metric_window_summary_panel(next(panel_ids), _grid(12, 22, 12, 8)),
    ]

    scenario_positions = [
        _grid(0, 30, 12, 8),
        _grid(12, 30, 12, 8),
        _grid(0, 38, 12, 8),
        _grid(12, 38, 12, 8),
    ]
    for group_key, grid_pos in zip(
        SCENARIO_PANEL_GROUPS[resolved_context.scenario_key],
        scenario_positions,
    ):
        panels.append(_metric_panel(group_key, next(panel_ids), grid_pos))

    return {
        "annotations": {"list": []},
        "description": (
            "Generated incident-focused dashboard for the dynamic dashboard prototype. "
            "The panel set is selected deterministically from the scenario key."
        ),
        "editable": True,
        "graphTooltip": 1,
        "id": None,
        "links": _dashboard_links(resolved_context),
        "panels": panels,
        "refresh": "30s",
        "schemaVersion": DEFAULT_GRAFANA_SCHEMA_VERSION,
        "style": "dark",
        "tags": [
            "maritime",
            "dynamic-dashboard",
            "incident-response",
            resolved_context.scenario_key,
        ],
        "templating": {"list": _templating_variables(resolved_context)},
        "time": {"from": DEFAULT_TIME_FROM, "to": DEFAULT_TIME_TO},
        "timepicker": {},
        "timezone": "browser",
        "title": DYNAMIC_DASHBOARD_TITLE,
        "uid": DYNAMIC_DASHBOARD_UID,
        "version": 1,
    }


def _coerce_context(context: DynamicDashboardContext | Mapping[str, Any]) -> DynamicDashboardContext:
    if isinstance(context, DynamicDashboardContext):
        raw_context = context
    elif isinstance(context, Mapping):
        raw_context = DynamicDashboardContext(**dict(context))
    else:
        raise TypeError("context must be a DynamicDashboardContext or a mapping")

    vessel_imo = (raw_context.vessel_imo or "").strip()
    if not vessel_imo:
        raise ValueError("DynamicDashboardContext.vessel_imo is required")

    scenario_key = _normalize_scenario_key(raw_context.scenario_key)
    generated_at = (raw_context.generated_at or _utc_now_iso()).strip()
    incident_window = _normalize_incident_window(raw_context.incident_window)

    return DynamicDashboardContext(
        vessel_imo=vessel_imo,
        scenario_key=scenario_key,
        app_external_id=_normalize_optional_text(raw_context.app_external_id),
        vessel_name=_normalize_optional_text(raw_context.vessel_name),
        app_name=_normalize_optional_text(raw_context.app_name),
        alert_name=_normalize_optional_text(raw_context.alert_name),
        severity=_normalize_optional_text(raw_context.severity),
        summary=_normalize_optional_text(raw_context.summary),
        source_alert_fingerprint=_normalize_optional_text(raw_context.source_alert_fingerprint),
        incident_started_at=_normalize_optional_text(raw_context.incident_started_at),
        generated_at=generated_at,
        incident_window=incident_window,
    )


def _normalize_scenario_key(value: str) -> ScenarioKey:
    normalized = (value or "").strip().lower()
    if normalized in SCENARIO_LABELS:
        return normalized  # type: ignore[return-value]
    return "generic_incident"


def _normalize_incident_window(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    for raw_option in INCIDENT_WINDOW_OPTIONS:
        if normalized == raw_option:
            return raw_option
    return DEFAULT_INCIDENT_WINDOW


def _normalize_optional_text(value: str | None) -> str | None:
    normalized = (value or "").strip()
    return normalized or None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _templating_variables(context: DynamicDashboardContext) -> list[dict[str, Any]]:
    return [
        _constant_variable("vessel", "Incident Vessel", context.vessel_imo),
        _constant_variable("app", "Incident App", context.app_external_id or ALL_APPS_VALUE),
        _constant_variable("scenario_key", "Scenario", context.scenario_key),
        _incident_window_variable(context.incident_window),
    ]


def _constant_variable(name: str, label: str, value: str) -> dict[str, Any]:
    return {
        "current": {"selected": True, "text": value, "value": value},
        "hide": 2,
        "label": label,
        "name": name,
        "options": [{"selected": True, "text": value, "value": value}],
        "query": value,
        "skipUrlSync": True,
        "type": "constant",
    }


def _incident_window_variable(selected_value: str) -> dict[str, Any]:
    query = (
        "SELECT '1 hour' AS __value, 'Last 1h' AS __text "
        "UNION ALL SELECT '6 hours' AS __value, 'Last 6h' AS __text "
        "UNION ALL SELECT '24 hours' AS __value, 'Last 24h' AS __text"
    )
    return {
        "current": {
            "selected": True,
            "text": INCIDENT_WINDOW_OPTIONS[selected_value],
            "value": selected_value,
        },
        "datasource": _datasource_ref(),
        "definition": query,
        "description": "Incident-focused time window for the generated dashboard",
        "hide": 0,
        "includeAll": False,
        "label": "Incident Window",
        "multi": False,
        "name": "incident_window",
        "options": [],
        "query": query,
        "refresh": 2,
        "regex": "",
        "skipUrlSync": False,
        "sort": 0,
        "type": "query",
    }


def _dashboard_links(context: DynamicDashboardContext) -> list[dict[str, Any]]:
    workbench_params = {
        "var-vessel": context.vessel_imo,
        "var-incident_window": context.incident_window,
    }
    if context.app_external_id:
        workbench_params["var-app"] = context.app_external_id

    noc_params = {
        "var-vessel": context.vessel_imo,
        "var-time_window": context.incident_window,
    }
    if context.app_external_id:
        noc_params["var-app_filter"] = context.app_external_id

    return [
        _dashboard_link(
            title="UDS Incident Workbench",
            tooltip="Static single-vessel incident workbench for the same context",
            path="/d/maritime_uds_monitoring/uds-incident-workbench",
            params=workbench_params,
        ),
        _dashboard_link(
            title="NOC Support",
            tooltip="Broader troubleshooting dashboard for the same vessel",
            path="/d/maritime_noc_support/noc-support",
            params=noc_params,
        ),
        _dashboard_link(
            title="Fleet Overview",
            tooltip="Fleet-wide summary dashboard",
            path="/d/maritime_fleet_overview/fleet-overview",
        ),
    ]


def _dashboard_link(
    *,
    title: str,
    tooltip: str,
    path: str,
    params: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    url = path
    if params:
        url = f"{path}?{urlencode(params)}"
    return {
        "asDropdown": False,
        "icon": "dashboard",
        "includeVars": False,
        "keepTime": True,
        "tags": [],
        "targetBlank": False,
        "title": title,
        "tooltip": tooltip,
        "type": "link",
        "url": url,
    }


def _datasource_ref() -> dict[str, str]:
    return {"type": "postgres", "uid": DEFAULT_DATASOURCE_UID}


def _grid(x: int, y: int, w: int, h: int) -> GridPos:
    return {"h": h, "w": w, "x": x, "y": y}


def _text_panel(panel_id: int, title: str, grid_pos: GridPos, content: str) -> dict[str, Any]:
    return {
        "gridPos": grid_pos,
        "id": panel_id,
        "options": {"content": content, "mode": "markdown"},
        "title": title,
        "type": "text",
    }


def _table_panel(
    panel_id: int,
    title: str,
    grid_pos: GridPos,
    raw_sql: str,
    *,
    field_overrides: list[dict[str, Any]] | None = None,
    sort_by: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    options: dict[str, Any] = {"showHeader": True}
    if sort_by:
        options["sortBy"] = sort_by

    return {
        "datasource": _datasource_ref(),
        "fieldConfig": {
            "defaults": {"custom": {"displayMode": "auto", "filterable": True}},
            "overrides": field_overrides or [],
        },
        "gridPos": grid_pos,
        "id": panel_id,
        "options": options,
        "targets": [{"format": "table", "rawSql": raw_sql, "refId": "A"}],
        "title": title,
        "type": "table",
    }


def _timeseries_panel(
    panel_id: int,
    title: str,
    grid_pos: GridPos,
    raw_sql: str,
    *,
    default_unit: str = "short",
    field_overrides: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "datasource": _datasource_ref(),
        "fieldConfig": {
            "defaults": {
                "color": {"mode": "palette-classic"},
                "custom": {"fillOpacity": 10, "lineWidth": 2},
                "unit": default_unit,
            },
            "overrides": field_overrides or [],
        },
        "gridPos": grid_pos,
        "id": panel_id,
        "options": {
            "legend": {"displayMode": "list", "placement": "bottom"},
            "tooltip": {"mode": "multi"},
        },
        "targets": [{"format": "time_series", "rawSql": raw_sql, "refId": "A"}],
        "title": title,
        "type": "timeseries",
    }


def _severity_overrides(field_name: str = "Severity") -> dict[str, Any]:
    return {
        "matcher": {"id": "byName", "options": field_name},
        "properties": [
            {
                "id": "mappings",
                "value": [
                    {
                        "options": {
                            "critical": {"color": "red", "text": "critical"},
                            "info": {"color": "green", "text": "info"},
                            "warning": {"color": "yellow", "text": "warning"},
                        },
                        "type": "value",
                    }
                ],
            },
            {"id": "custom.displayMode", "value": "color-background"},
        ],
    }


def _status_overrides(field_name: str = "Current Status") -> dict[str, Any]:
    return {
        "matcher": {"id": "byName", "options": field_name},
        "properties": [
            {
                "id": "mappings",
                "value": [
                    {
                        "options": {
                            "critical": {"color": "red", "text": "critical"},
                            "degraded": {"color": "yellow", "text": "degraded"},
                            "down": {"color": "red", "text": "down"},
                            "healthy": {"color": "green", "text": "healthy"},
                            "unknown": {"color": "gray", "text": "unknown"},
                        },
                        "type": "value",
                    }
                ],
            },
            {"id": "custom.displayMode", "value": "color-background"},
        ],
    }


def _level_overrides(field_name: str = "Level") -> dict[str, Any]:
    return {
        "matcher": {"id": "byName", "options": field_name},
        "properties": [
            {
                "id": "mappings",
                "value": [
                    {
                        "options": {
                            "critical": {"color": "red", "text": "critical"},
                            "error": {"color": "red", "text": "error"},
                            "warning": {"color": "yellow", "text": "warning"},
                            "info": {"color": "green", "text": "info"},
                            "debug": {"color": "blue", "text": "debug"},
                        },
                        "type": "value",
                    }
                ],
            },
            {"id": "custom.displayMode", "value": "color-background"},
        ],
    }


def _exact_unit_override(field_name: str, unit: str) -> dict[str, Any]:
    return {
        "matcher": {"id": "byName", "options": field_name},
        "properties": [{"id": "unit", "value": unit}],
    }


def _application_drilldown_overrides(
    application_field_name: str,
    app_id_field_name: str,
) -> list[dict[str, Any]]:
    # Mirror the static dashboards: app cells should jump back into the
    # existing workbench/NOC paths so the generated dashboard stays connected
    # to the rest of the demo flow.
    application_field_ref = '${__data.fields["' + app_id_field_name + '"]}'
    app_id_field_ref = "${__value.raw}"
    return [
        _field_links_override(
            application_field_name,
            _app_drilldown_links(application_field_ref),
        ),
        _field_links_override(
            app_id_field_name,
            _app_drilldown_links(app_id_field_ref),
        ),
    ]


def _alert_analysis_override(
    alert_field_name: str,
    app_id_field_name: str,
    severity_field_name: str,
) -> dict[str, Any]:
    app_ref = '${__data.fields["' + app_id_field_name + '"]}'
    severity_ref = '${__data.fields["' + severity_field_name + '"]}'
    return _field_links_override(
        alert_field_name,
        [
            {
                "title": "Open AI Analysis",
                "url": (
                    "http://localhost:8000/api/v1/uds/analyze/view"
                    f"?vessel=${{vessel}}&app={app_ref}&alert_name=${{__value.raw}}&severity={severity_ref}"
                ),
                "targetBlank": True,
            }
        ],
    )


def _field_links_override(field_name: str, links: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "matcher": {"id": "byName", "options": field_name},
        "properties": [{"id": "links", "value": links}],
    }


def _app_drilldown_links(app_ref: str) -> list[dict[str, Any]]:
    return [
        {
            "title": "Open Incident Workbench",
            "url": (
                "/d/maritime_uds_monitoring/uds-incident-workbench"
                f"?var-vessel=${{vessel}}&var-app={app_ref}&var-incident_window=${{incident_window}}"
            ),
            "targetBlank": False,
        },
        {
            "title": "Open NOC Support",
            "url": (
                "/d/maritime_noc_support/noc-support"
                f"?var-vessel=${{vessel}}&var-time_window=${{incident_window}}&var-app_filter={app_ref}"
            ),
            "targetBlank": False,
        },
    ]


def _incident_context_table_panel(panel_id: int, grid_pos: GridPos) -> dict[str, Any]:
    return _table_panel(
        panel_id,
        "Incident Context",
        grid_pos,
        _incident_context_query(),
        field_overrides=[
            _status_overrides(),
            _severity_overrides("Latest Severity"),
            *_application_drilldown_overrides("Application", "App ID"),
        ],
    )


def _application_status_table_panel(panel_id: int, grid_pos: GridPos) -> dict[str, Any]:
    return _table_panel(
        panel_id,
        "Vessel Application Status",
        grid_pos,
        _application_status_query(),
        field_overrides=[
            _status_overrides(),
            _severity_overrides("Latest Severity"),
            *_application_drilldown_overrides("Application", "App ID"),
        ],
        sort_by=[{"displayName": "Active Alerts", "desc": True}],
    )


def _recent_alerts_table_panel(panel_id: int, grid_pos: GridPos) -> dict[str, Any]:
    return _table_panel(
        panel_id,
        "Recent Alerts ($incident_window)",
        grid_pos,
        _recent_alerts_query(),
        field_overrides=[
            _severity_overrides(),
            *_application_drilldown_overrides("Application", "App ID"),
            _alert_analysis_override("Alert", "App ID", "Severity"),
        ],
        sort_by=[{"displayName": "Started", "desc": True}],
    )


def _incident_timeline_table_panel(panel_id: int, grid_pos: GridPos) -> dict[str, Any]:
    return _table_panel(
        panel_id,
        "Incident Timeline ($incident_window)",
        grid_pos,
        _incident_timeline_query(),
        field_overrides=[
            _severity_overrides("severity"),
            *_application_drilldown_overrides("application", "app_id"),
        ],
        sort_by=[{"displayName": "time", "desc": True}],
    )


def _recent_logs_table_panel(panel_id: int, grid_pos: GridPos) -> dict[str, Any]:
    return _table_panel(
        panel_id,
        "Recent Logs ($incident_window)",
        grid_pos,
        _recent_logs_query(),
        field_overrides=[
            _level_overrides(),
            *_application_drilldown_overrides("Application", "App ID"),
        ],
        sort_by=[{"displayName": "Logged At", "desc": True}],
    )


def _metric_window_summary_panel(panel_id: int, grid_pos: GridPos) -> dict[str, Any]:
    return _table_panel(
        panel_id,
        "Metric Window Summary ($incident_window)",
        grid_pos,
        _metric_window_summary_query(),
        sort_by=[{"displayName": "Metric", "desc": False}],
    )


def _metric_panel(group_key: str, panel_id: int, grid_pos: GridPos) -> dict[str, Any]:
    if group_key == "availability":
        return _timeseries_panel(
            panel_id,
            "Availability Signals ($incident_window)",
            grid_pos,
            _timeseries_query(["service_up", "health_check_status"]),
        )
    if group_key == "http_exceptions":
        return _timeseries_panel(
            panel_id,
            "HTTP And Exception History ($incident_window)",
            grid_pos,
            _timeseries_query(
                [
                    "http_request_duration_p95",
                    "http_error_rate_5xx",
                    "http_error_rate_4xx",
                    "dotnet_exceptions_rate",
                ]
            ),
            field_overrides=[
                _exact_unit_override("http_request_duration_p95", "s"),
                _exact_unit_override("http_error_rate_5xx", "percent"),
                _exact_unit_override("http_error_rate_4xx", "percent"),
            ],
        )
    if group_key == "cpu_handles":
        return _timeseries_panel(
            panel_id,
            "CPU And Handles ($incident_window)",
            grid_pos,
            _timeseries_query(["process_cpu_usage", "process_open_handles"]),
            field_overrides=[_exact_unit_override("process_cpu_usage", "percent")],
        )
    if group_key == "memory":
        return _timeseries_panel(
            panel_id,
            "Memory Footprint ($incident_window)",
            grid_pos,
            _timeseries_query(["process_memory_bytes"]),
            default_unit="bytes",
        )
    if group_key == "database_latency":
        return _timeseries_panel(
            panel_id,
            "Database Latency ($incident_window)",
            grid_pos,
            _timeseries_query(["db_query_duration_avg", "db_query_duration_p95"]),
            field_overrides=[
                _exact_unit_override("db_query_duration_avg", "s"),
                _exact_unit_override("db_query_duration_p95", "s"),
            ],
        )
    if group_key == "database_errors":
        return _timeseries_panel(
            panel_id,
            "Database Error Activity ($incident_window)",
            grid_pos,
            _timeseries_query(["db_query_rate", "db_query_errors", "db_deadlocks"]),
        )
    if group_key == "connectivity":
        return _timeseries_panel(
            panel_id,
            "Connectivity And Freshness ($incident_window)",
            grid_pos,
            _timeseries_query(["last_sync_age_seconds", "reporting_stale", "sync_delayed"]),
            field_overrides=[_exact_unit_override("last_sync_age_seconds", "s")],
        )

    raise ValueError(f"Unsupported metric panel group: {group_key}")


def _build_summary_markdown(context: DynamicDashboardContext) -> str:
    severity = context.severity or "unknown"
    app_label = context.app_name or context.app_external_id or "All applications"
    vessel_label = context.vessel_name or context.vessel_imo
    alert_label = context.alert_name or "Not specified"
    summary = context.summary or "No external summary was provided. The dashboard is using the deterministic scenario layout."
    fingerprint = context.source_alert_fingerprint or "Not provided"
    started = context.incident_started_at or "Not provided"
    scenario_label = SCENARIO_LABELS[context.scenario_key]
    scenario_description = SCENARIO_DESCRIPTIONS[context.scenario_key]

    return "\n".join(
        [
            f"# {scenario_label}",
            "",
            f"**Vessel:** {vessel_label}",
            f"**IMO:** {context.vessel_imo}",
            f"**Application:** {app_label}",
            f"**Alert:** {alert_label}",
            f"**Severity:** {severity}",
            f"**Incident Window:** {INCIDENT_WINDOW_OPTIONS[context.incident_window]}",
            f"**Started At:** {started}",
            f"**Generated At:** {context.generated_at}",
            f"**Fingerprint:** {fingerprint}",
            "",
            scenario_description,
            "",
            f"Summary: {summary}",
        ]
    )


def _incident_context_query() -> str:
    return _compact_sql(
        """
        WITH selected_vessel AS (
            SELECT id, name, imo_nr
            FROM udslocations
            WHERE imo_nr = '$vessel'
        ),
        latest_metrics AS (
            SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
                   ms.application_instance_id,
                   ms.metric_name,
                   ms.time,
                   ms.value
            FROM metric_samples ms
            WHERE ms.imo_nr = '$vessel'
            ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
        ),
        active_alerts AS (
            SELECT al.application_id, COUNT(*)::int AS active_alert_count
            FROM alerts al
            JOIN selected_vessel sv ON sv.id = al.uds_location_id
            WHERE COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
            GROUP BY al.application_id
        ),
        latest_alert AS (
            SELECT DISTINCT ON (al.application_id)
                   al.application_id,
                   al.alert_name,
                   al.severity,
                   al.starts_at
            FROM alerts al
            JOIN selected_vessel sv ON sv.id = al.uds_location_id
            ORDER BY al.application_id, al.starts_at DESC
        )
        SELECT sv.name AS "Vessel",
               sv.imo_nr AS "IMO",
               a.name AS "Application",
               a.external_id AS "App ID",
               a.app_type AS "Type",
               CASE
                   WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
                        OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0
                        THEN 'down'
                   WHEN COALESCE(aa.active_alert_count, 0) > 0 THEN 'degraded'
                   WHEN MAX(lm.time) IS NULL THEN 'unknown'
                   ELSE 'healthy'
               END AS "Current Status",
               COALESCE(aa.active_alert_count, 0) AS "Active Alerts",
               la.alert_name AS "Latest Alert",
               la.severity AS "Latest Severity",
               la.starts_at AS "Latest Incident Start",
               ROUND(COALESCE(MAX(CASE WHEN lm.metric_name = 'last_sync_age_seconds' THEN lm.value END), 0)::numeric, 0) AS "Last Sync Age (s)",
               COALESCE(MAX(CASE WHEN lm.metric_name = 'reporting_stale' THEN lm.value END), 0)::int AS "Reporting Stale",
               COALESCE(MAX(CASE WHEN lm.metric_name = 'sync_delayed' THEN lm.value END), 0)::int AS "Sync Delayed",
               MAX(lm.time) AS "Latest Sample"
        FROM selected_vessel sv
        JOIN uds_location_application_instances uai ON uai.uds_location_id = sv.id
        JOIN applications a ON a.id = uai.application_instance_id
        LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
        LEFT JOIN active_alerts aa ON aa.application_id = a.id
        LEFT JOIN latest_alert la ON la.application_id = a.id
        WHERE '${app}' = '__all' OR LOWER(a.external_id) = LOWER('${app}')
        GROUP BY sv.name, sv.imo_nr, a.id, a.name, a.external_id, a.app_type,
                 aa.active_alert_count, la.alert_name, la.severity, la.starts_at
        ORDER BY COALESCE(aa.active_alert_count, 0) DESC, la.starts_at DESC NULLS LAST, a.name
        """
    )


def _application_status_query() -> str:
    return _compact_sql(
        """
        WITH selected_vessel AS (
            SELECT id
            FROM udslocations
            WHERE imo_nr = '$vessel'
        ),
        latest_metrics AS (
            SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
                   ms.application_instance_id,
                   ms.metric_name,
                   ms.time,
                   ms.value
            FROM metric_samples ms
            WHERE ms.imo_nr = '$vessel'
            ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
        ),
        active_alerts AS (
            SELECT al.application_id, COUNT(*)::int AS active_alert_count
            FROM alerts al
            JOIN selected_vessel sv ON sv.id = al.uds_location_id
            WHERE COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
              AND (al.ends_at IS NULL OR al.ends_at > NOW())
            GROUP BY al.application_id
        ),
        latest_alert AS (
            SELECT DISTINCT ON (al.application_id)
                   al.application_id,
                   al.alert_name,
                   al.severity,
                   al.starts_at
            FROM alerts al
            JOIN selected_vessel sv ON sv.id = al.uds_location_id
            ORDER BY al.application_id, al.starts_at DESC
        )
        SELECT a.name AS "Application",
               a.external_id AS "App ID",
               CASE
                   WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
                        OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0
                        THEN 'down'
                   WHEN COALESCE(aa.active_alert_count, 0) > 0 THEN 'degraded'
                   WHEN MAX(lm.time) IS NULL THEN 'unknown'
                   ELSE 'healthy'
               END AS "Current Status",
               COALESCE(aa.active_alert_count, 0) AS "Active Alerts",
               la.alert_name AS "Latest Alert",
               la.severity AS "Latest Severity",
               la.starts_at AS "Latest Incident Start",
               ROUND(COALESCE(MAX(CASE WHEN lm.metric_name = 'last_sync_age_seconds' THEN lm.value END), 0)::numeric, 0) AS "Last Sync Age (s)",
               COALESCE(MAX(CASE WHEN lm.metric_name = 'reporting_stale' THEN lm.value END), 0)::int AS "Reporting Stale",
               COALESCE(MAX(CASE WHEN lm.metric_name = 'sync_delayed' THEN lm.value END), 0)::int AS "Sync Delayed",
               ROUND(MAX(CASE WHEN lm.metric_name = 'http_error_rate_5xx' THEN lm.value END)::numeric, 2) AS "5xx %",
               ROUND(MAX(CASE WHEN lm.metric_name = 'process_cpu_usage' THEN lm.value END)::numeric, 2) AS "CPU %",
               MAX(lm.time) AS "Latest Sample"
        FROM selected_vessel sv
        JOIN uds_location_application_instances uai ON uai.uds_location_id = sv.id
        JOIN applications a ON a.id = uai.application_instance_id
        LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
        LEFT JOIN active_alerts aa ON aa.application_id = a.id
        LEFT JOIN latest_alert la ON la.application_id = a.id
        WHERE '${app}' = '__all' OR LOWER(a.external_id) = LOWER('${app}')
        GROUP BY a.id, a.name, a.external_id, aa.active_alert_count, la.alert_name, la.severity, la.starts_at
        ORDER BY COALESCE(aa.active_alert_count, 0) DESC, la.starts_at DESC NULLS LAST, a.name
        """
    )


def _recent_alerts_query() -> str:
    return _compact_sql(
        """
        SELECT COALESCE(a.name, 'Unknown application') AS "Application",
               COALESCE(a.external_id, al.labels ->> 'app_id', '') AS "App ID",
               al.alert_name AS "Alert",
               al.severity AS "Severity",
               al.status AS "Status",
               al.alert_type AS "Type",
               al.starts_at AS "Started",
               al.ends_at AS "Ended",
               al.received_at AS "Received",
               COALESCE(al.annotations ->> 'summary', al.alert_name) AS "Summary"
        FROM alerts al
        JOIN udslocations u ON u.id = al.uds_location_id
        LEFT JOIN applications a ON a.id = al.application_id
        WHERE u.imo_nr = '$vessel'
          AND al.starts_at >= NOW() - INTERVAL '${incident_window}'
          AND (
              '${app}' = '__all'
              OR LOWER(COALESCE(a.external_id, al.labels ->> 'app_id', '')) = LOWER('${app}')
          )
        ORDER BY al.starts_at DESC
        LIMIT 200
        """
    )


def _incident_timeline_query() -> str:
    return _compact_sql(
        """
        WITH selected_vessel AS (
            SELECT id
            FROM udslocations
            WHERE imo_nr = '$vessel'
        ),
        window_start AS (
            SELECT NOW() - INTERVAL '${incident_window}' AS ts
        )
        SELECT *
        FROM (
            SELECT al.starts_at AS time,
                   'alert_started' AS event_type,
                   COALESCE(a.name, 'unknown') AS application,
                   COALESCE(a.external_id, al.labels ->> 'app_id', '') AS app_id,
                   COALESCE(al.severity, 'warning') AS severity,
                   al.alert_type AS category,
                   'firing' AS state,
                   COALESCE(al.annotations ->> 'summary', al.alert_name) AS message,
                   al.fingerprint AS correlation
            FROM alerts al
            JOIN selected_vessel sv ON sv.id = al.uds_location_id
            LEFT JOIN applications a ON a.id = al.application_id
            CROSS JOIN window_start ws
            WHERE al.starts_at >= ws.ts
              AND (
                  '${app}' = '__all'
                  OR LOWER(COALESCE(a.external_id, al.labels ->> 'app_id', '')) = LOWER('${app}')
              )
            UNION ALL
            SELECT al.ends_at AS time,
                   'alert_resolved' AS event_type,
                   COALESCE(a.name, 'unknown') AS application,
                   COALESCE(a.external_id, al.labels ->> 'app_id', '') AS app_id,
                   COALESCE(al.severity, 'warning') AS severity,
                   al.alert_type AS category,
                   'resolved' AS state,
                   COALESCE(al.annotations ->> 'summary', al.alert_name) || ' resolved' AS message,
                   al.fingerprint AS correlation
            FROM alerts al
            JOIN selected_vessel sv ON sv.id = al.uds_location_id
            LEFT JOIN applications a ON a.id = al.application_id
            CROSS JOIN window_start ws
            WHERE al.ends_at IS NOT NULL
              AND al.ends_at >= ws.ts
              AND (
                  '${app}' = '__all'
                  OR LOWER(COALESCE(a.external_id, al.labels ->> 'app_id', '')) = LOWER('${app}')
              )
            UNION ALL
            SELECT l.logged_at AS time,
                   'log' AS event_type,
                   COALESCE(a.name, l.app_external_id, 'unknown') AS application,
                   COALESCE(a.external_id, l.app_external_id, '') AS app_id,
                   LOWER(l.level) AS severity,
                   l.source AS category,
                   'observed' AS state,
                   l.message AS message,
                   l.correlation_key AS correlation
            FROM app_logs l
            JOIN selected_vessel sv ON sv.id = l.uds_location_id
            LEFT JOIN applications a ON a.id = l.application_id
            CROSS JOIN window_start ws
            WHERE l.logged_at >= ws.ts
              AND LOWER(COALESCE(l.source, '')) <> 'alerts'
              AND (
                  '${app}' = '__all'
                  OR LOWER(COALESCE(a.external_id, l.app_external_id, '')) = LOWER('${app}')
              )
        ) timeline
        ORDER BY time DESC
        LIMIT 500
        """
    )


def _recent_logs_query() -> str:
    return _compact_sql(
        """
        SELECT l.logged_at AS "Logged At",
               l.level AS "Level",
               l.source AS "Source",
               COALESCE(a.name, l.app_external_id, 'Unknown application') AS "Application",
               COALESCE(a.external_id, l.app_external_id, '') AS "App ID",
               l.message AS "Message",
               l.correlation_key AS "Correlation",
               l.context AS "Context"
        FROM app_logs l
        JOIN udslocations u ON u.id = l.uds_location_id
        LEFT JOIN applications a ON a.id = l.application_id
        WHERE u.imo_nr = '$vessel'
          AND l.logged_at >= NOW() - INTERVAL '${incident_window}'
          AND (
              '${app}' = '__all'
              OR LOWER(COALESCE(l.app_external_id, '')) = LOWER('${app}')
              OR LOWER(COALESCE(a.external_id, '')) = LOWER('${app}')
          )
        ORDER BY l.logged_at DESC
        LIMIT 100
        """
    )


def _metric_window_summary_query() -> str:
    return _compact_sql(
        """
        SELECT ms.metric_name AS "Metric",
               ROUND(MIN(ms.value)::numeric, 4) AS "Min",
               ROUND(AVG(ms.value)::numeric, 4) AS "Avg",
               ROUND(MAX(ms.value)::numeric, 4) AS "Max",
               ROUND(((ARRAY_AGG(ms.value ORDER BY ms.time DESC))[1])::numeric, 4) AS "Latest",
               MAX(ms.metric_unit) AS "Unit",
               MAX(ms.time) AS "Latest Sample"
        FROM metric_samples ms
        WHERE ms.imo_nr = '$vessel'
          AND $__timeFilter(ms.time)
          AND ms.time >= NOW() - INTERVAL '${incident_window}'
          AND (
              '${app}' = '__all'
              OR LOWER(COALESCE(ms.app_id, '')) = LOWER('${app}')
          )
        GROUP BY ms.metric_name
        ORDER BY CASE ms.metric_name
            WHEN 'service_up' THEN 1
            WHEN 'health_check_status' THEN 2
            WHEN 'process_uptime_seconds' THEN 3
            WHEN 'last_sync_age_seconds' THEN 4
            WHEN 'reporting_stale' THEN 5
            WHEN 'sync_delayed' THEN 6
            WHEN 'http_request_duration_p95' THEN 7
            WHEN 'http_error_rate_5xx' THEN 8
            WHEN 'http_error_rate_4xx' THEN 9
            WHEN 'dotnet_exceptions_rate' THEN 10
            WHEN 'process_cpu_usage' THEN 11
            WHEN 'process_memory_bytes' THEN 12
            WHEN 'process_open_handles' THEN 13
            WHEN 'db_query_duration_avg' THEN 14
            WHEN 'db_query_duration_p95' THEN 15
            WHEN 'db_query_rate' THEN 16
            WHEN 'db_query_errors' THEN 17
            WHEN 'db_deadlocks' THEN 18
            ELSE 99
        END
        """
    )


def _timeseries_query(metric_names: list[str]) -> str:
    metrics_sql = ", ".join(f"'{metric_name}'" for metric_name in metric_names)
    return _compact_sql(
        f"""
        SELECT ms.time AS "time",
               CASE
                   WHEN '${{app}}' = '{ALL_APPS_VALUE}' THEN COALESCE(ms.app_id, 'unknown') || ' | ' || ms.metric_name
                   ELSE ms.metric_name
               END AS metric,
               ms.value
        FROM metric_samples ms
        WHERE ms.imo_nr = '$vessel'
          AND ms.metric_name IN ({metrics_sql})
          AND $__timeFilter(ms.time)
          AND ms.time >= NOW() - INTERVAL '${{incident_window}}'
          AND (
              '${{app}}' = '{ALL_APPS_VALUE}'
              OR LOWER(COALESCE(ms.app_id, '')) = LOWER('${{app}}')
          )
        ORDER BY ms.time
        """
    )


def _compact_sql(sql: str) -> str:
    return " ".join(line.strip() for line in sql.splitlines() if line.strip())
