# Next Steps – Work Distribution

Personalized task list for the group. Each person owns a set of files.
The goal: no two people edit the same file at the same time, merge conflicts stay near zero.
For hardening/deployment backlog and post-RAG roadmap, see `docs/FUTURE_CHECKS.md`.

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

| # | What | Status |
|---|------|--------|
| 1 | Real LLM (Ollama) with tool-calling loop | ✅ Done – Kristian |
| 2 | RAG that retrieves maritime docs for the LLM | ✅ Done – Nidal (17 files, 76 chunks, end-to-end verified) |
| 3 | MCP server exposing DB tools to the agent | ✅ Done – Onu |
| 4 | Polished dashboards with severity colours, filters, Analyse trigger | IN_PROGRESS - core done (Jonas), polish ongoing |
| 5 | Human-in-the-loop flow visible end-to-end | IN_PROGRESS - links+agent done, final group testing remains |

---

## Kristian – LLM & Agent Core

**You own:** `services/agent/llm/ollama_client.py` and `services/agent/routes/analyze.py`

**Decision (18.02.2026):** We are using **Ollama locally** (free, no API key) with a
model that supports function calling: `llama3.2:3b` (light) or `llama3.1:8b` (better
quality, needs ~8 GB RAM). See `docs/underveisNotater.md` for full rationale.

### ✅ Priority 1 – connect real Ollama with tool calling (DONE 18.02.2026)

- [x] Ollama service enabled in `docker-compose.yml` with `ollama_data` volume.
- [x] `STUB_MODE` reads from env var (default `false`). Real Ollama call active.
- [x] Tool-calling loop implemented in `analyze.py`: Ollama decides which MCP tools
      to call, agent executes them, results sent back — loop repeats until final answer.
- [x] Model: `llama3.2` (pull with `docker exec -it maritime_ollama ollama pull llama3.2`)

### ✅ Priority 2 – structured output and parsing (DONE 18.02.2026)

- [x] System prompt asks for `**ANALYSIS:**`, `**CONFIDENCE:** N%`, `**SUGGESTED ACTIONS:**`
- [x] `_parse_confidence()` extracts the percentage → stored as 0.0–1.0 float
- [x] `_parse_suggested_actions()` extracts numbered list items
- [x] Failed analyses stored with `status='failed'` instead of crashing

### Coordinate with
- Nidal: RAG context goes directly into the system prompt. Once Nidal's docs are in,
  the LLM will reference them automatically — no changes needed in `analyze.py`.
- Jonas: analyse supports `POST /api/v1/analyze` with `{"event_id": N}` and
  Grafana-friendly `GET /api/v1/analyze/{event_id}`. Duplicate guard is default;
  use `force=true` for a fresh re-analysis.

---

## Nidal - RAG & Knowledge Base

**You own:** `services/agent/rag/client.py` and `docs/knowledge/`

### Priority 1 - RAG foundation

- [x] Decision: use **pgvector** in the existing TimescaleDB/Postgres service.
- [x] Added init script **`db/init/002_rag.sql`** with:
      - `CREATE EXTENSION IF NOT EXISTS vector;`
      - `knowledge_docs` table (`title`, `content`, `source`, `chunk_index`, `embedding`, `created_at`).
- [x] Added **`docs/knowledge/`** starter folder with authoring guide.
- [x] Added ingestion script **`services/agent/rag/ingest.py`** that:
      1. Reads all `.md` / `.txt` files in `docs/knowledge/`.
      2. Chunks text.
      3. Embeds chunks with Ollama (`nomic-embed-text`).
      4. Upserts rows into `knowledge_docs`.
- [x] Updated `retrieve_context()` in `rag/client.py`:
      1. Embeds query text.
      2. Runs pgvector similarity search.
      3. Returns top-K `RAGDocument` matches.
- [x] Agent startup auto-ingests when `knowledge_docs` is empty.

### ✅ Priority 2 – knowledge base content (DONE 2026-03-01)

