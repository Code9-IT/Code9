-- Queries used by grafana/dashboards/uds_monitoring.json
-- Variables:
--   $vessel          -> selected vessel IMO number
--   ${app}           -> selected application external_id
--   ${incident_window} -> selected drilldown window, e.g. '1 hour', '6 hours', '24 hours'

-- ------------------------------------------------------------------
-- Variable: vessel
-- ------------------------------------------------------------------
SELECT imo_nr AS __value, name || ' (' || imo_nr || ')' AS __text
FROM udslocations
WHERE imo_nr IS NOT NULL
ORDER BY name;

-- ------------------------------------------------------------------
-- Variable: app
-- Sorts impacted apps first so the drilldown follows active incidents.
-- ------------------------------------------------------------------
WITH selected_vessel AS (
  SELECT id
  FROM udslocations
  WHERE imo_nr = '$vessel'
),
latest_metrics AS (
  SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
         ms.application_instance_id,
         ms.metric_name,
         ms.time,
         ms.value
  FROM metric_samples ms
  WHERE ms.imo_nr = '$vessel'
  ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
),
active_alerts AS (
  SELECT al.application_id, COUNT(*)::int AS active_alert_count
  FROM alerts al
  JOIN selected_vessel sv ON sv.id = al.uds_location_id
  WHERE COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
    AND (al.ends_at IS NULL OR al.ends_at > NOW())
  GROUP BY al.application_id
),
app_board AS (
  SELECT
    a.external_id AS app_id,
    a.name AS app_name,
    CASE
      WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
        OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0
        THEN 'down'
      WHEN COALESCE(aa.active_alert_count, 0) > 0 THEN 'degraded'
      WHEN MAX(lm.time) IS NULL THEN 'unknown'
      ELSE 'healthy'
    END AS current_status,
    COALESCE(aa.active_alert_count, 0) AS active_alerts
  FROM selected_vessel sv
  JOIN uds_location_application_instances uai ON uai.uds_location_id = sv.id
  JOIN applications a ON a.id = uai.application_instance_id
  LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
  LEFT JOIN active_alerts aa ON aa.application_id = a.id
  GROUP BY a.id, a.external_id, a.name, aa.active_alert_count
)
SELECT
  app_id AS __value,
  app_name || ' | ' || current_status || ' | alerts=' || active_alerts AS __text
FROM app_board
ORDER BY
  CASE current_status
    WHEN 'down' THEN 0
    WHEN 'degraded' THEN 1
    WHEN 'unknown' THEN 2
    ELSE 3
  END,
  active_alerts DESC,
  app_name;

-- ------------------------------------------------------------------
-- Variable: incident_window
-- ------------------------------------------------------------------
SELECT '1 hour' AS __value, 'Last 1h' AS __text
UNION ALL
SELECT '6 hours' AS __value, 'Last 6h' AS __text
UNION ALL
SELECT '24 hours' AS __value, 'Last 24h' AS __text;

-- ------------------------------------------------------------------
-- Stat: Active Alerts
-- ------------------------------------------------------------------
SELECT COUNT(*) AS value
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
WHERE u.imo_nr = '$vessel'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW());

-- ------------------------------------------------------------------
-- Stat: Affected Apps
-- ------------------------------------------------------------------
SELECT COUNT(DISTINCT al.application_id) AS value
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
WHERE u.imo_nr = '$vessel'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW());

-- ------------------------------------------------------------------
-- Stat: Most Recent Incident Age
-- ------------------------------------------------------------------
SELECT EXTRACT(EPOCH FROM (NOW() - MAX(al.starts_at))) AS value
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
WHERE u.imo_nr = '$vessel'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW());

-- ------------------------------------------------------------------
-- Stat: Selected App Metric Age
-- ------------------------------------------------------------------
SELECT EXTRACT(EPOCH FROM (NOW() - MAX(ms.time))) AS value
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}';

-- ------------------------------------------------------------------
-- Table: Active Incident Queue
-- ------------------------------------------------------------------
SELECT
  a.name AS "Application",
  a.external_id AS "App ID",
  al.alert_name AS "Alert",
  al.severity AS "Severity",
  al.status AS "Status",
  al.alert_type AS "Type",
  al.starts_at AS "Started",
  ROUND((EXTRACT(EPOCH FROM (NOW() - al.starts_at)) / 60.0)::numeric, 1) AS "Open Minutes",
  al.received_at AS "Received",
  COALESCE(al.annotations ->> 'summary', al.alert_name) AS "Summary"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
LEFT JOIN applications a ON a.id = al.application_id
WHERE u.imo_nr = '$vessel'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW())
ORDER BY
  CASE LOWER(al.severity)
    WHEN 'critical' THEN 0
    WHEN 'warning' THEN 1
    ELSE 2
  END,
  al.starts_at DESC;

