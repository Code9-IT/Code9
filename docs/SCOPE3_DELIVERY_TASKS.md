# Scope 3 - Final Delivery Tasks

Last updated: 2026-04-02

This document defines the final sprint before presentation. It is written for
parallel work by 4 students with AI assistance, while keeping merge conflicts
and last-week architecture risk as low as possible.

Baseline:
- Scope 1 and Scope 2 are implemented and validated on a fresh stack
- Geir's 3 user stories have dashboard and MCP coverage
- The remaining gaps are product coherence, UDS-side AI integration, predictive
  support, and demo polish

This sprint is not about redesigning the system. It is about making the current
prototype feel intentional, connected, and presentation-ready.

For background, read these first:
- `CLAUDE.md`
- `docs/architecture.md`
- `docs/ROADMAP.md`
- `docs/SCOPE2_TASK_SPLIT.md`

## Why These Tasks Exist

Right now the system works, but it still feels like multiple strong prototype
pieces rather than one finished product:

- The legacy Ship Operations dashboard has AI analysis
- The UDS dashboards do not
- The validation page is too visible in the user-facing AI flow
- The legacy and UDS paths still feel disconnected
- Geir asked for predictive support, but today the system is mostly reactive
- Arnt asked for a chat-style AI experience, but that does not exist yet

These 4 tasks close those gaps without asking the team to rewrite the
architecture in the last week.

## Shared Rules

- Same status definitions everywhere: `healthy`, `degraded`, `critical`
- Same severity labels everywhere: `critical`, `warning`, `info`
- Prefer additive changes over rewrites
- Use asyncpg parameterized SQL (`$1`, `$2`, etc.), never f-strings for SQL
- Do not break Scope 1 or Scope 2 behavior while improving the delivery
- Run fresh-stack validation before marking a task done:
  - `docker compose down -v`
  - `docker compose up -d --build`
  - wait for `Backfill complete`
- Update `CLAUDE.md` and `README.md` if new endpoints, tools, or dashboards are
  added

Important:
- Stretch goals are optional. Core acceptance criteria come first.
- If a task has both "core" and "stretch" work, the core work must be finished
  before any stretch work starts.

## Shared Engineering Guardrails

These rules apply to all 4 tasks. They are here to keep the sprint safe,
mergeable, and presentation-ready even when the implementation work is being
done through AI assistants.

### Security and API safety

- Do not disable or weaken existing authentication. In particular:
  - do not remove MCP API key checks
  - do not hardcode secrets or new credentials into source files
- Do not add new state-changing `GET` endpoints
- If adding a new route, validate input with Pydantic models and return clear
  4xx errors for invalid requests
- Do not expose internal or developer-only pages from user-facing flows unless
  the task explicitly says so

### Database and schema safety

- Do not use string interpolation for SQL
- Prefer schema-light changes over large schema redesigns
- If a schema change is needed, keep it backward-compatible with the current
  prototype and fresh-stack startup flow
- Do not break existing Scope 1 or Scope 2 tables, dashboards, or MCP tools

### Product and UX safety

- Do not remove working demo paths unless the replacement is already working
- Prefer one clear path over two half-finished paths
- If changing confidence or AI wording, label it honestly as model-generated
  output, not as a guaranteed diagnosis
- Keep developer-only validation or tuning tools separate from normal demo
  navigation unless the task explicitly requires otherwise

### Code quality and merge safety

- Reuse existing helpers and patterns before adding new ones
- Keep changes scoped to the files owned by the task whenever possible
- If two tasks must touch the same file, make the change additive and easy to
  merge
- Leave concise comments only where the code would otherwise be hard to follow
- Update docs when a route, tool, dashboard role, or navigation path changes

### Validation expectation

Before marking a task done, verify:
- the new feature works
- the old working flow still works
- the task did not introduce a broken dashboard, broken route, or broken MCP tool

## Task Overview

| Task | Summary | Priority |
|------|---------|----------|
| Task 1 | UDS AI Integration | CRITICAL |
| Task 2 | AI Chat Interface | HIGH |
| Task 3 | Legacy/UDS Bridge + Dashboard Coherence | HIGH |
| Task 4 | Predictive Feature + AI UX Cleanup + Handover Docs | MEDIUM |

---

## Task 1 - UDS AI Integration

Goal:
Connect the AI agent to the UDS dashboards so the "agentic observability"
story also works for Geir's UDS user stories, not only for the legacy sensor
path.

### What currently exists

- The AI analysis pipeline is implemented in `services/agent/routes/analyze.py`
- The existing user-facing analysis flow is event-based and starts from the
  legacy `events` table
- The existing HTML analysis page is served from:
  - `GET /api/v1/analyze/{event_id}/view`
