# Architecture - Maritime Agentic Observability

## Purpose

This system provides two monitoring paths for a maritime application platform:

1. **Legacy ship telemetry** -- synthetic sensors, anomaly events, AI analysis
2. **UDS application monitoring** -- application health per vessel, metrics,
   alerts, logs, fleet-level overview, and incident investigation tools

The project implements three user stories:

- **Scope 1** (delivered): single-vessel incident handling
- **Scope 2** (delivered): multi-vessel fleet overview + NOC support

## High-Level Component View

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
              +-----------+-----------+                    |
              |           |           |                    |
       uds_monitoring  fleet_overview  (noc_support)       |
              |           |           |                    |
              +-----------+-----------+                    |
                          |                                |
                    MCP UDS tools (9 tools) <---------------+
                          |
                    agent analyze (UDS events)
```

## Main Services

| Service | Responsibility |
|---------|----------------|
| `timescaledb` | Stores legacy telemetry/events plus UDS tables and RAG vectors |
| `generator` | Produces legacy synthetic ship telemetry and anomaly events |
| `uds-seeder` | Produces periodic UDS metrics, alerts, and app logs (30-min cycle, 6-hour backfill) |
| `grafana` | Dashboards: Ship Operations, UDS Incident Monitoring, Fleet Overview, NOC Support |
| `agent` | AI analysis for events using Ollama + RAG + MCP tool loop |
| `mcp` | REST adapter exposing 12 database tools (3 legacy + 4 Scope 1 + 5 Scope 2) |
| `ollama` | Local LLM inference and embeddings |
| `ollama-init` | Pulls required models on stack startup |

## Data Model

### Legacy path

Defined in `db/init/001_init.sql`.

Tables: `telemetry`, `events`, `ai_analyses`

Used by: `services/generator/`, `services/agent/routes/analyze.py`,
`grafana/dashboards/ship_operations.json`

### UDS path

Defined in `db/init/003_uds.sql` and `db/init/004_uds_reference_data.sql`.

Core tables:
- `owners` -- vessel owners
- `udslocations` -- vessels (3 demo vessels: IMO9300001, IMO9300002, IMO9300003)
- `applications` -- platform apps (6 apps per vessel)
- `uds_location_application_instances` -- vessel-to-app links (18 rows)
- `metric_samples` -- time-series metrics (TimescaleDB hypertable)
- `alerts` -- active and resolved alerts
- `app_logs` -- application logs and alert-driven context
- `uds_location_owner_history` -- ownership history
- `monitoring_configs` -- compatibility shim

Seeded by: `db/seed/uds_seed.sql` via `scripts/uds_seed_loop.sh`

### RAG path

Defined in `db/init/002_rag.sql`.

Table: `knowledge_docs` with pgvector embeddings

Knowledge files: `docs/knowledge/` (17 maritime reference files)

## MCP Tool Architecture

The MCP server (`services/mcp/main.py`) is a FastAPI REST adapter that exposes
typed database tools. It is not the official MCP protocol (JSON-RPC 2.0 + SSE)
but follows the same tool definition structure.

Each tool has:
1. A definition in the `TOOLS` list (name, description, inputSchema)
2. A Pydantic `BaseModel` for argument validation
3. An async handler function
4. An entry in `TOOL_HANDLERS`
5. A dedicated HTTP POST endpoint

The agent calls tools via HTTP during the analysis loop. Tool access is filtered
by `UDS_FULL_TOOL_NAMES` in `services/agent/routes/analyze.py`.

### Tool inventory (12 tools)

| Tool | Path | Scope |
|------|------|-------|
| `get_telemetry` | Legacy | Scope 0 |
| `get_events` | Legacy | Scope 0 |
| `get_analysis` | Legacy | Scope 0 |
| `get_vessel_app_status` | UDS | Scope 1 |
| `get_vessel_alerts` | UDS | Scope 1 |
| `get_app_metric_history` | UDS | Scope 1 |
| `get_app_logs` | UDS | Scope 1 |
| `get_fleet_status` | UDS | Scope 2 |
| `get_fleet_alerts` | UDS | Scope 2 |
| `get_cross_vessel_correlation` | UDS | Scope 2 |
| `get_incident_timeline` | UDS | Scope 2 |
| `get_operational_snapshot` | UDS | Scope 2 |

## Dashboard Architecture

### Scope 1: UDS Incident Monitoring (`uds_monitoring.json`)
- Single-vessel focus
- Variables: `vessel`, `app`, `incident_window`
- Flow: select vessel -> review active alerts -> click app -> drilldown into
  metrics, logs, connectivity
- See `docs/UDS_dashboard_spec.md` for panel details

### Scope 2: Fleet Overview (`fleet_overview.json`)
- Multi-vessel focus (User Story 2)
- Fleet health cards, cross-vessel alert table, correlation view
- Drilldown links navigate to UDS Incident Monitoring with vessel pre-selected

### Scope 2: NOC Support (`noc_support.json`)
- Investigation-focused (User Story 3)
- Variables: `vessel`, `time_window` (1h–7d), `app_filter`
- 16 panels: operational state, incident timeline, error/warning summary,
  alert history, connectivity history, historical metrics
- Drilldown links navigate to UDS Incident Monitoring with vessel, app, and time window

### Legacy: Ship Operations (`ship_operations.json`)
- Sensor telemetry visualization
- Separate from the UDS monitoring path

## Design Limitations

### 1. Fresh DB bias
The prototype relies on init scripts for schema and reference data. Old local
volumes can drift. Use `docker compose down -v` for reliable validation.

### 2. Cold-start timing
First start depends on model pull, RAG ingest, and service readiness. Allow a
few minutes before demoing.

### 3. Security shortcuts
This is a local prototype:
- Event acknowledge has a GET alias
- MCP auth is optional if `MCP_API_KEY` is unset
- Demo credentials are convenience-oriented

### 4. Prototype log bridge
`app_logs` stores seeded and alert-driven log context. It is not a full
centralized log pipeline.

### 5. Fixed demo topology
3 vessels, 6 applications. Enough for Scope 1 and Scope 2 demo, but does not
prove full scalability claims.
