# Scope 1 Review Findings

Last updated: 2026-03-11

This document is the concentrated review context for the current integrated
Scope 1 branch. It is intended for:

- the student team
- later AI assistants
- future merge and demo preparation

Use this file together with:

- `docs/SCOPE1_HANDOFF_NOTES.md`
- `docs/NEXT_STEPS.md`
- `docs/FUTURE_CHECKS.md`
- `docs/UDS_dashboard_spec.md`

## Scope 1 target

The agreed Scope 1 target is User Story 1 from Geir:

> As a DevOps engineer, when I receive a warning or error from an application
> on a vessel, I need a dashboard that shows:
>
> - the complete operational state of all applications on that vessel
> - relevant historical metrics and logs
> - context necessary to evaluate the situation and take action

That means the review standard is not just "the code runs".
The review standard is whether the integrated prototype gives enough incident
context for a single-vessel application incident.

## Current integrated direction

The project now has two parallel paths:

### Legacy prototype path

- `telemetry`
- `events`
- `ai_analyses`
- `services/generator/`
- `grafana/dashboards/ship_operations.json`
- AI analysis through the agent

This path still matters, but it is not the main Scope 1 deliverable.

### Scope 1 UDS path

- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`
- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`
- `services/mcp/main.py` UDS tools
- `grafana/dashboards/uds_monitoring.json`

This is the path that should satisfy User Story 1.

## What is already integrated

### Del A

Integrated schema:

- `owners`
- `udslocations`
- `applications`
- `uds_location_application_instances`
- `metric_samples`
- `alerts`
- `uds_location_owner_history`
- `monitoring_configs` compatibility shim

### Del A support

Tracked reference data now exists in the repo:

- 3 vessels
- 6 applications
- vessel/application link rows
- owners and owner history

### Del B

Integrated seeding path:

- periodic `uds-seeder` service in `docker-compose.yml`
- tracked SQL seeding file
- retry loop that waits for schema and reference data

### Del C

Integrated UDS MCP tools:

- `get_vessel_app_status`
- `get_vessel_alerts`
- `get_app_metric_history`

### Del D

Integrated UDS dashboard:

- one vessel selector by `imo_nr`
- latest application status
- resource / availability / HTTP / DB metric tables
- active alerts table

## Small fixes already applied during integration review

These were fixed because they were low-risk and directly helpful:

1. Del B seeding now respects vessel/application links instead of assuming every
   vessel always has every application.
2. Del B wait-loop now checks:
   - UDS schema tables
   - vessels
   - applications
   - vessel/application link rows
3. demo vessel names `Edge Aurora` / `Edge Borealis` were corrected
4. obsolete `version:` was removed from `docker-compose.yml`
5. docs were updated to reflect the integrated Scope 1 branch instead of older
   partial branches

## Main review conclusion

The project is not structurally broken.

The important conclusion is this:

- the codebase is now coherent enough to continue from
- but Scope 1 does not fully satisfy User Story 1 yet

The remaining gaps are mostly about incident context and demo realism, not
about having to throw away the current implementation.

## Findings

### High

#### 1. User Story 1 is not fully met because the UDS path is weak on historical context

What exists:

- latest-state app health
- active alerts
- MCP support for metric history

What is missing in practice:

- the dashboard does not strongly surface historical metric drilldown
- the incident flow from alert to app history is still thin

Why this matters:

- User Story 1 explicitly asks for relevant historical metrics
- current UDS dashboard is mostly a present-state health board

Relevant files:

- `grafana/dashboards/uds_monitoring.json`
- `grafana/queries/uds_queries.sql`
- `services/mcp/main.py`

#### 2. User Story 1 asks for logs, but the UDS prototype does not currently model logs

What exists:

- `metric_samples`
- `alerts`

What does not exist:

- a log table
- seeded log entries
- log queries in MCP
- log panels in Grafana

Why this matters:

