# UDS App Health Dashboard (Del D)

This document describes the new Grafana dashboard implemented in `grafana/dashboards/uds_app_health.json`. It replaces the previous "Data Quality" view and focuses on application‑level observability for the UDS prototype.

## Goal
Show operators and developers the runtime health of the AI agent pipeline, event ingestion, and unacknowledged alarms.

## Provisioning
- Dashboard JSON lives in `grafana/dashboards/uds_app_health.json`.
- The existing provisioning YAML (`grafana/provisioning/dashboards/dashboards.yaml`) loads all files in that directory, so no additional configuration is required.
- The dashboard is auto‑imported into the "Maritime" folder when Grafana starts.

## Time range & templating
- Default time range: **last 1 hour**.
- Template variable `vessel` selects `vessel_id` from `telemetry`.

## Panels
1. **Latest AI Analyses** – table of the 5 most recent analyses for the selected vessel.
   ```sql
   SELECT a.id, a.timestamp, a.event_id, e.sensor_name, e.event_type, e.severity,
          a.status, a.confidence, a.model_used, a.analysis_text, a.suggested_actions
   FROM ai_analyses a
   JOIN events e ON a.event_id = e.id
   WHERE e.vessel_id = '$vessel'
   ORDER BY a.timestamp DESC
   LIMIT 5
   ```

2. **Avg Analysis Latency (s, 1h)** – stat showing the average time between an event and its analysis.
   ```sql
   SELECT AVG(EXTRACT(EPOCH FROM (a.timestamp - e.timestamp))) AS value
   FROM ai_analyses a
   JOIN events e ON a.event_id = e.id
   WHERE e.vessel_id = '$vessel'
     AND a.timestamp > NOW() - INTERVAL '1 hour'
   ```

3. **Analysis Error Rate (1h)** – stat percent of analyses that did not complete successfully in the past hour.
   ```sql
   SELECT ROUND(100.0 * SUM(CASE WHEN a.status != 'completed' THEN 1 ELSE 0 END) /
                NULLIF(COUNT(*),0),2) AS value
   FROM ai_analyses a
   JOIN events e ON a.event_id = e.id
   WHERE e.vessel_id = '$vessel'
     AND a.timestamp > NOW() - INTERVAL '1 hour'
   ```

4. **Telemetry Ingestion Rate (1h)** – bar chart of raw telemetry rows per minute.
   ```sql
   SELECT time_bucket('1 minute', timestamp) AS "time",
          COUNT(*) AS records
   FROM telemetry
   WHERE vessel_id = '$vessel'
     AND timestamp > NOW() - INTERVAL '1 hour'
   GROUP BY 1 ORDER BY 1
   ```

5. **Event Rate (1h)** – bar chart of anomaly events per minute.
   ```sql
   SELECT time_bucket('1 minute', timestamp) AS "time",
          COUNT(*) AS events
   FROM events
   WHERE vessel_id = '$vessel'
     AND timestamp > NOW() - INTERVAL '1 hour'
   GROUP BY 1 ORDER BY 1
   ```

6. **Unacknowledged Alarms** – table of recent events that have not been acknowledged.
   ```sql
   SELECT id, timestamp, vessel_id, sensor_name, event_type, severity, details
   FROM events
   WHERE vessel_id = '$vessel' AND acknowledged = FALSE
   ORDER BY timestamp DESC LIMIT 25
   ```

## Alerts (future work)
- *Unacknowledged alarms* &gt; 10
- *Avg analysis latency* &gt; 120 s
- *Analysis error rate* &gt; 5% over 1 h

Alerting rules can be defined in Grafana's alerting UI or added under `grafana/provisioning/alerting`.

## Testing locally
1. Start the stack: `docker compose up --build`.
2. Access Grafana at `http://localhost:3000` (admin/admin).
3. Navigate to **Maritime → UDS App Health**.
4. Generate a few anomalies via the `generator` or `curl -X POST …/api/v1/analyze` and confirm panels update.

## Next modifications
- Add service heartbeat table if explicit availability metrics are desired.
- Extend with Ollama/agent health panels once a metrics exporter is available.

## PR checklist
- [ ] `uds_app_health.json` imported successfully in Grafana (load/folder check).
- [ ] `data_quality.json` renamed/archived so old dashboard is not provisioned.
- [ ] SQL queries in `grafana/queries/uds_queries.sql` produce expected results.
- [ ] Documentation (`UDS_dashboard_spec.md`, README, NEXT_STEPS) updated accordingly.
- [ ] Local validation instructions added and verified.
- [ ] Optional alerting rules drafted or noted.
