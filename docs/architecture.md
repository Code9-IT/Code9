# Architecture - Maritime Agentic Observability

## Purpose

This repository now needs to be read as two layers:

1. **Implemented foundation**
   - legacy ship telemetry with AI analysis
   - UDS application monitoring for single-vessel, fleet, and NOC use cases
   - AI chat, predictive alert trends, and shared dashboard navigation
2. **Current pivot**
   - one agentic dynamic-dashboard flow that generates or updates a Grafana
     dashboard for the incident that matters now

That means the current architecture story is:
- **Scope 1** (delivered): single-vessel incident handling
- **Scope 2** (delivered): multi-vessel fleet overview + NOC support
- **Scope 3 foundation** (implemented): UDS AI analysis, AI chat, dashboard
  coherence, and predictive alert trend analysis
- **Dynamic dashboard pivot** (in progress): alert/warning -> orchestrator ->
  MCP context -> scenario classification -> generated Grafana dashboard

## Implemented Foundation

### High-Level Component View

```text
generator ----------------------> telemetry / events -----+
                                                           |
                                                           v
                                                  ship_operations.json
                                                           |
                                                     agent analyze
                                                     /           \
                                                RAG context    MCP tools (legacy)

004_uds_reference_data.sql --> UDS reference tables -------+
                                                           |
uds-seeder ------> metric_samples / alerts / app_logs      |
                          |                                |
       +------+-----------+-----------+--------------+     |
       |      |           |           |              |     |
  uds_mon  fleet_overview noc_support alert_trends   |     |
       |      |           |           |              |     |
       +------+-----------+-----------+--------------+     |
                          |                                |
                  MCP UDS tools (10 tools) <----------------+
                          |
                  agent analyze (UDS events) + AI chat
```

### Main Services

| Service | Responsibility |
|---------|----------------|
| `timescaledb` | Stores legacy telemetry/events plus UDS tables and RAG vectors |
| `generator` | Produces legacy synthetic ship telemetry and anomaly events |
| `uds-seeder` | Produces periodic UDS metrics, alerts, and app logs |
| `grafana` | Dashboards: Ship Operations, UDS Incident Workbench, Fleet Overview, NOC Support, Alert Trends |
| `agent` | AI analysis, AI chat, and the current extension point for dynamic-dashboard work |
| `mcp` | REST adapter exposing 13 database tools (legacy + UDS + predictive trend) |
| `ollama` | Local LLM inference and embeddings |
| `ollama-init` | Pulls required models on stack startup |

## Current Pivot / Next Layer

The current sprint adds a generated-dashboard path on top of the implemented
foundation. This is the piece Arnt and Geir are now asking the team to prove.

```text
alert / warning / selected incident
                |
                v
        orchestrator / trigger endpoint
                |
                v
          MCP context collection
                |
                v
        scenario classification
                |
                v
generated Grafana dashboard (stable UID: maritime_dynamic_incident)
```

Important constraints for this layer:
- it builds on the existing dashboards instead of replacing them
- it reuses the MCP tool layer rather than bypassing it
- it keeps dashboard structure deterministic
- the LLM is optional and limited to summary text, not raw Grafana JSON

This dynamic-dashboard layer is **not** part of the implemented foundation yet.
It is the current extension the team is building and demoing this week.

## Data Model

### Legacy path

Defined in `db/init/001_init.sql`.

Tables:
- `telemetry`
- `events`
- `ai_analyses`

Used by:
- `services/generator/`
- `services/agent/routes/analyze.py`
- `grafana/dashboards/ship_operations.json`

### UDS path

Defined in `db/init/003_uds.sql` and `db/init/004_uds_reference_data.sql`.

Core tables:
- `owners`
- `udslocations`
- `applications`
- `uds_location_application_instances`
- `metric_samples`
- `alerts`
- `app_logs`
- `uds_location_owner_history`
- `monitoring_configs`

Seeded by:
- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`

### RAG path

Defined in `db/init/002_rag.sql`.

Table:
- `knowledge_docs`

Knowledge files:
- `docs/knowledge/`

## MCP Tool Architecture

The MCP server (`services/mcp/main.py`) is a FastAPI REST adapter that exposes
typed database tools. It is not the official MCP protocol, but it follows the
same tool-definition idea and is the live data-access layer for the agent.

Each tool has:
1. a definition in the `TOOLS` list
2. a Pydantic model for argument validation
3. an async handler function
4. an entry in `TOOL_HANDLERS`
5. an HTTP POST endpoint

### Tool Inventory (13 total)

| Tool | Path | Scope |
|------|------|-------|
| `get_telemetry` | Legacy | Legacy |
| `get_events` | Legacy | Legacy |
| `get_analysis` | Legacy | Legacy |
| `get_vessel_app_status` | UDS | Scope 1 |
| `get_vessel_alerts` | UDS | Scope 1 |
| `get_app_metric_history` | UDS | Scope 1 |
| `get_app_logs` | UDS | Scope 1 |
| `get_fleet_status` | UDS | Scope 2 |
| `get_fleet_alerts` | UDS | Scope 2 |
| `get_cross_vessel_correlation` | UDS | Scope 2 |
| `get_incident_timeline` | UDS | Scope 2 |
| `get_operational_snapshot` | UDS | Scope 2 |
| `get_alert_trend` | UDS | Scope 3 foundation |

## Dashboard Foundation

### UDS Incident Workbench (`uds_monitoring.json`)
- single-vessel incident handling
- vessel/app/incident-window drilldown
- active alerts, recent metrics, logs, and app context

### Fleet Overview (`fleet_overview.json`)
- multi-vessel overview
- vessel health cards
- alert counts and cross-vessel context
- drilldown into the single-vessel workbench

### NOC Support (`noc_support.json`)
- investigation-focused vessel view
- incident timeline, operational snapshot, connectivity, and historical metrics

### Ship Operations (`ship_operations.json`)
- legacy telemetry visualization
- presenter-friendly bridge into the UDS flow

### Alert Trends (`alert_trends.json`)
- predictive alert-frequency analysis
- vessel/severity filtering
- backed by `get_alert_trend`

### Shared Navigation
- main demo dashboards share root navigation
- `uds_app_health.json` is treated as a developer-only AI pipeline dashboard

## Current Sprint Extension: Dynamic Incident Dashboard

Target shape:
- stable generated dashboard UID: `maritime_dynamic_incident`
- triggered first from explicit incident context, then optionally from latest alert
- reuses existing UDS MCP tools to gather context
- selects one deterministic scenario template such as:
  - connectivity
  - service_down
  - runtime_pressure
  - generic_incident
- writes the dashboard through the Grafana HTTP API
- keeps existing dashboards as fallback and drilldown context

## Design Limitations

### Fresh DB bias
The prototype still validates most reliably from a fresh DB volume.

### Cold-start timing
First startup still depends on model pull, RAG ingest, and service readiness.

### Security shortcuts
This is still a local demo-oriented prototype:
- demo credentials remain convenience-oriented
- MCP auth is optional if `MCP_API_KEY` is unset
- event acknowledge uses a confirmation-page workaround for Grafana

### Prototype log bridge
`app_logs` is seeded operational context, not a full production log pipeline.

### Fixed demo topology
3 vessels and 6 applications per vessel are enough for the current demo, but do
not prove full production scalability by themselves.