-- ------------------------------------------------------------------
-- Table: Application Incident Board
-- ------------------------------------------------------------------
WITH selected_vessel AS (
  SELECT id
  FROM udslocations
  WHERE imo_nr = '$vessel'
),
latest_metrics AS (
  SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
         ms.application_instance_id,
         ms.metric_name,
         ms.time,
         ms.value
  FROM metric_samples ms
  WHERE ms.imo_nr = '$vessel'
  ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
),
active_alerts AS (
  SELECT al.application_id, COUNT(*)::int AS active_alert_count
  FROM alerts al
  JOIN selected_vessel sv ON sv.id = al.uds_location_id
  WHERE COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
    AND (al.ends_at IS NULL OR al.ends_at > NOW())
  GROUP BY al.application_id
),
latest_alert AS (
  SELECT DISTINCT ON (al.application_id)
         al.application_id,
         al.alert_name,
         al.severity,
         al.starts_at
  FROM alerts al
  JOIN selected_vessel sv ON sv.id = al.uds_location_id
  ORDER BY al.application_id, al.starts_at DESC
)
SELECT
  a.name AS "Application",
  a.external_id AS "App ID",
  CASE
    WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
      OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0
      THEN 'down'
    WHEN COALESCE(aa.active_alert_count, 0) > 0 THEN 'degraded'
    WHEN MAX(lm.time) IS NULL THEN 'unknown'
    ELSE 'healthy'
  END AS "Current Status",
  COALESCE(aa.active_alert_count, 0) AS "Active Alerts",
  la.alert_name AS "Latest Alert",
  la.severity AS "Latest Severity",
  la.starts_at AS "Latest Incident Start",
  ROUND(MAX(CASE WHEN lm.metric_name = 'http_error_rate_5xx' THEN lm.value END)::numeric, 2) AS "5xx %",
  ROUND(MAX(CASE WHEN lm.metric_name = 'process_cpu_usage' THEN lm.value END)::numeric, 2) AS "CPU %",
  MAX(lm.time) AS "Latest Sample"
FROM selected_vessel sv
JOIN uds_location_application_instances uai ON uai.uds_location_id = sv.id
JOIN applications a ON a.id = uai.application_instance_id
LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
LEFT JOIN active_alerts aa ON aa.application_id = a.id
LEFT JOIN latest_alert la ON la.application_id = a.id
GROUP BY a.id, a.name, a.external_id, aa.active_alert_count, la.alert_name, la.severity, la.starts_at
ORDER BY COALESCE(aa.active_alert_count, 0) DESC, la.starts_at DESC NULLS LAST, a.name;

-- ------------------------------------------------------------------
-- Table: Selected App Context
-- ------------------------------------------------------------------
WITH selected_vessel AS (
  SELECT id, name, imo_nr
  FROM udslocations
  WHERE imo_nr = '$vessel'
),
latest_metrics AS (
  SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
         ms.application_instance_id,
         ms.metric_name,
         ms.time,
         ms.value
  FROM metric_samples ms
  WHERE ms.imo_nr = '$vessel'
  ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
),
active_alerts AS (
  SELECT al.application_id, COUNT(*)::int AS active_alert_count
  FROM alerts al
  JOIN selected_vessel sv ON sv.id = al.uds_location_id
  WHERE COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
    AND (al.ends_at IS NULL OR al.ends_at > NOW())
  GROUP BY al.application_id
),
latest_alert AS (
  SELECT DISTINCT ON (al.application_id)
         al.application_id,
         al.alert_name,
         al.severity,
         al.starts_at
  FROM alerts al
  JOIN selected_vessel sv ON sv.id = al.uds_location_id
  ORDER BY al.application_id, al.starts_at DESC
)
SELECT
  sv.name AS "Vessel",
  sv.imo_nr AS "IMO",
  a.name AS "Application",
  a.external_id AS "App ID",
  a.app_type AS "Type",
  CASE
    WHEN COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
      OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0
      THEN 'down'
    WHEN COALESCE(aa.active_alert_count, 0) > 0 THEN 'degraded'
    WHEN MAX(lm.time) IS NULL THEN 'unknown'
    ELSE 'healthy'
  END AS "Current Status",
  COALESCE(aa.active_alert_count, 0) AS "Active Alerts",
  la.alert_name AS "Latest Alert",
  la.severity AS "Latest Severity",
  la.starts_at AS "Latest Incident Start",
  MAX(lm.time) AS "Latest Sample"
FROM selected_vessel sv
JOIN uds_location_application_instances uai ON uai.uds_location_id = sv.id
JOIN applications a ON a.id = uai.application_instance_id
LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
LEFT JOIN active_alerts aa ON aa.application_id = a.id
LEFT JOIN latest_alert la ON la.application_id = a.id
WHERE a.external_id = '${app}'
GROUP BY sv.name, sv.imo_nr, a.id, a.name, a.external_id, a.app_type, aa.active_alert_count, la.alert_name, la.severity, la.starts_at;

