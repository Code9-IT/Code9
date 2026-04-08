# Roadmap - Backlog and Priorities

Last updated: 2026-04-08

This file tracks the backlog from the **current dynamic-dashboard pivot**
outward. For historical scope planning, see `docs/archive/`.

## Current Priority: Dynamic Dashboard Pivot

The repo already contains a strong Scope 1-3 prototype foundation. The current
top priority is to add one convincing generated-dashboard workflow for
**User Story 1**:

`alert/warning -> orchestrator -> MCP context -> scenario classification -> generated Grafana dashboard`

### Must-have this week

1. **Manual trigger path works**
   - `POST /api/v1/dynamic/trigger`
   - generated dashboard appears in Grafana
   - stable UID `maritime_dynamic_incident`

2. **Scenario-based dashboard selection**
   - deterministic scenario classification
   - dashboard content changes based on the incident type
   - existing dashboards remain the fallback and drilldown context

3. **Reliable demo path**
   - one reproducible incident scenario
   - one fallback path if the dynamic trigger fails
   - screenshots or a short backup video prepared before the presentation

4. **Docs aligned with the pivot**
   - README, CLAUDE, architecture, demo script, and task plan all tell the same story

## Secondary Priorities (after the core dynamic path works)

### Demo reliability and polish
- Re-run `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md` on the final merge candidate
- Verify naming, severity, and drilldown consistency across dashboards and MCP
- Confirm the seeded data still demonstrates the main single-vessel scenario
- Improve generated-dashboard explanation text and presentation flow

### Runtime and hardening
- Proper migration path for old DB volumes
- Cold-start timing and warmup reliability
- Legacy full-analysis warmup before demos
- Review demo credentials and optional MCP auth

### Presentation quality
- Keep the architecture slide consistent with Arnt's sketch
- Keep the MCP story concrete and grounded in the existing tool layer
- Avoid overselling the dynamic path as more complete than it is

## Implemented Foundation (do not reopen unless needed)

Already in the repo:
- Scope 1 single-vessel UDS incident handling
- Scope 2 fleet overview and NOC support
- Scope 3 foundation: UDS AI analysis, AI chat, dashboard coherence, predictive alert trends

These are the base system for the current pivot, not the thing to rebuild.

## Future Work

After the presentation / bachelor delivery:
- broader auth and authorization
- audit logging
- rate limiting
- automated tests
- configurable historical backfill
- production data integration
- official MCP protocol implementation instead of the current REST adapter
- broader agentic expansion beyond the single dynamic-dashboard flow
