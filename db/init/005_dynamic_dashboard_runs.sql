-- =============================================================
-- Maritime Observability - Dynamic Dashboard Runs (Scope 3.5)
-- =============================================================
-- One row per /api/v1/dynamic/trigger invocation. Acts as the audit
-- log for the dynamic-dashboard pivot so the demo flow can be
-- replayed and inspected after the fact.
--
-- Authoritative source of truth: this file. The runtime migration
-- in services/agent/main.py only runs ALTER TABLE ADD COLUMN IF NOT
-- EXISTS for the dry_run column to keep older volumes (created
-- before this column existed) compatible without a fresh init.
--
-- Schema shape matches the orchestrator INSERT in
-- services/agent/dynamic/orchestrator.py::_log_run().
-- =============================================================

CREATE TABLE IF NOT EXISTS dynamic_dashboard_runs (
    id                        BIGSERIAL    PRIMARY KEY,
    created_at                TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    trigger_mode              TEXT         NOT NULL,
    source_alert_fingerprint  VARCHAR(255),
    vessel_imo                VARCHAR(255) NOT NULL,
    app_external_id           VARCHAR(255),
    alert_name                VARCHAR(255),
    severity                  VARCHAR(50),
    scenario_key              VARCHAR(100) NOT NULL,
    dashboard_uid             VARCHAR(255) NOT NULL,
    summary                   TEXT         NOT NULL DEFAULT '',
    used_tools_json           JSONB        NOT NULL DEFAULT '[]'::jsonb,
    dashboard_json            JSONB        NOT NULL DEFAULT '{}'::jsonb,
    dry_run                   BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_runs_created_at
    ON dynamic_dashboard_runs (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_runs_vessel_app
    ON dynamic_dashboard_runs (vessel_imo, app_external_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_runs_scenario_key
    ON dynamic_dashboard_runs (scenario_key, created_at DESC);