- the written story says "historical metrics and logs"
- right now the UDS solution is metrics + alerts only

This is not necessarily a reason to rebuild the architecture.
It does require an explicit product decision:

- either add a lightweight log-like scope to the prototype
- or document clearly that Scope 1 covers metrics + alerts and logs are deferred

Relevant files:

- `db/init/003_uds.sql`
- `services/mcp/main.py`
- `grafana/dashboards/uds_monitoring.json`

### Medium

#### 3. Seeded incident scenarios are too narrow

Current seeded UDS incidents are mainly `ServiceDown` style incidents.

Why this matters:

- it under-tests the dashboard
- it under-tests MCP context
- it does not reflect warning/degraded scenarios well

Suggested expansion:

- warning severity
- degraded but still alive services
- stale reporting
- sync delay / freshness incidents

Relevant files:

- `db/seed/uds_seed.sql`
- `scripts/uds_seed_loop.sh`

#### 4. Fresh DB is effectively required for trustworthy Scope 1 testing

The integrated branch depends on init scripts for:

- legacy schema
- UDS schema
- tracked UDS reference data

Why this matters:

- old local volumes can silently look "sort of working"
- that creates false confidence during demos and reviews

Practical rule:

- serious Scope 1 validation should start from a reset DB volume

Relevant files:

- `db/init/001_init.sql`
- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`
- `scripts/reset_db.sh`

### Medium / Security

#### 5. Event acknowledge still has a state-changing GET alias

This is useful for Grafana links, but weak API design.

Why this matters:

- GET should not mutate state
- it is easy to trigger accidentally

Relevant file:

- `services/agent/routes/events.py`

#### 6. MCP auth still depends on `MCP_API_KEY` being non-empty

If `MCP_API_KEY` is empty, auth is effectively off.

Why this matters:

- fine for local prototype
- not okay to treat as a finished security solution

Relevant files:

- `services/mcp/main.py`
- `.env.example`
- `docker-compose.yml`

### Low

#### 7. The current demo topology is intentionally fixed to 3 vessels and 6 apps

This is acceptable for Scope 1.
It is not enough to claim the scalability part of the broader Geir description.

This should be framed honestly in the thesis/demo:

- we solved the one-vessel incident slice first
- multi-vessel and broader scale are later work

Relevant files:

- `db/init/004_uds_reference_data.sql`
- `db/seed/uds_seed.sql`

## What is good enough right now

These parts are good enough to continue integration work from:

- the UDS schema shape
- the reference data direction
- the seeding loop architecture
- the MCP UDS tools direction
- the UDS dashboard overall direction

The current codebase is a reasonable shared baseline for the group.

## What should be fixed next

Recommended order:

1. Run a full fresh-DB end-to-end test.
2. Fix any runtime mismatches found there.
3. Improve historical metric visibility in the UDS dashboard.
4. Decide how to handle the "logs" part of User Story 1.
5. Broaden seeded scenarios.

## Files most important for the next AI to read

1. `README.md`
2. `docs/SCOPE1_HANDOFF_NOTES.md`
3. `docs/SCOPE1_REVIEW_FINDINGS.md`
4. `docs/NEXT_STEPS.md`
5. `docs/FUTURE_CHECKS.md`
6. `docs/UDS_dashboard_spec.md`
7. `docker-compose.yml`
8. `db/init/001_init.sql`
9. `db/init/003_uds.sql`
10. `db/init/004_uds_reference_data.sql`
11. `db/seed/uds_seed.sql`
12. `scripts/uds_seed_loop.sh`
13. `services/mcp/main.py`
14. `grafana/dashboards/uds_monitoring.json`

## Final note

Do not evaluate this project as if it were already a production monitoring
platform.

Evaluate it as a bachelor prototype whose current job is:

- demonstrate a coherent Scope 1 architecture
- make User Story 1 credibly testable
- leave a clean base for the team to continue from
