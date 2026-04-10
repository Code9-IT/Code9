"""Build Grafana dashboard JSON dicts for each incident scenario.

All panels use the ``timescaledb`` datasource UID (provisioned in
grafana/provisioning/datasources/timescaledb.yaml).

The stable dashboard UID ``maritime_dynamic_incident`` ensures that every
trigger call overwrites the same slot in Grafana instead of creating new
dashboards.
"""

from __future__ import annotations

DASHBOARD_UID = "maritime_dynamic_incident"
DATASOURCE_UID = "timescaledb"

# Per-scenario visual identity (colors, icons)
_STYLE = {
    "service_down": {
        "accent":    "#F2495C",
        "bg_from":   "#1a0808",
        "bg_to":     "#1e1e2e",
        "border":    "#4a1010",
        "icon":      "&#128308;",   # 🔴
        "label":     "SERVICE DOWN",
    },
    "runtime_pressure": {
        "accent":    "#FF780A",
        "bg_from":   "#1a1000",
        "bg_to":     "#1e1e2e",
        "border":    "#4a2800",
        "icon":      "&#128992;",   # 🟠
        "label":     "RUNTIME PRESSURE",
    },
    "connectivity": {
        "accent":    "#5794F2",
        "bg_from":   "#080e1a",
        "bg_to":     "#1e1e2e",
        "border":    "#102040",
        "icon":      "&#128309;",   # 🔵
        "label":     "CONNECTIVITY ISSUE",
    },
    "generic_incident": {
        "accent":    "#FADE2A",
        "bg_from":   "#181400",
        "bg_to":     "#1e1e2e",
        "border":    "#3a3000",
        "icon":      "&#128993;",   # 🟡
        "label":     "INCIDENT",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _datasource() -> dict:
    return {"type": "postgres", "uid": DATASOURCE_UID}


def _base_panel(panel_id: int, title: str, panel_type: str, x: int, y: int, w: int, h: int) -> dict:
    return {
        "id": panel_id,
        "title": title,
        "type": panel_type,
        "datasource": _datasource(),
        "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "options": {},
        "fieldConfig": {"defaults": {}, "overrides": []},
        "targets": [],
    }


# ---------------------------------------------------------------------------
# Animated panels (new)
# ---------------------------------------------------------------------------

def _animated_incident_header(
    panel_id: int,
    scenario_key: str,
    vessel_imo: str,
    app_external_id: str,
    alert_name: str,
    severity: str,
) -> dict:
    """Full-width animated HTML banner — the visual centrepiece of the generated dashboard."""
    st = _STYLE.get(scenario_key, _STYLE["generic_incident"])
    a = st["accent"]
    sev_label = (severity.upper() + " &#9888;") if severity else "ACTIVE &#9888;"

    html = (
        f'<style>'
        f'@keyframes pulse-glow{{0%,100%{{box-shadow:0 0 6px {a}66,0 0 14px {a}33;opacity:1}}'
        f'50%{{box-shadow:0 0 22px {a}cc,0 0 40px {a}66;opacity:0.92}}}}'
        f'@keyframes badge-beat{{0%,100%{{transform:scale(1);background:{a}}}'
        f'50%{{transform:scale(1.06);background:{a}aa}}}}'
        f'@keyframes dot-blink{{0%,100%{{opacity:1}}49%{{opacity:1}}50%{{opacity:0}}99%{{opacity:0}}}}'
        f'@keyframes slide-in{{from{{transform:translateX(-24px);opacity:0}}to{{transform:translateX(0);opacity:1}}}}'
        f'@keyframes gradient-drift{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}'
        f'.inc-banner{{display:flex;align-items:center;padding:10px 20px;gap:14px;'
        f'background:linear-gradient(270deg,{st["bg_from"]},{st["bg_to"]},{st["bg_from"]});'
        f'background-size:300% 300%;'
        f'animation:pulse-glow 2.2s ease-in-out infinite,gradient-drift 12s ease infinite,slide-in 0.5s ease-out;'
        f'border-radius:8px;border-left:5px solid {a};border-top:1px solid {st["border"]};'
        f'border-bottom:1px solid {st["border"]};font-family:system-ui,sans-serif}}'
        f'.inc-dot{{width:10px;height:10px;border-radius:50%;background:{a};'
        f'box-shadow:0 0 8px {a};animation:dot-blink 1s step-start infinite;flex-shrink:0}}'
        f'.inc-icon{{font-size:22px;flex-shrink:0}}'
        f'.inc-body{{flex:1;min-width:0}}'
        f'.inc-title{{font-size:16px;font-weight:700;color:#fff;white-space:nowrap;overflow:hidden;'
        f'text-overflow:ellipsis;margin-bottom:3px}}'
        f'.inc-sub{{font-size:11px;color:#999;letter-spacing:.5px}}'
        f'.inc-right{{display:flex;flex-direction:column;align-items:flex-end;gap:5px;flex-shrink:0}}'
        f'.sev-badge{{padding:3px 14px;border-radius:20px;font-size:11px;font-weight:700;'
        f'color:#111;animation:badge-beat 1.6s ease-in-out infinite;white-space:nowrap}}'
        f'.scenario-tag{{font-size:10px;color:{a};letter-spacing:1.5px;text-transform:uppercase}}'
        f'</style>'
        f'<div class="inc-banner">'
        f'<div class="inc-dot"></div>'
        f'<span class="inc-icon">{st["icon"]}</span>'
        f'<div class="inc-body">'
        f'<div class="inc-title">{app_external_id} &mdash; {alert_name or "Incident detected"}</div>'
        f'<div class="inc-sub">Vessel&nbsp;{vessel_imo}&nbsp;&nbsp;&#183;&nbsp;&nbsp;'
        f'Dashboard auto-generated by Maritime AI Agent&nbsp;&nbsp;&#183;&nbsp;&nbsp;'
        f'Refreshes every 30 s</div>'
        f'</div>'
        f'<div class="inc-right">'
        f'<span class="sev-badge" style="background:{a}">{sev_label}</span>'
        f'<span class="scenario-tag">{st["label"]}</span>'
        f'</div>'
        f'</div>'
    )

    return {
        "id": panel_id,
        "title": "",
        "type": "text",
        "datasource": {"type": "datasource", "uid": "-- Mixed --"},
        "gridPos": {"x": 0, "y": 0, "w": 24, "h": 3},
        "options": {"mode": "html", "content": html},
        "fieldConfig": {"defaults": {}, "overrides": []},
        "targets": [],
        "transparent": True,
    }


def _severity_stat(panel_id: int, title: str, sql: str, x: int, y: int, warn: int, crit: int, unit: str = "short") -> dict:
    """Stat panel with background color that reacts to live alert counts."""
    return {
        "id": panel_id,
        "title": title,
        "type": "stat",
        "datasource": _datasource(),
        "gridPos": {"x": x, "y": y, "w": 6, "h": 4},
        "options": {
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
            "orientation": "horizontal",
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "textMode": "auto",
        },
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "thresholds"},
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": warn},
                        {"color": "red",    "value": crit},
                    ],
                },
            },
            "overrides": [],
        },
        "targets": [
            {"datasource": _datasource(), "format": "table", "rawSql": sql, "refId": "A"}
        ],
    }


