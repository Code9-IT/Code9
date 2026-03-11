# Scope 1 Handoff Notes

This file is the short handoff for the current integrated Scope 1 state.
It replaces the older "Del A / Del B only" version of this document.
For the deeper review and remaining findings, also read
`docs/SCOPE1_REVIEW_FINDINGS.md`.

## Recommended working branch

Use:

- `feat/scope1-del-a-b-integration`

Do not use these as your current working base:

- `origin/nidal-updates`
- `origin/feat/scope1-merged`
- `origin/feat/scope1-del-d-integration`

Reason:

- `feat/scope1-del-a-b-integration` is the first branch where Del A, Del B, Del C, and Del D point in the same UDS direction.
- Older branches represent partial integration stages.

## What is already integrated

The current integrated branch contains:

- Del A:
  - `db/init/003_uds.sql`
- Del A support data:
  - `db/init/004_uds_reference_data.sql`
- Del B:
  - `db/seed/uds_seed.sql`
  - `scripts/uds_seed_loop.sh`
  - `uds-seeder` service in `docker-compose.yml`
- Del C:
  - UDS MCP tools in `services/mcp/main.py`
  - API key support for MCP
- Del D:
  - `grafana/dashboards/uds_monitoring.json`
  - `grafana/queries/uds_queries.sql`
  - `docs/UDS_dashboard_spec.md`

Also already integrated:

- `data_quality.json` has been removed
- `ship_operations.json` was corrected back to latest active alarms ordering
- the Grafana analysis flow now prefers the full analysis path

## Current Scope 1 status

The project is now technically aligned around the UDS schema, but Scope 1 is
not fully closed against User Story 1 yet.

What already works conceptually:

- one-vessel UDS schema
- reference vessels and applications
- periodic mock seeding into `metric_samples` and `alerts`
- UDS dashboard for one selected vessel
- MCP tools for app status, alerts, and metric history

What is still missing or weaker than the user story expects:

- the dashboard does not yet show strong historical metric drilldown
- the UDS path does not model logs, only metrics and alerts
- seeded scenarios are still narrow
- full end-to-end validation still requires a fresh DB volume

## Known issues that still matter

### 1. Existing DB volumes may be out of date

The current setup relies on init scripts:

- `db/init/001_init.sql`
- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`

If a developer already has an older TimescaleDB volume, the DB may not match the
current code and dashboard assumptions.

Practical consequence:

- use a fresh DB volume for serious Scope 1 testing
- otherwise apply manual migrations

### 2. `analysis_mode` still has migration risk

The code expects `analysis_mode` in `ai_analyses`, and `001_init.sql` contains
it now, but older local databases may still be missing that column.

This is not a Del A / Del B problem anymore. It is an integration hygiene
problem for existing local environments.

### 3. Event acknowledge is still too open

The agent still exposes:

- `POST /api/v1/events/{event_id}/acknowledge`
- `GET /api/v1/events/{event_id}/acknowledge`

This is convenient for Grafana demos, but not good API design and not something
to carry forward without auth.

### 4. MCP auth is only enforced if `MCP_API_KEY` is set

If `MCP_API_KEY` is empty, the MCP API effectively runs without auth.

That is acceptable for a local prototype, but it should be treated as a known
security shortcut, not as a finished design.

## Geir files vs tracked repo files

`databasecodeFraGeir/` is still local and untracked in this repo.

That matters less than before, because the important Scope 1 equivalents are now
tracked in the repository:

- schema: `db/init/003_uds.sql`
- reference data: `db/init/004_uds_reference_data.sql`
- seeding: `db/seed/uds_seed.sql`

The local Geir files are still useful as source material and comparison input,
but the prototype no longer depends on them being present in every clone in
order to run.

## What to do before claiming Scope 1 works

1. Start from a fresh DB volume.
2. Bring the stack up and confirm:
   - UDS tables exist
   - reference vessels and apps exist
   - `uds-seeder` starts inserting rows
3. Verify Grafana:
   - vessel selector is populated
   - UDS panels show data
   - alerts table is populated
4. Verify MCP:
   - `get_vessel_app_status`
   - `get_vessel_alerts`
   - `get_app_metric_history`
5. Review the remaining gap against User Story 1:
   - historical metrics visibility
   - logs or log-like context
   - action-oriented incident context

## Definition of "good enough for now"

The current branch is good enough for integration work and end-to-end testing
because the four Scope 1 parts are finally aligned.

It is not yet good enough to claim that User Story 1 is fully solved.
