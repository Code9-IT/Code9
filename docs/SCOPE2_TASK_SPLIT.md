# Scope 2 - Task Split and Status

Last updated: 2026-03-28

Scope 2 implements User Story 2 (multi-vessel incident) and User Story 3 (NOC
support case). This document defines the task ownership, acceptance criteria, and
current status.

For the full project description and user stories, see
`docs/Project Description – Bachelor Project in Collaboration with Knowit (version 2).md`.

## User Stories

### User Story 2 - Multi-Vessel Incident

As a DevOps engineer, when I receive warnings or errors affecting multiple
applications across multiple vessels, I need a dashboard that:
- Provides a consolidated overview of all affected vessels
- Highlights correlated issues
- Makes it easy to identify systemic problems

### User Story 3 - NOC Support Case

As a NOC support engineer, when I receive a support ticket from a customer,
I want access to a dashboard that:
- Displays the full operational state of the vessel
- Shows recent errors, warnings, and connectivity status
- Provides historical context to support troubleshooting

## Shared Definitions

Use these consistently across all dashboards and MCP tools:
- `healthy` = no active condition that currently affects actionability
- `degraded` = active alerts, freshness issues, or resource issues exist
- `critical` = effectively unavailable, or a severe active issue exists

Same severity labels, status labels, color meaning, time-window naming,
vessel naming, and drilldown behavior everywhere.

## Task Status

| Task | Owner | Status | Main Files |
|------|-------|--------|------------|
| Task 1 - Fleet Overview Dashboard | Nidal | DONE | `grafana/dashboards/fleet_overview.json` |
| Task 2 - NOC Support Dashboard | Jonas | NOT STARTED | `grafana/dashboards/noc_support.json` (to create) |
| Task 3 - MCP Fleet/Incident Tools | Kristian | DONE | `services/mcp/main.py`, `db/seed/uds_seed.sql`, `services/agent/routes/analyze.py` |

## Task 1 - Fleet Overview Dashboard (Nidal) -- DONE

Delivers `grafana/dashboards/fleet_overview.json` with:
- Fleet health overview (one row per vessel)
- Cross-vessel active alert table
- Correlation view (same app/alert on multiple vessels)
- Fleet connectivity view
- Drilldown to single-vessel UDS Incident Monitoring dashboard

Acceptance:
- [x] User can immediately see which vessels are affected
- [x] User can identify fleet-level patterns without drilling down
- [x] Drilldown into single-vessel dashboard works

## Task 2 - NOC Support Dashboard (Jonas) -- NOT STARTED

Will deliver `grafana/dashboards/noc_support.json` with:
- Vessel selector, time window selector, optional app filter
- Vessel operational state summary
- Incident timeline (combined alerts + logs, chronological)
- Error/warning summary grouped by app
- Connectivity history
- Historical metrics (CPU, memory, latency, error rates)
- Alert history (firing + resolved)

Acceptance:
- [ ] NOC user can answer what happened, when, and on which app
- [ ] Dashboard shows both current state and historical context
- [ ] Connectivity visible enough to explain gaps
- [ ] Resolved incidents visible in selected time window

## Task 3 - MCP Fleet & Incident Tools (Kristian) -- DONE

Added 5 new MCP tools to `services/mcp/main.py`:
- `get_fleet_status` -- all vessels with status, alerts, app counts
- `get_fleet_alerts` -- fleet-wide alerts with severity filter
- `get_cross_vessel_correlation` -- apps/alerts on multiple vessels
- `get_incident_timeline` -- chronological alerts + logs for one vessel
- `get_operational_snapshot` -- full vessel state for NOC support

Also:
- Updated agent tool allowlist in `services/agent/routes/analyze.py`
- Added cross-vessel seed scenario (data-quality-processor stale on IMO9300001,
  degraded on IMO9300002)
- Added alert resolution logic to prevent accumulation across seed cycles
- Added 6-hour backfill on fresh database in `scripts/uds_seed_loop.sh`

Acceptance:
- [x] Existing Scope 1 MCP tools still work unchanged
- [x] New MCP tools return stable shapes
- [x] Seed data supports convincing multi-vessel demo

## Integration Checklist (after all tasks merge)

- [ ] Fresh-stack validation passes (docker compose down -v && up -d --build)
- [ ] Scope 1 dashboard still works
- [ ] Fleet overview dashboard works
- [ ] NOC support dashboard works (when Task 2 is done)
- [ ] All MCP tools respond correctly
- [ ] Severity colors and status labels are consistent
- [ ] Drilldown links work between dashboards
- [ ] Fleet correlation claims are backed by seed data

## Important Deadlines

- Before Easter: all 3 tasks completed and merged
- 15 April: GeoAI-week presentation at Kartverket
- Late April: presentation for Knowit stakeholders
- System must be demo-ready and polished before 15 April
