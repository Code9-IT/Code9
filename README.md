# Maritime Agentic Observability

Prototype developed in collaboration with **Knowit Sorlandet** and **Telenor
Maritime**.

This repository contains a locally runnable prototype for maritime application
monitoring and AI-supported incident investigation. The system combines Grafana
dashboards, time-series storage, a FastAPI agent service, a custom MCP-style REST
adapter, local Ollama models, and RAG-based document retrieval.

The prototype is intended as a technical foundation for further development. It
is not a production deployment.

## What Was Built

The final prototype contains four delivered parts:

1. **UDS incident monitoring baseline**
   - Single-vessel UDS Incident Workbench in Grafana
   - Application state, active alerts, metric history, freshness, and log context
   - MCP-style tools for vessel/application investigation

2. **Fleet and NOC monitoring**
   - Fleet Overview dashboard for multi-vessel monitoring
   - NOC Support dashboard for support-oriented vessel troubleshooting
   - Fleet-level MCP-style tools for status, alerts, correlation, timelines, and
     operational snapshots

3. **AI-supported investigation**
   - UDS-aware AI analysis page for selected alerts
   - AI operations chat page
   - Alert Trends dashboard and `get_alert_trend` tool
   - Traceable tool calls and retrieved RAG documents in AI-supported views

4. **Dynamic dashboard proof-of-concept**
   - Incident-triggered dashboard generation through deterministic Python code
   - Dynamic incident dashboard written to Grafana under the stable UID
     `maritime_dynamic_incident`
   - Optional dynamic fleet and NOC dashboard trigger endpoints

## Quick Start

### Prerequisites

- Docker Desktop with Docker Compose v2

No local PostgreSQL, Python, Grafana, or Ollama installation is required.

### Start the Stack

```bash
git clone <repo-url>
cd <repo-dir>
cp .env.example .env
docker compose up -d --build
```

First-start behavior:

- `ollama-init` pulls `llama3.2` and `nomic-embed-text`
- The database initializes the telemetry, RAG, UDS, and dynamic-dashboard schemas
- The agent retries RAG ingestion until embeddings are available
- The legacy generator inserts telemetry events
- `uds-seeder` backfills 6 hours of UDS history, then seeds every 30 minutes

Watch startup progress:

```bash
docker compose logs -f uds-seeder
```

Wait for `Backfill complete (11 historical cycles inserted)` before validating
dashboards.

### Open the Main Services

- Grafana: <http://localhost:3000> (`admin` / `code9-demo-admin`)
- Agent API docs: <http://localhost:8000/docs>
- MCP-style tool API docs: <http://localhost:8001/docs>
- AI Chat page: <http://localhost:8000/api/v1/chat>
- Dynamic dashboard selector: <http://localhost:8000/api/v1/dynamic/select>
- Validation dashboard: <http://localhost:8000/api/v1/validate/dashboard>

### Fresh-Stack Reset

The database initialization scripts only run on a fresh database volume. For
repeatable validation:

```bash
docker compose down -v
docker compose up -d --build
```

## Dynamic Dashboard Proof-of-Concept

The dynamic dashboard flow can be triggered from the API after the stack is
running and seeded.

Generate or update the default incident dashboard from the latest firing alert:

```bash
curl -X POST http://localhost:8000/api/v1/dynamic/trigger \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"latest_firing_alert\"}"
```

Open the generated dashboard in Grafana:

```text
http://localhost:3000/d/maritime_dynamic_incident
```

Useful dynamic-dashboard endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/dynamic/trigger` | Generate the incident-specific dashboard |
| `GET /api/v1/dynamic/status` | Check Grafana/MCP readiness and recent runs |
| `GET /api/v1/dynamic/select` | Browser-based selector for vessel/app/incident context |
| `GET /api/v1/dynamic/demo` | Demo page for triggering predefined incident scenarios |
| `POST /api/v1/dynamic/fleet/trigger` | Generate a fleet-focused dynamic dashboard |
| `POST /api/v1/dynamic/noc/trigger` | Generate a NOC-focused dynamic dashboard |

The dashboard structure is generated deterministically. The language model is
used for explanation and interpretation, not for producing Grafana JSON or SQL.

## Project Layout

```text
.
|-- docker-compose.yml
|-- .env.example
|-- db/
|   |-- init/
|   |   |-- 001_init.sql              # legacy telemetry schema
|   |   |-- 002_rag.sql               # pgvector RAG schema
|   |   |-- 003_uds.sql               # UDS application monitoring schema
|   |   |-- 004_uds_reference_data.sql # demo vessels, apps, and links
|   |   `-- 005_dynamic_dashboard_runs.sql
|   `-- seed/
|       `-- uds_seed.sql              # recurring UDS metrics, alerts, and logs
|
|-- docs/
|   |-- architecture.md               # architecture overview
|   |-- PRODUCTION_GUIDE.md           # operations guide
|   |-- ROADMAP.md                    # follow-up work and limitations
|   `-- knowledge/                    # RAG knowledge base
|
|-- grafana/
|   |-- dashboards/
|   |   |-- ship_operations.json      # legacy telemetry monitoring
|   |   |-- uds_monitoring.json       # UDS Incident Workbench
|   |   |-- fleet_overview.json       # fleet monitoring
|   |   |-- noc_support.json          # NOC support investigation
|   |   |-- alert_trends.json         # alert trend analysis
|   |   `-- uds_app_health.json       # developer-facing AI pipeline health
|   |-- provisioning/
|   `-- queries/
|
|-- scripts/
|   |-- inject_dynamic_incident.py    # demo helper for dynamic incidents
|   |-- reset_db.sh
|   `-- uds_seed_loop.sh
|
`-- services/
    |-- agent/                        # FastAPI agent, AI views, dynamic dashboards
    |   |-- dynamic/                  # dynamic-dashboard builders/orchestrators
    |   `-- routes/
    |-- generator/                    # legacy telemetry generator
    `-- mcp/                          # MCP-style REST adapter with 13 tools
