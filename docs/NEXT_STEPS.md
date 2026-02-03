# Next Steps – Work Distribution

Personalized task list for the group. Each person owns a set of files.
The goal: no two people edit the same file at the same time, merge conflicts stay near zero.

---

## Quick overview

| Student   | Domain                        | Primary files                                                  |
|-----------|-------------------------------|----------------------------------------------------------------|
| Kristian  | LLM & Agent Core              | `services/agent/llm/`, `services/agent/routes/analyze.py`      |
| Nidal     | RAG & Knowledge Base          | `services/agent/rag/`, `docs/knowledge/` (new)                 |
| Jonas     | Grafana Dashboards & UI       | `grafana/dashboards/`                                          |
| Onu       | MCP Server & Data Pipeline    | `services/mcp/` (new), `services/generator/`                   |

---

## What the project still needs (big picture)

The starter kit has a working skeleton — generator writes data, Grafana shows it, the agent
can be called and stores an analysis. Everything beyond that is stubbed or missing:

1. A **real LLM** that actually analyses events (Ollama, currently stubbed).
2. **RAG** that retrieves relevant maritime docs to ground the LLM (currently returns empty).
3. An **MCP server** to let the LLM query data sources via tools (not in the starter at all —
   the project description calls this "a central architectural component").
4. **Polished dashboards** with severity colours, vessel filters, and an Analyse trigger.
5. The full **human-in-the-loop** flow visible end-to-end (event → analysis → operator action).

---

## Kristian – LLM & Agent Core

**You own:** `services/agent/llm/ollama_client.py` and `services/agent/routes/analyze.py`

### Priority 1 – get a real LLM responding

- [ ] Make `STUB_MODE` controllable via an env var instead of being hard-coded to `True`
      in `ollama_client.py`. Add `STUB_MODE=true` to `.env.example` and the `agent`
      environment block in `docker-compose.yml` (open a PR for those shared files).
- [ ] Uncomment the real Ollama HTTP call in `ollama_client.py`.
- [ ] Uncomment and enable the `ollama` service in `docker-compose.yml` (PR).
- [ ] Pull a model inside the container:
      `docker exec -it maritime_ollama ollama pull llama3`
      (or `llama3.2` — smaller, faster on machines without a GPU).
- [ ] Test end-to-end: run `docker compose up --build`, wait for an event to appear, then
      `curl -X POST http://localhost:8000/api/v1/analyze -H "Content-Type: application/json" -d '{"event_id": <id>}'`
      and verify you get a real LLM response instead of the stub text.

### Priority 2 – make the response useful

- [ ] Improve the prompt in `_build_prompt()` so the LLM returns a **structured** output
      (e.g. numbered sections: explanation, impact, actions, confidence %).
- [ ] Parse `suggested_actions` from the LLM text (split on numbered list items or use a
      structured prompt format) instead of the current placeholder `["Investigate further"]`.
- [ ] Parse the confidence value the LLM outputs (0–100) and convert it to 0.0–1.0 before
      storing in `ai_analyses.confidence`.
- [ ] Add a timeout and error handler: if Ollama does not respond in time, store the
      analysis with `status = 'failed'` instead of crashing.

### Coordinate with
- Nidal: the RAG context string is inserted into your prompt by `_build_prompt()`. Once
  Nidal has real docs, test together to make sure they appear and help the LLM.
- Onu: later, MCP may replace or augment some of the direct data fetching in `analyze.py`.

---

## Nidal – RAG & Knowledge Base

**You own:** `services/agent/rag/client.py` and a new `docs/knowledge/` directory

### Priority 1 – choose a vector store and wire it up

- [ ] Decision: use **pgvector** (a PostgreSQL extension — no extra Docker service needed,
      already have TimescaleDB/Postgres running). Add to `services/agent/requirements.txt`.
- [ ] Create a new init script **`db/init/002_rag.sql`** (do NOT edit `001_init.sql` —
      open a PR):
      - `CREATE EXTENSION IF NOT EXISTS vector;`
      - A `knowledge_docs` table with columns: `id`, `title`, `content`, `source`,
        `embedding` (pgvector vector column), `created_at`.
