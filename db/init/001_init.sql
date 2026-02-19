-- =============================================================
-- Maritime Observability – Database Schema
-- Engine: TimescaleDB (PostgreSQL extension)
-- =============================================================
-- Runs automatically on first container start via
-- /docker-entrypoint-initdb.d/.
-- To wipe & recreate:  docker compose down -v
-- =============================================================

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ─── TELEMETRY ───────────────────────────────────────────
-- Continuous sensor readings.  One row = one reading.
-- Sensor names are intentionally generic (see sensors.py).
CREATE TABLE IF NOT EXISTS telemetry (
    timestamp       TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    vessel_id       TEXT             NOT NULL,   -- e.g. 'vessel_001'
    sensor_name     TEXT             NOT NULL,   -- e.g. 'engine_temp'
    value           DOUBLE PRECISION NOT NULL
);

-- Turn into a hypertable so TimescaleDB partitions by time
SELECT create_hypertable('telemetry', 'timestamp',
       chunk_time_interval => INTERVAL '1 hour',
       migrate_data        => true,
       if_not_exists       => TRUE);

-- ─── EVENTS ──────────────────────────────────────────────
-- Threshold breaches / anomalies detected by the generator
-- (or, later, by a dedicated alerting rule).
-- Each event is the trigger that asks the AI agent to analyse.
CREATE TABLE IF NOT EXISTS events (
    id                  SERIAL      PRIMARY KEY,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    vessel_id           TEXT        NOT NULL,
    sensor_name         TEXT        NOT NULL,
    event_type          TEXT        NOT NULL,   -- 'HIGH_TEMPERATURE', 'LOW_OIL_PRESSURE', …
    severity            TEXT        NOT NULL DEFAULT 'warning',  -- info | warning | critical
    details             TEXT,                   -- free-text description

    -- Human-in-the-loop ──────────────────────────────────
    -- TODO: link acknowledged_by to a proper user/operator table
    acknowledged        BOOLEAN     DEFAULT FALSE,
    acknowledged_by     TEXT,
    acknowledged_at     TIMESTAMPTZ
);

-- ─── AI ANALYSES ─────────────────────────────────────────
-- Stores every response the agent produces for an event.
-- An event can be analysed more than once (retry / re-analyse).
CREATE TABLE IF NOT EXISTS ai_analyses (
    id                  SERIAL      PRIMARY KEY,
    event_id            INTEGER     REFERENCES events(id),
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_text       TEXT,                   -- LLM-generated explanation
    suggested_actions   TEXT[],                 -- array of action strings
    confidence          FLOAT,                  -- 0.0 – 1.0
    model_used          TEXT,                   -- e.g. 'ollama/llama3' or 'stub'
    status              TEXT        NOT NULL DEFAULT 'pending'  -- pending | completed | failed
);

-- ─── INDEXES ─────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_telemetry_vessel_time  ON telemetry  (vessel_id,  timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time  ON telemetry  (sensor_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_vessel_time     ON events     (vessel_id,  timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_unacked         ON events     (acknowledged) WHERE acknowledged = FALSE;
CREATE INDEX IF NOT EXISTS idx_analyses_event         ON ai_analyses(event_id);
