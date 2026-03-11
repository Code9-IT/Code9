# Scope 1 Handoff Notes

Last updated: 2026-03-11

This is the handoff file for final Scope 1 integration work.
It is focused on final merge readiness, acceptance validation, and doc sync.

For detailed review rationale, also read:

- `docs/SCOPE1_REVIEW_FINDINGS.md`
- `docs/NEXT_STEPS.md`

## Recommended working base

Use:

- `feat/code9-scope1-team-base`

Avoid using older integration branches as your active base. They represent
partial or replaced states.

## Current integration status

The shared base already includes:

- UDS schema + reference data (`003_uds.sql`, `004_uds_reference_data.sql`)
- periodic UDS seeding (`uds_seed.sql`, `uds_seed_loop.sh`, `uds-seeder`)
- MCP UDS tool path (`services/mcp/main.py`)
- UDS dashboard baseline (`uds_monitoring.json`, `uds_queries.sql`)

Scope 1 is still open until incident context is complete in Grafana and the
fresh-DB acceptance run passes after Student 1-3 changes are merged.

## Student 4 scope (this handoff owner)

Do not implement Student 1-3 feature code. Own:

- final acceptance validation pass
- merge support and integration checklist
- documentation sync in:
  - `README.md`
  - `docs/NEXT_STEPS.md`
  - `docs/SCOPE1_REVIEW_FINDINGS.md`
  - `docs/SCOPE1_HANDOFF_NOTES.md`

## Scope 1 acceptance gate (run after Student 1-3 merge)

1. Fresh DB start:
   - `docker compose down -v`
   - `docker compose up --build`
2. DB validation:
   - UDS tables exist
   - UDS reference data exists
3. Seeder validation:
   - `metric_samples` and `alerts` receive rows
   - new scenario mix is visible (not only ServiceDown/critical-down)
4. Grafana validation:
   - vessel selector works
   - incident flow can move from alert to app context
   - historical metrics are visible in dashboard
   - logs/log-like context is visible (or explicitly documented if deferred)
5. MCP validation:
   - `get_vessel_app_status`
   - `get_vessel_alerts`
   - `get_app_metric_history`
   - log/log-like tool from Student 2 contract
6. Documentation sync:
   - no doc claims mismatch with merged behavior
   - README and docs point to one repeatable acceptance flow

## Merge-support checklist

- Pull latest `origin/feat/code9-scope1-team-base`.
- Merge Student 1-3 branches into the shared branch.
- Resolve conflicts without changing ownership boundaries.
- Run the acceptance gate above.
- Capture acceptance evidence in commit/PR notes.
- Update docs in one focused Student 4 doc PR/commit.

## Definition of done for Scope 1 handoff

Scope 1 is ready for demo/merge when:

- acceptance gate passes on a fresh DB run
- dashboard incident context includes current state + history + logs/log-like path
- docs and branch guidance are consistent with final merged behavior
