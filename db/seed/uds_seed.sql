BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

WITH
sync_run AS (
  SELECT
    gen_random_uuid() AS sync_id,
    date_trunc('minute', timezone('UTC', now())) AS sync_time_utc
),
ships AS (
  SELECT imo_nr
  FROM udslocations
  WHERE imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
),
apps AS (
  SELECT
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
  FROM applications a
  WHERE a.external_id IN (
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
    ('service_up', 'Application', 'Count', 'AGGREGATED'::text, 0),
    ('health_check_status', 'Application', 'Count', 'AGGREGATED'::text, 0),
    ('process_uptime_seconds', 'Application', 'Seconds', 'AGGREGATED'::text, 0),
    ('http_request_duration_p95', 'Application', 'Seconds', 'AGGREGATED'::text, 0),
    ('http_error_rate_5xx', 'Application', 'Percent', 'INTERVAL'::text, 600),
    ('http_error_rate_4xx', 'Application', 'Percent', 'INTERVAL'::text, 600),
    ('dotnet_exceptions_rate', 'Application', 'Count', 'AGGREGATED'::text, 0),
    ('process_cpu_usage', 'Application', 'Percent', 'INTERVAL'::text, 600),
    ('process_memory_bytes', 'Application', 'Bytes', 'INTERVAL'::text, 600),
    ('process_open_handles', 'Application', 'Count', 'AGGREGATED'::text, 0),
    ('db_query_duration_avg', 'Database', 'Seconds', 'AGGREGATED'::text, 0),
    ('db_query_duration_p95', 'Database', 'Seconds', 'AGGREGATED'::text, 0),
    ('db_query_rate', 'Database', 'Count', 'AGGREGATED'::text, 0),
    ('db_query_errors', 'Database', 'Count', 'AGGREGATED'::text, 0),
    ('db_deadlocks', 'Database', 'Count', 'AGGREGATED'::text, 0)
  ) v(metric_name, metric_type, metric_unit, query_type, seconds_per_value)
),
down_flags AS (
  SELECT
    s.imo_nr,
    a.app_id,
    (random() < 0.03) AS is_down
  FROM ships s
  CROSS JOIN apps a
),
expanded AS (
  SELECT
    sr.sync_id,
    sr.sync_time_utc,
    s.imo_nr,
    a.app_id,
    a.app_name,
    a.job_name,
    a.application_instance_id,
    df.is_down,
    md.metric_name,
    md.metric_type,
    md.metric_unit,
    md.query_type,
    CASE
      WHEN md.query_type = 'AGGREGATED' THEN sr.sync_time_utc
      ELSE t.sample_time
    END AS sample_time
  FROM sync_run sr
  CROSS JOIN ships s
  CROSS JOIN apps a
  JOIN down_flags df ON df.imo_nr = s.imo_nr AND df.app_id = a.app_id
  CROSS JOIN metric_defs md
  LEFT JOIN LATERAL (
    SELECT (sr.sync_time_utc - interval '20 minutes') AS sample_time
    UNION ALL
    SELECT (sr.sync_time_utc - interval '10 minutes')
    UNION ALL
    SELECT sr.sync_time_utc
  ) t ON (md.query_type = 'INTERVAL')
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
      'source', 'mock_collector'
    ) AS labels,
    CASE e.metric_name
      WHEN 'service_up' THEN CASE WHEN e.is_down THEN 0.0 ELSE 1.0 END
      WHEN 'health_check_status' THEN CASE WHEN e.is_down THEN 0.0 ELSE 1.0 END
      WHEN 'process_uptime_seconds' THEN
        GREATEST(0.0, 3600.0 + random() * 7200.0) * CASE WHEN e.is_down THEN 0.2 ELSE 1.0 END
      WHEN 'http_request_duration_p95' THEN
        CASE WHEN e.is_down THEN 2.0 + random() * 3.0 ELSE 0.05 + random() * 0.6 END
      WHEN 'http_error_rate_5xx' THEN
        CASE WHEN e.is_down THEN 20.0 + random() * 60.0 ELSE random() * 1.5 END
      WHEN 'http_error_rate_4xx' THEN
        CASE WHEN e.is_down THEN 5.0 + random() * 20.0 ELSE 0.2 + random() * 2.5 END
      WHEN 'dotnet_exceptions_rate' THEN
        CASE WHEN e.is_down THEN random() * 5.0 ELSE random() * 0.8 END
      WHEN 'process_cpu_usage' THEN
        CASE WHEN e.is_down THEN 70.0 + random() * 25.0 ELSE 10.0 + random() * 45.0 END
      WHEN 'process_memory_bytes' THEN
        CASE
          WHEN e.is_down THEN 800000000.0 + random() * 1200000000.0
          ELSE 400000000.0 + random() * 900000000.0
        END
      WHEN 'process_open_handles' THEN
        CASE WHEN e.is_down THEN 1500.0 + random() * 2500.0 ELSE 300.0 + random() * 1200.0 END
      WHEN 'db_query_duration_avg' THEN
        CASE WHEN e.is_down THEN 0.2 + random() * 0.8 ELSE 0.01 + random() * 0.12 END
      WHEN 'db_query_duration_p95' THEN
        CASE WHEN e.is_down THEN 0.8 + random() * 2.5 ELSE 0.05 + random() * 0.5 END
      WHEN 'db_query_rate' THEN
        CASE WHEN e.is_down THEN random() * 5.0 ELSE 10.0 + random() * 120.0 END
      WHEN 'db_query_errors' THEN
        CASE WHEN e.is_down THEN random() * 8.0 ELSE random() * 0.6 END
      WHEN 'db_deadlocks' THEN
        CASE WHEN e.is_down AND random() < 0.12 THEN 1.0 ELSE 0.0 END
      ELSE random() * 10.0
    END::double precision AS value,
    CASE WHEN e.query_type = 'AGGREGATED' THEN (random() * 0.15) ELSE NULL END::double precision AS min_jitter,
    CASE WHEN e.query_type = 'AGGREGATED' THEN (random() * 0.15) ELSE NULL END::double precision AS max_jitter
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

