# Production Guide

This document describes how to run, configure, and maintain the Maritime Agentic
Observability prototype. It is intended for maintainers and technical reviewers.

The repository is a locally runnable prototype. Before operational use, it needs
production hardening, deployment design, access control, backup routines, and
validation with real operational data.

## System Requirements

- Docker Desktop / Docker Engine 24+ with Compose v2
- 8 GB RAM minimum
- Approximately 5 GB disk space for Docker images and volumes
- Available local ports: 3000, 5432, 8000, 8001, 11434

No local Python, PostgreSQL, Grafana, or Ollama installation is required.

## First-Time Setup

```bash
git clone <repo-url>
cd <repo-dir>
cp .env.example .env
docker compose up -d --build
```

On first start:

1. `timescaledb` initializes all SQL scripts in `db/init/`
2. `ollama-init` pulls `llama3.2` and `nomic-embed-text`
3. `uds-seeder` backfills 6 hours of UDS history, then seeds every 30 minutes
4. `agent` ingests RAG knowledge documents
5. `generator` begins producing legacy telemetry events

Wait for the seeder to finish before validating dashboards:

```bash
docker compose logs -f uds-seeder
```

Look for `Backfill complete`.

## Restart and Reset

Restart without deleting data:

```bash
docker compose restart
```

Full reset with a fresh database:

```bash
docker compose down -v
docker compose up -d --build
```

The initialization scripts only run on a fresh database volume.

## Main URLs

| Service | URL |
|---------|-----|
| Grafana | http://localhost:3000 |
| Agent API docs | http://localhost:8000/docs |
| MCP-style tool API docs | http://localhost:8001/docs |
| AI Chat | http://localhost:8000/api/v1/chat |
| Dynamic dashboard selector | http://localhost:8000/api/v1/dynamic/select |
| Validation dashboard | http://localhost:8000/api/v1/validate/dashboard |

Default Grafana credentials:

```text
admin / code9-demo-admin
```

Change these before sharing the stack outside a local prototype environment.

## Configuration

Configuration is provided through `.env` or the defaults in `docker-compose.yml`.

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_NAME` | `maritime_telemetry` | Database name |
| `DB_PORT` | `5432` | Exposed PostgreSQL port |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana admin user |
| `GRAFANA_ADMIN_PASSWORD` | `code9-demo-admin` | Grafana admin password |
| `GRAFANA_PORT` | `3000` | Exposed Grafana port |
| `GRAFANA_URL` | `http://grafana:3000` | Internal Grafana URL used by agent |
| `GRAFANA_PUBLIC_URL` | `http://localhost:3000` | Public URL returned in dashboard links |
| `AGENT_PORT` | `8000` | Exposed agent API port |
| `MCP_PORT` | `8001` | Exposed MCP-style tool API port |
| `MCP_URL` | `http://mcp:8001` | Internal MCP URL used by agent |
| `MCP_API_KEY` | `code9-demo-key` | API key for MCP-style tool access |
| `OLLAMA_PORT` | `11434` | Exposed Ollama port |
| `OLLAMA_URL` | `http://ollama:11434` | Internal Ollama URL |
| `OLLAMA_MODEL` | `llama3.2` | LLM model |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model |
| `OLLAMA_TIMEOUT_SECONDS` | `300` | LLM call timeout |
| `RAG_TOP_K` | `5` | Number of RAG documents to retrieve |
| `RAG_MIN_SIMILARITY` | `0.60` | Minimum similarity threshold |
| `UDS_SEED_INTERVAL_SECONDS` | `1800` | UDS seed interval |
| `STUB_MODE` | `false` | Dynamic-dashboard dry-run/development fallback |

## Service Architecture

