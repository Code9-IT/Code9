# Demo Script

Step-by-step guide for demonstrating the Maritime Agentic Observability platform.
Use this for stakeholder demos and internal dry runs.

## Current Presentation Goal

The repo already contains a strong static observability foundation:
- Fleet Overview
- UDS Incident Workbench
- NOC Support
- AI Analysis
- AI Chat
- Alert Trends

The **current sprint demo target** is the new dynamic-dashboard flow layered on
top of that foundation:

1. show the existing baseline dashboard state
2. trigger or inject one incident
3. call the dynamic endpoint
4. show that a generated dashboard appears or updates in Grafana
5. use the existing dashboards as supporting context and fallback drilldown

If the dynamic flow is not fully ready on demo day, use the fallback demo path
further down in this document.

## Before the Demo

### Start the stack (10-15 minutes before)

```bash
docker compose down -v
docker compose up -d --build
```

### Wait for data

```bash
docker compose logs -f uds-seeder
```

Wait for `Backfill complete` so historical data is ready.

### Verify services

- Grafana: `http://localhost:3000` (admin / code9-demo-admin)
- Agent API: `http://localhost:8000/docs`
- MCP API: `http://localhost:8001/docs`

### Pre-warm the LLM (optional)

Open `http://localhost:8000/docs` and send one small analysis request so
Ollama is warm before the presentation.

## Preferred Demo Flow: Dynamic Dashboard Pivot

### 1. Problem framing (1 minute)

Talking point:
Traditional dashboards show what we preselected. The new goal is to let the
system notice what matters now and generate the right dashboard for the current
incident.

Open Grafana at `http://localhost:3000`.

### 2. Baseline state (1-2 minutes)

Open **Fleet Overview** first, then the **UDS Incident Workbench** for
`IMO9300001`.

Show:
- vessel-level status
- active alerts
- application health
- recent context already available in the foundation

Talking point:
This is the implemented observability base. It already supports the three user
stories through static dashboards and MCP-backed analysis.

### 3. Trigger the dynamic flow (2-3 minutes)

Use the dynamic path once it is ready:
- inject or select the incident scenario
- call `POST /api/v1/dynamic/trigger`
- use either `explicit_context` or the alert-driven mode, depending on what is
  stable on demo day

Show:
- the trigger request or UI action
- the returned dashboard URL / UID
- the generated dashboard in Grafana under `maritime_dynamic_incident`

Talking point:
This is the pivot. The system is no longer only explaining a static dashboard;
it is generating or updating the dashboard itself for the incident at hand.

### 4. Explain why the generated dashboard changed (1-2 minutes)

Show the generated dashboard and point out:
- top summary / explanation panel
- scenario-specific panels
- incident context
- links back to the existing dashboards

Talking point:
The dashboard structure is selected for the situation. That is the key
"beyond traditional dashboards" argument in the thesis.

### 5. Use the existing dashboards as supporting drilldown (2-3 minutes)

From the generated dashboard, return to:
- **UDS Incident Workbench** for single-vessel context
- **NOC Support** for full investigation context
- **Fleet Overview** if you need to remind the audience how the issue fits into
  the broader vessel state

Talking point:
The generated dashboard does not replace the foundation. It sits on top of it.

## Fallback Demo Flow: Existing Implemented Prototype

Use this if the dynamic flow is unavailable or only partially stable.

### 1. Fleet Overview (2 minutes)

Open **Fleet Overview**.

Show:
- all 3 vessels with operational status
- active alert counts
- where the most interesting vessel is

### 2. Single Vessel Incident Investigation (3 minutes)

Open **UDS Incident Workbench** for `IMO9300001`.

Show:
- application health overview
- active alerts
- recent metrics
- application logs

### 3. NOC Support Investigation (2 minutes)

Open **NOC Support** for `IMO9300001`.

Show:
- operational snapshot
- incident timeline
- connectivity state

### 4. AI Analysis (3 minutes)

Preferred path:
- click **AI Analysis** from an alert in **UDS Incident Workbench** or
  **NOC Support**

Optional legacy fallback:
- use `/api/v1/analyze/{event_id}/view` from **Ship Operations**

Show:
- AI-generated analysis text
- suggested actions
- confidence label
- retrieved documents
- tool-call trace

### 5. AI Chat and Alert Trends (optional supporting material)

If time allows, show:
- **AI Chat** for natural-language questions
- **Alert Trends** for predictive trend analysis

Use these as supporting proof that the system already has agentic and MCP-based
capabilities even before the new dynamic dashboard flow is fully merged.

## Fallback Assets To Prepare Before Presentation

Prepare these before the dry run:
- screenshots of the generated dashboard
- a 30-60 second screen recording of one successful run
- one copy-paste trigger command for the stable scenario
- one backup route using the existing static dashboards if the live trigger fails

## Key Demo Vessels

| Vessel | IMO | Characteristics |
|--------|-----|----------------|
| MV Edge Aurora | IMO9300001 | Best single-vessel demo target; stale and down app scenarios; mapped to legacy `vessel_001` |
| MV Edge Borealis | IMO9300002 | Useful secondary vessel with degraded data-quality-processor |
| MT Nordic Fjord | IMO9300003 | Mostly healthy baseline vessel |

## Audience Q&A Notes

**Why use a local LLM instead of a cloud API?**
Maritime environments may have limited or expensive connectivity. Local models
support offline or privacy-sensitive operation.

**Is the data real?**
The data is synthetic, but the scenarios are deterministic and chosen to be
operationally believable.

**How does the AI know about maritime systems?**
The RAG knowledge base in `docs/knowledge/` provides domain context, while MCP
tools provide the live operational data.

**How does this go beyond traditional dashboards?**
The foundation still uses dashboards, but the pivot adds an agentic step where
the system decides what dashboard to generate for the incident that is happening
now.