- [ ] Create the directory **`docs/knowledge/`** and put 4–6 sample maritime reference
      documents in it as plain `.txt` or `.md` files. Examples:
        - `engine_overheating.md` – what causes high engine temp, what to check
        - `oil_pressure_low.md`   – possible causes, safety implications
        - `rpm_spike.md`          – reasons, safety risks
        - `general_safety.md`     – generic maritime safety checklist
      These can be written from general knowledge — they do not need to be real Knowit docs.
- [ ] Write an **ingestion script** (e.g. `services/agent/rag/ingest.py`) that:
      1. Reads every file in `docs/knowledge/`.
      2. Embeds each document (use a simple sentence-embedding model via a Python lib —
         `sentence-transformers` is the standard choice, add to `requirements.txt`).
      3. Inserts the title, content, and embedding into `knowledge_docs`.
      This script can be run manually with `docker exec` for now — it does not need to be
      in the main loop.
- [ ] Update `retrieve_context()` in `rag/client.py`:
      1. Embed the query string `"{event_type} {sensor_name}"`.
      2. Run a similarity search against `knowledge_docs.embedding`.
      3. Return the top-3 results as `RAGDocument` objects.

### Priority 2 – tune and test

- [ ] Test that the retrieved docs actually show up in the LLM prompt by enabling
  Kristian's real Ollama call and checking the analysis output.
- [ ] Try adjusting K (top-K) and the similarity threshold to get better matches.
- [ ] If the embedding model is too slow to install inside the agent container, consider
  pre-computing embeddings at ingest time and only running the query embedding at runtime.

### Coordinate with
- Kristian: your output (the context string) is pasted directly into Kristian's prompt.
  Test together once both Priority 1 tasks are done.

---

## Jonas – Grafana Dashboards & UI

**You own:** `grafana/dashboards/ship_operations.json` and `grafana/dashboards/data_quality.json`

### Priority 1 – make the dashboards useful and readable

- [ ] **Severity colour-coding** in both Events tables:
      Use Grafana field overrides or value mappings on the `severity` column so that
      `critical` → red background, `warning` → yellow/orange, `info` → green.
- [ ] **Vessel dropdown filter:** add a Grafana variable (`$vessel`) to both dashboards
      so the user can pick one vessel or see all. Update all panel queries to use it:
      `WHERE vessel_id = '$vessel'` (with an `ALL` option that removes the filter).
- [ ] **Missing sensor panels:** the Ship Operations dashboard only shows engine_temp,
      oil_pressure, and engine_rpm. Add panels for `coolant_temp` and `fuel_consumption`
      (the generator already produces these — just copy an existing timeseries panel and
      change the sensor_name in the SQL).
- [ ] **Units:** make sure oil pressure shows `bar`, temperatures show `°C`,
      RPM shows `rpm`, fuel shows `L/h`. Grafana `unit` field in `fieldConfig.defaults`.

### Priority 2 – interactive features

- [ ] **"Analyse" trigger in the Events table:** Grafana table panels cannot natively call
      an API on click, but you can add a **link column** or use an **HTML panel** with a
      small inline `<script>` that does a `fetch('POST /api/v1/analyze', ...)`.
      Approach: add an `action` column to the Events table query that generates a link like
      `'http://localhost:8000/api/v1/analyze?event_id=' || id` and document that clicking
      it needs to be a POST (or switch the agent to accept GET for simplicity — coordinate
      with Kristian).
- [ ] **"Acknowledge" button:** same pattern for the Unacknowledged Events table — a link
      or HTML button that POSTs to `/api/v1/events/{id}/acknowledge?operator=...`.
- [ ] **Gap detection panel** on Data Quality dashboard: a query that finds gaps in the
      telemetry time series (e.g. minutes with zero rows for a given vessel).

### No coordination needed
You work entirely in `grafana/dashboards/`. The only shared touch point is if you want
the agent to accept GET instead of POST for the Analyse trigger — talk to Kristian first.

---

