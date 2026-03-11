# Maritime Agentic Observability – Starter Kit

Bachelor project in collaboration with **Knowit Sørlandet**.

A prototype that adds an **AI-agent layer** on top of a maritime
telemetry dashboard: when an anomaly is detected the agent explains
what happened and suggests corrective actions.

> Active development — core pipeline is live (Ollama tool-calling, MCP, generator).
> See [`docs/NEXT_STEPS.md`](docs/NEXT_STEPS.md) for task distribution across the group.
> See [`docs/SCOPE1_REVIEW_FINDINGS.md`](docs/SCOPE1_REVIEW_FINDINGS.md) for the current Scope 1 review baseline.

---

## Quick Start

### Prerequisites

| Tool | Min version | Why |
|------|-------------|-----|
| Docker Desktop | latest | runs everything |

That is it – no local Python, no database install.

### Steps

```bash
# 1) Clone
git clone <repo-url>
cd <repo-dir>

# 2) Copy env file  (edit passwords/ports if you like)
cp .env.example .env

# 3) Build + start all services
docker compose up --build
```

First run downloads images and may take a couple of minutes.

```bash
# 3b) Pull the two Ollama models (first run only – ~2.3 GB total)
docker exec -it maritime_ollama ollama pull nomic-embed-text   # embedding model for RAG (274 MB)
docker exec -it maritime_ollama ollama pull llama3.2           # LLM for analysis (2.0 GB)
```

> **Note:** The default `OLLAMA_MODEL` in `.env.example` is `llama3.2`.
> If your `.env` still has `llama3.2:1b`, change it to `llama3.2` - the `1b` tag does not exist
> and will cause analysis to fail with a 404.

> **Important for current Scope 1 work:** if you already have an older
> `timescaledb_data` volume, reset it before testing the integrated UDS path.
> The current prototype now depends on additional init scripts for UDS schema
> and reference data, and old DB volumes may not match the code.

```bash
# 4) Watch the generator to confirm data is flowing
docker compose logs -f generator
# You should see  [generator] Connected …  and periodic cycle messages.
```

```bash
# 5) Open Grafana in the browser
#    URL   → http://localhost:3000
#    Login → use GRAFANA_ADMIN_USER / GRAFANA_ADMIN_PASSWORD from your .env
#    Dashboards live under the "Maritime" folder.
```

### Trigger an analysis manually

```bash
# a) Find a recent event ID (grab any id from the Events table in Grafana, or:)
curl -s http://localhost:8000/api/v1/events?limit=1 | python -m json.tool

# b) Ask the agent to analyse that event (replace 1 with the real id)
curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"event_id": 1}'

# c) Force a fresh re-analysis for the same event (bypasses duplicate guard)
curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"event_id": 1, "force": true}'
```

The analysis appears in the **AI Analyses** panel
on the Ship Operations dashboard within the next Grafana refresh.
By default, repeated analyse calls for the same `event_id` return the latest
existing analysis. Set `"force": true` when you explicitly want a new LLM run.

### Add knowledge docs and ingest

```bash
# Put curated .md/.txt files in docs/knowledge/
# Then ingest/update embeddings:
docker exec maritime_agent python rag/ingest.py
```

### Stop

```bash
docker compose down
```

### Reset (wipe all data)

```bash
bash scripts/reset_db.sh        # Linux / macOS / Git Bash
# then:
docker compose up --build
```

---

## Project Layout

