BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Scope 1 seeded app states:
-- - healthy
-- - degraded
-- - down
-- - stale
-- - delayed
--
-- The goal is not perfect realism. The goal is to make the demo show:
-- - app health variation
-- - non-critical incident context
-- - freshness/connectivity constraints
-- - more than just ServiceDown alerts

WITH
sync_run AS (
  SELECT
    gen_random_uuid() AS sync_id,
    date_trunc('minute', timezone('UTC', now())) AS sync_time_utc
),
app_instances AS (
  SELECT
    u.imo_nr,
    u.id AS uds_location_id,
    a.id AS application_instance_id,
    a.external_id AS app_id,
    a.name AS app_name,
    CASE a.external_id
      WHEN 'time-series-processor' THEN 'uds-edge-time-series-processor'
      WHEN 'data-quality-processor' THEN 'uds-data-quality-processor'
      WHEN 'uds-topic-handler-edge' THEN 'uds-topic-handler-edge'
      WHEN 'uds-edge-data-api' THEN 'uds-edge-data-api'
      WHEN 'uds-edge-ingest-source-admin' THEN 'uds-edge-ingest-source-admin'
      WHEN 'uds-edge-parquet-sync' THEN 'uds-edge-parquet-sync'
      ELSE a.external_id
    END AS job_name
  FROM uds_location_application_instances uai
  JOIN udslocations u ON u.id = uai.uds_location_id
  JOIN applications a ON a.id = uai.application_instance_id
  WHERE u.imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
    AND a.external_id IN (
      'time-series-processor',
      'data-quality-processor',
      'uds-topic-handler-edge',
      'uds-edge-data-api',
      'uds-edge-ingest-source-admin',
      'uds-edge-parquet-sync'
    )
),
metric_defs AS (
  SELECT * FROM (VALUES
    ('service_up', 'Application', 'Count', 'AGGREGATED'::text),
    ('health_check_status', 'Application', 'Count', 'AGGREGATED'::text),
    ('process_uptime_seconds', 'Application', 'Seconds', 'AGGREGATED'::text),
    ('http_request_duration_p95', 'Application', 'Seconds', 'AGGREGATED'::text),
    ('http_error_rate_5xx', 'Application', 'Percent', 'INTERVAL'::text),
    ('http_error_rate_4xx', 'Application', 'Percent', 'INTERVAL'::text),
    ('dotnet_exceptions_rate', 'Application', 'Count', 'AGGREGATED'::text),
    ('process_cpu_usage', 'Application', 'Percent', 'INTERVAL'::text),
    ('process_memory_bytes', 'Application', 'Bytes', 'INTERVAL'::text),
    ('process_open_handles', 'Application', 'Count', 'AGGREGATED'::text),
    ('db_query_duration_avg', 'Database', 'Seconds', 'AGGREGATED'::text),
    ('db_query_duration_p95', 'Database', 'Seconds', 'AGGREGATED'::text),
    ('db_query_rate', 'Database', 'Count', 'AGGREGATED'::text),
    ('db_query_errors', 'Database', 'Count', 'AGGREGATED'::text),
    ('db_deadlocks', 'Database', 'Count', 'AGGREGATED'::text),
    ('last_sync_age_seconds', 'Connectivity', 'Seconds', 'AGGREGATED'::text),
    ('reporting_stale', 'Connectivity', 'Count', 'AGGREGATED'::text),
    ('sync_delayed', 'Connectivity', 'Count', 'AGGREGATED'::text)
  ) v(metric_name, metric_type, metric_unit, query_type)
),
scenario_flags AS (
  SELECT
    ai.*,
    CASE
      WHEN ai.imo_nr = 'IMO9300001' AND ai.app_id = 'uds-edge-data-api' THEN 'delayed'
      WHEN ai.imo_nr = 'IMO9300001' AND ai.app_id = 'data-quality-processor' THEN 'stale'
      WHEN ai.imo_nr = 'IMO9300002' AND ai.app_id = 'uds-edge-parquet-sync' THEN 'down'
      WHEN ai.imo_nr = 'IMO9300003' AND ai.app_id = 'time-series-processor' THEN 'degraded'
      WHEN scenario_roll < 0.08 THEN 'down'
      WHEN scenario_roll < 0.24 THEN 'degraded'
      WHEN scenario_roll < 0.34 THEN 'stale'
      WHEN scenario_roll < 0.44 THEN 'delayed'
      ELSE 'healthy'
    END AS scenario
  FROM (
    SELECT
      ai.*,
      (
        (
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 0)::bigint * 16777216 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 1)::bigint * 65536 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 2)::bigint * 256 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 3)::bigint
        ) / 4294967295.0
      ) AS scenario_roll
    FROM app_instances ai
    CROSS JOIN sync_run sr
  ) ai
),
expanded AS (
  SELECT
    sr.sync_id,
    sr.sync_time_utc,
    sf.imo_nr,
    sf.app_id,
    sf.app_name,
    sf.job_name,
    sf.application_instance_id,
    sf.scenario,
    md.metric_name,
    md.metric_type,
    md.metric_unit,
    md.query_type,
    CASE
      WHEN sf.scenario = 'stale' AND md.query_type = 'AGGREGATED' THEN sr.sync_time_utc - interval '50 minutes'
      WHEN sf.scenario = 'delayed' AND md.query_type = 'AGGREGATED' THEN sr.sync_time_utc - interval '15 minutes'
      WHEN md.query_type = 'AGGREGATED' THEN sr.sync_time_utc
      ELSE t.sample_time
    END AS sample_time
  FROM sync_run sr
  JOIN scenario_flags sf ON true
  CROSS JOIN metric_defs md
  LEFT JOIN LATERAL (
    SELECT sample_time
    FROM (
      VALUES
        (
          CASE
            WHEN sf.scenario = 'stale' THEN sr.sync_time_utc - interval '70 minutes'
            WHEN sf.scenario = 'delayed' THEN sr.sync_time_utc - interval '30 minutes'
            ELSE sr.sync_time_utc - interval '20 minutes'
          END
        ),
        (
          CASE
            WHEN sf.scenario = 'stale' THEN sr.sync_time_utc - interval '55 minutes'
            WHEN sf.scenario = 'delayed' THEN sr.sync_time_utc - interval '20 minutes'
            ELSE sr.sync_time_utc - interval '10 minutes'
          END
        ),
        (
          CASE
            WHEN sf.scenario = 'stale' THEN sr.sync_time_utc - interval '40 minutes'
            WHEN sf.scenario = 'delayed' THEN sr.sync_time_utc - interval '10 minutes'
            ELSE sr.sync_time_utc
          END
        )
    ) samples(sample_time)
    WHERE md.query_type = 'INTERVAL'
      AND (
        sf.scenario <> 'delayed'
        OR sample_time <> sr.sync_time_utc
      )
  ) t ON true
),
values_calc AS (
  SELECT
    e.sync_id,
    e.app_id,
    e.metric_name,
    e.sample_time AS time,
    e.application_instance_id,
    e.metric_type,
    e.metric_unit,
    e.imo_nr,
    jsonb_build_object(
      'job', e.job_name,
      'app_id', e.app_id,
      'app_name', e.app_name,
      'imo', e.imo_nr,
      'source', 'mock_collector',
      'scenario', e.scenario
    ) AS labels,
    CASE e.metric_name
      WHEN 'service_up' THEN
        CASE WHEN e.scenario = 'down' THEN 0.0 ELSE 1.0 END
      WHEN 'health_check_status' THEN
        CASE WHEN e.scenario = 'down' THEN 0.0 ELSE 1.0 END
      WHEN 'process_uptime_seconds' THEN
        CASE
          WHEN e.scenario = 'down' THEN GREATEST(0.0, 120.0 + random() * 900.0)
          WHEN e.scenario = 'delayed' THEN 1800.0 + random() * 5400.0
          ELSE 3600.0 + random() * 14400.0
        END
      WHEN 'http_request_duration_p95' THEN
        CASE
          WHEN e.scenario = 'down' THEN 2.5 + random() * 3.5
          WHEN e.scenario = 'degraded' THEN 0.8 + random() * 1.4
          WHEN e.scenario = 'delayed' THEN 0.4 + random() * 0.9
          WHEN e.scenario = 'stale' THEN 0.1 + random() * 0.4
          ELSE 0.04 + random() * 0.25
        END
      WHEN 'http_error_rate_5xx' THEN
        CASE
          WHEN e.scenario = 'down' THEN 25.0 + random() * 45.0
          WHEN e.scenario = 'degraded' THEN 3.0 + random() * 8.0
          WHEN e.scenario = 'delayed' THEN 0.8 + random() * 2.0
          ELSE random() * 1.0
        END
      WHEN 'http_error_rate_4xx' THEN
        CASE
          WHEN e.scenario = 'down' THEN 8.0 + random() * 18.0
          WHEN e.scenario = 'degraded' THEN 2.5 + random() * 6.0
          WHEN e.scenario = 'delayed' THEN 1.0 + random() * 2.0
          ELSE 0.2 + random() * 1.8
        END
      WHEN 'dotnet_exceptions_rate' THEN
        CASE
          WHEN e.scenario = 'down' THEN 2.0 + random() * 6.0
          WHEN e.scenario = 'degraded' THEN 0.6 + random() * 2.0
          WHEN e.scenario = 'delayed' THEN 0.3 + random() * 0.9
          ELSE random() * 0.5
        END
      WHEN 'process_cpu_usage' THEN
        CASE
          WHEN e.scenario = 'down' THEN 75.0 + random() * 20.0
          WHEN e.scenario = 'degraded' THEN 60.0 + random() * 22.0
          WHEN e.scenario = 'delayed' THEN 30.0 + random() * 18.0
          ELSE 8.0 + random() * 35.0
        END
      WHEN 'process_memory_bytes' THEN
        CASE
          WHEN e.scenario = 'down' THEN 900000000.0 + random() * 1300000000.0
          WHEN e.scenario = 'degraded' THEN 700000000.0 + random() * 900000000.0
          WHEN e.scenario = 'delayed' THEN 500000000.0 + random() * 600000000.0
          ELSE 350000000.0 + random() * 750000000.0
        END
      WHEN 'process_open_handles' THEN
        CASE
          WHEN e.scenario = 'down' THEN 1600.0 + random() * 2200.0
          WHEN e.scenario = 'degraded' THEN 900.0 + random() * 1200.0
          WHEN e.scenario = 'delayed' THEN 500.0 + random() * 600.0
          ELSE 220.0 + random() * 650.0
        END
      WHEN 'db_query_duration_avg' THEN
        CASE
          WHEN e.scenario = 'down' THEN 0.3 + random() * 0.7
          WHEN e.scenario = 'degraded' THEN 0.09 + random() * 0.25
          WHEN e.scenario = 'delayed' THEN 0.05 + random() * 0.14
          ELSE 0.01 + random() * 0.09
        END
      WHEN 'db_query_duration_p95' THEN
        CASE
          WHEN e.scenario = 'down' THEN 1.0 + random() * 2.8
          WHEN e.scenario = 'degraded' THEN 0.3 + random() * 0.9
          WHEN e.scenario = 'delayed' THEN 0.15 + random() * 0.45
          ELSE 0.04 + random() * 0.3
        END
      WHEN 'db_query_rate' THEN
        CASE
          WHEN e.scenario = 'down' THEN random() * 4.0
          WHEN e.scenario = 'stale' THEN random() * 3.0
          WHEN e.scenario = 'delayed' THEN 4.0 + random() * 18.0
          ELSE 12.0 + random() * 110.0
        END
      WHEN 'db_query_errors' THEN
        CASE
          WHEN e.scenario = 'down' THEN 1.0 + random() * 10.0
          WHEN e.scenario = 'degraded' THEN 0.5 + random() * 3.0
          WHEN e.scenario = 'delayed' THEN 0.1 + random() * 1.0
          ELSE random() * 0.4
        END
      WHEN 'db_deadlocks' THEN
        CASE
          WHEN e.scenario = 'degraded' AND random() < 0.25 THEN 1.0
          WHEN e.scenario = 'down' AND random() < 0.15 THEN 1.0
          ELSE 0.0
        END
      WHEN 'last_sync_age_seconds' THEN
        CASE
          WHEN e.scenario = 'stale' THEN 2400.0 + random() * 3600.0
          WHEN e.scenario = 'delayed' THEN 600.0 + random() * 900.0
          WHEN e.scenario = 'degraded' THEN 60.0 + random() * 180.0
          WHEN e.scenario = 'down' THEN 90.0 + random() * 300.0
          ELSE random() * 60.0
        END
      WHEN 'reporting_stale' THEN
        CASE WHEN e.scenario = 'stale' THEN 1.0 ELSE 0.0 END
      WHEN 'sync_delayed' THEN
        CASE WHEN e.scenario = 'delayed' THEN 1.0 ELSE 0.0 END
      ELSE random() * 10.0
    END::double precision AS value,
    CASE
      WHEN e.query_type = 'AGGREGATED'
        AND e.metric_name NOT IN ('service_up', 'health_check_status', 'reporting_stale', 'sync_delayed')
      THEN random() * 0.12
      ELSE NULL
    END::double precision AS min_jitter,
    CASE
      WHEN e.query_type = 'AGGREGATED'
        AND e.metric_name NOT IN ('service_up', 'health_check_status', 'reporting_stale', 'sync_delayed')
      THEN random() * 0.12
      ELSE NULL
    END::double precision AS max_jitter
  FROM expanded e
)
INSERT INTO metric_samples (
  sync_id,
  app_id,
  metric_name,
  time,
  application_instance_id,
  value,
  min_value,
  max_value,
  metric_type,
  metric_unit,
  imo_nr,
  labels
)
SELECT
  v.sync_id,
  v.app_id,
  v.metric_name,
  v.time,
  v.application_instance_id,
  GREATEST(0.0, v.value) AS value,
  CASE
    WHEN v.min_jitter IS NULL THEN NULL
    ELSE GREATEST(0.0, v.value - (v.value * (0.05 + v.min_jitter)))
  END AS min_value,
  CASE
    WHEN v.max_jitter IS NULL THEN NULL
    ELSE GREATEST(0.0, v.value + (v.value * (0.05 + v.max_jitter)))
  END AS max_value,
  v.metric_type,
  v.metric_unit,
  v.imo_nr,
  v.labels
