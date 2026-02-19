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

| # | What | Status |
|---|------|--------|
| 1 | Real LLM (Ollama) with tool-calling loop | ✅ Done – Kristian |
| 2 | RAG that retrieves maritime docs for the LLM | ⬜ Nidal |
| 3 | MCP server exposing DB tools to the agent | ✅ Done – Onu |
| 4 | Polished dashboards with severity colours, filters, Analyse trigger | ⬜ Jonas |
| 5 | Human-in-the-loop flow visible end-to-end | ⬜ Needs Jonas + testing |

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
- Jonas: the analyse endpoint is `POST /api/v1/analyze` with `{"event_id": N}`.
  For a GET-based Grafana link, Jonas can coordinate to add a GET alias.

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
- Kristian: RAG context drops straight into the system prompt in `analyze.py` — nothing
  needs to change on Kristian's end. Just make sure `retrieve_context()` returns
  `RAGDocument` objects with `title` and `content`. Test together when Priority 1 is done.

---

## Jonas – Grafana Dashboards & UI

**You own:** `grafana/dashboards/ship_operations.json` and `grafana/dashboards/data_quality.json`

---

### Goal: 2 dashboards, 1 ship, 2 audiences

This is the core architectural decision from the Arnt/Knowit meeting (02.02.2026):

> *"Lag 2 dashboard for 2 forskjellige personer med 2 anvendelsesområder:
> skipsoperasjon og drift av teknologiplatformen."*

| Dashboard | File | Audience | Purpose |
|-----------|------|----------|---------|
| **Ship Operations** | `ship_operations.json` | Chief engineer / Captain | Vessel health — is anything broken right now? |
| **Data Quality** | `data_quality.json` | Telenor Maritime / data platform team | Platform integrity — is the data trustworthy? |

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

#### Detail rows (collapsed – expand to investigate)

**Row: Engine details**

| Panel | Sensors |
|-------|---------|
| Fuel rack position | `dg1_fuel_rack_pos` … `dg5_fuel_rack_pos` (mm, alarm >55) |
| Charge air temperature | `dg1_charge_air_temp` … `dg5_charge_air_temp` (°C, alarm >120) |
| Turbocharger speed | `dg1_tc_speed` … `dg5_tc_speed` (rpm, alarm >22 000) |
| Cooling water flow | `dg1_cw_in_flow` … `dg5_cw_in_flow` (m³/h, alarm <5) |

**Row: Fuel quality**

| Panel | Sensors |
|-------|---------|
| HFO booster flows | `hfo_booster_a_flow`, `hfo_booster_b_flow`, `hfo_booster_c_flow` (m³/h) |
| MGO booster flows | `mgo_booster_a_flow`, `mgo_booster_b_flow` (m³/h) |
| HFO temperature | `hfo_fuel_temp`, `hfo_fuel_temp_b`, `hfo_fuel_temp_c` (°C) |
| HFO viscosity | `hfo_fuel_viscosity`, `hfo_fuel_viscosity_b`, `hfo_fuel_viscosity_c` (cSt) |
| HFO density | `hfo_density`, `hfo_density_b` (kg/m³) |
| MGO density | `mgo_density_a`, `mgo_density_b` (kg/m³) |
| Boiler fuel flow | `boiler_fuel_flow_a`, `boiler_fuel_flow_b` (m³/h) |

**Row: Scrubbers (full)**

| Panel | Sensors |
|-------|---------|
| SO₂ | `scrubber_fwd_so2`, `scrubber_aft_so2` (ppm) |
| CO₂ | `scrubber_fwd_co2`, `scrubber_aft_co2` (%) |
| Wash water pH | `scrubber_fwd_ph`, `scrubber_aft_ph` (pH, alarm <6.0) |
| Power | `scrubber_fwd_power`, `scrubber_aft_power` (W) |
| PAH | `scrubber_fwd_pah`, `scrubber_aft_pah` (µg/l) |
| Sulphur content | `scrubber_fwd_sulphur`, `scrubber_aft_sulphur` (%, alarm ≥0.10) |

**Row: Lubrication & emergency**

| Panel | Sensors |
|-------|---------|
| LO supply flow | `clean_lo_flow` (L/min, alarm <3) |
| LO return flow | `dirty_lo_flow` (L/min, alarm >20) |
| EMDG speed | `emdg_speed` (rpm) |

