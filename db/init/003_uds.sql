-- =============================================================
-- Maritime Observability - Scope 1 UDS schema
-- =============================================================
-- Adds Geir's UDS-oriented tables alongside the existing prototype
-- schema in 001_init.sql. Runs automatically on first DB init only.
--
-- Notes:
-- - The existing telemetry / events / ai_analyses schema must stay intact.
-- - metric_samples is modeled as a TimescaleDB hypertable on "time".
-- - A minimal monitoring_configs table is included as a compatibility shim
--   because Geir's init script inserts into it even though it is not present
--   in the DBML and is not used by Scope 1 dashboards or MCP tools.
-- - metric_samples includes imo_nr in the primary key so one sync run can
--   store the same app_id / metric_name / time across multiple vessels.
-- =============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- -------------------------------------------------------------
-- Core reference tables
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS owners (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(255) NOT NULL UNIQUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now())
);

CREATE TABLE IF NOT EXISTS udslocations (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id  VARCHAR(255) NOT NULL,
    name         VARCHAR(255) NOT NULL,
    imo_nr       VARCHAR(255) UNIQUE,
    owner_id     UUID REFERENCES owners(id),
    owner_from   TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now())
);

CREATE INDEX IF NOT EXISTS idx_udslocations_external_id
    ON udslocations (external_id);

CREATE INDEX IF NOT EXISTS idx_udslocations_name
    ON udslocations (name);

CREATE INDEX IF NOT EXISTS idx_udslocations_owner_id
    ON udslocations (owner_id);

CREATE TABLE IF NOT EXISTS applications (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    external_id  VARCHAR(255) NOT NULL UNIQUE,
    name         VARCHAR(255) NOT NULL,
    app_type     VARCHAR(255),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now())
);

CREATE INDEX IF NOT EXISTS idx_applications_name
    ON applications (name);

CREATE TABLE IF NOT EXISTS uds_location_application_instances (
    uds_location_id           UUID NOT NULL REFERENCES udslocations(id) ON DELETE CASCADE,
    application_instance_id   UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    PRIMARY KEY (uds_location_id, application_instance_id)
);

CREATE INDEX IF NOT EXISTS idx_uai_uds_location_id
    ON uds_location_application_instances (uds_location_id);

CREATE INDEX IF NOT EXISTS idx_uai_application_instance_id
    ON uds_location_application_instances (application_instance_id);

-- -------------------------------------------------------------
-- Time-series metrics
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metric_samples (
    sync_id                   UUID         NOT NULL,
    app_id                    VARCHAR(255) NOT NULL,
    metric_name               VARCHAR(255) NOT NULL,
    time                      TIMESTAMPTZ  NOT NULL,
    application_instance_id   UUID REFERENCES applications(id) ON DELETE SET NULL,
    value                     DOUBLE PRECISION NOT NULL,
    min_value                 DOUBLE PRECISION,
    max_value                 DOUBLE PRECISION,
    metric_type               VARCHAR(50)  NOT NULL,
    metric_unit               VARCHAR(50)  NOT NULL,
    imo_nr                    VARCHAR(255) NOT NULL,
    labels                    JSONB,
    PRIMARY KEY (sync_id, imo_nr, app_id, metric_name, time),
    CONSTRAINT chk_metric_samples_value_range
        CHECK (max_value IS NULL OR min_value IS NULL OR max_value >= min_value)
);

SELECT create_hypertable(
    'metric_samples',
    'time',
    chunk_time_interval => INTERVAL '1 day',
    migrate_data        => TRUE,
    if_not_exists       => TRUE
);

CREATE INDEX IF NOT EXISTS idx_metric_samples_imo_time
    ON metric_samples (imo_nr, time DESC);

CREATE INDEX IF NOT EXISTS idx_metric_samples_app_metric_time
    ON metric_samples (app_id, metric_name, time DESC);

CREATE INDEX IF NOT EXISTS idx_metric_samples_application_instance_time
    ON metric_samples (application_instance_id, time DESC);

