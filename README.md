# Maritime Agentic Observability – Starter Kit

Bachelor project in collaboration with **Knowit Sørlandet**.

A prototype that adds an **AI-agent layer** on top of a maritime
telemetry dashboard: when an anomaly is detected the agent explains
what happened and suggests corrective actions.

> Active development — core pipeline is live (Ollama tool-calling, MCP, generator).
> See [`docs/NEXT_STEPS.md`](docs/NEXT_STEPS.md) for task distribution across the group.

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
# 3b) Pull embedding model used by RAG retrieval
docker exec -it maritime_ollama ollama pull nomic-embed-text
```

```bash
# 4) Watch the generator to confirm data is flowing
docker compose logs -f generator
# You should see  [generator] Connected …  and periodic cycle messages.
```

```bash
# 5) Open Grafana in the browser
#    URL   → http://localhost:3000
#    Login → admin / admin   (or whatever is in your .env)
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
│   └── init/001_init.sql       ← schema (auto-runs on first DB start)
│
├── grafana/
│   ├── provisioning/           ← datasource + dashboard auto-config
│   └── dashboards/             ← JSON for "Ship Ops" + "Data Quality"
│
├── services/
│   ├── agent/                  ← FastAPI AI-agent
│   │   ├── main.py             ← app entry point
│   │   ├── routes/             ← HTTP endpoints
│   │   ├── rag/                ← RAG stub (vector search – Nidal)
│   │   └── llm/                ← Ollama client (llama3.2, live)
│   ├── mcp/                    ← MCP REST adapter (DB tools for agent)
│   └── generator/              ← synthetic data writer
│       ├── main.py             ← infinite loop: generate → insert
│       ├── sensors.py          ← sensor definitions + normal values
│       └── anomalies.py        ← random anomaly generation
│
├── docs/
│   ├── architecture.md         ← system overview + diagram
│   └── NEXT_STEPS.md          ← task distribution + 73-sensor reference
│
└── scripts/
    └── reset_db.sh             ← wipe + recreate the database
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

## What is stubbed?

| Component | Behaviour today | Next step |
|-----------|-----------------|-----------|
| **RAG** | pgvector retrieval + ingest ready | add curated docs in `docs/knowledge/` and ingest |
| **Grafana dashboards** | provisioned, core panels + links live | Ship Ops + Data Quality polish/testing (Jonas) |
| **Auth** | none | add JWT before any real deploy |
| **Analyse trigger** | manual `curl` + Grafana data links (`GET` aliases) | later hardening: POST-only UI + auth |

Search the codebase for `TODO` to find every pre-marked task.

---

## Contributing (group workflow)

1. Pull latest `main`.
2. Create a feature branch: `git checkout -b feat/your-name-feature`.
3. Work in **your** directory (see `docs/NEXT_STEPS.md`).
4. Push the branch and open a Pull Request.
5. Someone else reviews → merge → delete branch.
