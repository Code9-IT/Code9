# Production Guide

This document describes how to deploy, configure, and operate the Maritime
Agentic Observability platform. It is intended for handover to Knowit Sorlandet
and any future maintainers.

## System Requirements

- **Docker Desktop** (Docker Engine 24+ with Compose v2)
- **RAM**: 8 GB minimum (Ollama LLM requires ~4 GB for llama3.2)
- **Disk**: ~5 GB for Docker images + volumes
- **Ports**: 3000 (Grafana), 5432 (PostgreSQL), 8000 (Agent), 8001 (MCP), 11434 (Ollama)

No local Python, PostgreSQL, or Node.js installation is required.

## Deployment

### First-time setup

```bash
git clone <repo-url>
cd <repo-dir>
cp .env.example .env        # adjust credentials if needed
docker compose up -d --build
```

On first start:
1. `timescaledb` initializes the database and runs all SQL scripts in `db/init/`
2. `ollama-init` pulls `llama3.2` and `nomic-embed-text` models
3. `uds-seeder` backfills 6 hours of UDS history, then seeds every 30 minutes
4. `agent` ingests RAG knowledge documents on startup
5. `generator` begins producing legacy telemetry data

Wait for the seeder to finish before using dashboards:

```bash
docker compose logs -f uds-seeder
# Wait for "Backfill complete"
```

### Restarting without data loss

```bash
docker compose restart
```

### Full reset (fresh database)

Database init scripts only run on a fresh volume. To reset everything:

```bash
docker compose down -v          # removes all volumes
docker compose up -d --build    # rebuilds and reinitializes
```

## Configuration

All configuration is via environment variables in `.env` (or `docker-compose.yml`
defaults):

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASSWORD` | `postgres` | PostgreSQL password |
| `DB_NAME` | `maritime_telemetry` | Database name |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password |
| `MCP_API_KEY` | `code9-scope1-demo-key` | API key for MCP tool access |
| `OLLAMA_MODEL` | `llama3.2` | LLM model for analysis |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Embedding model for RAG |
| `OLLAMA_TIMEOUT_SECONDS` | `600` | LLM call timeout |
| `RAG_TOP_K` | `5` | Number of RAG documents to retrieve |
| `RAG_MIN_SIMILARITY` | `0.60` | Minimum cosine similarity for RAG |
| `RAG_AUTO_INGEST_RETRIES` | `120` | Agent startup RAG auto-ingest attempts (survives cold Ollama model pull) |
| `RAG_AUTO_INGEST_DELAY_SECONDS` | `15` | Delay between RAG auto-ingest retries |
| `UDS_SEED_INTERVAL_SECONDS` | `1800` | Interval between UDS seed runs |
| `ANOMALY_PROBABILITY` | `0.00008` | Legacy anomaly generation rate |

### Security notes

- Change `MCP_API_KEY` and database credentials for any non-local deployment
- Grafana admin password should be changed on first login
- MCP auth is only enforced when `MCP_API_KEY` is non-empty
- Do not expose ports 5432 or 11434 to the public internet

## Service Architecture

| Service | Port | Purpose |
|---------|------|---------|
| `timescaledb` | 5432 | PostgreSQL 16 + TimescaleDB + pgvector |
| `grafana` | 3000 | Dashboard visualization |
| `agent` | 8000 | AI analysis pipeline (FastAPI) |
| `mcp` | 8001 | MCP REST adapter (13 DB query tools) |
| `generator` | -- | Legacy telemetry data generator |
| `uds-seeder` | -- | UDS metrics, alerts, and logs seeder |
| `ollama` | 11434 | Local LLM inference |
| `ollama-init` | -- | One-shot model puller |

### Data flow

```
generator --------> legacy telemetry/events -------> ship_operations dashboard
                                                            |
                                                      agent analyze
                                                      /           \
                                                RAG context     MCP tools

uds-seeder -------> UDS metrics/alerts/logs -------> uds_monitoring
                                                      fleet_overview
                                                      noc_support
                                                      alert_trends
