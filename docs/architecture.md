# Architecture - Maritime Agentic Observability

## Purpose

This document summarizes the delivered prototype architecture. The repository
contains a locally runnable monitoring and incident-support stack with four
connected paths:

1. legacy Ship Operations telemetry monitoring
2. UDS application monitoring for single-vessel, fleet, and NOC workflows
3. AI-supported analysis, chat, and alert trends
4. a dynamic dashboard proof-of-concept for incident-specific Grafana views

## High-Level Component View

```text
generator ----------------------> telemetry / events -----+
                                                           |
                                                           v
                                                  ship_operations.json
                                                           |
                                                     agent analyze
                                                     /           \
                                                RAG context    MCP tools

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
                  MCP-style UDS tools <--------------------+
                          |
                  agent analyze + AI chat
                          |
                          v
       dynamic-dashboard orchestrator -> generated Grafana dashboard
                    stable UID: maritime_dynamic_incident
```

## Main Services

| Service | Responsibility |
|---------|----------------|
| `timescaledb` | PostgreSQL + TimescaleDB + pgvector data layer |
| `generator` | Legacy synthetic ship telemetry and anomaly events |
| `uds-seeder` | Periodic UDS metrics, alerts, and app logs |
| `grafana` | Static dashboards and generated dynamic dashboards |
| `agent` | AI analysis, AI chat, validation views, and dynamic-dashboard routes |
| `mcp` | MCP-style REST adapter exposing 13 predefined tools |
| `ollama` | Local LLM inference and embeddings |
| `ollama-init` | One-shot model puller on stack startup |

## Data Model

### Legacy Telemetry Path

Defined in `db/init/001_init.sql`.

Core tables:

- `telemetry`
- `events`
- `ai_analyses`

Used by:

- `services/generator/`
- `services/agent/routes/analyze.py`
- `grafana/dashboards/ship_operations.json`

### UDS Monitoring Path

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

### RAG Path

Defined in `db/init/002_rag.sql`.

Core table:

- `knowledge_docs`

Knowledge files:

- `docs/knowledge/`

### Dynamic Dashboard Path

Defined in `db/init/005_dynamic_dashboard_runs.sql`.

Core table:

- `dynamic_dashboard_runs`

Used by:

- `services/agent/routes/dynamic_dashboard.py`
- `services/agent/dynamic/`
- Grafana dashboard UID `maritime_dynamic_incident`

## MCP-Style Tool Architecture

The MCP server (`services/mcp/main.py`) is a FastAPI REST adapter that exposes
typed database tools. It is not the official MCP protocol, but it follows the
same controlled tool-access idea and is the live data-access layer for the
agent.

Each tool has:

1. a definition in the `TOOLS` list
2. a Pydantic model for argument validation
3. an async handler function
4. an entry in `TOOL_HANDLERS`
5. an HTTP POST endpoint

### Tool Inventory

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

### Ship Operations (`ship_operations.json`)

Legacy telemetry visualization with links to AI event analysis.

### UDS Incident Workbench (`uds_monitoring.json`)

Single-vessel incident handling with application state, alerts, recent context,
and drilldown support.

### Fleet Overview (`fleet_overview.json`)

Multi-vessel operational overview with fleet status and cross-vessel context.

### NOC Support (`noc_support.json`)

Support-oriented vessel investigation view with operational state, timelines,
connectivity, and historical panels.

### Alert Trends (`alert_trends.json`)

Alert frequency and trend view backed by the `get_alert_trend` tool.

### AI Pipeline Health (`uds_app_health.json`)

Developer-facing dashboard for AI/RAG health checks.

### Dynamic Incident Dashboard (`maritime_dynamic_incident`)

Runtime-generated Grafana dashboard created through
`POST /api/v1/dynamic/trigger`.

## Dynamic Dashboard Flow

```text
selected incident / latest firing alert
              |
              v
     dynamic-dashboard trigger
              |
              v
      MCP-style context collection
              |
              v
       scenario classification
              |
              v
 deterministic dashboard builder
              |
              v
       Grafana HTTP API upsert
```

Important design choices:

- The generated dashboard builds on the existing UDS data model.
- Context is collected through the MCP-style tool layer.
- Scenario classification selects a deterministic dashboard template.
- The language model is not used to generate Grafana JSON or SQL.
- Existing dashboards remain available as drilldown and fallback views.

## Design Limitations

- The prototype validates most reliably from a fresh database volume.
- First startup depends on model pull, RAG ingest, and service readiness.
- Demo credentials are convenience-oriented and must be changed before any
  non-local deployment.
- MCP auth is optional if `MCP_API_KEY` is unset.
- `app_logs` is seeded operational context, not a full production log pipeline.
- The demo topology uses 3 vessels and 6 applications per vessel.
