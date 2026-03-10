# Scope 1 Handoff Notes

This document is meant as a short AI-readable handoff for Del A and Del B work.
Use it together with the main project intro and Scope 1 task split.

## Recommended base branch

Use:

- `origin/feat/scope1-del-d-integration`

Do not use these as your working base for Del A / Del B:

- `origin/nidal-updates`
- `origin/feat/scope1-merged`

Reason:

- `origin/nidal-updates` is too old and was based on an outdated dashboard direction.
- `origin/feat/scope1-del-d-integration` already ports Del D onto the newer Scope 1 base.

## What is already integrated on this branch

These parts are already present in `feat/scope1-del-d-integration`:

- New Del D dashboard:
  `grafana/dashboards/uds_monitoring.json`
- Supporting dashboard docs:
  `docs/UDS_dashboard_spec.md`
- Supporting SQL reference:
  `grafana/queries/uds_queries.sql`
- Old `grafana/dashboards/data_quality.json` removed
- `grafana/dashboards/ship_operations.json` corrected so active alarms again show latest alarms first

## Important known issues on this branch

These are known inherited issues from `feat/scope1-merged`.
They are not blockers for Del A / Del B today, but the AI should know about them.

### 1. Quick vs full analysis issue

The current analysis flow still has a split between `quick` and `full` analysis in:

- `services/agent/routes/analyze.py`

Current risk:

- Grafana links currently go through `/view?refresh=true`
- That flow can end up using the quick path instead of the full tool-enabled path

This is **not** part of Del A or Del B, but it is a known integration issue.

### 2. `analysis_mode` migration issue

The code now uses `analysis_mode`, and `db/init/001_init.sql` includes it, but there is no proper migration for already-existing databases.

Current risk:

- If someone already has an older TimescaleDB volume, the running DB may not match the current schema
- Code may fail unless the DB is reset or manually migrated

This matters especially if testing against an existing local DB volume.

## Important note about Geir files

`databasecodeFraGeir/` is still local/untracked in this repo state.

That means:

- These files may not exist in every clone automatically
- Jonas and Kristian must make sure they have them locally or from Discord

Required Geir files:

- `databasecodeFraGeir/logging_db_dbml.txt`
- `databasecodeFraGeir/db_init_script (1).txt`
- `databasecodeFraGeir/db_seeding_script.txt`

## Notes for Del A (Database)

If you are doing Del A, be aware of the following:

- Build the UDS schema in a **new** file:
  `db/init/003_uds.sql`
- Do **not** replace the old telemetry/events schema in `db/init/001_init.sql`
- Keep the existing prototype pipeline intact
- The Del D dashboard expects these UDS tables to exist exactly:
  - `udslocations`
  - `applications`
  - `uds_location_application_instances`
  - `metric_samples`
  - `alerts`
- The dashboard and MCP queries assume vessel selection by `imo_nr`
- `metric_samples` should support latest-per-app-per-metric queries
- `metric_samples.time` should be the hypertable time column

### Del A mismatch to watch

Geir's init script references `monitoring_configs`, but that table is not in the DBML.

AI should not ignore this.
It must make an explicit decision:

- either add a minimal `monitoring_configs` table
- or remove/adapt that part of the init flow deliberately

## Notes for Del B (Seeding)

If you are doing Del B, be aware of the following:

- Work from the exact schema Del A creates
- Do not assume table/column names without checking Del A first
- The seeding goal is to fill:
  - `metric_samples`
  - `alerts`
- The intended cadence is every 30 minutes
- The Del D dashboard is built around Geir's UDS metrics, not the old ship sensor telemetry schema
- Del B will likely need changes in:
  - `docker-compose.yml`
  - seeding setup / script execution flow

### Del B integration watch-outs

- Avoid conflicting edits in `docker-compose.yml`
- Confirm the seeded vessel IDs match `imo_nr` values expected by the dashboard
- Confirm app identifiers map consistently across:
  - `applications.external_id`
  - `metric_samples.app_id`
  - `metric_samples.application_instance_id`
  - `alerts.application_id`

## Shared advice for Del A and Del B

- Branch from `feat/scope1-del-d-integration`
- Keep PRs/commits focused
- Do not reintroduce `data_quality.json`
- Do not branch from `origin/nidal-updates`
- Do not assume old dashboards or old telemetry schema are the Scope 1 target
- Scope 1 target is Geir's User Story 1 UDS flow

## Definition of “good enough for now”

For today, this branch is considered good enough as the working base for Del A and Del B because:

- Del D is already ported onto it
- The old wrong dashboard direction has been removed
- The remaining known problems are outside Del A / Del B scope

But before final integration/demo, the team should still revisit:

- quick vs full analysis behavior
- `analysis_mode` database migration / DB reset strategy
