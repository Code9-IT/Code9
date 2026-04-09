CREATE TABLE IF NOT EXISTS dynamic_dashboard_runs (
    id                        BIGSERIAL PRIMARY KEY,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT timezone('UTC', now()),
    trigger_mode              TEXT NOT NULL,
    source_alert_fingerprint  VARCHAR(255),
    vessel_imo                VARCHAR(255) NOT NULL,
    app_external_id           VARCHAR(255),
    alert_name                VARCHAR(255),
    severity                  VARCHAR(50),
    scenario_key              VARCHAR(100) NOT NULL,
    dashboard_uid             VARCHAR(255) NOT NULL,
    summary                   TEXT NOT NULL DEFAULT '',
    used_tools_json           JSONB NOT NULL DEFAULT '[]'::jsonb,
    dashboard_json            JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_runs_created_at
    ON dynamic_dashboard_runs (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_dynamic_dashboard_runs_vessel_app
    ON dynamic_dashboard_runs (vessel_imo, app_external_id, created_at DESC);
