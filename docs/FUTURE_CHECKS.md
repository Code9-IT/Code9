# Future Checks - Security, Gaps, and Follow-up Work

This file is the backlog for issues that should not block day-to-day prototype
work, but still matter for integration quality, demo quality, and any later
hardening.

Last updated: 2026-03-11

## How to use this file

- Use this as the single backlog for "important, but not the next commit".
- When something is fixed, mark it done and note the branch or commit.
- Keep immediate Scope 1 work in `docs/NEXT_STEPS.md`.

## P0 - Must validate before saying Scope 1 works

### 1. Fresh DB end-to-end test

- Status: OPEN
- Why it matters:
  - Scope 1 now depends on:
    - `001_init.sql`
    - `003_uds.sql`
    - `004_uds_reference_data.sql`
  - Existing local DB volumes may not match current code.
- Required validation:
  - reset DB volume
  - bring stack up
  - confirm `uds-seeder` inserts into `metric_samples` and `alerts`
  - confirm Grafana vessel selector is populated

### 2. Close the User Story 1 gap around historical context

- Status: OPEN
- Why it matters:
  - User Story 1 explicitly asks for relevant historical metrics and logs.
  - The current UDS dashboard mostly shows latest-state tables.
- Required follow-up:
  - add historical metric views or drilldowns in Grafana
  - decide how logs or log-like context will be represented for Scope 1

### 3. Broaden incident scenarios in mock data

- Status: IN_PROGRESS
- Why it matters:
  - Current UDS seeding is dominated by `ServiceDown` incidents.
  - This is too narrow for meaningful incident-review testing.
- Current direction:
  - Scope 1 seeding now targets `healthy`, `degraded`, `down`, `stale`, and
    `delayed` states.
  - Connectivity-style metrics such as `last_sync_age_seconds`,
    `reporting_stale`, and `sync_delayed` are part of the seeded UDS contract.
- Suggested follow-up:
  - verify the seeded mix is visible enough in Grafana after Student 1 updates
  - tune scenario probabilities if the demo becomes too noisy or too empty

## P1 - Important security and API hardening

### 4. State-changing GET endpoint for event acknowledge

- Status: OPEN
- File:
  - `services/agent/routes/events.py`
- Why it matters:
  - `GET /events/{id}/acknowledge` mutates state
  - this is demo-friendly but weak API design
- Future direction:
  - keep POST as canonical
  - remove GET alias or protect it behind auth/proxy rules

### 5. MCP auth is optional if `MCP_API_KEY` is empty

- Status: OPEN
- File:
  - `services/mcp/main.py`
- Why it matters:
  - empty `MCP_API_KEY` disables effective protection
- Future direction:
  - require non-empty key in non-dev mode
  - or fail startup when auth is expected but not configured

### 6. Demo credentials and broad local access

- Status: OPEN
- Files:
  - `.env.example`
  - `docker-compose.yml`
- Why it matters:
  - default Grafana credentials are still weak
  - services are exposed locally for convenience
- Future direction:
  - change demo defaults
  - define a safer "demo/prod-like" env profile

## P1.5 - Reliability and integration hygiene

### 7. `analysis_mode` migration path for existing DBs

- Status: OPEN
- Why it matters:
  - code expects `analysis_mode`
  - old local volumes may still miss it
- Future direction:
  - add a real migration strategy
  - or document reset-only policy explicitly for prototype branches

### 8. Remove stale integration assumptions from docs when code changes

- Status: OPEN
- Why it matters:
  - several docs previously described older merge states
  - this cost time during integration
- Future direction:
  - update docs in the same PR as integration changes

## P2 - Product and demo quality improvements

### 9. Route MCP metric history into the UDS dashboard

- Status: OPEN
- Why it matters:
  - the DB and MCP support metric history
  - the dashboard still emphasizes latest-state tables
- Future direction:
  - add time-series drilldowns for selected app metrics

### 10. Add more operational context around alerts

- Status: OPEN
- Why it matters:
  - current alert context is enough to show a table
  - it is not yet enough to guide a real incident response discussion
- Future direction:
  - link alerts to relevant recent metric windows
  - show app-specific context around the time of failure

### 11. Model connectivity constraints more directly

- Status: IN_PROGRESS
- Why it matters:
  - Geir's scope explicitly mentions maritime connectivity constraints
  - the prototype still needs stronger connectivity realism beyond basic delayed/stale states
- Current direction:
  - Scope 1 seeding now introduces delayed/stale reporting states and explicit
    connectivity/freshness metrics.
- Future direction:
  - expose freshness and sync behavior clearly in dashboard panels
  - consider stronger missing-window patterns if Student 1 needs more visible demo cases

## P3 - Later work after User Story 1

- User Story 2: multi-vessel incident view
- User Story 3: NOC support view
- stronger auth and authorization
- audit logging
- rate limiting
- deeper automated tests
- broader retrieval validation for RAG