- The legacy Ship Operations dashboard already links into this flow from:
  - `grafana/dashboards/ship_operations.json`
- The tool loop already knows about all UDS tools via `UDS_FULL_TOOL_NAMES`
- The UDS dashboards currently have no AI entry point

### What this task should do

1. Add a UDS-aware analysis entry point
- Accept UDS context instead of only legacy `event_id`
- Context may be based on vessel, app, alert, or a combination of those
- Reuse the existing analysis pipeline structure where possible
- Persist the result so it can be revisited later

2. Add AI drilldowns to the UDS dashboards
- Add panel-level data links in:
  - `grafana/dashboards/uds_monitoring.json`
  - `grafana/dashboards/noc_support.json`
- The user should be able to click a UDS alert or incident row and open an AI
  analysis relevant to that UDS context

3. Keep the result explainable
- The analysis page should show:
  - analysis text
  - suggested actions
  - retrieved docs
  - tool-call trace or equivalent transparency

4. Stretch goal
- Auto-trigger an analysis for critical UDS alerts so the analysis is ready
  before the user clicks

### Important files

- `services/agent/routes/analyze.py`
- `services/agent/models.py`
- `grafana/dashboards/uds_monitoring.json`
- `grafana/dashboards/noc_support.json`
- `db/init/001_init.sql` or another minimal storage change only if needed

### Tips for the AI assistant

- Do not build a second unrelated AI system. Extend the current analysis flow.
- Reuse the tool-calling loop instead of creating a special-case shortcut.
- The function `_tool_names_for_event()` (analyze.py, ~line 710) already
  selects UDS tools when `vessel_id` starts with "IMO". Build on this pattern.
- The tool loop is in `_run_tool_loop` (analyze.py, ~line 450). The UDS
  analysis just needs a different initial prompt, not a different loop.
- For Grafana data links: see how `ship_operations.json` line 814 does it.
  The pattern is a `dataLinks` array inside field overrides using
  `${__value.raw}` and other Grafana template variables.
- Keep storage changes minimal. A small extension is better than an entire new
  subsystem unless a separate table is clearly simpler.
- `services/agent/main.py` will also need a new `include_router` line if a
  new router file is created (see lines 129-131 for the existing pattern).
- The goal is not perfect AI UX yet. The goal is: UDS alert -> AI analysis
  works end-to-end and looks intentional.

### Acceptance criteria

- [ ] A user can click a UDS incident/alert row and open an AI analysis
- [ ] The analysis actually uses UDS MCP tools
- [ ] The analysis is persisted and can be reopened later
- [ ] The analysis page shows enough traceability to explain what the AI did
- [ ] Fresh-stack validation passes for this flow

---

## Task 2 - AI Chat Interface

Goal:
Build a simple but convincing natural-language AI assistant page that answers
questions using MCP tools and, when useful, RAG context.

This is the main response to Arnt's chatbot expectation.

### What currently exists

- The agent already has a working LLM tool-calling loop
- MCP exposes 12 tools
- RAG retrieval already exists
- The agent already serves inline HTML pages, so a simple chat page fits the
  current style

### What this task should do

1. Add a chat endpoint and page
- `GET /api/v1/chat` -> user-facing chat page
- `POST /api/v1/chat` -> submit a question and get an answer

2. Build one simple, reliable chat experience
- text input
- submit button
- loading state
- answer area
- optional tool-call trace

3. Keep scope controlled
- The chat page does not need streaming
- The chat page does not need multi-user history
- The chat page does not need embedded Grafana UI
- It only needs to work well enough for a clean demo

### Important files

- `services/agent/routes/chat.py` (new)
- `services/agent/main.py`

### Coordination note

- This task should NOT edit dashboard root navigation links
- Task 3 owns all dashboard-level navigation so merge conflicts stay low
- This task only needs to expose a stable chat URL that Task 3 can link to

### Tips for the AI assistant

- Reuse the existing tool loop structure from `analyze.py` (~line 450 for the
  loop, ~line 82 for the endpoint pattern)
- Use all 12 MCP tools unless there is a clear reason to restrict them
- The agent serves inline HTML (no template engine). See `_render_analysis_html()`
  in analyze.py (~line 300) and the validation dashboard in validation.py
  (~line 218) for how HTML pages are built as Python f-strings.
- Mount the new router in `services/agent/main.py` (see lines 129-131 for
  the pattern)
- Keep the prompt focused on answering operational questions, not writing long essays
- Include a few example questions on the page so the demo is easy to run

Example questions:
- Which vessels have critical alerts right now?
- What happened on IMO9300001 in the last 6 hours?
- Which app is degraded across multiple vessels?

### Acceptance criteria