| Service | Port | Purpose |
|---------|------|---------|
| `timescaledb` | 5432 | PostgreSQL 16 + TimescaleDB + pgvector |
| `grafana` | 3000 | Static and generated dashboards |
| `agent` | 8000 | AI analysis, chat, validation, dynamic dashboard routes |
| `mcp` | 8001 | MCP-style REST adapter with 13 tools |
| `generator` | -- | Legacy telemetry data generator |
| `uds-seeder` | -- | UDS metrics, alerts, and logs seeder |
| `ollama` | 11434 | Local LLM inference and embeddings |
| `ollama-init` | -- | One-shot model puller |

## Database Schema

Initialization scripts:

1. `001_init.sql` - legacy telemetry tables
2. `002_rag.sql` - pgvector RAG schema
3. `003_uds.sql` - UDS application monitoring schema
4. `004_uds_reference_data.sql` - demo vessels, applications, and links
5. `005_dynamic_dashboard_runs.sql` - generated dashboard run storage

Key tables:

| Table | Description |
|-------|-------------|
| `telemetry` | Legacy sensor readings |
| `events` | Legacy anomaly events |
| `ai_analyses` | Persisted AI analysis results |
| `knowledge_docs` | RAG knowledge chunks and embeddings |
| `udslocations` | Demo vessels with IMO numbers |
| `applications` | Monitored applications |
| `metric_samples` | UDS time-series metrics |
| `alerts` | Active and historical alerts |
| `app_logs` | Prototype application log context |
| `dynamic_dashboard_runs` | Generated dashboard run history |

## Dynamic Dashboard Proof-of-Concept

Generate or update the default incident dashboard:

```bash
curl -X POST http://localhost:8000/api/v1/dynamic/trigger \
  -H "Content-Type: application/json" \
  -d "{\"mode\":\"latest_firing_alert\"}"
```

Open the generated dashboard:

```text
http://localhost:3000/d/maritime_dynamic_incident
```

For a controlled demo scenario:

```bash
docker compose exec agent python /app/scripts/inject_dynamic_incident.py --scenario service_down
```

Then trigger the dashboard with the printed request body.

## Health Checks

- MCP health: `GET http://localhost:8001/health`
- Agent health: `GET http://localhost:8000/health`
- Grafana health: `GET http://localhost:3000/api/health`
- Database health: Docker Compose `pg_isready` healthcheck

## Troubleshooting

### Dashboards show no data

1. Wait for `uds-seeder` backfill to complete.
2. Check `docker logs maritime_uds_seeder`.
3. Check `docker logs maritime_timescaledb`.
4. Verify the Grafana datasource under Grafana data source settings.

### LLM analysis is slow or hangs

1. Check that models are available:

   ```bash
   docker exec maritime_ollama ollama list
   ```

2. Check Ollama logs:

   ```bash
   docker logs maritime_ollama
   ```

3. Restart the agent after Ollama is ready:

   ```bash
   docker compose restart agent
   ```

### RAG knowledge base is empty

The agent retries RAG ingestion during startup. If the model pull takes longer
than expected, restart the agent after Ollama is ready:

```bash
docker compose restart agent
```

### Reset everything

```bash
docker compose down -v
docker compose up -d --build
```

## Backup

Data is stored in Docker volumes:

- `timescaledb_data`
- `ollama_data`

Example database backup:

```bash
docker exec maritime_timescaledb pg_dump -U postgres maritime_telemetry > backup.sql
```

## Security Notes

- Do not expose the local prototype directly to the public internet.
- Change all demo credentials before any non-local deployment.
- Keep `MCP_API_KEY` non-empty outside local debugging.
- Add proper authentication and authorization before operational use.
- Review CORS settings before deployment.

## Known Limitations

- The topology is fixed to 3 demo vessels and 6 demo applications.
- UDS data is seeded for repeatable scenarios and is not live production data.
- There is no migration strategy for existing database volumes.
- `app_logs` is a lightweight prototype bridge, not a full log pipeline.
- Local Ollama model quality and latency are limited.
- The dynamic dashboard is a proof-of-concept and needs broader validation.