def _severity_stats_row(vessel_imo: str, app_external_id: str, y: int) -> list[dict]:
    """Four stat panels at row y — react to live data with background colours."""
    return [
        _severity_stat(
            20, "Critical Alerts",
            f"SELECT COUNT(*)::int FROM alerts a "
            f"JOIN udslocations l ON l.id=a.uds_location_id "
            f"JOIN applications app ON app.id=a.application_id "
            f"WHERE l.imo_nr='{vessel_imo}' AND app.external_id='{app_external_id}' "
            f"AND a.severity='critical' AND a.status='firing'",
            0, y, warn=1, crit=2,
        ),
        _severity_stat(
            21, "All Active Alerts",
            f"SELECT COUNT(*)::int FROM alerts a "
            f"JOIN udslocations l ON l.id=a.uds_location_id "
            f"WHERE l.imo_nr='{vessel_imo}' AND a.status='firing'",
            6, y, warn=2, crit=6,
        ),
        _severity_stat(
            22, "Apps Affected",
            f"SELECT COUNT(DISTINCT a.application_id)::int FROM alerts a "
            f"JOIN udslocations l ON l.id=a.uds_location_id "
            f"WHERE l.imo_nr='{vessel_imo}' AND a.status='firing'",
            12, y, warn=2, crit=4,
        ),
        _severity_stat(
            23, "Incident Age (min)",
            f"SELECT ROUND(EXTRACT(EPOCH FROM (NOW() - MIN(a.starts_at)))/60)::int "
            f"FROM alerts a JOIN udslocations l ON l.id=a.uds_location_id "
            f"JOIN applications app ON app.id=a.application_id "
            f"WHERE l.imo_nr='{vessel_imo}' AND app.external_id='{app_external_id}' "
            f"AND a.status='firing'",
            18, y, warn=10, crit=60, unit="none",
        ),
    ]