FROM values_calc v
ON CONFLICT DO NOTHING;

-- Resolve previous firing alerts for all seeded apps before inserting fresh ones.
-- This prevents alert accumulation: each seed cycle produces a clean snapshot of
-- the current scenario state rather than an ever-growing backlog.
WITH
sync_run AS (
  SELECT date_trunc('minute', timezone('UTC', now())) AS sync_time_utc
),
seeded_apps AS (
  SELECT
    u.id AS uds_location_id,
    a.id AS application_id
  FROM uds_location_application_instances uai
  JOIN udslocations u ON u.id = uai.uds_location_id
  JOIN applications a ON a.id = uai.application_instance_id
  WHERE u.imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
    AND a.external_id IN (
      'time-series-processor',
      'data-quality-processor',
      'uds-topic-handler-edge',
      'uds-edge-data-api',
      'uds-edge-ingest-source-admin',
      'uds-edge-parquet-sync'
    )
)
UPDATE alerts
SET status = 'resolved',
    ends_at = (SELECT sync_time_utc FROM sync_run)
WHERE status = 'firing'
  AND ends_at IS NULL
  AND (uds_location_id, application_id) IN (
    SELECT uds_location_id, application_id FROM seeded_apps
  );

WITH
sync_run AS (
  SELECT date_trunc('minute', timezone('UTC', now())) AS sync_time_utc
),
app_instances AS (
  SELECT
    u.id AS uds_location_id,
    u.imo_nr,
    a.id AS application_id,
    a.external_id AS app_id
  FROM uds_location_application_instances uai
  JOIN udslocations u ON u.id = uai.uds_location_id
  JOIN applications a ON a.id = uai.application_instance_id
  WHERE u.imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
    AND a.external_id IN (
      'time-series-processor',
      'data-quality-processor',
      'uds-topic-handler-edge',
      'uds-edge-data-api',
      'uds-edge-ingest-source-admin',
      'uds-edge-parquet-sync'
    )
),
scenario_flags AS (
  SELECT
    ai.*,
    CASE
      WHEN ai.imo_nr = 'IMO9300001' AND ai.app_id = 'uds-edge-data-api' THEN 'delayed'
      WHEN ai.imo_nr = 'IMO9300001' AND ai.app_id = 'data-quality-processor' THEN 'stale'
      WHEN ai.imo_nr = 'IMO9300002' AND ai.app_id = 'uds-edge-parquet-sync' THEN 'down'
      WHEN ai.imo_nr = 'IMO9300003' AND ai.app_id = 'time-series-processor' THEN 'degraded'
      WHEN scenario_roll < 0.08 THEN 'down'
      WHEN scenario_roll < 0.24 THEN 'degraded'
      WHEN scenario_roll < 0.34 THEN 'stale'
      WHEN scenario_roll < 0.44 THEN 'delayed'
      ELSE 'healthy'
    END AS scenario,
    (
      (
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 0)::bigint * 16777216 +
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 1)::bigint * 65536 +
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 2)::bigint * 256 +
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 3)::bigint
      ) / 4294967295.0
    ) AS subtype_roll
  FROM (
    SELECT
      ai.*,
      (
        (
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 0)::bigint * 16777216 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 1)::bigint * 65536 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 2)::bigint * 256 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 3)::bigint
        ) / 4294967295.0
      ) AS scenario_roll
    FROM app_instances ai
    CROSS JOIN sync_run sr
  ) ai
  CROSS JOIN sync_run sr
)
INSERT INTO alerts (
  id,
  uds_location_id,
  application_id,
  alert_name,
  severity,
  status,
  alert_type,
  fingerprint,
  labels,
  annotations,
  starts_at,
  ends_at,
  received_at
)
SELECT
  gen_random_uuid(),
  sf.uds_location_id,
  sf.application_id,
  CASE
    WHEN sf.scenario = 'down' THEN 'ServiceDown'
    WHEN sf.scenario = 'degraded' AND sf.subtype_roll < 0.5 THEN 'HighLatency'
    WHEN sf.scenario = 'degraded' THEN 'ResourcePressure'
    WHEN sf.scenario = 'stale' THEN 'ReportingStale'
    WHEN sf.scenario = 'delayed' THEN 'SyncDelayed'
  END,
  CASE
    WHEN sf.scenario = 'down' THEN 'critical'
    ELSE 'warning'
  END,
  'firing',
  CASE
    WHEN sf.scenario = 'down' THEN 'service_down'
    WHEN sf.scenario = 'degraded' AND sf.subtype_roll < 0.5 THEN 'latency_degraded'
    WHEN sf.scenario = 'degraded' THEN 'resource_pressure'
    WHEN sf.scenario = 'stale' THEN 'reporting_stale'
    WHEN sf.scenario = 'delayed' THEN 'sync_delayed'
  END,
  md5(
    sf.imo_nr || ':' || sf.app_id || ':' || sf.scenario || ':' ||
    (SELECT sync_time_utc FROM sync_run)::text
  )::varchar(255),
  jsonb_build_object(
    'imo', sf.imo_nr,
    'app_id', sf.app_id,
    'scenario', sf.scenario
  ),
  CASE
    WHEN sf.scenario = 'down' THEN jsonb_build_object('summary', 'Service down detected for ' || sf.app_id)
    WHEN sf.scenario = 'degraded' AND sf.subtype_roll < 0.5 THEN jsonb_build_object('summary', 'High latency detected for ' || sf.app_id)
    WHEN sf.scenario = 'degraded' THEN jsonb_build_object('summary', 'Resource pressure detected for ' || sf.app_id)
    WHEN sf.scenario = 'stale' THEN jsonb_build_object('summary', 'Reporting has gone stale for ' || sf.app_id)
    WHEN sf.scenario = 'delayed' THEN jsonb_build_object('summary', 'Metric sync is delayed for ' || sf.app_id)
  END,
  CASE
    WHEN sf.scenario = 'stale' THEN (SELECT sync_time_utc FROM sync_run) - interval '40 minutes'
    WHEN sf.scenario = 'delayed' THEN (SELECT sync_time_utc FROM sync_run) - interval '12 minutes'
    ELSE (SELECT sync_time_utc FROM sync_run)
  END,
  NULL,
  (SELECT sync_time_utc FROM sync_run)
