# Next Steps - Scope 1 Integration

This file replaces the older person-by-person work split.
The project is now in an integration phase where Del A, B, C, and D already
exist in the same branch and the next work should be driven by the User Story 1
gap, not by the old ownership split.

For longer-term backlog items, see `docs/FUTURE_CHECKS.md`.
For the concentrated review baseline, see `docs/SCOPE1_REVIEW_FINDINGS.md`.

## Scope 1 target

User Story 1:

- one vessel
- one or more warnings/errors from applications on that vessel
- complete operational state of the hosted applications
- relevant historical metrics and logs
- enough context to evaluate the situation and take action

## What is already in place

### Del A - UDS schema

- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`

Current result:

- UDS schema exists
- 3 reference vessels exist
- 6 reference applications exist
- vessel/application link rows exist

### Del B - UDS seeding

- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`
- `uds-seeder` service in `docker-compose.yml`

Current result:

- periodic UDS seeding exists
- seeding now respects vessel/application link rows
- seeding waits until schema and reference data are ready

### Del C - MCP UDS tools

- `services/mcp/main.py`

Current result:

- `get_vessel_app_status`
- `get_vessel_alerts`
- `get_app_metric_history`
- API key support for MCP

### Del D - UDS dashboard

- `grafana/dashboards/uds_monitoring.json`
- `grafana/queries/uds_queries.sql`
- `docs/UDS_dashboard_spec.md`

Current result:

- one-vessel UDS dashboard exists
- vessel selector is based on `imo_nr`
- app health tables and alert tables are in place

## What still blocks full User Story 1 closure

### 1. Historical metrics are not surfaced strongly enough

The data and MCP support exist, but the dashboard still behaves mostly like a
latest-state health board.

What should be added next:

- time-series drilldown for selected application metrics
- at least one clear path from alert -> app -> recent metric history

### 2. Logs are not represented in the UDS path

The current UDS implementation models:

- `metric_samples`
- `alerts`

It does not yet model log delivery or log history in the UDS side.

Decision needed:

- either add a lightweight log-like representation for Scope 1
- or document clearly that Scope 1 covers metrics + alerts only, and that logs
  are postponed

### 3. Seeded scenarios are too narrow

Current seeded UDS incidents are weighted around service-down style failures.

What should be expanded next:

- warning-level alerts
- degraded-but-not-down scenarios
- stale reporting / delayed sync style issues

### 4. Full end-to-end verification is still required

The integrated code is not enough by itself. The stack still needs a fresh DB
run and validation.

Required test flow:

1. start from a fresh DB volume
2. run `docker compose up`
3. confirm reference data exists
4. confirm `uds-seeder` inserts into `metric_samples` and `alerts`
5. confirm Grafana UDS panels render
6. confirm MCP UDS tools return expected data

## Current recommended execution order

1. Run the full fresh-DB integration test.
2. Fix any schema/seeding/runtime mismatches discovered there.
3. Add historical metric views to the UDS dashboard.
4. Decide how to cover the "logs" part of User Story 1.
5. Expand seeded incident scenarios.
6. Only then declare Scope 1 functionally complete.

## What does not need focus right now

These are real issues, but they are not the next Scope 1 blocker:

- User Story 2 and 3
- RAG tuning beyond what already works
- JWT / full auth
- rate limiting
- audit logging

## Practical notes for the team

- Work from `feat/scope1-del-a-b-integration`
- Treat `databasecodeFraGeir/` as local source material, not as the runnable source of truth
- Use the tracked repo files for schema, reference data, and seeding
- If something only works on an old DB volume, do not trust that result