```
.
├── docker-compose.yml          ← all services in one file
├── .env.example                ← environment variables template
│
├── db/
│   ├── init/001_init.sql       ← legacy telemetry/events/ai_analyses schema
│   ├── init/003_uds.sql        ← Scope 1 UDS schema
│   ├── init/004_uds_reference_data.sql ← tracked UDS reference data
│   └── seed/uds_seed.sql       ← periodic mock UDS metrics/alerts
│
├── grafana/
│   ├── provisioning/           ← datasource + dashboard auto-config
│   └── dashboards/             ← JSON for "Ship Ops" + "UDS Monitoring"
│
├── services/
│   ├── agent/                  ← FastAPI AI-agent
│   │   ├── main.py             ← app entry point
│   │   ├── routes/             ← HTTP endpoints
│   │   ├── rag/                ← RAG (pgvector retrieval + ingest, live)
│   │   └── llm/                ← Ollama client (llama3.2, live)
│   ├── mcp/                    ← MCP REST adapter (DB tools for agent)
│   └── generator/              ← synthetic data writer
│       ├── main.py             ← infinite loop: generate → insert
│       ├── sensors.py          ← sensor definitions + normal values
│       └── anomalies.py        ← random anomaly generation
│
├── docs/
│   ├── architecture.md         ← system overview + diagram
│   ├── NEXT_STEPS.md          ← task distribution + 73-sensor reference
│   ├── FUTURE_CHECKS.md       ← security backlog + RAG quality roadmap
│   └── knowledge/             ← 17 curated maritime RAG knowledge files (Points 1–10)
│
└── scripts/
    ├── reset_db.sh             ← wipe + recreate the database
    └── uds_seed_loop.sh        ← periodic UDS seed runner
```

---

## Tech Stack

| Tool | Role |
|------|------|
| **TimescaleDB** | Time-series database (PostgreSQL) |
| **Grafana 11** | Dashboard visualisation |
| **FastAPI** | Agent HTTP API |
| **Ollama** | Local LLM (llama3.2) – live, tool-calling enabled |
| **Docker Compose** | Single-command local environment |

---

## Current state

| Component | Status | Notes |
|-----------|--------|-------|
| **RAG** | ✅ Live | 17 curated maritime knowledge files, 76 chunks in pgvector. Auto-ingests on first startup. |
| **LLM analysis** | ✅ Live | Ollama `llama3.2` with tool-calling loop. Analyses stored in `ai_analyses`. |
| **UDS schema + seed path** | IN_PROGRESS | Scope 1 schema, reference data, and periodic UDS seeding are integrated, but require fresh DB validation. |
| **Grafana dashboards** | IN_PROGRESS | Ship Operations and UDS Monitoring are provisioned. UDS Monitoring still needs stronger historical incident context for full User Story 1 coverage. |
| **Auto-analysis** | ❌ Manual only | Events must be analysed via `POST /api/v1/analyze` or Grafana data link. No background worker yet. |
| **Auth** | ❌ Prototype only | MCP has API-key support, but agent auth and production-safe endpoint protection are still missing. |

Search the codebase for `TODO` to find every pre-marked task.

---

## Scope 1 acceptance flow (Student 4)

Run this only after Student 1-3 feature merges are in `feat/code9-scope1-team-base`.

1. Start from a fresh DB:
   - `docker compose down -v`
   - `docker compose up --build`
2. Validate DB initialization:
   - UDS schema tables exist
   - UDS reference data exists
3. Validate seeding:
   - `metric_samples` and `alerts` receive new rows
   - scenario mix includes more than only ServiceDown/critical-down
4. Validate Grafana:
   - vessel selector works
   - incident flow links alert -> app -> recent historical metrics
   - logs/log-like context is visible (or explicitly documented if deferred)
5. Validate MCP tools:
   - `get_vessel_app_status`
   - `get_vessel_alerts`
   - `get_app_metric_history`
   - log/log-like retrieval tool from Scope 1 merge
6. Sync docs:
   - update `README.md`, `docs/NEXT_STEPS.md`, `docs/SCOPE1_REVIEW_FINDINGS.md`,
     and `docs/SCOPE1_HANDOFF_NOTES.md` so they match the merged behavior.

See `docs/SCOPE1_HANDOFF_NOTES.md` for the merge-support checklist.

---

## Contributing (group workflow)

1. Pull latest `main`.
2. Create a feature branch: `git checkout -b feat/your-name-feature`.
3. Work in **your** directory (see `docs/NEXT_STEPS.md`).
4. Push the branch and open a Pull Request.
5. Someone else reviews → merge → delete branch.