## Onu – MCP Server & Data Pipeline

**You own:** a new `services/mcp/` directory and `services/generator/`

### Priority 1 – build the MCP server

MCP (Model Context Protocol) is explicitly called out in the project description as "a
central architectural component." The starter kit does not include it. This is your main
deliverable.

- [ ] **Research MCP.** Read: https://modelcontextprotocol.io/docs/concepts/server
      Understand: a server exposes *tools* that an LLM can call. Each tool has a name,
      a description, and input/output schema.
- [ ] Create `services/mcp/` with:
      - `Dockerfile`
      - `requirements.txt` (start with `fastapi`, `uvicorn`, `asyncpg`, `python-dotenv`)
      - `main.py` – FastAPI app that exposes the MCP tool definitions as HTTP endpoints
- [ ] Implement these **three tools** (minimum):
      1. `get_telemetry` – inputs: `vessel_id`, `sensor_name`, `minutes_back` (default 60).
         Queries `telemetry` table, returns the last N minutes of readings.
      2. `get_events`    – inputs: `vessel_id` (optional), `acknowledged` (optional bool).
         Returns recent events from the `events` table.
      3. `get_analysis`  – input: `event_id`.
         Returns the latest `ai_analyses` row for that event, or `null` if none exists.
- [ ] Add the MCP service to `docker-compose.yml` (open a PR):
      - Build from `./services/mcp`
      - Expose port 8001 (or any free port)
      - Same DB env vars as the agent
      - Depends on `timescaledb` (healthy)
- [ ] Test: start everything with `docker compose up --build`, then curl each tool endpoint
      and verify you get real data back.

### Priority 2 – generator enhancements

- [ ] **Burst mode** in `services/generator/anomalies.py`: add an env var `BURST_MODE`
      (default `false`). When `true`, every cycle fires 3–5 anomalies across different
      sensors/vessels. Useful for live demos.
- [ ] **Time weighting** in `anomalies.py`: make anomalies slightly more likely during
      certain hours (e.g. simulate higher load during 06:00–14:00 UTC).
- [ ] **New sensors** in `sensors.py`: add `nav_speed` (knots, baseline ~12, anomaly >25)
      and `rudder_angle` (degrees, baseline ~0, anomaly > ±20). Add matching event
      definitions in `anomalies.py`.
- [ ] Update `docker-compose.yml` generator env block with the new `BURST_MODE` var (PR).

### Coordinate with
- Kristian (later): once MCP is working, discuss how the LLM can be taught to *call* the
  MCP tools instead of having data pre-fetched. This is the "agentic" part of the
  architecture. It does not need to happen in Priority 1.

---

## Shared-file rules (everyone reads this)

| Shared file                      | Who will touch it   | How to handle                          |
|----------------------------------|---------------------|----------------------------------------|
| `docker-compose.yml`             | Kristian, Onu       | Each opens a separate PR. Do not merge both at the same time. |
| `db/init/` (new init scripts)    | Nidal (`002`), Onu (maybe `003`) | Use different numbered files. |
| `services/agent/requirements.txt`| Nidal               | Branch + PR.                           |
| `.env.example`                   | Kristian            | Branch + PR. Others pull before adding their own vars. |

1. **Never push directly to `master`.** Always: `git checkout -b feat/<your-name>-<what>`
2. **Pull before you start.** `git pull origin master` at the beginning of every session.
3. **Keep PRs small.** One logical change per PR. Easier to review.
4. **If you need to touch someone else's file,** open an issue or Slack message first.

---

## Suggested group workflow

1. Everyone does their **Priority 1** tasks first — these can happen in parallel.
2. Once Kristian has Ollama running, do a group test: `docker compose up --build` together
   and verify the full pipeline (generator → event → manual analyse → analysis in Grafana).
3. Once Nidal has RAG returning docs, run the pipeline again — the LLM should now have
   context in its prompt.
4. Onu presents the MCP server to the group. Discuss how to connect it to the agent in
   a future iteration.
5. Jonas demos the polished dashboards.
6. Group decides on next priorities based on what works and what does not.
