-- =============================================================
-- Maritime Observability - Database Schema
-- Engine: TimescaleDB (PostgreSQL extension)
-- =============================================================
-- Runs automatically on first container start via
-- /docker-entrypoint-initdb.d/.
-- To wipe and recreate: docker compose down -v
-- =============================================================

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- TELEMETRY
CREATE TABLE IF NOT EXISTS telemetry (
    timestamp       TIMESTAMPTZ      NOT NULL DEFAULT NOW(),
    vessel_id       TEXT             NOT NULL,
    sensor_name     TEXT             NOT NULL,
    value           DOUBLE PRECISION NOT NULL
);

SELECT create_hypertable(
    'telemetry',
    'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    migrate_data => true,
    if_not_exists => TRUE
);

-- EVENTS
CREATE TABLE IF NOT EXISTS events (
    id                  SERIAL      PRIMARY KEY,
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    vessel_id           TEXT        NOT NULL,
    sensor_name         TEXT        NOT NULL,
    event_type          TEXT        NOT NULL,
    severity            TEXT        NOT NULL DEFAULT 'warning',
    details             TEXT,
    acknowledged        BOOLEAN     DEFAULT FALSE,
    acknowledged_by     TEXT,
    acknowledged_at     TIMESTAMPTZ
);

-- AI ANALYSES
CREATE TABLE IF NOT EXISTS ai_analyses (
    id                  SERIAL      PRIMARY KEY,
    event_id            INTEGER     REFERENCES events(id),
    timestamp           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    analysis_mode       TEXT        NOT NULL DEFAULT 'full',
    analysis_text       TEXT,
    suggested_actions   TEXT[],
    confidence          FLOAT,
    model_used          TEXT,
    status              TEXT        NOT NULL DEFAULT 'pending'
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_telemetry_vessel_time
    ON telemetry (vessel_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_sensor_time
    ON telemetry (sensor_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_vessel_time
    ON events (vessel_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_events_unacked
    ON events (acknowledged) WHERE acknowledged = FALSE;
CREATE INDEX IF NOT EXISTS idx_analyses_event
    ON ai_analyses(event_id);
CREATE INDEX IF NOT EXISTS idx_analyses_event_mode
    ON ai_analyses(event_id, analysis_mode, timestamp DESC);
