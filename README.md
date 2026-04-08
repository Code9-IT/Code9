# Maritime Agentic Observability

Bachelor project (UiA) in collaboration with **Knowit Sorlandet**.

An AI-agent-enhanced monitoring and observability system for maritime application
platforms. The system monitors applications running on vessels, detects incidents,
and provides AI-driven analysis using RAG-grounded knowledge and MCP tool access.

## User Stories

The project implements three user stories from Geir Borgi (Telenor Maritime):

1. **Single Vessel Incident** (Scope 1 -- delivered):
   When a warning or error arrives from an application on a vessel, show the full
   operational state, historical metrics/logs, and enough context to take action.

2. **Multi-Vessel Incident** (Scope 2 -- delivered):
   When warnings affect multiple vessels, provide a consolidated overview that
   highlights correlated issues and systemic problems.

3. **NOC Support Case** (Scope 2 -- delivered):
   When a support ticket arrives, show full vessel state, recent errors, connectivity
   status, and historical context for troubleshooting.

## Current Focus

After the 2026-04-07 meeting with Arnt and Geir, the team is building a small
agentic **dynamic dashboard** flow on top of the existing prototype: an agent
detects an incident, picks a scenario template, and writes a Grafana dashboard
via the Grafana HTTP API. The single working document is
[`docs/DYNAMIC_DASHBOARD_TASK_PLAN.md`](docs/DYNAMIC_DASHBOARD_TASK_PLAN.md).

This week's milestone: `POST /api/v1/dynamic/trigger` produces a dashboard
under the stable UID `maritime_dynamic_incident`.

## Current Status

**Scope 1** and **Scope 2** are complete: all three user stories have dashboard
and MCP tool coverage.

**Scope 3 Task 1 (UDS AI Integration)** is complete: clicking a UDS alert in
`uds_monitoring.json` or `noc_support.json` opens an AI analysis page at
`/api/v1/uds/analyze/view`. The analysis uses UDS MCP tools, RAG context, and
Ollama, and shows tool-call trace and retrieved documents for traceability.

**Scope 3 Task 2 (AI Chat Interface)** is complete: the agent exposes a
user-facing AI chat page at `/api/v1/chat` that uses the same Ollama + RAG +
MCP building blocks as event analysis, intended for demo-style operational
questions about vessels, alerts, degraded apps, and incidents.

**Scope 3 Task 3 (Dashboard Coherence)** is complete: the main Grafana
dashboards share root navigation between Ship Operations, Fleet Overview,
UDS Incident Workbench, NOC Support, and AI Chat. The legacy vessel
`vessel_001` is intentionally bridged to MV Edge Aurora (`IMO9300001`) for the
presenter-facing demo flow. The previous `UDS App Health` dashboard is renamed
to `AI Pipeline Health (Developer)` and is intentionally kept outside the main
demo navigation.

See `docs/SCOPE3_DELIVERY_TASKS.md` for remaining scope 3 tasks.
Historical task-planning docs are kept under `docs/archive/`.

## Quick Start

### Prerequisites

- Docker Desktop

No local PostgreSQL or Python install is required.

### Start the stack

```bash
git clone <repo-url>
cd <repo-dir>
cp .env.example .env
docker compose up -d --build
```

First-start behavior:

- `ollama-init` pulls `llama3.2` and `nomic-embed-text`
- The agent retries RAG ingest until embeddings are available
- The generator inserts legacy telemetry events
- `uds-seeder` backfills 6 hours of UDS history, then seeds every 30 minutes

Watch startup progress:

```bash
docker compose logs -f uds-seeder
```

Wait for `Backfill complete (11 historical cycles inserted)` before using dashboards.

### Open the main services

- Grafana: `http://localhost:3000` (admin / code9-demo-admin)
- Agent API: `http://localhost:8000/docs`
- MCP API: `http://localhost:8001/docs`
- AI Chat page: `http://localhost:8000/api/v1/chat`
- Validation dashboard: `http://localhost:8000/api/v1/validate/dashboard`

### Fresh-stack reset

The database init scripts only run on a fresh DB volume. For reliable validation:

```bash
docker compose down -v
docker compose up -d --build
```

## Project Layout