-- ------------------------------------------------------------------
-- Table: Selected App Recent Alerts
-- ------------------------------------------------------------------
SELECT
  al.alert_name AS "Alert",
  al.severity AS "Severity",
  al.status AS "Status",
  al.alert_type AS "Type",
  al.starts_at AS "Started",
  al.ends_at AS "Ended",
  al.received_at AS "Received",
  COALESCE(al.annotations ->> 'summary', al.alert_name) AS "Summary"
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
JOIN applications a ON a.id = al.application_id
WHERE u.imo_nr = '$vessel'
  AND a.external_id = '${app}'
  AND al.starts_at >= NOW() - INTERVAL '${incident_window}'
ORDER BY al.starts_at DESC;

-- ------------------------------------------------------------------
-- Time series: Availability Signals
-- ------------------------------------------------------------------
SELECT ms.time AS "time", ms.metric_name AS metric, ms.value
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}'
  AND ms.metric_name IN ('service_up', 'health_check_status')
  AND $__timeFilter(ms.time)
  AND ms.time >= NOW() - INTERVAL '${incident_window}'
ORDER BY ms.time;

-- ------------------------------------------------------------------
-- Time series: HTTP And Exception History
-- ------------------------------------------------------------------
SELECT ms.time AS "time", ms.metric_name AS metric, ms.value
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}'
  AND ms.metric_name IN ('http_request_duration_p95', 'http_error_rate_5xx', 'http_error_rate_4xx', 'dotnet_exceptions_rate')
  AND $__timeFilter(ms.time)
  AND ms.time >= NOW() - INTERVAL '${incident_window}'
ORDER BY ms.time;

-- ------------------------------------------------------------------
-- Time series: CPU And Handles
-- ------------------------------------------------------------------
SELECT ms.time AS "time", ms.metric_name AS metric, ms.value
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}'
  AND ms.metric_name IN ('process_cpu_usage', 'process_open_handles')
  AND $__timeFilter(ms.time)
  AND ms.time >= NOW() - INTERVAL '${incident_window}'
ORDER BY ms.time;

-- ------------------------------------------------------------------
-- Time series: Memory Footprint
-- ------------------------------------------------------------------
SELECT ms.time AS "time", ms.metric_name AS metric, ms.value
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}'
  AND ms.metric_name IN ('process_memory_bytes')
  AND $__timeFilter(ms.time)
  AND ms.time >= NOW() - INTERVAL '${incident_window}'
ORDER BY ms.time;

-- ------------------------------------------------------------------
-- Time series: Database Latency
-- ------------------------------------------------------------------
SELECT ms.time AS "time", ms.metric_name AS metric, ms.value
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}'
  AND ms.metric_name IN ('db_query_duration_avg', 'db_query_duration_p95')
  AND $__timeFilter(ms.time)
  AND ms.time >= NOW() - INTERVAL '${incident_window}'
ORDER BY ms.time;

-- ------------------------------------------------------------------
-- Time series: Database Error Activity
-- ------------------------------------------------------------------
SELECT ms.time AS "time", ms.metric_name AS metric, ms.value
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}'
  AND ms.metric_name IN ('db_query_rate', 'db_query_errors', 'db_deadlocks')
  AND $__timeFilter(ms.time)
  AND ms.time >= NOW() - INTERVAL '${incident_window}'
ORDER BY ms.time;

-- ------------------------------------------------------------------
-- Table: Metric Window Summary
-- ------------------------------------------------------------------
SELECT
  ms.metric_name AS "Metric",
  ROUND(MIN(ms.value)::numeric, 4) AS "Min",
  ROUND(AVG(ms.value)::numeric, 4) AS "Avg",
  ROUND(MAX(ms.value)::numeric, 4) AS "Max",
  ROUND(((ARRAY_AGG(ms.value ORDER BY ms.time DESC))[1])::numeric, 4) AS "Latest",
  MAX(ms.metric_unit) AS "Unit",
  MAX(ms.time) AS "Latest Sample"
FROM metric_samples ms
WHERE ms.imo_nr = '$vessel'
  AND ms.app_id = '${app}'
  AND $__timeFilter(ms.time)
  AND ms.time >= NOW() - INTERVAL '${incident_window}'
GROUP BY ms.metric_name
ORDER BY
  CASE ms.metric_name
    WHEN 'service_up' THEN 1
    WHEN 'health_check_status' THEN 2
    WHEN 'process_uptime_seconds' THEN 3
    WHEN 'http_request_duration_p95' THEN 4
    WHEN 'http_error_rate_5xx' THEN 5
    WHEN 'http_error_rate_4xx' THEN 6
    WHEN 'dotnet_exceptions_rate' THEN 7
    WHEN 'process_cpu_usage' THEN 8
    WHEN 'process_memory_bytes' THEN 9
    WHEN 'process_open_handles' THEN 10
    WHEN 'db_query_duration_avg' THEN 11
    WHEN 'db_query_duration_p95' THEN 12
    WHEN 'db_query_rate' THEN 13
    WHEN 'db_query_errors' THEN 14
    WHEN 'db_deadlocks' THEN 15
    ELSE 99
  END;