# ---------------------------------------------------------------------------
# Existing data panels (unchanged queries, updated y positions)
# ---------------------------------------------------------------------------

def _app_status_panel(panel_id: int, vessel_imo: str, x: int, y: int, w: int, h: int) -> dict:
    panel = _base_panel(panel_id, f"App Status \u2014 {vessel_imo}", "table", x, y, w, h)
    panel["targets"] = [{
        "datasource": _datasource(), "format": "table", "refId": "A",
        "rawSql": (
            f'SELECT app.external_id AS "Application",'
            f' CASE'
            f'   WHEN COUNT(CASE WHEN a.severity IN (\'critical\',\'high\') AND a.status=\'firing\' THEN 1 END)>0 THEN \'critical\''
            f'   WHEN COUNT(CASE WHEN a.status=\'firing\' THEN 1 END)>0 THEN \'degraded\''
            f'   ELSE \'healthy\' END AS "Status",'
            f' COUNT(CASE WHEN a.status=\'firing\' THEN 1 END)::int AS "Active Alerts",'
            f' MAX(ms.time) AS "Last Metric"'
            f' FROM uds_location_application_instances uai'
            f' JOIN udslocations loc ON loc.id=uai.uds_location_id'
            f' JOIN applications app ON app.id=uai.application_instance_id'
            f' LEFT JOIN alerts a ON a.uds_location_id=loc.id AND a.application_id=app.id'
            f' LEFT JOIN metric_samples ms ON ms.imo_nr=loc.imo_nr AND ms.application_instance_id=app.id'
            f' WHERE loc.imo_nr=\'{vessel_imo}\''
            f' GROUP BY app.external_id ORDER BY "Status" DESC, app.external_id'
        ),
    }]
    panel["options"] = {"sortBy": [{"displayName": "Status", "desc": True}], "footer": {"show": False}}
    panel["fieldConfig"] = {
        "defaults": {},
        "overrides": [{
            "matcher": {"id": "byName", "options": "Status"},
            "properties": [
                {"id": "custom.displayMode", "value": "color-background"},
                {"id": "mappings", "value": [
                    {"type": "value", "options": {"critical": {"text": "Critical", "color": "red"}}},
                    {"type": "value", "options": {"degraded": {"text": "Degraded", "color": "orange"}}},
                    {"type": "value", "options": {"healthy":  {"text": "Healthy",  "color": "green"}}},
                ]},
            ],
        }],
    }
    return panel


def _active_alerts_panel(panel_id: int, vessel_imo: str, app_external_id: str, x: int, y: int, w: int, h: int) -> dict:
    panel = _base_panel(panel_id, f"Active Alerts \u2014 {app_external_id}", "table", x, y, w, h)
    panel["targets"] = [{
        "datasource": _datasource(), "format": "table", "refId": "A",
        "rawSql": (
            f'SELECT a.alert_name AS "Alert", a.severity AS "Severity",'
            f' a.status AS "Status", a.alert_type AS "Type",'
            f' a.starts_at AS "Started At",'
            f' COALESCE(a.annotations->>\'summary\',\'\') AS "Summary"'
            f' FROM alerts a'
            f' JOIN udslocations loc ON loc.id=a.uds_location_id'
            f' JOIN applications app ON app.id=a.application_id'
            f' WHERE loc.imo_nr=\'{vessel_imo}\' AND app.external_id=\'{app_external_id}\''
            f' AND a.status=\'firing\' ORDER BY a.starts_at DESC LIMIT 20'
        ),
    }]
    panel["options"] = {"footer": {"show": False}}
    panel["fieldConfig"] = {
        "defaults": {},
        "overrides": [{
            "matcher": {"id": "byName", "options": "Severity"},
            "properties": [
                {"id": "custom.displayMode", "value": "color-background"},
                {"id": "mappings", "value": [
                    {"type": "value", "options": {"critical": {"color": "red"}}},
                    {"type": "value", "options": {"high":     {"color": "orange"}}},
                    {"type": "value", "options": {"warning":  {"color": "yellow"}}},
                    {"type": "value", "options": {"info":     {"color": "blue"}}},
                ]},
            ],
        }],
    }
    return panel