```text
.
|-- CLAUDE.md                          # AI assistant instructions (read this first)
|-- docker-compose.yml
|-- .env.example
|
|-- db/
|   |-- init/
|   |   |-- 001_init.sql               # legacy telemetry schema
|   |   |-- 002_rag.sql                # pgvector RAG schema
|   |   |-- 003_uds.sql                # UDS application monitoring schema
|   |   `-- 004_uds_reference_data.sql # 3 vessels, 6 apps, 18 links
|   `-- seed/
|       `-- uds_seed.sql               # periodic seed with scenario flags
|
|-- grafana/
|   |-- dashboards/
|   |   |-- uds_monitoring.json        # Scope 1: single-vessel incident workbench
|   |   |-- fleet_overview.json        # Scope 2: multi-vessel fleet overview
|   |   |-- noc_support.json           # Scope 2: NOC support investigation board
|   |   |-- ship_operations.json       # legacy telemetry dashboard mapped to MV Edge Aurora (IMO9300001)
|   |   |-- alert_trends.json          # Scope 3: predictive alert trend analysis
|   |   `-- uds_app_health.json        # AI pipeline health dashboard (developer-only)
|   |-- provisioning/
|   `-- queries/
|       `-- uds_queries.sql            # reference SQL for dashboard panels
|
|-- services/
|   |-- agent/                         # AI analysis service (FastAPI)
|   |-- generator/                     # legacy telemetry generator
|   `-- mcp/                           # MCP REST adapter (13 tools)
|
|-- scripts/
|   |-- uds_seed_loop.sh              # seed loop with 6-hour backfill
|   `-- reset_db.sh                    # database reset utility
|
`-- docs/
    |-- architecture.md                # system architecture
    |-- ROADMAP.md                     # backlog and priorities
    |-- SCOPE1_ACCEPTANCE_CHECKLIST.md # repeatable validation flow
    |-- SCOPE3_DELIVERY_TASKS.md       # Scope 3 final sprint task definitions
    |-- UDS_dashboard_spec.md          # dashboard panel specifications
    |-- PRODUCTION_GUIDE.md            # deployment and operations guide
    |-- DEMO_SCRIPT.md                 # step-by-step demo walkthrough
    |-- knowledge/                     # RAG knowledge base (17 files)
    |-- thesis/                        # thesis-specific planning docs
    `-- archive/                       # historical planning, handoff, and task docs
```

## Architecture

The system has two monitoring paths:

### Legacy telemetry path
- `services/generator/` produces synthetic sensor data and anomaly events
- `services/agent/` runs AI analysis using Ollama + RAG + MCP tools
- `grafana/dashboards/ship_operations.json` visualizes telemetry

### User-facing AI chat path
- `services/agent/routes/chat.py` serves `GET/POST /api/v1/chat`
- The chat uses the same Ollama + RAG + MCP building blocks as event analysis
- Intended for demo questions about vessels, alerts, degraded apps, and incidents

### UDS application monitoring path
- `db/init/003_uds.sql` + `004_uds_reference_data.sql` define the schema
- `uds-seeder` inserts metrics, alerts, and logs every 30 minutes
- `services/mcp/main.py` exposes 10 UDS tools (4 single-vessel + 5 fleet/incident + 1 predictive)
- `grafana/dashboards/uds_monitoring.json` for the single-vessel incident workbench
- `grafana/dashboards/fleet_overview.json` for multi-vessel overview
- `grafana/dashboards/noc_support.json` for NOC support investigation
- `grafana/dashboards/alert_trends.json` for predictive alert trend analysis

### UDS AI analysis
- `GET /api/v1/uds/analyze/view?vessel=IMO9300001&app=...&alert_name=...&severity=...`
- Grafana data links on alert columns open this endpoint in a new tab
- The agent uses UDS MCP tools (get_vessel_app_status, get_incident_timeline, etc.)
- Results are persisted and keyed by vessel + app + alert name for reopening

### MCP tools (13 total)

| Tool | Scope | Purpose |
|------|-------|---------|
| `get_telemetry` | Legacy | Raw telemetry query |
| `get_events` | Legacy | Event list with filters |
| `get_analysis` | Legacy | AI analysis for an event |
| `get_vessel_app_status` | Scope 1 | All apps on one vessel |
| `get_vessel_alerts` | Scope 1 | Active alerts for one vessel |
| `get_app_metric_history` | Scope 1 | Time-series metrics for one app |
| `get_app_logs` | Scope 1 | Recent logs for one app |
| `get_fleet_status` | Scope 2 | All vessels with status |
| `get_fleet_alerts` | Scope 2 | Fleet-wide alerts |
| `get_cross_vessel_correlation` | Scope 2 | Cross-vessel pattern detection |
| `get_incident_timeline` | Scope 2 | Chronological event timeline |
| `get_operational_snapshot` | Scope 2 | Full vessel state for NOC |
| `get_alert_trend` | Scope 3 | Alert frequency trend detection (predictive) |

## Dashboards

| Dashboard | File | Purpose |
|-----------|------|---------|
| Ship Operations | `ship_operations.json` | Legacy telemetry monitoring |
| UDS Monitoring | `uds_monitoring.json` | Single-vessel incident investigation |
| Fleet Overview | `fleet_overview.json` | Multi-vessel operational overview |
| NOC Support | `noc_support.json` | Full vessel state for support cases |
| Alert Trends | `alert_trends.json` | Predictive alert frequency analysis |

## Scope 1 Acceptance

Use `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md` for the repeatable validation flow.

## Known Limitations

- `GET /api/v1/events/{event_id}/acknowledge` returns HTTP 405 (`Allow: POST`); the Grafana flow uses the new `/acknowledge/confirm` confirmation page that issues an explicit POST
- MCP auth is only enforced if `MCP_API_KEY` is non-empty
- The demo topology is fixed to 3 vessels and 6 applications
- `app_logs` is a lightweight prototype bridge, not a full log pipeline
- Cold-start legacy analysis may need warmup time before demo
- Fresh DB volumes are the only reliable validation path (no migration strategy)

See `docs/ROADMAP.md` for the full backlog.

## Group Workflow

1. Work from feature branches, never push directly to main.
2. Keep changes scoped to your task's file ownership.
3. Update docs in the same PR when behavior changes.
4. Run fresh-stack validation after merges.
5. Use `docs/ROADMAP.md` for current backlog and follow-up priorities.
