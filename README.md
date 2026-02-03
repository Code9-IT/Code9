# Maritime Agentic Observability – Starter Kit

Bachelor project in collaboration with **Knowit Sørlandet**.

A prototype that adds an **AI-agent layer** on top of a maritime
telemetry dashboard: when an anomaly is detected the agent explains
what happened and suggests corrective actions.

> This is a **starter kit**, not a finished product.  Many parts are
> intentionally stubbed out.  See [`docs/WORK_DISTRIBUTION.md`](docs/WORK_DISTRIBUTION.md)
> for how to split the remaining work across the group.

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

# b) Ask the agent to analyse that event  (replace 1 with the real id)
curl -X POST http://localhost:8000/api/v1/analyze \
     -H "Content-Type: application/json" \
     -d '{"event_id": 1}'
```

The analysis (currently a stub) appears in the **AI Analyses** panel
on the Ship Operations dashboard within the next Grafana refresh.

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
│   │   ├── rag/                ← RAG stub (vector search – TODO)
│   │   └── llm/                ← Ollama client stub
│   └── generator/              ← synthetic data writer
│       ├── main.py             ← infinite loop: generate → insert
│       ├── sensors.py          ← sensor definitions + normal values
│       └── anomalies.py        ← random anomaly generation
│
├── docs/
│   ├── architecture.md         ← system overview + diagram
│   └── WORK_DISTRIBUTION.md   ← who works on what
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
| **Ollama** | Local LLM – stubbed out, enable when ready |
| **Docker Compose** | Single-command local environment |

---

## What is stubbed?

| Component | Behaviour today | Next step |
|-----------|-----------------|-----------|
| **RAG** | returns empty context | add vector DB + docs |
| **Ollama / LLM** | returns canned text | pull a model, flip `STUB_MODE` |
| **Auth** | none | add JWT before any real deploy |
| **Analyse trigger** | manual `curl` | wire a button into Grafana |

Search the codebase for `TODO` to find every pre-marked task.

---

## Contributing (group workflow)

1. Pull latest `master`.
2. Create a feature branch: `git checkout -b feat/your-feature`.
3. Work in **your** directory (see `docs/WORK_DISTRIBUTION.md`).
4. Push the branch and open a Pull Request.
5. Someone else reviews → merge → delete branch.
