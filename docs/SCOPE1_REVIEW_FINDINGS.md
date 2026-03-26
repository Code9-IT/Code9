# Scope 1 Review Findings

Last updated: 2026-03-12

This document is the concentrated review and acceptance baseline for the current
Scope 1 integration branch.

Read together with:

- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`
- `docs/SCOPE1_HANDOFF_NOTES.md`
- `docs/NEXT_STEPS.md`
- `docs/FUTURE_CHECKS.md`
- `docs/UDS_dashboard_spec.md`

## Scope 1 target

The agreed target is User Story 1 from Geir:

> As a DevOps engineer, when I receive a warning or error from an application
> on a vessel, I need a dashboard that shows:
>
> - the complete operational state of all applications on that vessel
> - relevant historical metrics and logs
> - context necessary to evaluate the situation and take action

The standard is therefore not just "the code runs". The standard is whether the
prototype gives credible incident context for a single-vessel application
incident.

## Current review conclusion

The project is no longer structurally broken, and the main UDS Scope 1 gaps from
the earlier review are now closed for prototype purposes.

On `feat/scope1-student1-2-3-integration`, Scope 1 now provides:

- an incident-first Grafana dashboard for one vessel
- historical metrics inside Grafana, not only through MCP
- log/log-like context through `app_logs`
- broader seeded scenarios including degraded, stale, and delayed states
- visible connectivity and freshness signals
- working MCP access for status, alerts, metric history, and app logs

That is now a coherent bachelor prototype baseline for User Story 1.

## Evidence from the fresh-stack Student 4 validation

Acceptance rerun performed on 2026-03-12 from a fresh DB volume.

Verified:

- `udslocations` rows: 3
- `applications` rows: 6
- `uds_location_application_instances` rows: 18
- first UDS seed cycle inserted:
  - 468 `metric_samples`
  - 11 `alerts`
  - 29 `app_logs`
- seeded alert types were not limited to `ServiceDown`
- Grafana provisioned dashboard UID `maritime_uds_monitoring`
- MCP returned non-empty data for:
  - `get_vessel_app_status`
  - `get_vessel_alerts`
  - `get_app_metric_history`
  - `get_app_logs`
- validation dashboard loaded successfully
- quick analysis validation completed successfully on event `1`

## What was closed from the earlier review

### 1. Historical metrics are now surfaced in Grafana

Closed for the current prototype scope.

What exists now:

- selected app drilldown in `uds_monitoring.json`
- time-series panels for availability, connectivity/freshness, HTTP/errors,
  CPU/handles, memory, and database behavior
- `incident_window` variable for 1h / 6h / 24h slices
- metric summary table inside the same dashboard

Relevant files:

- `grafana/dashboards/uds_monitoring.json`
- `grafana/queries/uds_queries.sql`
- `docs/UDS_dashboard_spec.md`

### 2. Log/log-like context now exists in the UDS path

Closed for the current prototype scope.

What exists now:

- tracked `app_logs` table in the UDS schema
- seeded app logs and alert-driven log context
- MCP access through `get_app_logs`
- Grafana table for recent logs on the selected vessel/app pair

Relevant files:

- `db/init/003_uds.sql`
- `db/seed/uds_seed.sql`
- `services/mcp/main.py`
- `grafana/dashboards/uds_monitoring.json`

### 3. Seeded scenarios are broader and more realistic

Closed for the current prototype scope.

What exists now:

- `healthy`
- `degraded`
- `down`
- `stale`
- `delayed`

Connectivity/freshness signals now include:

- `last_sync_age_seconds`
- `reporting_stale`
- `sync_delayed`

Alert types now include more than simple `ServiceDown` behavior.

Relevant files:

- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`

### 4. Fresh-DB technical acceptance was rerun successfully

Closed as a fresh-stack validation milestone for the current branch.

Verified on the fresh-stack rerun:

- UDS schema and tracked reference data load on startup
- `uds-seeder` inserts metrics, alerts, and logs
- MCP tools return meaningful UDS incident data
- `UDS Incident Monitoring` is provisioned in Grafana
- validation dashboard loads, and quick analysis validation works

This still needs to be rerun on the final merge candidate after any further
code changes.

## Remaining findings

### Medium

#### 1. Existing DB volumes still rely on reset/runtime-guard behavior

Scope 1 now works from a fresh DB and the agent adds runtime schema guards, but
the project still does not have a formal migration strategy for older local
volumes.

Why it matters:

- old local DB state can hide real integration issues
- team members can get different results if they skip reset

Relevant files:

- `db/init/001_init.sql`
- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`
- `services/agent/main.py`

#### 2. Fresh-start bootstrap still depends on startup timing

The fresh-stack check passed, but first startup still depends on model pull,
RAG ingest, and service readiness settling in the right order.

Observed during the validation rerun:

- the agent retried RAG ingest until embeddings were available
- `ollama-init` needed warmup time before the agent finished ingest cleanly

Why it matters:

- the first run can take time
- demo preparation should allow for that warmup period

Relevant files:

- `docker-compose.yml`
- `services/agent/main.py`
- `services/agent/llm/ollama_client.py`
- `scripts/uds_seed_loop.sh`

#### 3. Legacy full analysis still needs a final warmup/signoff if it is part of the demo

This does not block Scope 1 UDS acceptance, but it is still a real integration
note.

Observed during the validation rerun:

- quick validation completed successfully
- one cold-start full analysis job remained `running` after the first minute

Why it matters:

- the group should not overclaim legacy full-analysis readiness without a final
  signoff pass
- if that path is used in a demo, it should be warmed up first

Relevant files:

- `services/agent/routes/analyze.py`
- `services/agent/routes/validation.py`
- `services/agent/llm/ollama_client.py`

### Low

#### 4. Event acknowledge still has a state-changing GET alias

This is still weak API design, even if it is convenient for Grafana links.

Relevant file:

- `services/agent/routes/events.py`

#### 5. MCP auth is still effectively optional if `MCP_API_KEY` is empty

That is acceptable for a local prototype, but it should not be treated as a
finished security solution.

Relevant files:

- `services/mcp/main.py`
- `.env.example`
- `docker-compose.yml`

#### 6. The demo topology is intentionally fixed to 3 vessels and 6 apps

That is fine for Scope 1. It is not enough to claim the broader scalability
part of Geir's full platform description.

Relevant files:

- `db/init/004_uds_reference_data.sql`
- `db/seed/uds_seed.sql`

#### 7. `app_logs` is still a lightweight prototype bridge

The logs path is now good enough for User Story 1 prototype context, but it is
not a full centralized application log pipeline.

Relevant files:

- `db/init/003_uds.sql`
- `db/seed/uds_seed.sql`
- `services/mcp/main.py`

## What is good enough now

These parts are good enough to carry into the final merge/demo round:

- tracked UDS schema direction
- tracked reference data
- seeded metrics, alerts, and logs
- incident-first UDS dashboard
- MCP UDS tools
- fresh-stack acceptance flow
- validation dashboard and quick analysis path

## What should happen next

Recommended order:

1. Keep the docs synchronized with the branch that will actually be merged.
2. Re-run the acceptance checklist on the final merge candidate.
3. Do one manual Grafana signoff pass.
4. Only then spend time on low-priority hardening.