- [x] 17 curated maritime knowledge files added to `docs/knowledge/` covering Points 1–10:
  - Point 1 (Ship systems): `main_engine.md`, `auxiliary_engines.md`, `fuel_system.md`,
    `cooling_system.md`, `electrical_system.md`, `propulsion_system.md`,
    `ballast_system.md`, `navigation_systems.md`, `p1_event_context.md`
  - Points 2–10: `p2_sensors_what_they_measure.md`, `p3_normal_values_thresholds.md`,
    `p4_alarm_types_cascading.md`, `p5_troubleshooting_procedures.md`,
    `p6_stale_missing_sensor_data.md`, `p8_data_quality_lineage.md`,
    `p9_maritime_regulations.md`, `p10_incident_analysis_reporting.md`
- [x] All sources verified as primary (IMO CDN, IACS, OEM). No mirror/aggregator links.
- [x] All IAS sensor tags cross-checked against `services/generator/sensors.py`.
- [x] Auto-ingest verified: 76 chunks in `knowledge_docs` on startup.
- [x] End-to-end test: `HIGH_DG5_CHARGE_AIR_TEMP` event returned grounded analysis
      with correct threshold (120°C) and root causes from `main_engine.md`.
- [x] Pushed to `origin/feat/kristian-updates` (commit `e1f6094`).

### Priority 3 – validate and tune (NEXT)

- [ ] Test retrieval quality for 5+ representative event types (fuel viscosity, scrubber SO₂,
      low LO flow, engine overload, low tank weight).
- [ ] Tune `RAG_TOP_K` and `RAG_MIN_SIMILARITY` in `.env` based on results.
- [ ] Point 7 (Application state): awaiting Geir's IAS scripts (meeting 03.03.2026).
- [ ] Point 11 (Color Line/Knowit-specific): awaiting documents from Color Line.

### Coordinate with
- Kristian: RAG context already plugs into `analyze.py` system prompt — no changes needed.
- Jonas: AI analysis quality in Grafana table should now show maritime-grounded answers.

---

## Jonas - Grafana Dashboards & UI

**You own:** `grafana/dashboards/ship_operations.json` and `grafana/dashboards/uds_monitoring.json`

---

### Goal: 2 dashboards, 1 ship, 2 audiences

This is the core architectural decision from the Arnt/Knowit meeting (02.02.2026):

> *"Lag 2 dashboard for 2 forskjellige personer med 2 anvendelsesområder:
> skipsoperasjon og drift av teknologiplatformen."*

| Dashboard | File | Audience | Purpose |
|-----------|------|----------|---------|
| **Ship Operations** | `ship_operations.json` | Chief engineer / Captain | Vessel health — is anything broken right now? |
| **UDS Monitoring** | `uds_monitoring.json` | Knowit / land-operatører | UDS app health — which applications need attention right now? |

**Each dashboard must have two levels of detail:**
- **Main view** — the most important panels visible immediately on load.
  One screen, no scrolling. KPIs and active alarms only.
- **Detail rows** (collapsed by default, expand on click) — all remaining sensors
  grouped by subsystem. Useful when investigating a specific issue.

---

### Dashboard 1 – Ship Operations (chief engineer)

#### Main view (always visible)

| Panel | Type | Sensors / query |
|-------|------|-----------------|
| DG engine speeds | Time-series | `dg1_engine_speed` … `dg5_engine_speed` (rpm) |
| DG power output | Time-series | `dg1_power_mw` … `dg5_power_mw` (MW) |
| DG engine load | Gauge × 5 | `dg1_engine_load` … `dg5_engine_load` (%) — red at 90% |
| Fuel tanks | Stat / gauge | `hfo_tank_weight` (low alarm 500 t), `mgo_tank_weight` (low alarm 200 t) |
| Scrubber emissions | Time-series | `scrubber_fwd_so2`, `scrubber_aft_so2` (ppm) — red at 400 ppm |
| Speed & depth | Time-series | `vessel_speed` (knots), `water_depth` (m) — red at 15 m |
| Active alarms | Table | `SELECT * FROM events WHERE acknowledged = false ORDER BY timestamp DESC LIMIT 10` |

#### Detail rows (collapsed - expand to investigate)

For Scope 1, the replacement dashboard is grouped by UDS application health:
- Availability
- Resources
- HTTP and exceptions
- Database
- Active alerts

