# Roadmap - Backlog and Priorities

Last updated: 2026-04-01

This file tracks the current backlog. For historical context, see the archived
Scope 1 docs in `docs/archive/`.

## Recently Completed

These items are done and should not be reopened:

### Scope 1 baseline (completed 2026-03-12)
- UDS schema and reference data load on fresh DB
- Seeded scenarios include healthy, degraded, stale, delayed, and down states
- UDS Incident Monitoring dashboard with incident-first drilldown
- 4 MCP tools for single-vessel incident handling
- Fresh-stack acceptance validated

### Scope 2 Task 1 - Fleet Overview Dashboard (completed 2026-03-27)
- Fleet health overview with vessel-level status cards
- Cross-vessel alert table and correlation view
- Drilldown from fleet overview to single-vessel incident dashboard
- Fleet connectivity view

### Scope 2 Task 3 - MCP Fleet/Incident Tools (completed 2026-03-28)
- 5 new MCP tools: get_fleet_status, get_fleet_alerts,
  get_cross_vessel_correlation, get_incident_timeline,
  get_operational_snapshot
- Agent tool allowlist updated for all 9 UDS tools
- Cross-vessel seed scenario (data-quality-processor on IMO9300001 + IMO9300002)
- 6-hour backfill on fresh database start
- Alert resolution logic to prevent accumulation across seed cycles
- Fleet overview dashboard drilldown fix and app-level links

### Scope 2 Task 2 - NOC Support Dashboard (completed 2026-04-01)
- 16-panel investigation dashboard: `grafana/dashboards/noc_support.json`
- Vessel selector, time window (1h–7d), optional app filter
- Incident timeline, error/warning summary, alert history, connectivity history
- Historical metrics (HTTP, CPU, memory, DB latency)
- Drilldown to UDS Incident Monitoring with vessel, app, and time window

## Current Priority: Integration and Polish

### Integration pass after all tasks merge
- Run fresh-stack validation with all dashboards
- Verify naming/status/severity consistency across dashboards and MCP
- Verify drilldown links between all dashboards
- Verify seed data demonstrates cross-vessel and NOC use cases

## P0 - Before demo (15 April deadline)

### 1. Fresh-stack acceptance on final merge candidate
- Re-run `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md` on the merged main branch
- Verify all 4 UDS/fleet dashboards load and show meaningful data
- Verify all 12 MCP tools return correct results

### 2. Keep docs aligned with merged code
- Update CLAUDE.md, README.md, and this file after each merge

## P1 - Reliability and Hardening

### 3. Proper migration path for old DB volumes
- Status: OPEN
- The prototype still works best from a fresh DB volume
- Runtime guards help but do not replace migrations

### 4. Cold-start timing
- Status: IMPROVED (backfill added, model pull reliable)
- First start still depends on model pull + RAG ingest + service readiness
- Give the stack a few minutes on first startup before demoing

### 5. Legacy full analysis warmup
- Status: OPEN
- Quick validation works; full analysis may need extra warmup on cold start
- Only demo this path if it has been warmed up and verified

## P1.5 - Security and API Cleanup

### 6. State-changing GET endpoint for event acknowledge
- Status: OPEN
- File: `services/agent/routes/events.py`
- `GET /events/{id}/acknowledge` mutates state; should be POST-only

### 7. MCP auth is optional if `MCP_API_KEY` is empty
- Status: OPEN
- File: `services/mcp/main.py`
- Empty key disables effective protection

### 8. Demo credentials and broad local access
- Status: OPEN
- Default credentials are demo-oriented; services exposed locally

## P2 - Demo Quality

### 9. Deeper or configurable historical backfill
- Status: PARTIALLY ADDRESSED
- 6-hour backfill now runs on fresh DB, but window is not configurable
- Could vary scenario mix across backfill horizon

### 10. Dashboard ergonomics
- Status: IN PROGRESS
- Fleet overview drilldown now works (fixed in Scope 2)
- Room for layout and panel ordering improvements

### 11. Stronger live tool use in legacy full analysis
- Status: OPEN
- Main proof point is now UDS incident flow
- Better tool usage would improve the validation/demo story

## P3 - Future Work (post-bachelor or post-demo)

- Stronger auth and authorization
- Audit logging
- Rate limiting
- Automated tests
- Broader RAG retrieval validation
- Real production data integration
- MCP protocol upgrade (current REST adapter, could move to official MCP SDK)
- Agentic expansion of UDS path (connect AI agent to UDS incident context)
