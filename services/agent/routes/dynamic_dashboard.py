"""Dynamic dashboard API routes."""

from __future__ import annotations

from html import escape
import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from dynamic.fleet_orchestrator import DynamicFleetDashboardOrchestrator, FleetTriggerRequest
from dynamic.noc_orchestrator import DynamicNOCDashboardOrchestrator, NOCTriggerRequest
from dynamic.orchestrator import DynamicDashboardOrchestrator, TriggerRequest
from scripts.inject_dynamic_incident import SCENARIOS, _fingerprint, inject as inject_dynamic_incident


router = APIRouter(tags=["dynamic-dashboard"])
orchestrator = DynamicDashboardOrchestrator()
fleet_orchestrator = DynamicFleetDashboardOrchestrator()
noc_orchestrator = DynamicNOCDashboardOrchestrator()


class DynamicTriggerRequest(BaseModel):
    mode: Literal["explicit_context", "latest_firing_alert"] = "explicit_context"
    vessel_imo: str | None = None
    app_external_id: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    source_alert_fingerprint: str | None = None
    dry_run: bool = False

    @field_validator("vessel_imo", "app_external_id", "alert_name", "severity", "source_alert_fingerprint")
    @classmethod
    def _normalize_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split()).strip()
        return normalized or None


class DynamicTriggerResponse(BaseModel):
    dashboard_uid: str
    dashboard_url: str
    scenario_key: str
    trigger_mode: str
    generated_at: str
    summary: str
    used_tools: list[str] = Field(default_factory=list)
    dry_run: bool = False
    # Populated only when dry_run=true so callers have a usable fallback
    # if Grafana is unreachable on demo day. Skipped for live runs to keep
    # the response payload small.
    dashboard_json: dict[str, Any] | None = None
    grafana_result: dict[str, Any] | None = None


class DynamicStatusRun(BaseModel):
    created_at: str
    trigger_mode: str
    vessel_imo: str
    app_external_id: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    scenario_key: str
    dashboard_uid: str
    dry_run: bool = False


class DynamicStatusResponse(BaseModel):
    status: str
    dashboard_uid: str
    dashboard_url: str
    grafana_reachable: bool
    mcp_reachable: bool
    recent_runs: list[DynamicStatusRun] = Field(default_factory=list)


class DynamicVesselOption(BaseModel):
    vessel_imo: str
    vessel_name: str
    external_id: str | None = None
    status: str
    active_alert_count: int = 0
    app_count: int = 0


class DynamicApplicationOption(BaseModel):
    app_external_id: str
    app_name: str
    status: str
    active_alert_count: int = 0
    latest_metric_at: str | None = None


class DynamicIncidentOption(BaseModel):
    fingerprint: str
    alert_name: str
    severity: str | None = None
    alert_type: str | None = None
    app_external_id: str | None = None
    app_name: str | None = None
    starts_at: str | None = None
    received_at: str | None = None
    summary: str | None = None


class DynamicVesselOptionsResponse(BaseModel):
    vessels: list[DynamicVesselOption] = Field(default_factory=list)


class DynamicApplicationOptionsResponse(BaseModel):
    vessel_imo: str
    vessel_name: str | None = None
    applications: list[DynamicApplicationOption] = Field(default_factory=list)


class DynamicIncidentOptionsResponse(BaseModel):
    vessel_imo: str
    app_external_id: str | None = None
    incidents: list[DynamicIncidentOption] = Field(default_factory=list)


class DynamicDemoRunRequest(BaseModel):
    scenario: Literal["service_down", "connectivity", "runtime_pressure", "propulsion_anomaly"]
    dry_run: bool = False


class DynamicDemoRunResponse(BaseModel):
    scenario: str
    description: str
    fingerprint: str
    trigger: DynamicTriggerResponse


class DynamicFleetTriggerRequest(BaseModel):
    mode: Literal["latest_correlated_incident", "explicit_context"] = "latest_correlated_incident"
    app_external_id: str | None = None
    alert_name: str | None = None
    dry_run: bool = False

    @field_validator("app_external_id", "alert_name")
    @classmethod
    def _normalize_fleet_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split()).strip()
        return normalized or None


class DynamicNOCTriggerRequest(BaseModel):
    mode: Literal["explicit_context", "latest_alerted_vessel"] = "explicit_context"
    vessel_imo: str | None = None
    app_external_id: str | None = None
    alert_name: str | None = None
    severity: str | None = None
    source_alert_fingerprint: str | None = None
    dry_run: bool = False

    @field_validator("vessel_imo", "app_external_id", "alert_name", "severity", "source_alert_fingerprint")
    @classmethod
    def _normalize_noc_optional_string(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split()).strip()
        return normalized or None


