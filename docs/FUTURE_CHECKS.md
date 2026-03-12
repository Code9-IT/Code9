# Future Checks - Security, Gaps, and Follow-up Work

Last updated: 2026-03-12

This file is the backlog for work that still matters after Scope 1 became
functionally coherent. Keep immediate merge and acceptance work in
`docs/NEXT_STEPS.md`.

## Recently closed on the current integration branch

These items were earlier blockers and should not be reopened as if they were
still missing:

- historical metrics are now visible in Grafana for the selected app
- lightweight logs/log-like context now exist through `app_logs`
- seeded scenarios now include degraded, stale, delayed, and down cases
- fresh-stack UDS acceptance was rerun successfully on 2026-03-12

## P0 - Re-run before the final merge

### 1. Repeat fresh-stack acceptance on the last merge candidate

- Status: OPEN
- Why it matters:
  - the current branch passed on 2026-03-12
  - any later merge can still regress schema, seeding, MCP, or Grafana wiring
- Reference:
  - `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md`

### 2. Keep docs aligned with the branch that is actually being merged

- Status: OPEN
- Why it matters:
  - stale docs already cost time during Scope 1 integration
  - this repo changed quickly across several intermediate branches

## P1 - Important reliability and hardening work

### 3. Proper migration path for old DB volumes

- Status: OPEN
- Why it matters:
  - the current prototype works best from a fresh DB volume
  - runtime guards help, but they do not replace migrations
- Future direction:
  - add formal migrations
  - or document a strict reset-only policy for prototype branches

### 4. Reduce cold-start timing sensitivity

- Status: IN_PROGRESS
- Why it matters:
  - first start still depends on model pull, RAG ingest, and service readiness
- Current direction:
  - `ollama-init` pulls models
  - the agent retries RAG ingest
  - `uds-seeder` waits for schema and reference data
- Future direction:
  - keep startup reliable without manual intervention
  - reduce noisy warmup retries if time allows

### 5. Legacy full analysis warmup/performance signoff

- Status: OPEN
- Why it matters:
  - quick validation works on the fresh stack
  - one cold-start full analysis job stayed `running` longer than the first
    minute during the Student 4 validation rerun
- Future direction:
  - warm the path up before demoing it
  - inspect model/runtime behavior if the group wants that path to be a major
    proof point

## P1.5 - Security and API cleanup

### 6. State-changing GET endpoint for event acknowledge

- Status: OPEN
- File:
  - `services/agent/routes/events.py`
- Why it matters:
  - `GET /events/{id}/acknowledge` mutates state
- Future direction:
  - keep POST as canonical
  - remove or restrict the GET alias later

### 7. MCP auth is optional if `MCP_API_KEY` is empty

- Status: OPEN
- File:
  - `services/mcp/main.py`
- Why it matters:
  - empty `MCP_API_KEY` disables effective protection
- Future direction:
  - require non-empty key in non-dev mode
  - or fail startup when auth is expected but not configured

### 8. Demo credentials and broad local access

- Status: OPEN
- Files:
  - `.env.example`
  - `docker-compose.yml`
- Why it matters:
  - default credentials are still demo-oriented
  - services are exposed locally for convenience
- Future direction:
  - define a safer demo profile if this needs broader sharing

## P2 - Product and demo quality improvements

### 9. Richer historical backfill immediately after a fresh start

- Status: OPEN
- Why it matters:
  - the graphs work now
  - they will still look stronger if the demo starts with more history already
    present
- Future direction:
  - optionally backfill a few recent windows on fresh startup

### 10. Stronger alert-to-context ergonomics in Grafana

- Status: IN_PROGRESS
- Why it matters:
  - the dashboard already supports alert -> app -> recent history
  - there is still room for cleaner drilldown ergonomics and panel ordering
- Future direction:
  - tune layout and panel order only if the team has spare time

### 11. Stronger live tool use in legacy full analysis

- Status: OPEN
- Why it matters:
  - the main Scope 1 proof point is now the UDS incident flow, not legacy full
    analysis
  - still, better live tool usage would improve the validation/demo story
- Future direction:
  - refine prompting and tool selection only if the team has spare capacity

## P3 - Later work after User Story 1

- User Story 2: multi-vessel incident view
- User Story 3: NOC support view
- stronger auth and authorization
- audit logging
- rate limiting
- deeper automated tests
- broader retrieval validation for RAG
