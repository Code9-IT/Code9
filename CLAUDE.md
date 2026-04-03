# CLAUDE.md - Project Instructions for AI Assistants

This file is the primary entry point for any AI assistant working on this codebase.
Read this file first, then read the files referenced below as needed.

## What This Project Is

Bachelor thesis project (UiA) in collaboration with Knowit Sorlandet.
Maritime agentic observability: AI-agent-enhanced monitoring for UDS application
platform deployed on vessels.

The system monitors multiple applications running on multiple vessels. Each vessel
runs 6 applications that produce metrics, alerts, and logs. The AI agent interprets
incidents using RAG-grounded knowledge and MCP tool access.

## Tech Stack

- **Database**: PostgreSQL 16 + TimescaleDB + pgvector
- **Dashboards**: Grafana 11.0.0
- **Backend**: Python / FastAPI (agent, MCP, generator services)
- **LLM**: Ollama (llama3.2 locally) with nomic-embed-text for embeddings
- **RAG**: pgvector similarity search over docs/knowledge/ files
- **Orchestration**: Docker Compose (all services containerized)

## How To Run

```bash
docker compose down -v          # fresh start (required for reliable validation)
docker compose up -d --build    # start all services
docker compose logs -f uds-seeder  # wait for "Backfill complete"
```

- Grafana: http://localhost:3000 (admin / code9-demo-admin)
- Agent API: http://localhost:8000/docs
- MCP API: http://localhost:8001/docs

## Current Status (updated 2026-04-01)

### Scope 1 - Single Vessel Incident (User Story 1) -- COMPLETE
- 3 vessels, 6 apps per vessel, 18 vessel-app links
- UDS seeding every 30 min with 6-hour backfill on fresh DB
- Grafana incident dashboard: `grafana/dashboards/uds_monitoring.json`
- 4 MCP tools: get_vessel_app_status, get_vessel_alerts, get_app_metric_history, get_app_logs
- Legacy telemetry path with AI analysis also functional

### Scope 2 - Multi-Vessel + NOC Support (User Stories 2 & 3) -- COMPLETE
- Task 1 (Nidal): Fleet Overview Dashboard -- DONE
  - `grafana/dashboards/fleet_overview.json`
- Task 2 (Jonas): NOC Support Dashboard -- DONE
  - `grafana/dashboards/noc_support.json`
- Task 3 (Kristian): MCP Fleet/Incident Tools + Seed -- DONE
  - 5 new MCP tools in `services/mcp/main.py`
  - Cross-vessel seed scenario in `db/seed/uds_seed.sql`
  - Agent allowlist updated in `services/agent/routes/analyze.py`

### Scope 3 - Integration / Demo Polish (in progress)
- User-facing AI chat page available at `GET /api/v1/chat`
- Chat submission endpoint available at `POST /api/v1/chat`
- Chat reuses Ollama + RAG + all 12 MCP tools for operational questions

## Architecture Overview

```
generator ---------> telemetry / events ---------> ship_operations.json
                                                          |
                                                    agent analyze
                                                    /           \
                                               RAG context    MCP tools

004_uds_reference_data.sql --> UDS reference tables
                                      |
uds-seeder -----------------------> metric_samples / alerts / app_logs
                                      |
                          +-----------+-----------+
                          |           |           |
                   uds_monitoring  fleet_overview  noc_support
                          |           |           |
                          +-----MCP UDS tools-----+
                               (12 tools total)
```

## Key Files To Read

### Core runtime
- `docker-compose.yml` -- service definitions
- `services/mcp/main.py` -- MCP REST adapter, all 12 tool implementations
- `services/agent/routes/analyze.py` -- AI analysis pipeline + MCP tool filtering
- `services/agent/routes/chat.py` -- user-facing AI chat page + free-form question route
- `services/agent/rag/ingest.py` -- RAG knowledge ingestion
- `db/init/003_uds.sql` -- UDS schema
- `db/init/004_uds_reference_data.sql` -- reference data (3 vessels, 6 apps, 18 links)
- `db/seed/uds_seed.sql` -- periodic seed data with scenario flags
- `scripts/uds_seed_loop.sh` -- seed loop controller with backfill