@router.post("/dynamic/trigger", response_model=DynamicTriggerResponse)
async def trigger_dynamic_dashboard(request: DynamicTriggerRequest):
    """Trigger one deterministic dynamic-dashboard generation run."""
    try:
        result = await orchestrator.trigger(
            TriggerRequest(
                mode=request.mode,
                dry_run=request.dry_run,
                vessel_imo=request.vessel_imo,
                app_external_id=request.app_external_id,
                alert_name=request.alert_name,
                severity=request.severity,
                source_alert_fingerprint=request.source_alert_fingerprint,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic dashboard trigger failed: {exc}") from exc

    return DynamicTriggerResponse(**result)


@router.get("/dynamic/status", response_model=DynamicStatusResponse)
async def dynamic_dashboard_status():
    """Expose readiness and recent runs for the dynamic-dashboard flow."""
    try:
        result = await orchestrator.status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic dashboard status failed: {exc}") from exc

    return DynamicStatusResponse(**result)


@router.post("/dynamic/fleet/trigger", response_model=DynamicTriggerResponse)
async def trigger_dynamic_fleet_dashboard(request: DynamicFleetTriggerRequest):
    """Trigger one deterministic fleet-focused dynamic dashboard generation run."""
    try:
        result = await fleet_orchestrator.trigger(
            FleetTriggerRequest(
                mode=request.mode,
                dry_run=request.dry_run,
                app_external_id=request.app_external_id,
                alert_name=request.alert_name,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic fleet dashboard trigger failed: {exc}") from exc

    return DynamicTriggerResponse(**result)


@router.post("/dynamic/noc/trigger", response_model=DynamicTriggerResponse)
async def trigger_dynamic_noc_dashboard(request: DynamicNOCTriggerRequest):
    """Trigger one deterministic NOC support dashboard generation run."""
    try:
        result = await noc_orchestrator.trigger(
            NOCTriggerRequest(
                mode=request.mode,
                dry_run=request.dry_run,
                vessel_imo=request.vessel_imo,
                app_external_id=request.app_external_id,
                alert_name=request.alert_name,
                severity=request.severity,
                source_alert_fingerprint=request.source_alert_fingerprint,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic NOC dashboard trigger failed: {exc}") from exc

    return DynamicTriggerResponse(**result)


@router.get("/dynamic/options/vessels", response_model=DynamicVesselOptionsResponse)
async def dynamic_vessel_options():
    """List selectable vessels for the dynamic dashboard selector."""
    try:
        fleet_status = await orchestrator.mcp_client.get_fleet_status()
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic vessel options failed: {exc}") from exc

    vessels = sorted(
        (
            DynamicVesselOption(
                vessel_imo=str(item.get("imo_nr") or ""),
                vessel_name=str(item.get("name") or item.get("imo_nr") or "Unknown vessel"),
                external_id=item.get("external_id"),
                status=str(item.get("status") or "unknown"),
                active_alert_count=int(item.get("active_alert_count") or 0),
                app_count=int(item.get("app_count") or 0),
            )
            for item in list(fleet_status.get("vessels") or [])
            if item.get("imo_nr")
        ),
        key=lambda item: (item.vessel_name.lower(), item.vessel_imo),
    )
    return DynamicVesselOptionsResponse(vessels=vessels)


@router.get("/dynamic/options/apps", response_model=DynamicApplicationOptionsResponse)
async def dynamic_application_options(vessel_imo: str):
    """List applications for one selected vessel."""
    try:
        vessel_status = await orchestrator.mcp_client.get_vessel_app_status(vessel_imo)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic application options failed: {exc}") from exc

    vessel = vessel_status.get("vessel") or {}
    applications = sorted(
        (
            DynamicApplicationOption(
                app_external_id=str(item.get("external_id") or ""),
                app_name=str(item.get("name") or item.get("external_id") or "Unknown application"),
                status=str(item.get("status") or "unknown"),
                active_alert_count=int(item.get("active_alert_count") or 0),
                latest_metric_at=item.get("latest_metric_at"),
            )
            for item in list(vessel_status.get("applications") or [])
            if item.get("external_id")
        ),
        key=lambda item: (-item.active_alert_count, item.app_name.lower(), item.app_external_id),
    )
    return DynamicApplicationOptionsResponse(
        vessel_imo=vessel_imo,
        vessel_name=vessel.get("name"),
        applications=applications,
    )


@router.get("/dynamic/options/incidents", response_model=DynamicIncidentOptionsResponse)
async def dynamic_incident_options(vessel_imo: str, app_external_id: str | None = None):
    """List active incidents for one vessel and optional application."""
    try:
        vessel_alerts = await orchestrator.mcp_client.get_vessel_alerts(vessel_imo, hours=24)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic incident options failed: {exc}") from exc

    incidents = []
    for item in list(vessel_alerts.get("alerts") or []):
        if app_external_id and item.get("app_external_id") != app_external_id:
            continue
        incidents.append(
            DynamicIncidentOption(
                fingerprint=str(item.get("fingerprint") or ""),
                alert_name=str(item.get("alert_name") or "Unknown alert"),
                severity=item.get("severity"),
                alert_type=item.get("alert_type"),
                app_external_id=item.get("app_external_id"),
                app_name=item.get("app_name"),
                starts_at=item.get("starts_at"),
                received_at=item.get("received_at"),
                summary=_annotation_summary(item.get("annotations")),
            )
        )
    incidents.sort(
        key=lambda item: (
            str(item.received_at or ""),
            str(item.starts_at or ""),
            item.alert_name.lower(),
        ),
        reverse=True,
    )
    return DynamicIncidentOptionsResponse(
        vessel_imo=vessel_imo,
        app_external_id=app_external_id,
        incidents=incidents,
    )


@router.get("/dynamic/select", response_class=HTMLResponse)
async def dynamic_dashboard_selector_page():
    """Selector UI for vessel/app/incident-driven dynamic dashboard runs."""
    return HTMLResponse(_render_dynamic_selector_html())


@router.get("/dynamic/demo", response_class=HTMLResponse)
async def dynamic_dashboard_demo_page():
    """Browser-only controls for the dynamic dashboard demo flow."""
    return HTMLResponse(_render_dynamic_demo_html())


@router.post("/dynamic/demo/run", response_model=DynamicDemoRunResponse)
async def run_dynamic_dashboard_demo(request: DynamicDemoRunRequest):
    """Inject one known scenario and regenerate the dynamic dashboard."""
    scenario_key = request.scenario
    scenario = SCENARIOS[scenario_key]
    fingerprint = _fingerprint(
        scenario["vessel_imo"],
        scenario["app_external_id"],
        scenario_key,
    )

    try:
        await inject_dynamic_incident(scenario_key)
        trigger_result = await orchestrator.trigger(
            TriggerRequest(
                mode="explicit_context",
                dry_run=request.dry_run,
                vessel_imo=scenario["vessel_imo"],
                app_external_id=scenario["app_external_id"],
                alert_name=scenario["alert_name"],
                severity=scenario["severity"],
                source_alert_fingerprint=fingerprint,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Dynamic demo run failed: {exc}") from exc

    return DynamicDemoRunResponse(
        scenario=scenario_key,
        description=scenario["description"],
        fingerprint=fingerprint,
        trigger=DynamicTriggerResponse(**trigger_result),
    )


def _annotation_summary(raw_annotations: Any) -> str | None:
    if raw_annotations is None:
        return None
    if isinstance(raw_annotations, dict):
        return raw_annotations.get("summary")
    if isinstance(raw_annotations, str):
        try:
            parsed = json.loads(raw_annotations)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed.get("summary")
    return None


def _render_dynamic_selector_html() -> str:
    dashboard_url = "http://localhost:3000/d/maritime_dynamic_incident/dynamic-incident-dashboard"
    demo_url = "/api/v1/dynamic/demo"
    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dynamic Dashboard Selector</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --ink: #17202b;
      --muted: #576275;
      --card: rgba(255,255,255,0.84);
      --line: rgba(23,32,43,0.12);
      --hero: #18314f;
      --hero-ink: #f7f2e9;
      --accent: #b85d17;
      --accent-soft: rgba(184,93,23,0.12);
      --warn: #9b2c2c;
      --shadow: 0 18px 42px rgba(16,37,66,0.12);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(184,93,23,0.16), transparent 26rem),
        radial-gradient(circle at top right, rgba(24,49,79,0.16), transparent 26rem),
        linear-gradient(180deg, #f9f4ec 0%, var(--bg) 100%);
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 24px auto 40px;
      display: grid;
      gap: 18px;
    }}
    .hero {{
      padding: 28px;
      border-radius: 24px;
      color: var(--hero-ink);
      background: linear-gradient(135deg, rgba(24,49,79,0.98), rgba(17,37,66,0.92));
      box-shadow: var(--shadow);
    }}
    .eyebrow {{
      margin: 0 0 8px;
      font-size: 0.78rem;
      letter-spacing: 0.16em;
      text-transform: uppercase;
      opacity: 0.8;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.7rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }}
    .hero p {{
      max-width: 58rem;
      margin: 14px 0 0;
      color: rgba(247,242,233,0.88);
      line-height: 1.55;
      font-size: 1.02rem;
    }}
    .hero-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .hero-actions a {{
      text-decoration: none;
      color: var(--hero-ink);
      border: 1px solid rgba(247,242,233,0.2);
      padding: 10px 16px;
      border-radius: 999px;
      background: rgba(247,242,233,0.08);
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 1.2fr) minmax(300px, 0.9fr);
      gap: 18px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 22px;
      box-shadow: 0 12px 28px rgba(16,37,66,0.08);
      backdrop-filter: blur(10px);
    }}
    .selector-card, .status-card {{
      padding: 22px;
    }}
    .selector-card h2, .status-card h2 {{
      margin: 0 0 16px;
      font-size: 1.1rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .selector-grid {{
      display: grid;
      gap: 14px;
    }}
    .field {{
      display: grid;
      gap: 8px;
    }}
    label {{
      font-size: 0.92rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
    }}
    select, button {{
      width: 100%;
      font: inherit;
      border-radius: 14px;
    }}
    select {{
      appearance: none;
      padding: 13px 14px;
      border: 1px solid rgba(23,32,43,0.14);
      background: rgba(255,255,255,0.92);
      color: var(--ink);
    }}
    .checkbox-row {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 4px 0;
      color: var(--muted);
      text-transform: none;
      letter-spacing: normal;
    }}
    .checkbox-row input {{
      width: 18px;
      height: 18px;
      accent-color: var(--accent);
    }}
    .actions {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      padding-top: 4px;
    }}
    .actions button {{
      width: auto;
      border: none;
      padding: 12px 18px;
      cursor: pointer;
    }}
    .primary {{
      background: var(--accent);
      color: white;
    }}
    .secondary {{
      background: rgba(24,49,79,0.08);
      color: var(--ink);
    }}
    .status-card {{
      display: grid;
      gap: 14px;
      align-content: start;
    }}
    .pill {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      width: fit-content;
      padding: 8px 12px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 700;
    }}
    .summary-box {{
      padding: 16px;
      border-radius: 16px;
      background: rgba(24,49,79,0.05);
      min-height: 120px;
    }}
    .summary-box strong {{
      display: block;
      margin-bottom: 8px;
    }}
    .summary-box p {{
      margin: 0;
      line-height: 1.5;
      color: var(--muted);
    }}
    .meta {{
      display: grid;
      gap: 8px;
      font-size: 0.96rem;
    }}
    .meta div {{
      display: grid;
      grid-template-columns: 110px 1fr;
      gap: 10px;
    }}
    .meta span:first-child {{
      color: var(--muted);
    }}
    .status-line {{
      min-height: 1.4rem;
      color: var(--muted);
      margin: 0;
    }}
    .status-line.error {{
      color: var(--warn);
    }}
    .hint {{
      margin: 0;
      line-height: 1.5;
      color: var(--muted);
    }}
    .links {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .links a {{
      color: var(--accent);
      text-decoration: none;
      font-weight: 700;
    }}
    code {{
      font-family: "Cascadia Code", Consolas, monospace;
    }}
    @media (max-width: 900px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">Dynamic Dashboard Selector</p>
      <h1>Pick the incident first.</h1>
      <p>
        Choose a vessel, narrow to one application, and then generate the incident-focused
        Grafana dashboard for that exact context. This uses the same dynamic trigger backend
        as the demo flow, but lets an operator decide what to inspect.
      </p>
      <div class="hero-actions">
        <a href="{escape(demo_url)}">Open Demo Controls</a>
        <a href="{escape(dashboard_url)}" target="_blank" rel="noreferrer">Open Current Dashboard</a>
      </div>
    </section>

    <section class="layout">
      <article class="card selector-card">
        <h2>Context</h2>
        <div class="selector-grid">
          <div class="field">
            <label for="vesselSelect">Ship</label>
            <select id="vesselSelect">
              <option value="">Loading vessels...</option>
            </select>
          </div>

          <div class="field">
            <label for="appSelect">Application</label>
            <select id="appSelect" disabled>
              <option value="">Choose a ship first</option>
            </select>
          </div>

          <div class="field">
            <label for="incidentSelect">Incident</label>
            <select id="incidentSelect" disabled>
              <option value="">Choose an application first</option>
            </select>
          </div>

          <label class="checkbox-row" for="dryRun">
            <input id="dryRun" type="checkbox">
            Generate as dry run if you only want the payload and summary
          </label>

          <div class="actions">
            <button class="primary" id="generateButton" type="button" disabled>Generate Dashboard</button>
            <button class="secondary" id="refreshButton" type="button">Refresh Lists</button>
          </div>
        </div>
      </article>

      <aside class="card status-card">
        <h2>Run Status</h2>
        <span class="pill">Operator-Driven</span>
        <div class="summary-box">
          <strong id="summaryTitle">No incident selected yet</strong>
          <p id="summaryCopy">Pick a ship, application, and alert to generate the dashboard for that specific context.</p>
        </div>
        <div class="meta">
          <div><span>Ship</span><span id="metaVessel">-</span></div>
          <div><span>Application</span><span id="metaApp">-</span></div>
          <div><span>Severity</span><span id="metaSeverity">-</span></div>
          <div><span>Fingerprint</span><span id="metaFingerprint">-</span></div>
        </div>
        <p class="status-line" id="statusLine"></p>
        <div class="links">
          <a href="{escape(dashboard_url)}" id="dashboardLink" target="_blank" rel="noreferrer">Open Current Dynamic Dashboard</a>
        </div>
        <p class="hint">
          The selected incident is sent to <code>POST /api/v1/dynamic/trigger</code> with
          <code>explicit_context</code>, so the same dashboard UID is regenerated for your choice.
        </p>
      </aside>
    </section>
  </main>

  <script>
    const vesselSelect = document.getElementById("vesselSelect");
    const appSelect = document.getElementById("appSelect");
    const incidentSelect = document.getElementById("incidentSelect");
    const dryRunInput = document.getElementById("dryRun");
    const generateButton = document.getElementById("generateButton");
    const refreshButton = document.getElementById("refreshButton");
    const statusLine = document.getElementById("statusLine");
    const summaryTitle = document.getElementById("summaryTitle");
    const summaryCopy = document.getElementById("summaryCopy");
    const metaVessel = document.getElementById("metaVessel");
    const metaApp = document.getElementById("metaApp");
    const metaSeverity = document.getElementById("metaSeverity");
    const metaFingerprint = document.getElementById("metaFingerprint");
    const dashboardLink = document.getElementById("dashboardLink");

    let vesselOptions = [];
    let appOptions = [];
    let incidentOptions = [];

    function setStatus(message, isError = false) {{
      statusLine.textContent = message;
      statusLine.className = isError ? "status-line error" : "status-line";
    }}

    function resetSelect(select, placeholder, disabled = true) {{
      select.innerHTML = "";
      const option = document.createElement("option");
      option.value = "";
      option.textContent = placeholder;
      select.appendChild(option);
      select.disabled = disabled;
    }}

    function selectedOption(list, key, value) {{
      return list.find((item) => item[key] === value) || null;
    }}

    function updateSidebar() {{
      const vessel = selectedOption(vesselOptions, "vessel_imo", vesselSelect.value);
      const app = selectedOption(appOptions, "app_external_id", appSelect.value);
      const incident = selectedOption(incidentOptions, "fingerprint", incidentSelect.value);
      metaVessel.textContent = vessel ? `${{vessel.vessel_name}} (${{vessel.vessel_imo}})` : "-";
      metaApp.textContent = app ? `${{app.app_name}} (${{app.app_external_id}})` : "-";
      metaSeverity.textContent = incident?.severity || "-";
      metaFingerprint.textContent = incident?.fingerprint || "-";
      summaryTitle.textContent = incident ? incident.alert_name : "No incident selected yet";
      summaryCopy.textContent = incident?.summary || "Pick a ship, application, and alert to generate the dashboard for that specific context.";
      generateButton.disabled = !(vessel && app);
    }}

    function syncQueryParams() {{
      const params = new URLSearchParams(window.location.search);
      if (vesselSelect.value) {{
        params.set("vessel_imo", vesselSelect.value);
      }} else {{
        params.delete("vessel_imo");
      }}
      if (appSelect.value) {{
        params.set("app_external_id", appSelect.value);
      }} else {{
        params.delete("app_external_id");
      }}
      if (incidentSelect.value) {{
        params.set("source_alert_fingerprint", incidentSelect.value);
      }} else {{
        params.delete("source_alert_fingerprint");
      }}
      const query = params.toString();
      const next = query ? `${{window.location.pathname}}?${{query}}` : window.location.pathname;
      window.history.replaceState(null, "", next);
    }}

    async function loadVessels() {{
      setStatus("Loading vessels...");
      resetSelect(vesselSelect, "Loading vessels...", true);
      const res = await fetch("/api/v1/dynamic/options/vessels");
      if (!res.ok) {{
        throw new Error("Could not load vessels");
      }}
      const data = await res.json();
      vesselOptions = data.vessels || [];
      resetSelect(vesselSelect, "Select a ship", false);
      for (const vessel of vesselOptions) {{
        const option = document.createElement("option");
        option.value = vessel.vessel_imo;
        option.textContent = `${{vessel.vessel_name}} (${{vessel.status}}, ${{vessel.active_alert_count}} alerts)`;
        vesselSelect.appendChild(option);
      }}
      setStatus(vesselOptions.length ? "Choose a ship to continue." : "No vessels available.");
    }}

    async function loadApps(vesselImo, preferredApp = "") {{
      appOptions = [];
      resetSelect(appSelect, vesselImo ? "Loading applications..." : "Choose a ship first", !vesselImo);
      resetSelect(incidentSelect, "Choose an application first", true);
      if (!vesselImo) {{
        updateSidebar();
        return;
      }}
      const res = await fetch(`/api/v1/dynamic/options/apps?vessel_imo=${{encodeURIComponent(vesselImo)}}`);
      if (!res.ok) {{
        throw new Error("Could not load applications");
      }}
      const data = await res.json();
      appOptions = data.applications || [];
      resetSelect(appSelect, appOptions.length ? "Select an application" : "No applications found", false);
      for (const app of appOptions) {{
        const option = document.createElement("option");
        option.value = app.app_external_id;
        option.textContent = `${{app.app_name}} (${{app.status}}, ${{app.active_alert_count}} alerts)`;
        appSelect.appendChild(option);
      }}
      if (preferredApp && appOptions.some((item) => item.app_external_id === preferredApp)) {{
        appSelect.value = preferredApp;
      }}
      updateSidebar();
      await loadIncidents(vesselImo, appSelect.value);
    }}

    async function loadIncidents(vesselImo, appExternalId, preferredFingerprint = "") {{
      incidentOptions = [];
      if (!vesselImo) {{
        resetSelect(incidentSelect, "Choose an application first", true);
        updateSidebar();
        return;
      }}
      if (!appExternalId) {{
        resetSelect(incidentSelect, "Choose an application first", true);
        updateSidebar();
        return;
      }}
      resetSelect(incidentSelect, "Loading incidents...", true);
      const query = new URLSearchParams({{ vessel_imo: vesselImo, app_external_id: appExternalId }});
      const res = await fetch(`/api/v1/dynamic/options/incidents?${{query.toString()}}`);
      if (!res.ok) {{
        throw new Error("Could not load incidents");
      }}
      const data = await res.json();
      incidentOptions = data.incidents || [];
      resetSelect(
        incidentSelect,
        incidentOptions.length ? "Select an incident (optional)" : "No active incidents for this application",
        false
      );
      for (const incident of incidentOptions) {{
        const option = document.createElement("option");
        option.value = incident.fingerprint;
        option.textContent = `${{incident.alert_name}} (${{incident.severity || "n/a"}})`;
        incidentSelect.appendChild(option);
      }}
      if (preferredFingerprint && incidentOptions.some((item) => item.fingerprint === preferredFingerprint)) {{
        incidentSelect.value = preferredFingerprint;
      }}
      updateSidebar();
    }}

    async function generateDashboard() {{
      const vessel = selectedOption(vesselOptions, "vessel_imo", vesselSelect.value);
      const app = selectedOption(appOptions, "app_external_id", appSelect.value);
      const incident = selectedOption(incidentOptions, "fingerprint", incidentSelect.value);
      if (!vessel || !app) {{
        setStatus("Pick both a ship and an application first.", true);
        return;
      }}
      generateButton.disabled = true;
      setStatus("Generating dynamic dashboard...");
      try {{
        const payload = {{
          mode: "explicit_context",
          vessel_imo: vessel.vessel_imo,
          app_external_id: app.app_external_id,
          alert_name: incident?.alert_name || null,
          severity: incident?.severity || null,
          source_alert_fingerprint: incident?.fingerprint || null,
          dry_run: dryRunInput.checked,
        }};
        const res = await fetch("/api/v1/dynamic/trigger", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(payload),
        }});
        const data = await res.json();
        if (!res.ok) {{
          throw new Error(data.detail || "Dynamic trigger failed");
        }}
        summaryTitle.textContent = data.scenario_key.replaceAll("_", " ");
        summaryCopy.textContent = data.summary;
        dashboardLink.href = data.dashboard_url;
        setStatus(data.dry_run ? "Dry run complete. Summary and JSON were generated." : "Dashboard regenerated successfully.");
        if (!data.dry_run) {{
          window.open(data.dashboard_url, "_blank", "noopener,noreferrer");
        }}
      }} catch (error) {{
        setStatus(error.message || "Dynamic trigger failed", true);
      }} finally {{
        generateButton.disabled = false;
      }}
    }}

    async function bootstrap() {{
      const params = new URLSearchParams(window.location.search);
      const preferredVessel = params.get("vessel_imo") || "";
      const preferredApp = params.get("app_external_id") || "";
      const preferredFingerprint = params.get("source_alert_fingerprint") || "";
      try {{
        await loadVessels();
        if (preferredVessel && vesselOptions.some((item) => item.vessel_imo === preferredVessel)) {{
          vesselSelect.value = preferredVessel;
        }}
        await loadApps(vesselSelect.value, preferredApp);
        if (preferredFingerprint) {{
          await loadIncidents(vesselSelect.value, appSelect.value, preferredFingerprint);
        }}
        updateSidebar();
        syncQueryParams();
      }} catch (error) {{
        setStatus(error.message || "Failed to load selector data", true);
      }}
    }}

    vesselSelect.addEventListener("change", async () => {{
      syncQueryParams();
      try {{
        await loadApps(vesselSelect.value);
        setStatus("Application list updated.");
      }} catch (error) {{
        setStatus(error.message || "Failed to load applications", true);
      }}
      syncQueryParams();
    }});

    appSelect.addEventListener("change", async () => {{
      syncQueryParams();
      try {{
        await loadIncidents(vesselSelect.value, appSelect.value);
        setStatus("Incident list updated.");
      }} catch (error) {{
        setStatus(error.message || "Failed to load incidents", true);
      }}
      syncQueryParams();
    }});

    incidentSelect.addEventListener("change", () => {{
      updateSidebar();
      syncQueryParams();
    }});

    refreshButton.addEventListener("click", bootstrap);
    generateButton.addEventListener("click", generateDashboard);
    bootstrap();
  </script>
</body>
</html>
""".strip()


def _render_dynamic_demo_html() -> str:
    scenario_cards = []
    accent_by_key = {
        "service_down": "#d65d0e",
        "connectivity": "#2a7f62",
        "runtime_pressure": "#9c3f3f",
    }
    for key, scenario in SCENARIOS.items():
        title = key.replace("_", " ").title()
        accent = accent_by_key.get(key, "#5a6577")
        scenario_cards.append(
            f"""
            <article class="scenario-card" style="--accent:{accent}">
              <p class="scenario-kicker">{escape(title)}</p>
              <h2>{escape(scenario["alert_name"])}</h2>
              <p class="scenario-copy">{escape(scenario["description"])}</p>
              <dl class="scenario-meta">
                <div><dt>Vessel</dt><dd>{escape(scenario["vessel_imo"])}</dd></div>
                <div><dt>Application</dt><dd>{escape(scenario["app_external_id"])}</dd></div>
                <div><dt>Severity</dt><dd>{escape(scenario["severity"])}</dd></div>
              </dl>
              <div class="scenario-actions">
                <button class="run-live" onclick="runScenario('{escape(key)}', false)">Run Live Demo</button>
                <button class="run-dry" onclick="runScenario('{escape(key)}', true)">Dry Run</button>
              </div>
            </article>
            """
        )

    scenario_json = json.dumps(SCENARIOS)
    dashboard_url = "http://localhost:3000/d/maritime_dynamic_incident/dynamic-incident-dashboard"

    return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dynamic Dashboard Demo Controls</title>
  <style>
    :root {{
      --bg: #f3ede2;
      --ink: #17202b;
      --muted: #5a6577;
      --card: rgba(255,255,255,0.78);
      --line: rgba(23,32,43,0.12);
      --hero: #102542;
      --hero-ink: #f7f3eb;
      --ok: #2b7a4b;
      --warn: #b56c1d;
      --error: #9b2c2c;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(214,93,14,0.12), transparent 28rem),
        radial-gradient(circle at top right, rgba(16,37,66,0.14), transparent 28rem),
        linear-gradient(180deg, #f8f3ea 0%, var(--bg) 100%);
      min-height: 100vh;
    }}
    main {{
      width: min(1180px, calc(100vw - 32px));
      margin: 24px auto 40px;
      display: grid;
      gap: 18px;
    }}
    .hero {{
      background: linear-gradient(135deg, rgba(16,37,66,0.97), rgba(24,49,80,0.92));
      color: var(--hero-ink);
      border-radius: 24px;
      padding: 28px;
      box-shadow: 0 18px 40px rgba(16,37,66,0.18);
    }}
    .eyebrow {{
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.16em;
      font-size: 0.78rem;
      opacity: 0.78;
    }}
    h1 {{
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.8rem);
      line-height: 0.95;
      letter-spacing: -0.04em;
    }}
    .hero p:last-of-type {{
      max-width: 60rem;
      font-size: 1.05rem;
      line-height: 1.55;
      color: rgba(247,243,235,0.88);
    }}
    .hero-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 18px;
    }}
    .hero-actions a, .hero-actions button {{
      appearance: none;
      border: 1px solid rgba(247,243,235,0.22);
      background: rgba(247,243,235,0.08);
      color: var(--hero-ink);
      border-radius: 999px;
      padding: 10px 16px;
      font: inherit;
      text-decoration: none;
      cursor: pointer;
    }}
    .layout {{
      display: grid;
      grid-template-columns: 1.35fr 0.9fr;
      gap: 18px;
    }}
    .scenario-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
    }}
    .scenario-card, .status-card, .guide-card {{
      background: var(--card);
      backdrop-filter: blur(12px);
      border: 1px solid var(--line);
      border-radius: 20px;
      box-shadow: 0 10px 25px rgba(16,37,66,0.08);
    }}
    .scenario-card {{
      padding: 18px;
      border-top: 4px solid var(--accent);
    }}
    .scenario-kicker {{
      margin: 0 0 8px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.72rem;
      color: var(--accent);
    }}
    .scenario-card h2 {{
      margin: 0;
      font-size: 1.5rem;
      line-height: 1.05;
    }}
    .scenario-copy {{
      min-height: 4.2rem;
      color: var(--muted);
      line-height: 1.45;
    }}
    .scenario-meta {{
      display: grid;
      gap: 8px;
      margin: 12px 0 16px;
    }}
    .scenario-meta div {{
      display: grid;
      grid-template-columns: 90px 1fr;
      gap: 10px;
      font-size: 0.95rem;
    }}
    .scenario-meta dt {{
      color: var(--muted);
    }}
    .scenario-meta dd {{
      margin: 0;
      font-weight: 600;
      word-break: break-word;
    }}
    .scenario-actions {{
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
    }}
    .scenario-actions button {{
      appearance: none;
      border: none;
      border-radius: 999px;
      padding: 10px 14px;
      font: inherit;
      cursor: pointer;
    }}
    .run-live {{
      background: var(--accent);
      color: white;
    }}
    .run-dry {{
      background: rgba(16,37,66,0.08);
      color: var(--ink);
    }}
    .status-card, .guide-card {{
      padding: 18px;
    }}
    .status-card h2, .guide-card h2 {{
      margin: 0 0 14px;
      font-size: 1.1rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }}
    .status-banner {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: rgba(43,122,75,0.12);
      color: var(--ok);
      font-weight: 700;
    }}
    .status-copy {{
      margin-top: 16px;
      line-height: 1.55;
      color: var(--muted);
    }}
    .summary-box {{
      margin-top: 16px;
      background: rgba(16,37,66,0.05);
      border-radius: 16px;
      padding: 14px;
    }}
    .summary-box strong {{
      display: block;
      margin-bottom: 6px;
      font-size: 1rem;
    }}
    .summary-box p {{
      margin: 0;
      line-height: 1.45;
    }}
    .result-meta {{
      display: grid;
      gap: 8px;
      margin-top: 16px;
      font-size: 0.95rem;
    }}
    .result-meta div {{
      display: grid;
      grid-template-columns: 116px 1fr;
      gap: 10px;
    }}
    .result-meta span:first-child {{
      color: var(--muted);
    }}
    .tool-list {{
      margin: 14px 0 0;
      padding-left: 18px;
      line-height: 1.55;
      color: var(--muted);
    }}
    .guide-card ol {{
      margin: 0;
      padding-left: 18px;
      line-height: 1.6;
      color: var(--muted);
    }}
    .guide-card p {{
      color: var(--muted);
      line-height: 1.55;
    }}
    .status-error {{
      background: rgba(155,44,44,0.12);
      color: var(--error);
    }}
    .status-warn {{
      background: rgba(181,108,29,0.14);
      color: var(--warn);
    }}
    @media (max-width: 920px) {{
      .layout {{
        grid-template-columns: 1fr;
      }}
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <p class="eyebrow">Dynamic Dashboard MVP</p>
      <h1>Demo Scenario Controls</h1>
      <p>
        Simulate a known vessel application incident, let the agent regenerate the
        Grafana dashboard, then switch to the dashboard tab and refresh. This is a
        demo operator panel, not a production workflow.
      </p>
      <div class="hero-actions">
        <a href="/api/v1/dynamic/select">Open Incident Selector</a>
        <a href="{escape(dashboard_url)}" target="_blank" rel="noreferrer">Open Dashboard</a>
        <a href="/api/v1/dynamic/status" target="_blank" rel="noreferrer">Open Status JSON</a>
        <button type="button" onclick="refreshStatus()">Refresh Status</button>
      </div>
    </section>

    <section class="layout">
      <section class="scenario-grid">
        {''.join(scenario_cards)}
      </section>

      <section>
        <article class="status-card">
          <h2>Run Status</h2>
          <div id="statusBanner" class="status-banner">Ready</div>
          <p id="statusCopy" class="status-copy">
            Pick one scenario, wait for the run to finish, then refresh the Grafana tab.
          </p>
          <div class="summary-box">
            <strong id="resultHeadline">No scenario triggered yet</strong>
            <p id="resultSummary">The latest live run will appear here with the incident summary and used tools.</p>
          </div>
          <div class="result-meta" id="resultMeta">
            <div><span>Dashboard</span><span>{escape(dashboard_url)}</span></div>
            <div><span>Trigger mode</span><span>-</span></div>
            <div><span>Scenario</span><span>-</span></div>
            <div><span>Dry run</span><span>-</span></div>
          </div>
          <ul class="tool-list" id="toolList">
            <li>Used tools will appear here after a run.</li>
          </ul>
        </article>

        <article class="guide-card" style="margin-top:18px">
          <h2>Demo Flow</h2>
          <ol>
            <li>Click one scenario button here.</li>
            <li>Wait for the green success status.</li>
            <li>Switch to the Grafana dashboard tab and press Ctrl+F5.</li>
            <li>Point at Incident Summary, Incident Context, and Scenario Trends.</li>
          </ol>
          <p>
            The goal is to show the same dashboard workspace being rewritten around a
            different incident, not a brand-new UI layout every time.
          </p>
        </article>
      </section>
    </section>
  </main>

  <script>
    const dashboardUrl = {json.dumps(dashboard_url)};
    const scenarioData = {scenario_json};

    function setStatus(text, tone) {{
      const banner = document.getElementById("statusBanner");
      banner.textContent = text;
      banner.className = "status-banner";
      if (tone === "error") {{
        banner.classList.add("status-error");
      }} else if (tone === "warn") {{
        banner.classList.add("status-warn");
      }}
    }}

    function renderTrigger(trigger, scenario, description, fingerprint) {{
      document.getElementById("statusCopy").textContent =
        "Run complete. Refresh the Grafana dashboard tab to show the new incident context.";
      document.getElementById("resultHeadline").textContent =
        `${{scenario.replaceAll("_", " ")}} -> ${{trigger.scenario_key}}`;
      document.getElementById("resultSummary").textContent = trigger.summary;
      document.getElementById("resultMeta").innerHTML = `
        <div><span>Dashboard</span><span><a href="${{dashboardUrl}}" target="_blank" rel="noreferrer">${{trigger.dashboard_uid}}</a></span></div>
        <div><span>Trigger mode</span><span>${{trigger.trigger_mode}}</span></div>
        <div><span>Scenario</span><span>${{trigger.scenario_key}}</span></div>
        <div><span>Dry run</span><span>${{trigger.dry_run}}</span></div>
        <div><span>Fingerprint</span><span>${{fingerprint}}</span></div>
        <div><span>Description</span><span>${{description}}</span></div>
      `;
      const tools = trigger.used_tools || [];
      document.getElementById("toolList").innerHTML = tools.length
        ? tools.map((tool) => `<li>${{tool}}</li>`).join("")
        : "<li>No tool trace returned.</li>";
    }}

    async function refreshStatus() {{
      try {{
        const res = await fetch("/api/v1/dynamic/status");
        if (!res.ok) throw new Error(`Status request failed (${{res.status}})`);
        const data = await res.json();
        if (data.status === "ok") {{
          setStatus("System Ready", "ok");
          document.getElementById("statusCopy").textContent =
            `Grafana reachable: ${{data.grafana_reachable}}. MCP reachable: ${{data.mcp_reachable}}.`;
        }} else {{
          setStatus("Status Unclear", "warn");
        }}
      }} catch (error) {{
        setStatus("Status Check Failed", "error");
        document.getElementById("statusCopy").textContent = String(error);
      }}
    }}

    async function runScenario(scenario, dryRun) {{
      const scenarioTitle = scenario.replaceAll("_", " ");
      setStatus(dryRun ? "Running Dry Run..." : "Running Live Demo...", "warn");
      document.getElementById("statusCopy").textContent =
        `Injecting and triggering ${{scenarioTitle}}. This can take a few seconds.`;
      try {{
        const res = await fetch("/api/v1/dynamic/demo/run", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ scenario, dry_run: dryRun }}),
        }});
        const data = await res.json();
        if (!res.ok) {{
          throw new Error(data.detail || `Demo run failed (${{res.status}})`);
        }}
        setStatus(dryRun ? "Dry Run Ready" : "Dashboard Updated", "ok");
        renderTrigger(data.trigger, data.scenario, data.description, data.fingerprint);
      }} catch (error) {{
        setStatus("Run Failed", "error");
        document.getElementById("statusCopy").textContent = String(error);
      }}
    }}

    refreshStatus();
  </script>
</body>
</html>
""".strip()


@router.get("/dynamic/monitor", response_class=HTMLResponse)
async def dynamic_monitor_page(presentation: bool = False):
    """Presentation shell: Grafana iframe + catastrophic event overlay.

    Open this page during a demo. Press **L** to stage a critical incident.
    A dramatic overlay appears; clicking *Investigate* opens the generated
    dynamic dashboard in Grafana.
    """
    return HTMLResponse(_render_monitor_html(presentation=presentation))


def _render_monitor_html(*, presentation: bool = False) -> str:
    grafana_workbench = (
        "http://localhost:3000/d/maritime_uds_monitoring/uds-incident-workbench"
        "?orgId=1&kiosk"
    )
    scenario_json = json.dumps(SCENARIOS)
    body_class = "presentation-mode" if presentation else ""

    return """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Maritime Monitoring — Live</title>
<style>
  :root {
    --red: #F2495C;
    --red-glow: rgba(242,73,92,0.45);
    --dark: #0b0e13;
    --card: #11151d;
    --border: #1e2533;
    --text: #e4e8f0;
    --muted: #6b7a90;
    --accent: #5794F2;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  html, body {
    height: 100%; width: 100%;
    overflow: hidden;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: var(--dark);
    color: var(--text);
  }

  /* ---- Grafana iframe fills everything ---- */
  #grafana-frame {
    position: fixed; inset: 0;
    width: 100%; height: 100%;
    border: none;
    z-index: 1;
  }

  /* ---- Subtle status bar at bottom ---- */
  #status-bar {
    position: fixed; bottom: 0; left: 0; right: 0;
    height: 32px;
    background: linear-gradient(90deg, rgba(11,14,19,0.92), rgba(11,14,19,0.96));
    backdrop-filter: blur(8px);
    display: flex; align-items: center;
    padding: 0 16px;
    gap: 10px;
    z-index: 5;
    border-top: 1px solid var(--border);
    font-size: 11px;
    color: var(--muted);
    letter-spacing: 0.5px;
  }
  body.presentation-mode #status-bar {
    display: none;
  }
  #status-bar .dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #73BF69;
    box-shadow: 0 0 6px #73BF69;
    animation: blink-dot 1.4s step-start infinite;
  }
  #status-bar.alert-active .dot {
    background: var(--red);
    box-shadow: 0 0 8px var(--red);
  }
  @keyframes blink-dot {
    0%,100% { opacity: 1; } 50% { opacity: 0.15; }
  }

  /* ---- Keyboard hint ---- */
  .kbd {
    display: inline-block;
    padding: 1px 6px;
    border-radius: 3px;
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    font-family: monospace;
    font-size: 10px;
    color: var(--muted);
  }

  /* ---- Full-screen overlay ---- */
  #overlay {
    position: fixed; inset: 0;
    z-index: 100;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  #overlay.visible {
    display: flex;
  }

  /* Backdrop dims and blurs the Grafana iframe */
  #overlay-backdrop {
    position: absolute; inset: 0;
    background: rgba(8,4,4,0.70);
    backdrop-filter: blur(6px);
    animation: fade-in 0.4s ease-out;
  }
  @keyframes fade-in {
    from { opacity: 0; } to { opacity: 1; }
  }

  /* The alert card itself */
  #alert-card {
    position: relative;
    z-index: 101;
    width: min(640px, 90vw);
    background: var(--card);
    border: 1px solid var(--red);
    border-radius: 16px;
    box-shadow:
      0 0 40px var(--red-glow),
      0 0 120px rgba(242,73,92,0.15),
      0 20px 60px rgba(0,0,0,0.5);
    animation: card-enter 0.5s cubic-bezier(0.16,1,0.3,1);
    overflow: hidden;
  }
  @keyframes card-enter {
    from { opacity: 0; transform: translateY(30px) scale(0.96); }
    to   { opacity: 1; transform: translateY(0) scale(1); }
  }

  /* Pulsing red top strip */
  #alert-strip {
    height: 5px;
    background: var(--red);
    animation: strip-pulse 1.8s ease-in-out infinite;
  }
  @keyframes strip-pulse {
    0%,100% { opacity: 1; box-shadow: 0 0 12px var(--red-glow); }
    50%     { opacity: 0.6; box-shadow: 0 0 30px var(--red-glow); }
  }

  /* Header area with icon + title */
  #alert-header {
    padding: 28px 32px 0;
    display: flex;
    align-items: flex-start;
    gap: 16px;
  }

  #alert-icon {
    flex-shrink: 0;
    width: 52px; height: 52px;
    border-radius: 14px;
    background: rgba(242,73,92,0.12);
    border: 1px solid rgba(242,73,92,0.25);
    display: flex; align-items: center; justify-content: center;
    font-size: 26px;
    animation: icon-pulse 2s ease-in-out infinite;
  }
  @keyframes icon-pulse {
    0%,100% { transform: scale(1); }
    50%     { transform: scale(1.08); }
  }

  #alert-title-block { flex: 1; min-width: 0; }

  #alert-label {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--red);
    margin-bottom: 6px;
  }

  #alert-title {
    font-size: 22px;
    font-weight: 700;
    line-height: 1.25;
    color: #fff;
  }

  #alert-subtitle {
    margin-top: 4px;
    font-size: 13px;
    color: var(--muted);
  }

  /* Severity badge */
  #alert-severity {
    flex-shrink: 0;
    padding: 5px 16px;
    border-radius: 20px;
    background: var(--red);
    color: #fff;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    animation: badge-beat 1.6s ease-in-out infinite;
  }
  @keyframes badge-beat {
    0%,100% { transform: scale(1); }
    50%     { transform: scale(1.06); }
  }

  /* Body content */
  #alert-body {
    padding: 20px 32px 0;
  }

  #alert-summary {
    font-size: 16px;
    line-height: 1.5;
    font-weight: 600;
    color: var(--text);
    padding: 14px 18px;
    background: rgba(242,73,92,0.06);
    border-left: 3px solid var(--red);
    border-radius: 0 8px 8px 0;
    margin-bottom: 10px;
  }

  #alert-next-step {
    font-size: 12px;
    line-height: 1.45;
    color: var(--muted);
    margin-bottom: 18px;
  }

  /* Detail grid */
  #alert-details {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px 20px;
    margin-bottom: 8px;
  }
  .detail-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  .detail-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--muted);
  }
  .detail-value {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
  }

  /* Action bar */
  #alert-actions {
    padding: 20px 32px 28px;
    display: flex;
    align-items: center;
    gap: 12px;
  }

  #btn-investigate {
    flex: 1;
    appearance: none;
    border: none;
    padding: 14px 24px;
    border-radius: 10px;
    background: var(--red);
    color: #fff;
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.5px;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  #btn-investigate:hover {
    background: #e5384b;
    box-shadow: 0 0 20px var(--red-glow);
    transform: translateY(-1px);
  }

  #btn-dismiss {
    appearance: none;
    border: 1px solid var(--border);
    background: transparent;
    color: var(--muted);
    padding: 14px 20px;
    border-radius: 10px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
  }
  #btn-dismiss:hover {
    border-color: var(--muted);
    color: var(--text);
  }

  /* ---- Processing spinner overlay ---- */
  #processing {
    position: fixed; inset: 0;
    z-index: 200;
    display: none;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(8,4,4,0.80);
    backdrop-filter: blur(8px);
  }
  #processing.visible { display: flex; }

  .spinner {
    width: 48px; height: 48px;
    border: 3px solid var(--border);
    border-top-color: var(--red);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
    margin-bottom: 20px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  #processing-text {
    font-size: 14px;
    color: var(--text);
    letter-spacing: 0.5px;
  }
  #processing-sub {
    font-size: 12px;
    color: var(--muted);
    margin-top: 6px;
  }

  /* ---- Sound effect visual cue (screen flash) ---- */
  @keyframes screen-flash {
    0%   { opacity: 0.3; }
    100% { opacity: 0; }
  }
  #screen-flash {
    position: fixed; inset: 0;
    background: var(--red);
    z-index: 300;
    pointer-events: none;
    opacity: 0;
  }
  #screen-flash.flash {
    animation: screen-flash 0.4s ease-out;
  }

  @media (max-width: 760px) {
    #alert-header,
    #alert-body,
    #alert-actions {
      padding-left: 22px;
      padding-right: 22px;
    }

    #alert-details {
      grid-template-columns: 1fr;
      gap: 12px;
    }
  }
</style>
</head>
<body class=\"""" + body_class + """\">

<iframe id="grafana-frame"
        src=\"""" + grafana_workbench + """\"
        allow="fullscreen"></iframe>

<div id="status-bar">
  <div class="dot"></div>
  <span id="status-text">Maritime Monitoring — Live</span>
  <span id="status-hint" style="margin-left:auto; display:flex; align-items:center; gap:10px;">
    <button id="btn-stage" onclick="stageCriticalEvent()"
      style="appearance:none; border:1px solid rgba(242,73,92,0.4); background:rgba(242,73,92,0.1);
             color:#F2495C; padding:3px 12px; border-radius:4px; font-size:11px; font-weight:600;
             cursor:pointer; letter-spacing:0.5px;">
      STAGE EVENT
    </button>
    <button id="btn-reset" onclick="document.getElementById('grafana-frame').src=GRAFANA_WORKBENCH; dismiss();"
      style="appearance:none; border:1px solid var(--border); background:transparent;
             color:var(--muted); padding:3px 10px; border-radius:4px; font-size:11px;
             cursor:pointer;">
      RESET
    </button>
    <span style="color:var(--border);">|</span>
    <span class="kbd">L</span> <span class="kbd">R</span> <span class="kbd">Esc</span>
  </span>
</div>

<div id="screen-flash"></div>

<div id="processing">
  <div class="spinner"></div>
  <div id="processing-text">Detecting anomaly pattern...</div>
  <div id="processing-sub">Agent is analyzing MCP data sources</div>
</div>

<div id="overlay">
  <div id="overlay-backdrop"></div>
  <div id="alert-card">
    <div id="alert-strip"></div>
    <div id="alert-header">
      <div id="alert-icon">&#9888;&#65039;</div>
      <div id="alert-title-block">
        <div id="alert-label">CRITICAL INCIDENT DETECTED</div>
        <div id="alert-title">—</div>
        <div id="alert-subtitle">—</div>
      </div>
      <div id="alert-severity">CRITICAL</div>
    </div>
    <div id="alert-body">
      <div id="alert-summary">—</div>
      <div id="alert-next-step">Open the investigation dashboard to review propulsion metrics and agent analysis.</div>
      <div id="alert-details">
        <div class="detail-item">
          <span class="detail-label">Vessel</span>
          <span class="detail-value" id="det-vessel">—</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Affected System</span>
          <span class="detail-value" id="det-system">—</span>
        </div>
        <div class="detail-item">
          <span class="detail-label">Detected At</span>
          <span class="detail-value" id="det-time">—</span>
        </div>
      </div>
    </div>
    <div id="alert-actions">
      <button id="btn-investigate" onclick="investigate()">
        <span>&#128269;</span> Open Investigation
      </button>
      <button id="btn-dismiss" onclick="dismiss()">Dismiss</button>
    </div>
  </div>
</div>

<script>
  const SCENARIOS = """ + scenario_json + """;
  const GRAFANA_WORKBENCH = '""" + grafana_workbench + """';

  // Always use the propulsion anomaly scenario for demo
  const DEMO_SCENARIO = 'propulsion_anomaly';

  const VESSEL_NAMES = {
    'IMO9300001': 'MV Edge Aurora',
    'IMO9300002': 'MV Edge Borealis',
    'IMO9300003': 'MT Nordic Fjord',
  };

  let dashboardUrl = null;
  let isRunning = false;

  /* ---- Focus management ----
     The iframe steals keyboard focus. We reclaim it whenever the
     user moves the mouse, so L/R/Esc work reliably. */
  window.addEventListener('mousemove', () => {
    if (document.activeElement === document.getElementById('grafana-frame')) {
      window.focus();
    }
  });
  // Also reclaim on any click on the status bar area
  document.getElementById('status-bar').addEventListener('click', () => window.focus());

  /* ---- Keyboard listener ---- */
  document.addEventListener('keydown', (e) => {
    if (e.key === 'l' || e.key === 'L') {
      if (!isRunning) stageCriticalEvent();
    }
    if (e.key === 'r' || e.key === 'R') {
      document.getElementById('grafana-frame').src = GRAFANA_WORKBENCH;
      dismiss();
    }
    if (e.key === 'Escape') dismiss();
  });

  /* ---- Stage the event ---- */
  async function stageCriticalEvent() {
    if (isRunning) return;
    isRunning = true;
    document.getElementById('btn-stage').disabled = true;
    const scenarioKey = DEMO_SCENARIO;

    // 1. Show processing spinner
    document.getElementById('processing').classList.add('visible');
    document.getElementById('status-bar').classList.add('alert-active');

    // 2. Animate processing text
    const phases = [
      ['Detecting anomaly pattern...', 'Scanning vessel telemetry streams'],
      ['Correlating sensor signals...', 'Matching against known failure modes'],
      ['Agent analyzing incident...', 'Calling MCP tools for context'],
      ['Generating incident dashboard...', 'Building Grafana visualization'],
    ];
    let phase = 0;
    const phaseTimer = setInterval(() => {
      phase++;
      if (phase < phases.length) {
        document.getElementById('processing-text').textContent = phases[phase][0];
        document.getElementById('processing-sub').textContent = phases[phase][1];
      }
    }, 1500);

    try {
      // 3. Call the existing demo/run endpoint
      const res = await fetch('/api/v1/dynamic/demo/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario: scenarioKey, dry_run: false }),
      });

      clearInterval(phaseTimer);

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Trigger failed');
      }

      const data = await res.json();
      dashboardUrl = data.trigger.dashboard_url;

      // 4. Hide processing, flash screen, show overlay
      document.getElementById('processing').classList.remove('visible');

      const flash = document.getElementById('screen-flash');
      flash.classList.add('flash');
      setTimeout(() => flash.classList.remove('flash'), 500);

      showOverlay(data, scenarioKey);

    } catch (err) {
      clearInterval(phaseTimer);
      document.getElementById('processing').classList.remove('visible');
      document.getElementById('status-bar').classList.remove('alert-active');
      alert('Event staging failed: ' + err.message);
      isRunning = false;
      document.getElementById('btn-stage').disabled = false;
    }
  }

  /* ---- Populate and show the overlay ---- */
  function showOverlay(data, scenarioKey) {
    const t = data.trigger;
    const s = SCENARIOS[scenarioKey];
    const vesselName = VESSEL_NAMES[s.vessel_imo] || s.vessel_imo;

    // Content
    document.getElementById('alert-label').textContent = 'CRITICAL EVENT';
    document.getElementById('alert-title').textContent =
      'Propulsion anomaly detected';
    document.getElementById('alert-subtitle').textContent =
      vesselName + ' \\u00b7 Immediate investigation required';
    document.getElementById('alert-severity').textContent = 'CRITICAL';
    document.getElementById('alert-summary').textContent =
      'Multiple propulsion signals deviated at the same time. Possible propeller obstruction or impact damage.';
    document.getElementById('det-vessel').textContent = vesselName + ' (' + s.vessel_imo + ')';
    document.getElementById('det-system').textContent = 'Propulsion line';
    document.getElementById('det-time').textContent = new Date(t.generated_at).toLocaleString();

    // Show
    document.getElementById('overlay').classList.add('visible');
  }

  /* ---- Actions ---- */
  function investigate() {
    if (dashboardUrl) {
      document.getElementById('grafana-frame').src = dashboardUrl + '?orgId=1&kiosk';
    }
    dismiss();
  }

  function dismiss() {
    document.getElementById('overlay').classList.remove('visible');
    document.getElementById('status-bar').classList.remove('alert-active');
    isRunning = false;
    document.getElementById('btn-stage').disabled = false;
  }
</script>
</body>
</html>
""".strip()
