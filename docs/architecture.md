# Architecture – Maritime Agentic Observability

## What this prototype does

Traditional maritime dashboards show raw sensor data.  Operators must
manually decide what every blip means.  This prototype adds an **AI
agent layer** on top: when an anomaly is detected the agent explains
*why* it happened and *what to do* – the core idea behind
**agentic observability**.

---

## Component diagram

```
┌────────────┐   writes    ┌───────────────┐   queries   ┌────────────┐
│ Generator  │ ──────────> │  TimescaleDB  │ <────────── │  Grafana   │
│ (synth data│             │  telemetry    │             │  dashboards│
│  + events) │             │  events       │             │  (live)    │
└────────────┘             │  ai_analyses  │             └─────┬──────┘
                           └───────┬───────┘                   │
                                   │  fetch event               │ operator clicks
                                   ▼                            │ "Analyze/Acknowledge" links
                           ┌───────────────┐                   │
                           │  Agent        │ <─────────────────┘
                           │  (FastAPI)    │
                           └───┬───────┬───┘
                               │       │
                  tool-calling │       │ sends prompt + tools
                  loop (async) │       ▼
                               │  ┌──────────┐
                               │  │  Ollama  │
                               │  │  (LLM)   │
                               │  └──────────┘
                               │       │ calls tool →
                               ▼       ▼
                       ┌──────────┐  ┌──────────────┐
                       │ RAG layer │  │  MCP Server  │
                       │ (context)│  │  (port 8001) │
                       └──────────┘  │  get_telemetry│
                       (pgvector) │  get_events   │
                                     │  get_analysis │
                                     └──────────────┘
```

### Data flow – step by step

1. **Generator** inserts a batch of synthetic telemetry every few seconds.
2. If a sensor breaches a threshold the generator also inserts a row into `events`.
3. **Grafana** polls the DB on its own refresh interval and renders live charts.
4. An operator calls the analysis endpoint via `POST /api/v1/analyze` or
   Grafana data links (`GET /api/v1/analyze/{event_id}`).
5. **Agent** fetches the event, asks **RAG** for context docs, builds a prompt.
6. The prompt is sent to **Ollama** (or the stub); the reply is stored in
   `ai_analyses`. Repeated calls reuse the latest analysis by default unless
   `force=true` is provided.
7. Grafana picks up the new row and shows the analysis on the dashboard.

---

## Services

| Service       | Image / language | Responsibility                              |
|---------------|------------------|---------------------------------------------|
| timescaledb   | TimescaleDB 16   | Time-series storage (all three tables)      |
| grafana       | Grafana 11       | Visualisation – 2 auto-provisioned dashboards |
| agent         | Python / FastAPI | Orchestrates tool-calling loop → LLM → stores analysis |
| generator     | Python (script)  | Writes synthetic data + anomaly events      |
| mcp           | Python / FastAPI | REST adapter: exposes DB tools to the agent (port 8001) |
| ollama        | Ollama           | Local LLM inference – llama3.2 or llama3.1  |

---

## Dashboards

| Dashboard        | Audience                        | Key panels                                    |
|------------------|---------------------------------|-----------------------------------------------|
| Ship Operations  | Kaptein / operativt personell   | Engine temp, oil pressure, RPM, events, AI    |
| Data Quality     | Data-trust / overvåkning        | Records/min, events vs analyses, unacked list |

---

## Status – what is done and what remains

| Component | Status | Notes / TODO                                              |
|-----------|---------|------------------------------------------------------------|
| MCP server | ✅ Running on port 8001 | REST adapter with 3 tools. Not the official MCP wire protocol — see `underveisNotater.md`. |
| Ollama    | DONE | Tool-calling loop active in agent (`llama3.2` default model). |
| RAG       | IN_PROGRESS | pgvector retrieval + ingest are wired; add curated docs in `docs/knowledge/` |
| Auth      | ⬜ None | Add JWT / role-based access before any production use     |
| Anomaly detection | ✅ Rule-based in generator | Sufficient for prototype          |

---

## Tech choices & rationale

* **TimescaleDB** – drop-in Postgres extension; great tooling ecosystem,
  native hypertables for time-series compression and fast range scans.
* **FastAPI** – async, Pydantic-first, fast to iterate.  Ideal for the
  agent micro-service.
* **Ollama** – runs locally, no cloud GPU needed for early demos.
  Swappable for any OpenAI-compatible endpoint later.
* **Docker Compose** – single command to spin everything up; no
  cloud infra needed.