def _metric_history_panel(panel_id: int, vessel_imo: str, app_external_id: str, x: int, y: int, w: int, h: int) -> dict:
    panel = _base_panel(panel_id, f"Metric History \u2014 {app_external_id}", "timeseries", x, y, w, h)
    panel["targets"] = [{
        "datasource": _datasource(), "format": "time_series", "refId": "A",
        "rawSql": (
            f'SELECT ms.time AS "time", ms.value AS "Value", ms.metric_name AS "metric"'
            f' FROM metric_samples ms'
            f' JOIN applications app ON app.id=ms.application_instance_id'
            f' WHERE ms.imo_nr=\'{vessel_imo}\' AND app.external_id=\'{app_external_id}\''
            f' AND ms.time >= NOW() - INTERVAL \'6 hours\' ORDER BY ms.time ASC'
        ),
    }]
    panel["options"] = {
        "tooltip": {"mode": "multi"},
        "legend": {"displayMode": "list", "placement": "bottom"},
    }
    panel["fieldConfig"] = {"defaults": {"custom": {"lineWidth": 2}}, "overrides": []}
    return panel


def _logs_panel(panel_id: int, vessel_imo: str, app_external_id: str, x: int, y: int, w: int, h: int) -> dict:
    panel = _base_panel(panel_id, f"Recent Logs \u2014 {app_external_id}", "table", x, y, w, h)
    panel["targets"] = [{
        "datasource": _datasource(), "format": "table", "refId": "A",
        "rawSql": (
            f'SELECT l.logged_at AS "Time", l.level AS "Level",'
            f' l.source AS "Source", l.message AS "Message"'
            f' FROM app_logs l'
            f' JOIN udslocations loc ON loc.id=l.uds_location_id'
            f' WHERE loc.imo_nr=\'{vessel_imo}\' AND l.app_external_id=\'{app_external_id}\''
            f' AND l.logged_at >= NOW() - INTERVAL \'6 hours\' ORDER BY l.logged_at DESC LIMIT 50'
        ),
    }]
    panel["options"] = {"footer": {"show": False}}
    panel["fieldConfig"] = {
        "defaults": {},
        "overrides": [{
            "matcher": {"id": "byName", "options": "Level"},
            "properties": [
                {"id": "custom.displayMode", "value": "color-background"},
                {"id": "mappings", "value": [
                    {"type": "value", "options": {"error":    {"color": "red"}}},
                    {"type": "value", "options": {"critical": {"color": "red"}}},
                    {"type": "value", "options": {"warning":  {"color": "orange"}}},
                    {"type": "value", "options": {"info":     {"color": "blue"}}},
                ]},
            ],
        }],
    }
    return panel


def _alert_trend_panel(panel_id: int, vessel_imo: str, x: int, y: int, w: int, h: int) -> dict:
    panel = _base_panel(panel_id, "Alert Trend \u2014 Last 24 h", "barchart", x, y, w, h)
    panel["targets"] = [{
        "datasource": _datasource(), "format": "time_series", "refId": "A",
        "rawSql": (
            f'SELECT time_bucket(\'1 hour\', a.starts_at) AS "time",'
            f' COUNT(*)::int AS "Alerts", a.severity AS "severity"'
            f' FROM alerts a JOIN udslocations loc ON loc.id=a.uds_location_id'
            f' WHERE loc.imo_nr=\'{vessel_imo}\' AND a.starts_at >= NOW() - INTERVAL \'24 hours\''
            f' GROUP BY 1, a.severity ORDER BY 1 ASC'
        ),
    }]
    panel["options"] = {
        "orientation": "auto", "groupWidth": 0.7,
        "legend": {"displayMode": "list", "placement": "bottom"},
    }
    return panel


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def _base_dashboard(scenario_key: str, vessel_imo: str, app_external_id: str, title: str) -> dict:
    return {
        "uid":           DASHBOARD_UID,
        "title":         title,
        "tags":          ["dynamic", "maritime", scenario_key],
        "timezone":      "browser",
        "refresh":       "30s",
        "schemaVersion": 39,
        "version":       0,
        "panels":        [],
        "time":          {"from": "now-6h", "to": "now"},
        "timepicker":    {},
        "templating":    {"list": []},
        "annotations":   {"list": []},
    }


def build_service_down(vessel_imo: str, app_external_id: str, summary: str,
                       alert_name: str = "", severity: str = "") -> dict:
    title = f"Incident: Service Down \u2014 {app_external_id} on {vessel_imo}"
    dash = _base_dashboard("service_down", vessel_imo, app_external_id, title)
    # y=0  h=3   animated header
    # y=3  h=4   severity stats row
    # y=7  h=8   app status + alerts
    # y=15 h=8   logs full-width
    dash["panels"] = (
        [_animated_incident_header(1, "service_down", vessel_imo, app_external_id, alert_name, severity)]
        + _severity_stats_row(vessel_imo, app_external_id, y=3)
        + [
            _app_status_panel(5, vessel_imo,                           x=0,  y=7,  w=12, h=8),
            _active_alerts_panel(6, vessel_imo, app_external_id,       x=12, y=7,  w=12, h=8),
            _logs_panel(7, vessel_imo, app_external_id,                x=0,  y=15, w=24, h=8),
        ]
    )
    return dash