```

## Architecture Overview

The prototype has four connected paths.

### Legacy Ship Operations Path

- `services/generator/` produces synthetic telemetry events
- `ship_operations.json` visualizes legacy vessel telemetry
- AI analysis can explain selected telemetry events using RAG and MCP-style tools

### UDS Application Monitoring Path

- `db/init/003_uds.sql` and `004_uds_reference_data.sql` define the UDS schema and
  reference data
- `uds-seeder` inserts recurring UDS metrics, alerts, and logs
- Grafana dashboards show single-vessel, fleet, NOC, and alert-trend views
- MCP-style tools expose UDS data to the agent in a controlled way

### AI-Supported Investigation Path

- `GET /api/v1/uds/analyze/view?...` opens an AI analysis page for a selected alert
- `GET /api/v1/chat` opens the AI operations chat interface
- RAG retrieves project knowledge documents from `docs/knowledge/`
- Tool-call traces and retrieved documents are shown for review

### Dynamic Dashboard Path

- `POST /api/v1/dynamic/trigger` collects incident context and writes a targeted
  Grafana dashboard
- Dynamic dashboard runs are stored in `dynamic_dashboard_runs`
- The generated dashboard uses the stable Grafana UID `maritime_dynamic_incident`

## MCP-Style Tools

The custom MCP-style REST adapter exposes 13 tools: 3 legacy telemetry tools and
10 UDS monitoring tools.

| Tool | Area | Purpose |
|------|-------|---------|
| `get_telemetry` | Legacy | Raw telemetry query |
| `get_events` | Legacy | Event list with filters |
| `get_analysis` | Legacy | Stored AI analysis for an event |
| `get_vessel_app_status` | UDS incident monitoring | Application status for one vessel |
| `get_vessel_alerts` | UDS incident monitoring | Active alerts for one vessel |
| `get_app_metric_history` | UDS incident monitoring | Time-series metrics for one app |
| `get_app_logs` | UDS incident monitoring | Recent logs for one app |
| `get_fleet_status` | Fleet/NOC | Operational status across vessels |
| `get_fleet_alerts` | Fleet/NOC | Fleet-wide active alerts |
| `get_cross_vessel_correlation` | Fleet/NOC | Cross-vessel incident patterns |
| `get_incident_timeline` | Fleet/NOC | Chronological alerts and logs |
| `get_operational_snapshot` | Fleet/NOC | Full vessel state for NOC support |
| `get_alert_trend` | Alert trends | Alert frequency trend detection |

## Dashboards

| Dashboard | File / UID | Purpose |
|-----------|------------|---------|
| Ship Operations | `ship_operations.json` | Legacy telemetry monitoring |
| UDS Incident Workbench | `uds_monitoring.json` | Single-vessel incident investigation |
| Fleet Overview | `fleet_overview.json` | Multi-vessel operational overview |
| NOC Support | `noc_support.json` | Full vessel state for support cases |
| Alert Trends | `alert_trends.json` | Alert frequency and trend analysis |
| AI Pipeline Health | `uds_app_health.json` | Developer-facing AI/RAG health checks |
| Dynamic Incident Dashboard | `maritime_dynamic_incident` | Runtime-generated incident dashboard |

## Validation

The project was validated through scenario-based checks and fresh-stack
validation. The most important repeatable checks are:

1. Start from a clean database volume with `docker compose down -v`.
2. Rebuild and start all services with `docker compose up -d --build`.
3. Wait for the UDS seeder backfill to complete.
4. Open Grafana and verify the main dashboards load.
5. Confirm seeded UDS states such as healthy, degraded, down, stale, and delayed.
6. Open AI analysis and chat pages.
7. Trigger the dynamic dashboard proof-of-concept and open the generated Grafana
   dashboard.

## Documentation

| Document | Purpose |
|----------|---------|
| [`docs/architecture.md`](docs/architecture.md) | Architecture overview |
| [`docs/PRODUCTION_GUIDE.md`](docs/PRODUCTION_GUIDE.md) | Deployment and operations notes |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Known gaps and suggested follow-up work |
| [`docs/knowledge/`](docs/knowledge/) | RAG knowledge base documents |

## Known Limitations

- The system is a local prototype, not a production deployment.
- The demo topology is fixed to 3 vessels and 6 applications.
- UDS data is seeded for repeatable scenarios and is not live production data.
- MCP API-key authentication is only enforced when `MCP_API_KEY` is non-empty.
- The prototype does not include a production migration strategy.
- `app_logs` is a lightweight prototype bridge, not a full log pipeline.
- Local Ollama inference may require warmup time and has limited model capacity.
- Dynamic dashboard generation is implemented as a proof-of-concept and requires
  further validation before operational use.

See [`docs/ROADMAP.md`](docs/ROADMAP.md) for suggested follow-up work.