### Dashboards
- `grafana/dashboards/uds_monitoring.json` -- Scope 1: single-vessel incident board
- `grafana/dashboards/fleet_overview.json` -- Scope 2: multi-vessel fleet overview
- `grafana/dashboards/noc_support.json` -- Scope 2: NOC support investigation board
- `grafana/dashboards/ship_operations.json` -- legacy telemetry dashboard

### Documentation
- `README.md` -- project overview and quick start
- `docs/architecture.md` -- system architecture
- `docs/ROADMAP.md` -- backlog and current priorities
- `docs/SCOPE2_TASK_SPLIT.md` -- Scope 2 task ownership and acceptance criteria
- `docs/SCOPE1_ACCEPTANCE_CHECKLIST.md` -- repeatable validation flow
- `docs/UDS_dashboard_spec.md` -- dashboard panel specifications
- `docs/knowledge/` -- RAG knowledge base (17 maritime reference files)

### Historical (in docs/archive/)
These are kept for reference but are no longer the active project docs:
- `docs/archive/SCOPE1_HANDOFF_NOTES.md`
- `docs/archive/SCOPE1_REVIEW_FINDINGS.md`
- `docs/archive/NEXT_STEPS.md`
- `docs/archive/FUTURE_CHECKS.md`
- `docs/archive/WORK_DISTRIBUTION.md`
- `docs/archive/underveisNotater.md`

## MCP Tools (12 total)

### Legacy (3 tools)
- `get_telemetry` -- raw telemetry query
- `get_events` -- event list with optional filters
- `get_analysis` -- retrieve AI analysis for an event

### UDS Scope 1 (4 tools)
- `get_vessel_app_status` -- all apps on one vessel with health status
- `get_vessel_alerts` -- active alerts for one vessel
- `get_app_metric_history` -- time-series metrics for one app on one vessel
- `get_app_logs` -- recent logs for one app on one vessel

### UDS Scope 2 (5 tools)
- `get_fleet_status` -- operational status of all vessels
- `get_fleet_alerts` -- fleet-wide active alerts with optional severity filter
- `get_cross_vessel_correlation` -- apps/alert types affecting multiple vessels
- `get_incident_timeline` -- chronological alerts + logs for one vessel
- `get_operational_snapshot` -- full vessel state for NOC support

## Important Conventions

### Code style
- All SQL in MCP/agent uses asyncpg parameterized queries ($1, $2), never f-strings
- Pydantic BaseModel for all MCP tool argument validation
- Each MCP tool needs: TOOLS definition, Pydantic model, handler function, TOOL_HANDLERS entry, HTTP endpoint
- Agent tool filtering: `UDS_FULL_TOOL_NAMES` set in analyze.py controls which MCP tools the agent can call

### Shared status definitions (must be consistent across all dashboards and tools)
- `healthy` = no active condition that currently affects actionability
- `degraded` = active alerts, freshness issues, or resource issues exist
- `critical` = effectively unavailable, or a severe active issue exists

### Seed data
- Scenario flags in uds_seed.sql assign deterministic states per vessel+app
- IMO9300001 has the most interesting scenarios (stale, down apps)
- data-quality-processor is stale on IMO9300001 AND degraded on IMO9300002 (cross-vessel correlation demo)
- Do not make everything red; keep scenarios believable for maritime domain

### Git workflow
- Never push directly to main
- Feature branches for each scope 2 task
- Fresh-stack validation (docker compose down -v) before any merge to main
- Keep docs updated in the same PR when behavior changes

## Folders That Are Local-Only (in .gitignore)

- `KristianEkstraFolder/` -- personal meeting notes and working docs
- `geirDatabasebiter/` -- Geir's original database reference files
- `tester/` -- test/simulation data
- `databasecodeFraGeir/` -- old Geir files

These are NOT part of the repo and should never be committed.

## When You Update This Project

If you add new MCP tools, dashboards, or make architectural changes:
1. Update this CLAUDE.md file
2. Update README.md if user-facing behavior changes
3. Update docs/ROADMAP.md if backlog items change
4. Update docs/SCOPE1_ACCEPTANCE_CHECKLIST.md if validation steps change
5. Keep docs/architecture.md current with the system design
