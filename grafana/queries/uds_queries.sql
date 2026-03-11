-- Queries used by grafana/dashboards/uds_monitoring.json

-- 1) Active alerts count
SELECT COUNT(*) AS value
FROM alerts al
JOIN udslocations u ON u.id = al.uds_location_id
WHERE u.imo_nr = '$vessel'
  AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
  AND (al.ends_at IS NULL OR al.ends_at > NOW());

-- 2) Apps with issues
WITH latest_metrics AS (
  SELECT DISTINCT ON (ms.application_instance_id, ms.metric_name)
         ms.application_instance_id,
         ms.metric_name,
         ms.value
  FROM metric_samples ms
  WHERE ms.imo_nr = '$vessel'
  ORDER BY ms.application_instance_id, ms.metric_name, ms.time DESC
),
active_alerts AS (
  SELECT al.application_id, COUNT(*)::int AS active_alert_count
  FROM alerts al
  JOIN udslocations u ON u.id = al.uds_location_id
  WHERE u.imo_nr = '$vessel'
    AND COALESCE(LOWER(al.status), 'firing') NOT IN ('resolved', 'closed', 'completed', 'cleared')
    AND (al.ends_at IS NULL OR al.ends_at > NOW())
  GROUP BY al.application_id
)
app_health AS (
  SELECT a.id
  FROM applications a
  JOIN uds_location_application_instances uai ON uai.application_instance_id = a.id
  JOIN udslocations u ON u.id = uai.uds_location_id
  LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
  LEFT JOIN active_alerts aa ON aa.application_id = a.id
  WHERE u.imo_nr = '$vessel'
  GROUP BY a.id, aa.active_alert_count
  HAVING COALESCE(MAX(CASE WHEN lm.metric_name = 'service_up' THEN lm.value END), 1) <= 0
      OR COALESCE(MAX(CASE WHEN lm.metric_name = 'health_check_status' THEN lm.value END), 1) <= 0
      OR COALESCE(aa.active_alert_count, 0) > 0
)
SELECT COUNT(*) AS value
FROM app_health;

-- 3) Application status summary
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
  END AS "Status",
  COALESCE(aa.active_alert_count, 0) AS "Active Alerts",
  ROUND(MAX(CASE WHEN lm.metric_name = 'process_cpu_usage' THEN lm.value END)::numeric, 2) AS "CPU %",
  ROUND(MAX(CASE WHEN lm.metric_name = 'process_memory_bytes' THEN lm.value END)::numeric, 0) AS "Memory Bytes",
  ROUND(MAX(CASE WHEN lm.metric_name = 'http_error_rate_5xx' THEN lm.value END)::numeric, 2) AS "5xx %",
  ROUND(MAX(CASE WHEN lm.metric_name = 'db_query_errors' THEN lm.value END)::numeric, 2) AS "DB Errors",
  MAX(lm.time) AS "Latest Sample"
FROM selected_vessel sv
JOIN uds_location_application_instances uai ON uai.uds_location_id = sv.id
JOIN applications a ON a.id = uai.application_instance_id
LEFT JOIN latest_metrics lm ON lm.application_instance_id = a.id
LEFT JOIN active_alerts aa ON aa.application_id = a.id
GROUP BY a.id, a.name, a.external_id, aa.active_alert_count
ORDER BY a.name;
