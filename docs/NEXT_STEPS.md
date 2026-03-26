# Next Steps - Scope 1 Finalization

Last updated: 2026-03-12

This file now describes the post-integration work for Scope 1. It is no longer
the old student split plan.

Companion docs:

- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`
- `docs/SCOPE1_HANDOFF_NOTES.md`
- `docs/SCOPE1_REVIEW_FINDINGS.md`
- `docs/FUTURE_CHECKS.md`

## Current conclusion

The UDS Scope 1 path is now functionally coherent and has passed a fresh-stack
acceptance rerun on `feat/scope1-student1-2-3-integration`.

What was verified on 2026-03-12:

- the stack booted from `docker compose down -v` and `docker compose up -d --build`
- tracked UDS schema and reference data loaded correctly
- the fresh DB contained:
  - 3 vessels
  - 6 applications
  - 18 vessel/application link rows
- the first `uds-seeder` cycle inserted:
  - 468 `metric_samples`
  - 11 `alerts`
  - 29 `app_logs`
- the seeded alert mix included:
  - `service_down`
  - `latency_degraded`
  - `reporting_stale`
  - `sync_delayed`
- Grafana provisioned `UDS Incident Monitoring`
- MCP returned real UDS incident data for `IMO9300001`
- the validation dashboard returned HTTP 200
- quick analysis validation completed successfully on the fresh stack

## What that means

The real remaining work is not rebuilding Scope 1 architecture anymore.
It is:

- keeping docs aligned with the actual merge candidate
- rerunning acceptance after further merges
- doing one last browser-based signoff before the final demo or PR

## What still needs explicit attention

### High priority

1. Re-run the acceptance checklist on the latest merge candidate.
2. Keep the docs synchronized with the branch that the group actually plans to
   merge.
3. Do one manual Grafana signoff pass on `UDS Incident Monitoring` after the
   last code merge.

### Medium priority

1. If the group wants to demo legacy full analysis, run it early and verify it
   separately.
   Reason:
   - on the fresh-stack validation, quick validation completed
   - one cold-start full analysis job was still `running` after the first minute
2. Decide whether the dashboard needs any final visual polish for the demo.

### Low priority

Do not spend time here unless the group finishes early:

- auth hardening
- removing the acknowledge GET route
- migration strategy for older DB volumes
- multi-vessel Scope 2 work
- NOC Scope 3 work
- deeper RAG tuning beyond what already works

## Recommended demo flow

1. Open Grafana at `http://localhost:3000`
2. Open `UDS Incident Monitoring`
3. Select `IMO9300001`
4. Use `Active Incident Queue` or `Application Incident Board`
5. Click `Application` or `App ID` to pivot into the selected app drilldown
6. Show:
   - recent alerts
   - recent logs
   - connectivity/freshness
   - recent metric history
   - metric window summary
7. Optionally open `http://localhost:8000/api/v1/validate/dashboard`
8. Only demo legacy full analysis if it has already warmed up cleanly

## Files to keep in sync from now on

- `README.md`
- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`
- `docs/SCOPE1_HANDOFF_NOTES.md`
- `docs/SCOPE1_REVIEW_FINDINGS.md`
- `docs/FUTURE_CHECKS.md`
- `docs/UDS_dashboard_spec.md`
