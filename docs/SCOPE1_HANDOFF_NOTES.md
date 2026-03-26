# Scope 1 Handoff Notes

This file is the short handoff for the current integrated Scope 1 state.

For deeper review and remaining findings, also read:

- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`
- `docs/SCOPE1_REVIEW_FINDINGS.md`
- `docs/NEXT_STEPS.md`

## Recommended working branch

Current integrated working branch:

- `feat/scope1-student1-2-3-integration`

Treat older branches such as `feat/scope1-merged`,
`feat/scope1-del-d-integration`, and `feat/scope1-del-a-b-integration` as
historical integration steps, not as the best current base.

## What is already integrated

### UDS schema and seed path

- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`
- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`
- `uds-seeder` service in `docker-compose.yml`

### UDS incident visibility

- `grafana/dashboards/uds_monitoring.json`
- `grafana/queries/uds_queries.sql`
- `docs/UDS_dashboard_spec.md`

### UDS data access

- `services/mcp/main.py`
- API key support for MCP
- UDS tools for:
  - vessel app status
  - vessel alerts
  - app metric history
  - app logs

### Legacy analysis support

- validation dashboard in `services/agent/routes/validation.py`
- quick and full analysis routing in `services/agent/routes/analyze.py`
- runtime schema guards in `services/agent/main.py`

## Fresh-stack acceptance rerun summary

Student 4 reran the acceptance flow on 2026-03-12 from a fresh DB volume.

Confirmed:

- UDS schema and reference data load correctly on startup
- fresh DB counts:
  - `udslocations`: 3
  - `applications`: 6
  - `uds_location_application_instances`: 18
- first `uds-seeder` cycle inserted:
  - `metric_samples`: 468
  - `alerts`: 11
  - `app_logs`: 29
- seeded alert mix included degraded, stale, delayed, and down cases
- Grafana provisioned `UDS Incident Monitoring`
- MCP returned non-empty results for status, alerts, metric history, and logs
- validation dashboard returned HTTP 200
- quick analysis validation completed on the fresh stack

## Real remaining risks

### 1. Fresh DB is still the only trustworthy validation path

The stack works from a fresh DB and runtime guards help in some places, but the
project still does not have a formal migration strategy for older local DBs.

Practical rule:

- use `docker compose down -v` before serious Scope 1 validation

### 2. Legacy full analysis should still be warmed up before a demo

During the fresh-stack validation rerun:

- quick validation completed successfully
- one full analysis job was still `running` after the first minute

Practical rule:

- if you want to demo legacy full analysis, run it early and verify it
  separately
- do not make that path the main Scope 1 proof point

### 3. Bootstrap timing still matters on first start

The first run may still take time because model pull, RAG ingest, generator,
and `uds-seeder` need to settle.

Practical rule:

- give the stack a few minutes on the first startup
- watch `ollama-init`, `agent`, `generator`, and `uds-seeder` logs

### 4. Security shortcuts are still present

These are known prototype shortcuts, not current Scope 1 blockers:

- acknowledge still has a GET alias
- MCP auth is optional if `MCP_API_KEY` is empty
- demo credentials are still convenience-oriented

## Geir files vs tracked repo files

`databasecodeFraGeir/` is still local and untracked.

That no longer blocks the runnable prototype, because the important Scope 1
files are now tracked in the repo:

- schema: `db/init/003_uds.sql`
- reference data: `db/init/004_uds_reference_data.sql`
- seeding: `db/seed/uds_seed.sql`

The Geir files are still useful as source material and comparison input, but
they are no longer the runnable source of truth.

## Definition of good enough now

The current branch is good enough for:

- final merge preparation
- repeatable acceptance testing
- demo preparation of the UDS incident flow

It is not the same thing as a production-ready platform.
