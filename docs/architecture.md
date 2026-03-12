# Architecture - Maritime Agentic Observability

## Purpose

This prototype now contains two related monitoring paths:

1. Legacy ship telemetry
   - synthetic sensors
   - anomaly events
   - AI analysis on those events
2. Scope 1 UDS incident monitoring
   - application health per vessel
   - UDS metrics, alerts, and app logs
   - Grafana and MCP access for one-vessel incident handling

The Scope 1 goal is User Story 1:

- one vessel
- all hosted applications on that vessel
- relevant historical metrics and logs
- enough context to evaluate the situation and take action

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
uds-seeder --------------------------------------------> metric_samples / alerts / app_logs
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
| `uds-seeder` | Produces periodic UDS mock metrics, alerts, and app logs |
| `grafana` | Shows Ship Operations and UDS Incident Monitoring dashboards |
| `agent` | Runs AI analysis for legacy anomaly events |
| `mcp` | Exposes both legacy and UDS database tools |
| `ollama` | Local LLM inference for agent and embeddings |
| `ollama-init` | Pulls required models on stack startup |

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
- `app_logs`
- `uds_location_owner_history`
- `monitoring_configs` as a compatibility shim

Used by:

- `grafana/dashboards/uds_monitoring.json`
- `services/mcp/main.py`

## Scope 1 architecture status

What is structurally correct now:

- Del A, B, C, and D all target the same UDS schema
- vessel selection is based on `udslocations.imo_nr`
- app health is based on linked applications, metrics, alerts, and app logs
- seeded data respects vessel-to-application links
- Grafana supports alert -> app -> recent metric/log history drilldown
- connectivity and freshness are visible through seeded metrics and dashboard
  panels

What is still intentionally limited:

- `app_logs` is a lightweight log bridge, not full centralized log ingestion
- the demo topology is still 3 vessels / 6 applications
- the legacy analysis path is related to Scope 1, but it is not the main proof
  point for User Story 1

## Important design limitations

### 1. Fresh DB bias

The prototype still relies on init scripts for both schema and reference data.
Old local volumes can drift away from code expectations.

### 2. Cold-start timing matters

First start still depends on model pull, RAG ingest, and service readiness.
That is acceptable for a local prototype, but it means the stack should be
started a little ahead of any demo.

### 3. Security shortcuts

The project is still a local prototype:

- event acknowledge still has a GET alias
- MCP auth is optional if `MCP_API_KEY` is unset
- convenience-oriented demo credentials still exist

### 4. Prototype log bridge, not full log collection

The current `app_logs` path is intentionally small:

- it stores seeded app log context plus alert-driven incident rows
- it closes the Scope 1 User Story 1 gap around logs for the prototype
- it does not replace a future full application log pipeline