FROM scenario_flags sf
WHERE sf.scenario <> 'healthy'
ON CONFLICT DO NOTHING;

WITH
sync_run AS (
  SELECT date_trunc('minute', timezone('UTC', now())) AS sync_time_utc
),
app_instances AS (
  SELECT
    u.id AS uds_location_id,
    u.imo_nr,
    a.id AS application_id,
    a.external_id AS app_id,
    a.name AS app_name
  FROM uds_location_application_instances uai
  JOIN udslocations u ON u.id = uai.uds_location_id
  JOIN applications a ON a.id = uai.application_instance_id
  WHERE u.imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
    AND a.external_id IN (
      'time-series-processor',
      'data-quality-processor',
      'uds-topic-handler-edge',
      'uds-edge-data-api',
      'uds-edge-ingest-source-admin',
      'uds-edge-parquet-sync'
    )
),
scenario_flags AS (
  SELECT
    ai.*,
    CASE
      WHEN ai.imo_nr = 'IMO9300001' AND ai.app_id = 'uds-edge-data-api' THEN 'delayed'
      WHEN ai.imo_nr = 'IMO9300001' AND ai.app_id = 'data-quality-processor' THEN 'stale'
      WHEN ai.imo_nr = 'IMO9300002' AND ai.app_id = 'uds-edge-parquet-sync' THEN 'down'
      WHEN ai.imo_nr = 'IMO9300003' AND ai.app_id = 'time-series-processor' THEN 'degraded'
      WHEN scenario_roll < 0.08 THEN 'down'
      WHEN scenario_roll < 0.24 THEN 'degraded'
      WHEN scenario_roll < 0.34 THEN 'stale'
      WHEN scenario_roll < 0.44 THEN 'delayed'
      ELSE 'healthy'
    END AS scenario,
    (
      (
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 0)::bigint * 16777216 +
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 1)::bigint * 65536 +
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 2)::bigint * 256 +
        get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':subtype'), 'hex'), 3)::bigint
      ) / 4294967295.0
    ) AS subtype_roll
  FROM (
    SELECT
      ai.*,
      (
        (
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 0)::bigint * 16777216 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 1)::bigint * 65536 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 2)::bigint * 256 +
          get_byte(decode(md5(ai.imo_nr || ':' || ai.app_id || ':' || sr.sync_time_utc::text || ':scenario'), 'hex'), 3)::bigint
        ) / 4294967295.0
      ) AS scenario_roll
    FROM app_instances ai
    CROSS JOIN sync_run sr
  ) ai
  CROSS JOIN sync_run sr
)
INSERT INTO app_logs (
  uds_location_id,
  application_id,
  app_external_id,
  level,
  source,
  message,
  logged_at,
  correlation_key,
  context
)
SELECT
  sf.uds_location_id,
  sf.application_id,
  sf.app_id,
  CASE
    WHEN sf.scenario = 'down' THEN 'error'
    WHEN sf.scenario IN ('degraded', 'stale', 'delayed') THEN 'warning'
    ELSE 'info'
  END,
  CASE
    WHEN sf.scenario = 'down' THEN 'application'
    WHEN sf.scenario = 'degraded' THEN 'runtime'
    WHEN sf.scenario = 'stale' THEN 'sync-agent'
    WHEN sf.scenario = 'delayed' THEN 'connectivity'
    ELSE 'sync-agent'
  END,
  CASE
    WHEN sf.scenario = 'down' THEN 'Health checks are failing and the application is unavailable.'
    WHEN sf.scenario = 'degraded' AND sf.subtype_roll < 0.5 THEN 'Request latency is elevated and server errors are increasing.'
    WHEN sf.scenario = 'degraded' THEN 'CPU, handle count, or database pressure is elevated.'
    WHEN sf.scenario = 'stale' THEN 'No fresh metrics received in the expected reporting window; showing last known values.'
    WHEN sf.scenario = 'delayed' THEN 'Metric sync is delayed, likely due to intermittent vessel connectivity.'
    ELSE 'Periodic sync completed successfully and the application is healthy.'
  END,
  CASE
    WHEN sf.scenario = 'stale' THEN (SELECT sync_time_utc FROM sync_run) - interval '38 minutes'
    WHEN sf.scenario = 'delayed' THEN (SELECT sync_time_utc FROM sync_run) - interval '10 minutes'
    WHEN sf.scenario = 'degraded' THEN (SELECT sync_time_utc FROM sync_run) - interval '4 minutes'
    WHEN sf.scenario = 'down' THEN (SELECT sync_time_utc FROM sync_run) - interval '2 minutes'
    ELSE (SELECT sync_time_utc FROM sync_run) - interval '1 minute'
  END,
  md5(
    sf.imo_nr || ':' || sf.app_id || ':' || sf.scenario || ':' ||
    (SELECT sync_time_utc FROM sync_run)::text || ':app-log'
  )::varchar(255),
  jsonb_build_object(
    'imo', sf.imo_nr,
    'app_id', sf.app_id,
    'app_name', sf.app_name,
    'scenario', sf.scenario,
    'sync_window', CASE
      WHEN sf.scenario = 'stale' THEN 'missing metrics > 35m'
      WHEN sf.scenario = 'delayed' THEN 'sync delayed 10m+'
      ELSE 'normal'
    END
  )
FROM scenario_flags sf;

COMMIT;