def build_runtime_pressure(vessel_imo: str, app_external_id: str, summary: str,
                            alert_name: str = "", severity: str = "") -> dict:
    title = f"Incident: Runtime Pressure \u2014 {app_external_id} on {vessel_imo}"
    dash = _base_dashboard("runtime_pressure", vessel_imo, app_external_id, title)
    dash["panels"] = (
        [_animated_incident_header(1, "runtime_pressure", vessel_imo, app_external_id, alert_name, severity)]
        + _severity_stats_row(vessel_imo, app_external_id, y=3)
        + [
            _metric_history_panel(5, vessel_imo, app_external_id,      x=0,  y=7,  w=16, h=8),
            _active_alerts_panel(6, vessel_imo, app_external_id,       x=16, y=7,  w=8,  h=8),
            _app_status_panel(7, vessel_imo,                           x=0,  y=15, w=12, h=8),
            _logs_panel(8, vessel_imo, app_external_id,                x=12, y=15, w=12, h=8),
        ]
    )
    return dash


def build_connectivity(vessel_imo: str, app_external_id: str, summary: str,
                       alert_name: str = "", severity: str = "") -> dict:
    title = f"Incident: Connectivity \u2014 {app_external_id} on {vessel_imo}"
    dash = _base_dashboard("connectivity", vessel_imo, app_external_id, title)
    dash["panels"] = (
        [_animated_incident_header(1, "connectivity", vessel_imo, app_external_id, alert_name, severity)]
        + _severity_stats_row(vessel_imo, app_external_id, y=3)
        + [
            _alert_trend_panel(5, vessel_imo,                          x=0,  y=7,  w=12, h=8),
            _active_alerts_panel(6, vessel_imo, app_external_id,       x=12, y=7,  w=12, h=8),
            _metric_history_panel(7, vessel_imo, app_external_id,      x=0,  y=15, w=16, h=8),
            _logs_panel(8, vessel_imo, app_external_id,                x=16, y=15, w=8,  h=8),
        ]
    )
    return dash


def build_generic_incident(vessel_imo: str, app_external_id: str, summary: str,
                            alert_name: str = "", severity: str = "") -> dict:
    title = f"Incident: {app_external_id} on {vessel_imo}"
    dash = _base_dashboard("generic_incident", vessel_imo, app_external_id, title)
    dash["panels"] = (
        [_animated_incident_header(1, "generic_incident", vessel_imo, app_external_id, alert_name, severity)]
        + _severity_stats_row(vessel_imo, app_external_id, y=3)
        + [
            _app_status_panel(5, vessel_imo,                           x=0,  y=7,  w=12, h=8),
            _active_alerts_panel(6, vessel_imo, app_external_id,       x=12, y=7,  w=12, h=8),
            _metric_history_panel(7, vessel_imo, app_external_id,      x=0,  y=15, w=16, h=8),
            _logs_panel(8, vessel_imo, app_external_id,                x=16, y=15, w=8,  h=8),
        ]
    )
    return dash


_BUILDERS = {
    "service_down":     build_service_down,
    "runtime_pressure": build_runtime_pressure,
    "connectivity":     build_connectivity,
    "generic_incident": build_generic_incident,
}


def build_dashboard(
    scenario_key: str,
    vessel_imo: str,
    app_external_id: str,
    summary: str = "",
    alert_name: str = "",
    severity: str = "",
) -> dict:
    """Return the Grafana dashboard dict for the given scenario.

    Args:
        scenario_key: One of ``service_down``, ``runtime_pressure``,
            ``connectivity``, or ``generic_incident``.
        vessel_imo: IMO number, e.g. ``IMO9300001``.
        app_external_id: Application external ID, e.g. ``data-quality-processor``.
        summary: Context summary to log (not displayed directly; used in run log).
        alert_name: Triggering alert name — shown in the animated header.
        severity: Alert severity — drives the badge colour in the header.
    """
    builder = _BUILDERS.get(scenario_key, build_generic_incident)
    return builder(vessel_imo, app_external_id, summary, alert_name, severity)