- [ ] `/api/v1/chat` opens in a browser and works
- [ ] The assistant uses MCP tools to answer data questions
- [ ] The answer page shows enough traceability to explain what the AI used
- [ ] The page has a stable URL ready for dashboard navigation
- [ ] Fresh-stack validation passes

---

## Task 3 - Legacy/UDS Bridge + Dashboard Coherence

Goal:
Make the system feel like one product family instead of separate legacy and UDS
prototypes. This task owns naming clarity and dashboard-to-dashboard
navigation.

### What currently exists

- Legacy path uses `vessel_001`
- UDS path uses `IMO9300001`, `IMO9300002`, `IMO9300003`
- The two paths share a database but are not visibly connected
- Dashboard naming and navigation are still inconsistent
- `uds_app_health.json` is useful but confusingly named for a user-facing demo

### What this task should do

1. Add a lightweight legacy/UDS vessel bridge
- Preferred approach:
  - mapping
  - labels
  - drilldowns
  - explanatory context
- Higher-risk approach:
  - change the generator vessel ID directly

Default rule:
- Start with the lightweight bridge
- Only change core vessel IDs if the lighter approach still feels too weak

2. Own all dashboard-level navigation
- Add root-level `"links"` navigation across the main dashboards
- Include the chat link from Task 2 in the shared navigation
- Keep navigation consistent across the product

3. Clarify the role of `uds_app_health.json`
- Either rename it clearly, for example:
  - `AI Pipeline Health`
  - `System Health`
- Or intentionally leave it out of the main demo navigation if it is only for
  developers

4. Improve the Ship Operations dashboard as the legacy entry point
- Show the UDS relationship clearly
- Add a clean path from Ship Operations to the mapped UDS context

### Important files

- `grafana/dashboards/ship_operations.json`
- `grafana/dashboards/fleet_overview.json`
- `grafana/dashboards/uds_monitoring.json` (root navigation only)
- `grafana/dashboards/noc_support.json` (root navigation only)
- `grafana/dashboards/uds_app_health.json`
- `services/generator/sensors.py` only if the team chooses the higher-risk ID path
- `db/init/004_uds_reference_data.sql` only if a mapping object is added there

### Tips for the AI assistant

- Do not start by changing `vessel_001` to `IMO9300001`
- First try to make the connection explicit through navigation, labels, or a
  simple mapping layer
- The success criterion is product coherence, not database purity
- Treat `uds_app_health.json` as optional in the main demo path unless it is
  clearly framed

### Acceptance criteria

- [ ] A presenter can explain the relationship between legacy and UDS in one
      sentence without sounding defensive
- [ ] Main demo dashboards have coherent navigation links
- [ ] Ship Operations shows or links to the relevant UDS context
- [ ] `uds_app_health.json` is either clearly renamed or intentionally excluded
      from main demo navigation
- [ ] Fresh-stack validation passes and navigation works

---

## Task 4 - Predictive Feature + AI UX Cleanup + Handover Docs

Goal:
Add one real predictive/trend-based feature, clean up the AI experience, and
prepare the documentation needed for presentation and handover.

### What currently exists

- The system is reactive, not predictive
- The analysis page exposes an internal validation link
- Confidence is displayed as if it were precise, even though it is LLM-written
- The demo and handover docs are still missing
- `GET /events/{id}/acknowledge` still mutates state

### What this task should do

Core work:

1. Add one real predictive/trend feature
- Pick ONE and finish it properly
- Good options:
  - rising alert frequency
  - worsening latency/error trend
  - stale reporting trend
  - rising incident count

The result should be visible in one of these forms:
- a Grafana panel
- an MCP tool
- both

2. Clean up the AI analysis page UX
- Remove the visible link to the internal validation/RAG tuning page from the
  normal user-facing analysis page
- Make confidence more honest, for example:
  - `Low`
  - `Medium`
  - `High`
  - or `Model confidence`

Secondary work after the core feature is done:

3. Fix or remove the `GET` acknowledge mutation path

4. Add handover and demo docs
- `docs/PRODUCTION_GUIDE.md`
- `docs/DEMO_SCRIPT.md`

### Important files

- `services/mcp/main.py` if the predictive feature is exposed as a tool
- `services/agent/routes/analyze.py` for user-facing AI page cleanup only
- `services/agent/routes/events.py`
- `docs/PRODUCTION_GUIDE.md` (new)
- `docs/DEMO_SCRIPT.md` (new)

### Tips for the AI assistant

- Do not spend the whole task polishing docs before the predictive feature exists
- One credible trend feature is better than 3 half-finished ideas
- Keep the predictive feature explainable in plain language during the demo
- Treat AI page cleanup as product polish, not a redesign
- The "Open RAG Tuning" link is in `_render_analysis_html()` (analyze.py,
  ~line 336). Remove or hide it from the user-facing page.
