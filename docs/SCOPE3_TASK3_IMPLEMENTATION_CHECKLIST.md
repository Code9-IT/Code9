# Scope 3 Task 3 Implementation Checklist

Last updated: 2026-04-02

This checklist turns Task 3 into a concrete, merge-safe implementation plan for
dashboard work spread across multiple teammates and machines.

Scope:
- Root navigation, naming clarity, and the lightweight legacy/UDS bridge
- No backend, schema, generator, or Task 1/Task 2/Task 4 ownership changes

## 1. Navigation Contract

- [ ] Keep the main demo dashboards in one shared root-navigation set:
  - Ship Operations (Legacy)
  - Fleet Overview
  - UDS Incident Workbench
  - NOC Support
- [ ] Do not add the chat link until Task 2 actually provides a working stable
      URL
- [ ] Keep `uds_app_health.json` out of the main demo navigation

## 2. Hidden Bridge Variables

Use the same hidden variable names in the 4 main dashboards:

- [ ] `bridge_legacy_vessel = vessel_001`
- [ ] `bridge_uds_vessel = IMO9300001`
- [ ] `bridge_default_incident_window = 6 hours`
- [ ] `bridge_default_noc_window = 24 hours`
- [ ] `bridge_default_noc_app_filter = __all`

Rules:
- [ ] Use these variables for root-link defaults instead of repeating raw
      literals across files
- [ ] Keep the variables hidden with `hide = 2` and `skipUrlSync = true`
- [ ] Do not use a database mapping table for this demo bridge unless Task 3 is
      explicitly re-scoped

## 3. Ship Operations

- [ ] Show the legacy/UDS relationship clearly in dashboard copy
- [ ] Keep a clean root link from Ship Operations to the mapped UDS workbench
- [ ] Keep a clean root link from Ship Operations to the mapped NOC view
- [ ] Keep the alarm-table drilldown that opens the mapped UDS workbench

## 4. Context Handoff Rules

- [ ] Ship Operations -> UDS uses the hidden bridge defaults
- [ ] Ship Operations -> NOC uses the hidden bridge defaults
- [ ] Fleet Overview root links use the hidden bridge defaults
- [ ] UDS Incident Workbench -> NOC preserves `vessel`, `incident_window`, and
      `app`
- [ ] NOC Support -> UDS Incident Workbench preserves `vessel` and uses a
      normalized 24-hour incident window for the root link

## 5. `uds_app_health.json`

- [ ] Rename it clearly as developer-oriented health
- [ ] Keep it outside the main demo path
- [ ] Tag or document it as developer-only so teammates do not accidentally add
      it back into presenter navigation

## 6. Merge Safety

- [ ] Task 3 edits only:
  - dashboard root `links`
  - dashboard titles and descriptions
  - hidden bridge/navigation variables
  - Task 3 docs
- [ ] Do not change panel-level AI links owned by Task 1
- [ ] Do not add chat navigation owned by Task 2 before the route exists
- [ ] Do not change legacy generator vessel IDs unless the team explicitly
      accepts the higher-risk path

## 7. Validation

- [ ] Dashboard JSON parses locally
- [ ] Grafana provisions all edited dashboards
- [ ] Confirm the main dashboards expose the expected root link counts
- [ ] Manually click this path in Grafana:
  - Ship Operations -> UDS Incident Workbench -> NOC Support -> Fleet Overview
    -> Ship Operations
- [ ] Treat full fresh-stack signoff as an integration gate; if a failure comes
      from legacy AI/RAG startup or another task's scope, record it separately
      instead of broadening Task 3