---

### Dashboard 2 – Data Quality (Telenor Maritime)

#### Main view (always visible)

| Panel | Type | Query / purpose |
|-------|------|-----------------|
| Sensor coverage | Stat | Count of distinct `sensor_name` values seen in last 5 min |
| Data freshness | Stat | Time since last row in `telemetry` for this vessel |
| Event rate | Bar chart | Events per hour over last 24 h |
| Unacknowledged alarms | Table | `SELECT * FROM events WHERE acknowledged = false` |
| Latest AI analyses | Table | `SELECT * FROM ai_analyses ORDER BY timestamp DESC LIMIT 5` |

#### Detail rows (collapsed – expand to investigate)

**Row: Per-sensor freshness**

A table showing each sensor name and the timestamp of its most recent reading.
Highlight any sensor not seen in the last 30 seconds (generator runs every 3 s).

```sql
SELECT sensor_name,
       MAX(timestamp) AS last_seen,
       NOW() - MAX(timestamp) AS staleness
FROM   telemetry
WHERE  vessel_id = '$vessel'
GROUP  BY sensor_name
ORDER  BY staleness DESC;
```

**Row: Gap detection**

Identify time windows where fewer than the expected number of sensors reported:

```sql
SELECT time_bucket('1 minute', timestamp) AS bucket,
       COUNT(DISTINCT sensor_name)         AS sensors_seen
FROM   telemetry
WHERE  vessel_id = '$vessel'
  AND  timestamp > NOW() - INTERVAL '1 hour'
GROUP  BY bucket
ORDER  BY bucket;
```
Show as a bar chart — any bar below 73 (total sensors) = a data gap.

**Row: All alarm states**

A table of every event in the last 24 hours with severity colour-coding:
`critical` → red, `warning` → orange, `info` → green.

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

- [ ] **Vessel variable:** Add a `$vessel` Grafana variable to both dashboards.
      Use `SELECT DISTINCT vessel_id FROM telemetry` as the query.
      All panels use `WHERE vessel_id = '$vessel'`.
- [ ] **Severity colours:** In Events tables — `critical` → red, `warning` → orange.
- [ ] **Units** in `fieldConfig.defaults.unit`: rpm, MW, %, m3/h, tons, ppm, %, pH, m, knots,
      L/min, kg/m3, cSt, degC, W, µg/l.
- [ ] **Collapsed rows:** Use Grafana row panels with `collapsed: true` for the Detail rows
      so the main view loads clean.
- [ ] **"Analyse" trigger:** The endpoint is `POST http://localhost:8000/api/v1/analyze`
      with body `{"event_id": N}`. Since Grafana tables can't POST natively, use a
      **Data links** URL with `method=POST` or coordinate with Kristian to add a GET alias.
- [ ] **"Acknowledge" button:** POST to `/api/v1/events/{id}/acknowledge?operator=...`.
      Same approach as Analyse — data link or HTML panel button.

### No coordination needed (mostly)
You work entirely in `grafana/dashboards/`. Only exception: if you want a GET alias
for the Analyse trigger, ask Kristian. Everything else is self-contained.

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
- [ ] **New sensors** in `sensors.py`: add `nav_speed` (knots, baseline ~12, anomaly >25)
      and `rudder_angle` (degrees, baseline ~0, anomaly > ±20). Add matching event
      definitions in `anomalies.py`.
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

1. **Never push directly to `master`.** Always: `git checkout -b feat/<your-name>-<what>`
2. **Pull before you start.** `git pull origin master` at the beginning of every session.
3. **Keep PRs small.** One logical change per PR. Easier to review.
4. **If you need to touch someone else's file,** open an issue or Slack message first.

---

## Suggested group workflow

1. ✅ Kristian + Onu: core pipeline done. Pull `llama3.2` and verify end-to-end.
2. ⬜ **Nidal**: implement RAG (pgvector + docs). Test by checking that `analysis_text`
   in Grafana references the maritime documents.
3. ⬜ **Jonas**: polish dashboards. Add severity colours, vessel filter, Analyse trigger.
4. Group test together: `docker compose up --build` → trigger an event → click Analyse
   in Grafana → verify the full pipeline (generator → event → LLM analysis → dashboard).
5. Final: user stories, thesis writeup, demo preparation.
