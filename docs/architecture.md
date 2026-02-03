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
                                   ▼                            │ "Analyze" (TODO)
                           ┌───────────────┐                   │
                           │  Agent        │ <─────────────────┘
                           │  (FastAPI)    │
                           └───┬───────┬───┘
                               │       │
                     retrieves │       │ sends prompt
                               ▼       ▼
                       ┌──────────┐  ┌──────────┐
                       │ RAG stub │  │  Ollama  │
                       │ (context)│  │  (LLM)   │
                       └──────────┘  └──────────┘
                       (empty today)  (stubbed today)
```

### Data flow – step by step

1. **Generator** inserts a batch of synthetic telemetry every few seconds.
2. If a sensor breaches a threshold the generator also inserts a row into `events`.
3. **Grafana** polls the DB on its own refresh interval and renders live charts.
4. An operator (or, later, an automated trigger) calls `POST /api/v1/analyze`
   with the `event_id`.
5. **Agent** fetches the event, asks **RAG** for context docs, builds a prompt.
6. The prompt is sent to **Ollama** (or the stub); the reply is stored in
   `ai_analyses`.
7. Grafana picks up the new row and shows the analysis on the dashboard.

---

## Services

| Service       | Image / language | Responsibility                              |
|---------------|------------------|---------------------------------------------|
| timescaledb   | TimescaleDB 16   | Time-series storage (all three tables)      |
| grafana       | Grafana 11       | Visualisation – 2 auto-provisioned dashboards |
| agent         | Python / FastAPI | Orchestrates RAG → LLM pipeline             |
| generator     | Python (script)  | Writes synthetic data + anomaly events      |
| ollama        | Ollama (optional)| Local LLM inference (commented out in MVP) |

---

## Dashboards

| Dashboard        | Audience                        | Key panels                                    |
|------------------|---------------------------------|-----------------------------------------------|
| Ship Operations  | Kaptein / operativt personell   | Engine temp, oil pressure, RPM, events, AI    |
| Data Quality     | Data-trust / overvåkning        | Records/min, events vs analyses, unacked list |

---

## Stubs – what is *not* real yet

| Component | Status | TODO                                                      |
|-----------|---------|------------------------------------------------------------|
| RAG       | Empty list returned | Implement vector-DB ingestion + retrieval       |
| Ollama    | Canned text returned | Pull a model, set `STUB_MODE = False`          |
| Auth      | None | Add JWT / role-based access before production               |
| Anomaly detection | Rule-based in generator | Move to streaming rule engine     |

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