- Confidence is parsed from LLM text at ~line 1112 in analyze.py. Rather than
  changing the parsing, change the HTML display: map 0-0.5 -> Low, 0.5-0.75 ->
  Medium, 0.75-1.0 -> High
- For the trend tool SQL, the `alerts` table has `starts_at`, `ends_at`,
  `uds_location_id`, `alert_type`, `severity` columns. Time-bucket queries
  over these can detect rising frequency patterns.

### Acceptance criteria

Core:
- [ ] At least one predictive/trend feature exists and is visible
- [ ] The user-facing analysis page does not link to internal developer tools
- [ ] Confidence is presented honestly rather than as fake precision

Secondary:
- [ ] `docs/PRODUCTION_GUIDE.md` exists
- [ ] `docs/DEMO_SCRIPT.md` exists
- [ ] `GET /events/{id}/acknowledge` is fixed or removed
- [ ] Fresh-stack validation passes

---

## File Ownership (Merge Conflict Prevention)

| File | Task 1 | Task 2 | Task 3 | Task 4 |
|------|--------|--------|--------|--------|
| `services/agent/routes/analyze.py` (UDS analysis logic) | OWNS | -- | -- | -- |
| `services/agent/routes/analyze.py` (user-facing HTML cleanup only) | -- | -- | -- | OWNS |
| `services/agent/routes/chat.py` | -- | OWNS | -- | -- |
| `services/agent/main.py` | add route | OWNS | -- | -- |
| `services/agent/routes/events.py` | -- | -- | -- | OWNS |
| `services/agent/models.py` | OWNS | -- | -- | -- |
| `services/mcp/main.py` | -- | -- | -- | OWNS |
| `grafana/dashboards/uds_monitoring.json` | OWNS (panel-level AI links) | -- | OWNS (root navigation only) | -- |
| `grafana/dashboards/noc_support.json` | OWNS (panel-level AI links) | -- | OWNS (root navigation only) | -- |
| `grafana/dashboards/ship_operations.json` | -- | -- | OWNS | -- |
| `grafana/dashboards/fleet_overview.json` | -- | -- | OWNS | -- |
| `grafana/dashboards/uds_app_health.json` | -- | -- | OWNS | -- |
| `services/generator/sensors.py` | -- | -- | OWNS only if needed | -- |
| `db/init/001_init.sql` | OWNS only if needed | -- | -- | -- |
| `db/init/004_uds_reference_data.sql` | -- | -- | OWNS only if needed | -- |
| `db/seed/uds_seed.sql` | OWNS only if auto-trigger is implemented | -- | -- | -- |
| `docs/PRODUCTION_GUIDE.md` | -- | -- | -- | OWNS |
| `docs/DEMO_SCRIPT.md` | -- | -- | -- | OWNS |

Important ownership notes:
- Task 3 owns all dashboard root navigation links
- Task 1 owns panel-level AI links on UDS dashboards
- Task 2 should not modify dashboard JSON unless absolutely necessary
- Task 4 should not change Task 1 analysis logic, only the user-facing page
  presentation

## Integration Checklist (after all 4 tasks merge)

- [ ] Fresh-stack validation passes
- [ ] Main demo dashboards load with data
- [ ] Navigation links work between the main demo dashboards
- [ ] UDS alert -> AI analysis works end-to-end
- [ ] Chat answers real data questions using MCP tools
- [ ] Legacy and UDS feel connected through mapping, labels, or shared identity
- [ ] At least one predictive/trend indicator is visible
- [ ] The analysis page is clean and user-facing
- [ ] `docs/PRODUCTION_GUIDE.md` and `docs/DEMO_SCRIPT.md` exist
- [ ] All MCP tools still respond correctly
- [ ] `CLAUDE.md` and `README.md` are updated if the feature surface changed

## Delivery Guidance

If time gets tight, prioritize in this order:

1. Task 1 - UDS AI Integration
2. Task 3 - Legacy/UDS Bridge + Dashboard Coherence
3. Task 2 - AI Chat Interface
4. Task 4 - Predictive Feature + AI UX Cleanup + Handover Docs

Reason:
- Without Task 1, the AI story is still mostly legacy-only
- Without Task 3, the product still feels split
- Task 2 gives a strong "wow" factor
- Task 4 matters a lot, but only after the system feels coherent

## Important Deadlines

- ~2026-04-07: all 4 tasks completed and merged
- 2026-04-08 to 2026-04-09: integration testing and demo rehearsal
- 2026-04-10 (approx): presentation to AI master students at Kartverket
- 2026-04-15: GeoAI-week deadline
- Late April: presentation for Knowit stakeholders
