# Architecture - Maritime Agentic Observability

## Purpose

This prototype now contains two related monitoring paths:

1. The original ship telemetry path
   - synthetic sensors
   - anomaly events
   - AI analysis on those events
2. The Scope 1 UDS path
   - application health per vessel
   - UDS metrics and alerts
   - dashboard and MCP access for one-vessel incident handling

The Scope 1 goal is User Story 1:

- one vessel
- all hosted applications on that vessel
- relevant operational context when something goes wrong

## High-level component view

```text
generator ------------------------> telemetry / events ----------+
                                                                  |
                                                                  v
                                                         ship_operations.json
                                                                  |
                                                                  v
                                                           agent analyze flow
                                                                  |
                                                          +-------+-------+
                                                          |               |
                                                          v               v
                                                      RAG context       MCP tools

004_uds_reference_data.sql ---> UDS reference tables ----+
                                                         |
uds-seeder --------------------------------------------> metric_samples / alerts
                                                         |
                                                         v
                                                 uds_monitoring.json
                                                         |
                                                         v
                                                     MCP UDS tools
```

## Main services

| Service | Responsibility |
|---------|----------------|
| `timescaledb` | Stores legacy telemetry/events plus UDS tables |
| `generator` | Produces legacy synthetic ship telemetry and anomaly events |
| `uds-seeder` | Produces periodic UDS mock metrics and alerts |
| `grafana` | Shows Ship Operations and UDS Monitoring dashboards |
| `agent` | Runs AI analysis for legacy anomaly events |
| `mcp` | Exposes both legacy and UDS database tools |
| `ollama` | Local LLM inference for agent and embeddings |

## Data model split

### Legacy path

Defined in:

- `db/init/001_init.sql`

Tables:

- `telemetry`
- `events`
- `ai_analyses`

Used by:

- `services/generator/`
- `grafana/dashboards/ship_operations.json`
- `services/agent/routes/analyze.py`

### UDS Scope 1 path

Defined in:

- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`

Seeded by:

- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`

Core tables:

- `owners`
- `udslocations`
- `applications`
- `uds_location_application_instances`
- `metric_samples`
- `alerts`
- `uds_location_owner_history`
- `monitoring_configs` as a compatibility shim

Used by:

- `grafana/dashboards/uds_monitoring.json`
- `services/mcp/main.py`

## Scope 1 architecture status

What is structurally correct now:

- Del A, B, C, and D all target the same UDS schema
- vessel selection is based on `udslocations.imo_nr`
- app health is based on `applications`, links, metrics, and alerts
- seeded data now respects vessel-to-application links

What is still incomplete against User Story 1:

- the UDS dashboard is mostly latest-state oriented
- historical metrics exist in DB and MCP, but are not yet surfaced well in Grafana
- the UDS path does not currently model logs
- incident context is therefore weaker than the written user story

## Important design limitations

### 1. Fresh DB bias

The current prototype relies on init scripts for both schema and reference data.
That means old local volumes can drift away from code expectations.

### 2. Security shortcuts

The project is still a local prototype:

- event acknowledge still has a GET alias
- MCP auth is optional if `MCP_API_KEY` is unset
- demo credentials still exist in `.env.example`

### 3. Narrow mock incident model

The UDS seeding path currently focuses on a small set of health metrics and a
single main alert type (`ServiceDown`). That is enough to demonstrate the flow,
but not enough to cover the broader operational scenarios described by Geir.
