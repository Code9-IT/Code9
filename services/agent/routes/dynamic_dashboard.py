"""Dynamic dashboard API routes."""

from __future__ import annotations

from html import escape
import json
from typing import Any, Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from dynamic.orchestrator import DynamicDashboardOrchestrator, TriggerRequest
from scripts.inject_dynamic_incident import SCENARIOS, _fingerprint, inject as inject_dynamic_incident


router = APIRouter(tags=["dynamic-dashboard"])
orchestrator = DynamicDashboardOrchestrator()


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


class DynamicDemoRunRequest(BaseModel):
    scenario: Literal["service_down", "connectivity", "runtime_pressure"]
    dry_run: bool = False


class DynamicDemoRunResponse(BaseModel):
    scenario: str
    description: str
    fingerprint: str
    trigger: DynamicTriggerResponse


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
