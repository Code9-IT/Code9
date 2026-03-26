# UDS Incident Monitoring Dashboard

This document describes the Scope 1 Grafana dashboard in
`grafana/dashboards/uds_monitoring.json`.

## Goal
Turn the UDS dashboard into an incident board for User Story 1, not just a
latest-state vessel health board.

The main dashboard outcome is now:

- select one vessel
- identify the affected app from active alerts
- pivot directly into that app's recent alert and metric history
- inspect the incident over a clear drilldown window inside Grafana itself

## Current Scope
The dashboard is intentionally focused on one-vessel incident handling using:

- `metric_samples`
- `alerts`
- `app_logs`

This is still a prototype, but it now includes a lightweight log/log-like path
for selected applications in addition to alerts and metric history.

## Data Sources
- `udslocations`
- `applications`
- `uds_location_application_instances`
- `metric_samples`
- `alerts`
- `app_logs`

Tracked repo implementation lives in:

- `db/init/003_uds.sql`
- `db/init/004_uds_reference_data.sql`
- `db/seed/uds_seed.sql`

## Provisioning
Grafana auto-loads every JSON file in `grafana/dashboards/`, so no extra
provisioning changes are required.

## Variables
- `vessel`
  - selects one ship by `imo_nr`, labeled as `name (imo_nr)`
- `app`
  - selects one application on the selected vessel
  - the dropdown sorts incident-affected apps first
  - the value is `applications.external_id`
- `incident_window`
  - controls the drilldown window for the selected application
  - options: `Last 1h`, `Last 6h`, `Last 24h`

## Incident Flow
1. Select a vessel with `vessel`.
2. Review `Active Incident Queue` to see active alerts and affected apps.
3. Click `Application` or `App ID` in either incident table to set the `app`
   drilldown target on the same dashboard.
4. Use `Selected App Drilldown` and `incident_window` to inspect recent alerts,
   logs, availability, connectivity/freshness, HTTP/errors, resources, memory,
   and database behavior.
5. Use `Metric Window Summary` for a compact min/avg/max/latest view of the
   same incident window.

## Panels
### Incident Overview
1. `Active Alerts`
   - count of active alerts for the selected vessel
2. `Affected Apps`
   - distinct app count across active alerts on the selected vessel
3. `Most Recent Incident Age`
   - seconds since the latest active incident started
4. `Selected App Metric Age`
   - freshness of the currently selected app's most recent metric sample
5. `Active Incident Queue`
   - active alert table for the selected vessel
   - includes app, alert, severity, status, type, start time, open minutes, and summary
   - `Application` and `App ID` fields are clickable drilldown links
6. `Application Incident Board`
   - one row per app on the selected vessel
   - shows current status, active alert count, latest alert, latest severity,
     incident start, 5xx rate, CPU, and latest sample
   - `Application` and `App ID` fields are clickable drilldown links

### Selected App Drilldown
7. `Selected App Context`
   - one-row summary for the selected vessel/app pair
   - shows current status, active alerts, latest alert metadata, and latest sample
8. `Selected App Recent Alerts`
    - alert history for the selected app inside the chosen `incident_window`
9. `Selected App Recent Logs`
   - recent log/log-like context for the selected app inside the chosen
     `incident_window`
   - includes `Level`, `Source`, `Message`, `Correlation`, and raw `Context`
10. `Availability Signals ($incident_window)`
    - `service_up`
    - `health_check_status`
11. `Connectivity And Freshness ($incident_window)`
    - `last_sync_age_seconds`
    - `reporting_stale`
    - `sync_delayed`
12. `HTTP And Exception History ($incident_window)`
    - `http_request_duration_p95`
    - `http_error_rate_5xx`
    - `http_error_rate_4xx`
    - `dotnet_exceptions_rate`
13. `CPU And Handles ($incident_window)`
    - `process_cpu_usage`
    - `process_open_handles`
14. `Memory Footprint ($incident_window)`
    - `process_memory_bytes`
15. `Database Latency ($incident_window)`
    - `db_query_duration_avg`
    - `db_query_duration_p95`
16. `Database Error Activity ($incident_window)`
    - `db_query_rate`
    - `db_query_errors`
    - `db_deadlocks`
17. `Metric Window Summary ($incident_window)`
    - grouped by metric name
    - shows min, avg, max, latest, unit, and latest sample time

## Notes
- `grafana/queries/uds_queries.sql` mirrors the dashboard queries for review and
  maintenance.
- The dashboard default time range remains `now-24h`, while `incident_window`
  gives a clearer app-focused incident slice inside that range.
- `ship_operations.json` stays in place as the original sensor dashboard.
- `app_logs` currently mixes trigger-generated alert logs with seeded
  application/sync logs, which is good enough for the prototype's incident
  context goal.
- This dashboard now closes the specific Grafana gap from the review:
  alert -> affected app -> recent metric/log history is visible in Grafana
  without needing MCP first.