Each detail row is a table over the Geir schema tables `metric_samples`,
`alerts`, `udslocations`, `applications`, and
`uds_location_application_instances` for one selected vessel.

See `docs/UDS_dashboard_spec.md` and `grafana/queries/uds_queries.sql` for the
actual dashboard structure and SQL used in the implementation.

---

### Dashboard 2 – UDS Monitoring (Knowit / land-operasjon)

#### Main view (always visible)

| Panel | Type | Query / purpose |
|-------|------|-----------------|
| Active alerts | Stat | Count of unresolved rows in `alerts` for selected `imo_nr` |
| Apps with issues | Stat | Derived from latest `service_up`, `health_check_status`, and alert count |
| Apps reporting | Stat | Distinct `application_instance_id` seen in `metric_samples` over last 35 min |
| Latest metric age | Stat | Time since newest `metric_samples.time` for selected `imo_nr` |
| Application status summary | Table | Latest per-app status, CPU, memory, error rate, DB errors |

#### Detail rows (collapsed - expand to investigate)

For Scope 1, the replacement dashboard is grouped by UDS application health:
- Availability
- Resources
- HTTP and exceptions
- Database
- Active alerts

Each detail row is a table over the Geir schema tables `metric_samples`,
`alerts`, `udslocations`, `applications`, and
`uds_location_application_instances` for one selected vessel.

See `docs/UDS_dashboard_spec.md` and `grafana/queries/uds_queries.sql` for the
actual dashboard structure and SQL used in the implementation.

---

### Complete sensor list for reference

Use these exact `sensor_name` values in your SQL (`WHERE sensor_name = '...'`).

**DG engines (DG1–DG5, 35 sensors)**
```
dg1_engine_speed    dg2_engine_speed    dg3_engine_speed    dg4_engine_speed    dg5_engine_speed
dg1_power_mw        dg2_power_mw        dg3_power_mw        dg4_power_mw        dg5_power_mw
dg1_fuel_rack_pos   dg2_fuel_rack_pos   dg3_fuel_rack_pos   dg4_fuel_rack_pos   dg5_fuel_rack_pos
dg1_charge_air_temp dg2_charge_air_temp dg3_charge_air_temp dg4_charge_air_temp dg5_charge_air_temp
dg1_tc_speed        dg2_tc_speed        dg3_tc_speed        dg4_tc_speed        dg5_tc_speed
dg1_cw_in_flow      dg2_cw_in_flow      dg3_cw_in_flow      dg4_cw_in_flow      dg5_cw_in_flow
dg1_engine_load     dg2_engine_load     dg3_engine_load     dg4_engine_load     dg5_engine_load
```

**Fuel system (19 sensors)**
```
hfo_booster_a_flow  hfo_booster_b_flow  hfo_booster_c_flow
mgo_booster_a_flow  mgo_booster_b_flow
hfo_tank_weight     mgo_tank_weight
hfo_fuel_temp       hfo_fuel_temp_b     hfo_fuel_temp_c
hfo_fuel_viscosity  hfo_fuel_viscosity_b  hfo_fuel_viscosity_c
hfo_density         hfo_density_b
mgo_density_a       mgo_density_b
boiler_fuel_flow_a  boiler_fuel_flow_b
```

**Scrubbers FWD + AFT (12 sensors)**
```
scrubber_fwd_so2    scrubber_aft_so2
scrubber_fwd_co2    scrubber_aft_co2
scrubber_fwd_ph     scrubber_aft_ph
scrubber_fwd_power  scrubber_aft_power
scrubber_fwd_pah    scrubber_aft_pah
scrubber_fwd_sulphur  scrubber_aft_sulphur
```

**Lubrication & emergency (3 sensors)**
```
clean_lo_flow   dirty_lo_flow   emdg_speed
```

**Navigation (4 sensors)**
```
water_depth   vessel_speed   vessel_latitude   vessel_longitude
```

Total: **73 sensors** — all are in `telemetry`. `vessel_latitude` and `vessel_longitude`
have no alarm thresholds (informational only).

---

### Implementation checklist

- [x] **Vessel variable:** `$vessel` is used in both dashboards.
      Use `SELECT DISTINCT vessel_id FROM telemetry` as the query.
      All panels use `WHERE vessel_id = '$vessel'`.