```

## Database Schema

The database has four initialization scripts:

1. `001_init.sql` — Legacy telemetry tables (events, telemetry, ai_analyses)
2. `002_rag.sql` — pgvector RAG schema (knowledge_docs)
3. `003_uds.sql` — UDS application monitoring (udslocations, applications,
   metric_samples, alerts, app_logs)
4. `004_uds_reference_data.sql` — Reference data (3 vessels, 6 apps, 18 links)

### Key tables

| Table | Description |
|-------|-------------|
| `udslocations` | Vessels with IMO numbers |
| `applications` | Monitored applications |
| `metric_samples` | TimescaleDB hypertable for time-series metrics |
| `alerts` | Active and historical alerts |
| `app_logs` | Application log entries |
| `events` | Legacy anomaly events |
| `telemetry` | Legacy sensor readings |
| `ai_analyses` | Persisted AI analysis results (extended with vessel_imo / app_external_id / alert_name for the UDS path) |
| `knowledge_docs` | RAG knowledge base chunks with pgvector embeddings |

## MCP Tools (13 total)

| Tool | Scope | Purpose |
|------|-------|---------|
| `get_telemetry` | Legacy | Raw telemetry query |
| `get_events` | Legacy | Event list with filters |
| `get_analysis` | Legacy | AI analysis for an event |
| `get_vessel_app_status` | Scope 1 | All apps on one vessel |
| `get_vessel_alerts` | Scope 1 | Active alerts for one vessel |
| `get_app_metric_history` | Scope 1 | Time-series metrics for one app |
| `get_app_logs` | Scope 1 | Recent logs for one app |
| `get_fleet_status` | Scope 2 | All vessels with operational status |
| `get_fleet_alerts` | Scope 2 | Fleet-wide alerts with severity filter |
| `get_cross_vessel_correlation` | Scope 2 | Cross-vessel pattern detection |
| `get_incident_timeline` | Scope 2 | Chronological event timeline |
| `get_operational_snapshot` | Scope 2 | Full vessel state for NOC |
| `get_alert_trend` | Scope 3 | Alert frequency trend detection (predictive) |

## Dashboards

| Dashboard | Purpose |
|-----------|---------|
| Ship Operations | Legacy telemetry monitoring with AI analysis |
| UDS Monitoring | Single-vessel incident investigation |
| Fleet Overview | Multi-vessel operational overview |
| NOC Support | Full vessel state for support cases |
| Alert Trends | Predictive alert frequency analysis |

## Monitoring and Health Checks

- **MCP health**: `GET http://localhost:8001/health`
- **Agent health**: `GET http://localhost:8000/health`
- **Database**: `pg_isready -U postgres -d maritime_telemetry` (via Docker healthcheck)
- **Grafana**: check `http://localhost:3000/api/health`

## Troubleshooting

### LLM not responding

```bash
docker exec maritime_ollama ollama list    # check if models are pulled
docker logs maritime_ollama                # check for errors
docker restart maritime_ollama
```

### Dashboards show "No data"

1. Wait for `uds-seeder` backfill to complete
2. Check database connectivity: `docker logs maritime_timescaledb`
3. Verify Grafana datasource: Settings > Data Sources > timescaledb > Test

### Agent analysis hangs

- Check Ollama is running and responsive
- Increase `OLLAMA_TIMEOUT_SECONDS` if the model is slow
- Check agent logs: `docker logs maritime_agent`

### RAG knowledge base is empty after a fresh-volume start

The agent retries RAG auto-ingest while waiting for the Ollama embeddings
endpoint to come up. The default retry budget is `120 attempts * 15s = 30
minutes`, sized to survive a cold-start `llama3.2 + nomic-embed-text` pull.
On a slow link the model pull can still exceed that window. If
`docker logs maritime_agent` shows
`RAG auto-ingest skipped after N attempts`, do one of the following:

```bash
# 1. Confirm Ollama is healthy and the embeddings model is present:
docker exec maritime_ollama ollama list

# 2. Restart the agent so the startup hook re-runs ingest_if_empty():
docker compose restart agent

# 3. Or extend the retry budget for the next cold start:
#    RAG_AUTO_INGEST_RETRIES=240 RAG_AUTO_INGEST_DELAY_SECONDS=15 docker compose up -d
```

### Reset everything

```bash
docker compose down -v
docker compose up -d --build
```

## Backup and Data Persistence

Data is stored in Docker volumes:
- `timescaledb_data` — All database data
- `ollama_data` — Downloaded LLM models

To back up the database:

```bash
docker exec maritime_timescaledb pg_dump -U postgres maritime_telemetry > backup.sql
```

## Known Limitations

- Demo topology is fixed to 3 vessels and 6 applications
- No migration strategy — fresh volumes are the only reliable reset path
- MCP auth is API-key only (no JWT/OAuth)
- `app_logs` is a lightweight prototype bridge, not a full log pipeline
- LLM analysis quality depends on model size and prompt engineering
- No multi-user or authentication on the agent service
