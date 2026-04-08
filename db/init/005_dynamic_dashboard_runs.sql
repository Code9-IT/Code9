-- =============================================================
-- Dynamic Dashboard Runs - Logging table
-- =============================================================
-- Tracks every dynamic dashboard trigger so the team can review
-- what was generated, when, and from which incident context.
--
-- Used by: Workstream B orchestrator (writes), Workstream C demo
-- scripts (reads/verifies), GET /api/v1/dynamic/status (reads).
-- =============================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS dynamic_dashboard_runs (
    id                        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at                TIMESTAMPTZ  NOT NULL DEFAULT timezone('UTC', now()),
    trigger_mode              VARCHAR(50)  NOT NULL,
    source_alert_fingerprint  VARCHAR(255),
    vessel_imo                VARCHAR(255) NOT NULL,
    app_external_id           VARCHAR(255) NOT NULL,
    alert_name                VARCHAR(255),
    severity                  VARCHAR(50),
    scenario_key              VARCHAR(100) NOT NULL,
    dashboard_uid             VARCHAR(255) NOT NULL,
    summary                   TEXT,
    used_tools_json           JSONB        NOT NULL DEFAULT '[]'::jsonb,
    dashboard_json            JSONB,
    dry_run                   BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_ddr_created_at
    ON dynamic_dashboard_runs (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ddr_vessel_imo
    ON dynamic_dashboard_runs (vessel_imo);

CREATE INDEX IF NOT EXISTS idx_ddr_scenario_key
    ON dynamic_dashboard_runs (scenario_key);

CREATE INDEX IF NOT EXISTS idx_ddr_dashboard_uid
    ON dynamic_dashboard_runs (dashboard_uid);
