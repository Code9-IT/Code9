# Maritime Agentic Observability Starter Kit

Bachelor project in collaboration with **Knowit Sorlandet**.

This repository now contains two parallel monitoring paths:

1. Legacy ship telemetry
   - synthetic sensors
   - anomaly events
   - AI analysis for telemetry incidents
2. Scope 1 UDS incident monitoring
   - application health per vessel
   - periodic UDS metrics, alerts, and app logs
   - Grafana and MCP support for single-vessel incident handling

The current Scope 1 target is User Story 1 from Geir:

> When a warning or error arrives from an application on a vessel, the team
> needs a dashboard that shows the full operational state of the vessel's
> applications, relevant historical metrics and logs, and enough context to
> evaluate the situation and take action.

Useful companion docs:

- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`
- `docs/SCOPE1_HANDOFF_NOTES.md`
- `docs/SCOPE1_REVIEW_FINDINGS.md`
- `docs/NEXT_STEPS.md`
- `docs/UDS_dashboard_spec.md`
- `docs/FUTURE_CHECKS.md`

## Current status

As of 2026-03-12, a fresh-stack Student 4 validation on
`feat/scope1-student1-2-3-integration` confirmed:

- tracked UDS schema and reference data load on a fresh DB volume
- the repo seeds 3 demo vessels, 6 applications, and 18 vessel/application links
- `uds-seeder` inserts `metric_samples`, `alerts`, and `app_logs`
- `UDS Incident Monitoring` is provisioned in Grafana
- MCP UDS tools return vessel status, alerts, metric history, and app logs
- the validation dashboard loads, and quick legacy-event analysis completes

The main remaining work is now final merge discipline, documentation hygiene,
and low-priority hardening.

One important caveat still exists: legacy **full** analysis can take longer than
the first minute on a cold start, so if you plan to demo that path, warm it up
and verify it separately. That does not block Scope 1 UDS acceptance.

## Quick start

### Prerequisites

- Docker Desktop

No local PostgreSQL or Python install is required for the normal workflow.

### Start the stack

```bash
git clone <repo-url>
cd <repo-dir>
cp .env.example .env
docker compose up -d --build
```

Important first-start behavior:

- `ollama-init` pulls `llama3.2` and `nomic-embed-text`
- the agent retries RAG ingest until embeddings are available
- the generator inserts one startup event if the legacy `events` table is empty
- `uds-seeder` waits until the UDS schema and reference data exist

Useful startup logs:

```bash
docker compose logs -f ollama-init agent generator uds-seeder
```

### Open the main services

- Grafana: `http://localhost:3000`
- Agent docs: `http://localhost:8000/docs`
- Validation dashboard: `http://localhost:8000/api/v1/validate/dashboard`
- MCP docs: `http://localhost:8001/docs`

Default demo Grafana credentials from `.env.example` are:

- user: `admin`
- password: `code9-demo-admin`

### Important reset rule

The database init scripts only auto-run on a fresh DB volume. For trustworthy
Scope 1 validation, reset the stack like this:

```bash
docker compose down -v
docker compose up -d --build
```

If you test against an old volume, you may hide schema drift or init problems.

### Scope 1 acceptance

Use `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md` as the repeatable acceptance flow.
That checklist covers:

- fresh DB startup
- UDS schema and reference data
- seeding into metrics, alerts, and logs
- Grafana incident flow
- MCP sanity checks
- validation and legacy-analysis sanity checks

## Project layout

```text
.
|-- docker-compose.yml
|-- .env.example
|
|-- db/
|   |-- init/001_init.sql
|   |-- init/002_rag.sql
|   |-- init/003_uds.sql
|   |-- init/004_uds_reference_data.sql
|   `-- seed/uds_seed.sql
|
|-- grafana/
|   |-- dashboards/
|   |   |-- ship_operations.json
|   |   `-- uds_monitoring.json
|   |-- provisioning/
|   `-- queries/uds_queries.sql
|
|-- services/
|   |-- agent/
|   |-- generator/
|   `-- mcp/
|
|-- scripts/
|   |-- reset_db.sh
|   `-- uds_seed_loop.sh
|
`-- docs/
    |-- SCOPE1_ACCEPTANCE_CHECKLIST.md
    |-- SCOPE1_HANDOFF_NOTES.md
    |-- SCOPE1_REVIEW_FINDINGS.md
    |-- NEXT_STEPS.md
    |-- FUTURE_CHECKS.md
    `-- UDS_dashboard_spec.md
```

## Scope 1 path summary

### Legacy path

Defined mainly by:

- `db/init/001_init.sql`
- `services/generator/`
- `services/agent/routes/analyze.py`
- `grafana/dashboards/ship_operations.json`

Tables:

- `telemetry`
- `events`
- `ai_analyses`

### UDS path

Defined mainly by:

- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`
- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`
- `services/mcp/main.py`
- `grafana/dashboards/uds_monitoring.json`

Tables:

- `owners`
- `udslocations`
- `applications`
- `uds_location_application_instances`
- `metric_samples`
- `alerts`
- `app_logs`
- `uds_location_owner_history`
- `monitoring_configs` (compatibility shim)

## Known limitations

These are still real, but they are not the main Scope 1 blocker anymore:

- `GET /api/v1/events/{event_id}/acknowledge` still mutates state
- MCP auth is only enforced if `MCP_API_KEY` is non-empty
- existing DB volumes still rely on reset/runtime-guard behavior instead of a
  full migration strategy
- the demo topology is intentionally fixed to 3 vessels and 6 applications
- `app_logs` is a lightweight prototype bridge, not a full centralized log
  pipeline
- cold-start legacy full analysis may need extra warmup time before a demo

See `docs/FUTURE_CHECKS.md` for the current backlog.

## Group workflow

1. Work from the current integration branch or a short-lived feature branch on top of it.
2. Keep changes narrow and scoped.
3. Update docs in the same PR when behavior changes.
4. Re-run the Scope 1 acceptance checklist after meaningful merges.
5. Treat `databasecodeFraGeir/` as local source material, not the runnable
   source of truth.
