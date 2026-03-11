# Next Steps - Scope 1 Work Split

Last updated: 2026-03-11

This file is the active execution plan for finishing Scope 1 (User Story 1).
It replaces older per-person notes and keeps ownership explicit to reduce merge
conflicts.

Use this together with:

- `docs/SCOPE1_REVIEW_FINDINGS.md`
- `docs/SCOPE1_HANDOFF_NOTES.md`
- `README.md`

## Scope 1 target

User Story 1 requires one-vessel incident context with:

- complete operational state for hosted applications
- relevant historical metrics and logs/log-like context
- enough context to evaluate and act

## Active 4-student split

### Student 1 - UDS dashboard incident flow + historical metrics

Own files:

- `grafana/dashboards/uds_monitoring.json`
- `grafana/queries/uds_queries.sql`
- `docs/UDS_dashboard_spec.md`

Deliver:

- alert -> app -> recent history incident navigation in Grafana
- time-series historical metrics in the dashboard itself
- clear time-window context around incidents (for example 1h/6h/24h)

Done when:

- vessel selection works
- affected app can be identified from active incidents
- recent metric history is visible without leaving Grafana

### Student 2 - logs/log-like UDS context + MCP access

Own files:

- `db/init/003_uds.sql`
- `services/mcp/main.py`

Deliver:

- lightweight log/log-like table for UDS incident context
- MCP tool support for fetching logs in a recent time window
- stable contract others can consume

Done when:

- DB has tracked log/log-like schema
- MCP can retrieve app incident logs for one vessel/app/time window

### Student 3 - broader seeding scenarios + freshness/connectivity realism

Own files:

- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`

Deliver:

- warning + degraded + down + stale/delayed scenario coverage
- explicit freshness/connectivity-like signals
- less dependence on only ServiceDown/critical-down cases

Done when:

- seeded incidents cover multiple severities/states
- connectivity/freshness behavior is visible in demo data

### Student 4 - final validation + docs + merge support

Own files:

- `README.md`
- `docs/NEXT_STEPS.md`
- `docs/SCOPE1_REVIEW_FINDINGS.md`
- `docs/SCOPE1_HANDOFF_NOTES.md`

Deliver:

- repeatable fresh-DB acceptance flow for Scope 1
- checklist covering DB, seeder scenarios, Grafana incident context, MCP tools
- docs synced with final merged behavior

Done when:

- acceptance flow is documented and repeatable
- docs do not claim missing features after they are merged
- merge support notes are clear for final integration

## Integration order

1. Student 2 defines log schema + MCP contract.
2. Student 3 seeds new scenarios against that contract.
3. Student 1 wires incident/historical flow in Grafana.
4. Student 4 runs acceptance and updates docs.

## Coordination rules

- Student 1 is the only editor of `uds_monitoring.json`.
- Student 3 is the main editor of `uds_seed.sql`.
- Student 4 does not rewrite Student 1-3 feature code; Student 4 validates and documents.

## Out of scope for this final Scope 1 pass

- full auth hardening
- removing acknowledge GET alias
- migration strategy for old DB volumes
- multi-vessel scaling work
- NOC support dashboard scope
