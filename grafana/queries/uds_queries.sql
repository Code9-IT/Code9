-- Queries used by UDS App Health dashboard

-- 1) Latest AI analyses
SELECT a.id, a.timestamp, a.event_id, e.sensor_name, e.event_type, e.severity,
       a.status, a.confidence, a.model_used, a.analysis_text, a.suggested_actions
FROM ai_analyses a
JOIN events e ON a.event_id = e.id
WHERE e.vessel_id = '$vessel'
ORDER BY a.timestamp DESC
LIMIT 5;

-- 2) Average analysis latency (s, 1h)
SELECT AVG(EXTRACT(EPOCH FROM (a.timestamp - e.timestamp))) AS value
FROM ai_analyses a
JOIN events e ON a.event_id = e.id
WHERE e.vessel_id = '$vessel'
  AND a.timestamp > NOW() - INTERVAL '1 hour';

-- 3) Analysis error rate (1h)
SELECT ROUND(100.0 * SUM(CASE WHEN a.status != 'completed' THEN 1 ELSE 0 END) /
             NULLIF(COUNT(*),0),2) AS value
FROM ai_analyses a
JOIN events e ON a.event_id = e.id
WHERE e.vessel_id = '$vessel'
  AND a.timestamp > NOW() - INTERVAL '1 hour';

-- 4) Telemetry ingestion rate (1h)
SELECT time_bucket('1 minute', timestamp) AS "time",
       COUNT(*) AS records
FROM telemetry
WHERE vessel_id = '$vessel'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY 1 ORDER BY 1;

-- 5) Event rate (1h)
SELECT time_bucket('1 minute', timestamp) AS "time",
       COUNT(*) AS events
FROM events
WHERE vessel_id = '$vessel'
  AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY 1 ORDER BY 1;

-- 6) Unacknowledged alarms
SELECT id, timestamp, vessel_id, sensor_name, event_type, severity, details
FROM events
WHERE vessel_id = '$vessel' AND acknowledged = FALSE
ORDER BY timestamp DESC LIMIT 25;