- [x] **Severity colours:** Events tables use `critical` -> red, `warning` -> orange.
- [x] **Units** in `fieldConfig.defaults.unit` / overrides: rpm, MW, %, m3/h, tons, ppm, %, pH, m, knots,
      L/min, kg/m3, cSt, degC, W, µg/l.
- [x] **Collapsed rows:** Detail rows are configured with `collapsed: true` for the Detail rows
      so the main view loads clean.
- [x] **"Analyse" trigger:** Data links are wired to
      `GET http://localhost:8000/api/v1/analyze/{event_id}`.
      Use `?force=true` if you need a fresh re-analysis for an already-analysed event.
- [x] **"Acknowledge" button:** Data links are wired to
      `GET /api/v1/events/{id}/acknowledge?operator=...` (GET alias to POST endpoint).

### No coordination needed (mostly)
You work primarily in `grafana/dashboards/`. GET aliases for Analyse/Acknowledge
are already implemented in agent routes.

---

## Onu – MCP Server & Data Pipeline

**You own:** `services/mcp/` and `services/generator/`

### Priority 1 – MCP server ✅ DONE (18.02.2026)

`services/mcp/` is implemented and merged into main. It exposes three tools:
- `get_telemetry` — last N minutes of sensor readings for a vessel
- `get_events`    — recent anomaly events (optional vessel/acknowledged filter)
- `get_analysis`  — latest AI analysis for a given event_id

The service runs on port 8001 and is wired into `docker-compose.yml`.
Kristian's agent can call tools via `POST http://mcp:8001/tools/call`.

**Note on protocol:** The current implementation is a REST adapter (not the official
MCP wire protocol). This is intentional and sufficient for our architecture since
Ollama does not natively speak MCP. See `docs/underveisNotater.md` for details.

### Priority 2 – generator enhancements

- [ ] **Burst mode** in `services/generator/anomalies.py`: add an env var `BURST_MODE`
      (default `false`). When `true`, every cycle fires 3–5 anomalies across different
      sensors/vessels. Useful for live demos.
- [ ] **Time weighting** in `anomalies.py`: make anomalies slightly more likely during
      certain hours (e.g. simulate higher load during 06:00–14:00 UTC).
- [ ] Update `docker-compose.yml` generator env block with the new `BURST_MODE` var (PR).

### Coordinate with
- Kristian: the tool-calling loop is live. The agent already calls your MCP tools
  automatically when Ollama requests them. No further changes needed on your end
  unless you want to add more tools (e.g. `get_telemetry_stats`).

---

## Shared-file rules (everyone reads this)

| Shared file                      | Who will touch it   | How to handle                          |
|----------------------------------|---------------------|----------------------------------------|
| `docker-compose.yml`             | Kristian, Onu       | Each opens a separate PR. Do not merge both at the same time. |
| `db/init/` (new init scripts)    | Nidal (`002`), Onu (maybe `003`) | Use different numbered files. |
| `services/agent/requirements.txt`| Nidal               | Branch + PR.                           |
| `.env.example`                   | Kristian            | Branch + PR. Others pull before adding their own vars. |

1. **Never push directly to `main`.** Always: `git checkout -b feat/<your-name>-<what>`
2. **Pull before you start.** `git pull origin main` at the beginning of every session.
3. **Keep PRs small.** One logical change per PR. Easier to review.
4. **If you need to touch someone else's file,** open an issue or Slack message first.

---

## Suggested group workflow

1. ✅ Kristian + Onu: core pipeline done. Pull `llama3.2` and verify end-to-end.
2. ✅ **Nidal**: RAG complete (17 files, 76 chunks, end-to-end verified). Next: validate retrieval quality across event types and tune `RAG_TOP_K` / `RAG_MIN_SIMILARITY`.
3. IN_PROGRESS **Jonas**: continue dashboard polish (UI/readability + demo tweaks). Core triggers are in place.
4. Group test together: `docker compose up --build` → trigger an event → click Analyse
   in Grafana → verify the full pipeline (generator → event → LLM analysis → dashboard).
5. Final: user stories, thesis writeup, demo preparation.