WITH
sync_run AS (
  SELECT date_trunc('minute', timezone('UTC', now())) AS sync_time_utc
),
ships AS (
  SELECT id AS uds_location_id, imo_nr
  FROM udslocations
  WHERE imo_nr IN ('IMO9300001', 'IMO9300002', 'IMO9300003')
),
apps AS (
  SELECT id AS application_id, external_id AS app_id
  FROM applications
  WHERE external_id IN (
    'time-series-processor',
    'data-quality-processor',
    'uds-topic-handler-edge',
    'uds-edge-data-api',
    'uds-edge-ingest-source-admin',
    'uds-edge-parquet-sync'
  )
),
down_flags AS (
  SELECT
    s.imo_nr,
    a.app_id,
    (random() < 0.03) AS is_down
  FROM ships s
  CROSS JOIN apps a
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
  sh.uds_location_id,
  ap.application_id,
  'ServiceDown',
  'critical',
  'firing',
  'service_down',
  md5(df.imo_nr || ':' || df.app_id || ':ServiceDown:' || (SELECT sync_time_utc FROM sync_run)::text)::varchar(255),
  jsonb_build_object('imo', df.imo_nr, 'app_id', df.app_id),
  jsonb_build_object('summary', 'Service down detected for ' || df.app_id),
  (SELECT sync_time_utc FROM sync_run),
  NULL,
  (SELECT sync_time_utc FROM sync_run) + interval '1 minute'
FROM down_flags df
JOIN ships sh ON sh.imo_nr = df.imo_nr
JOIN apps ap ON ap.app_id = df.app_id
WHERE df.is_down
ON CONFLICT DO NOTHING;

COMMIT;