CREATE INDEX IF NOT EXISTS idx_metric_samples_imo_app_instance_metric_time
    ON metric_samples (imo_nr, application_instance_id, metric_name, time DESC);

CREATE INDEX IF NOT EXISTS idx_metric_samples_sync_id
    ON metric_samples (sync_id);

-- -------------------------------------------------------------
-- Alerts
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uds_location_id  UUID         NOT NULL REFERENCES udslocations(id) ON DELETE CASCADE,
    application_id   UUID REFERENCES applications(id) ON DELETE SET NULL,
    alert_name       VARCHAR(255) NOT NULL,
    severity         VARCHAR(50)  NOT NULL,
    status           VARCHAR(50)  NOT NULL DEFAULT 'firing',
    alert_type       VARCHAR(100) NOT NULL,
    fingerprint      VARCHAR(255) NOT NULL,
    labels           JSONB,
    annotations      JSONB,
    starts_at        TIMESTAMPTZ  NOT NULL,
    ends_at          TIMESTAMPTZ,
    received_at      TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    CONSTRAINT chk_alerts_time_window
        CHECK (ends_at IS NULL OR ends_at >= starts_at)
);

CREATE INDEX IF NOT EXISTS idx_alerts_uds_location_id
    ON alerts (uds_location_id);

CREATE INDEX IF NOT EXISTS idx_alerts_application_id
    ON alerts (application_id);

CREATE INDEX IF NOT EXISTS idx_alerts_alert_name
    ON alerts (alert_name);

CREATE INDEX IF NOT EXISTS idx_alerts_severity
    ON alerts (severity);

CREATE INDEX IF NOT EXISTS idx_alerts_status
    ON alerts (status);

CREATE INDEX IF NOT EXISTS idx_alerts_alert_type
    ON alerts (alert_type);

CREATE INDEX IF NOT EXISTS idx_alerts_starts_at
    ON alerts (starts_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_received_at
    ON alerts (received_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_fingerprint
    ON alerts (fingerprint);

CREATE INDEX IF NOT EXISTS idx_alerts_uds_location_starts_at
    ON alerts (uds_location_id, starts_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_uds_location_status_starts_at
    ON alerts (uds_location_id, status, starts_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_application_starts_at
    ON alerts (application_id, starts_at DESC);

CREATE INDEX IF NOT EXISTS idx_alerts_severity_status_received_at
    ON alerts (severity, status, received_at DESC);

-- -------------------------------------------------------------
-- Ownership history
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS uds_location_owner_history (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    uds_location_id  UUID        NOT NULL REFERENCES udslocations(id) ON DELETE CASCADE,
    owner_id         UUID        NOT NULL REFERENCES owners(id) ON DELETE RESTRICT,
    owner_from       TIMESTAMPTZ NOT NULL,
    owner_to         TIMESTAMPTZ,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT timezone('UTC', now()),
    CONSTRAINT chk_uds_location_owner_history_window
        CHECK (owner_to IS NULL OR owner_to >= owner_from)
);

CREATE INDEX IF NOT EXISTS idx_uds_location_owner_history_location
    ON uds_location_owner_history (uds_location_id);

CREATE INDEX IF NOT EXISTS idx_uds_location_owner_history_owner
    ON uds_location_owner_history (owner_id);

CREATE INDEX IF NOT EXISTS idx_uds_location_owner_history_owner_from
    ON uds_location_owner_history (owner_from DESC);

CREATE INDEX IF NOT EXISTS idx_uds_location_owner_history_owner_to
    ON uds_location_owner_history (owner_to DESC);

-- -------------------------------------------------------------
-- Compatibility shim for Geir's init script
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS monitoring_configs (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    imo_number              VARCHAR(255) NOT NULL UNIQUE REFERENCES udslocations(imo_nr) ON DELETE CASCADE,
    monitoring_config_json  JSONB        NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    updated_at              TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    updated_by              VARCHAR(255) NOT NULL DEFAULT 'system'
);
