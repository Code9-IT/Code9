# UDS Monitoring Dashboard

This document describes the Scope 1 Grafana dashboard in
`grafana/dashboards/uds_monitoring.json`.

## Goal
Replace the old `data_quality.json` dashboard with a land-operations view for
User Story 1: one vessel, six UDS applications, latest health metrics, and
active alerts from Geir's UDS schema.

## Data sources
- `udslocations`
- `applications`
- `uds_location_application_instances`
- `metric_samples`
- `alerts`

The dashboard is designed for the schema described in:
- `databasecodeFraGeir/logging_db_dbml.txt`
- `databasecodeFraGeir/db_init_script (1).txt`
- `databasecodeFraGeir/db_seeding_script.txt`

## Provisioning
Grafana already auto-loads every JSON file in `grafana/dashboards/`, so no
extra provisioning changes are required.

## Variable
- `vessel`: selects one ship by `imo_nr`, labeled as `name (imo_nr)`

## Panels
1. Overview stats
   - Active alerts
   - Apps with issues
   - Apps reporting in the last 35 minutes
   - Latest metric age
2. Application status summary
   - Derived status per app: `healthy`, `degraded`, `down`, `unknown`
   - Key latest values and latest sample timestamp
3. Availability metrics
   - `service_up`
   - `health_check_status`
   - `process_uptime_seconds`
4. Resource metrics
   - `process_cpu_usage`
   - `process_memory_bytes`
   - `process_open_handles`
5. HTTP and exception metrics
   - `http_request_duration_p95`
   - `http_error_rate_5xx`
   - `http_error_rate_4xx`
   - `dotnet_exceptions_rate`
6. Database metrics
   - `db_query_duration_avg`
   - `db_query_duration_p95`
   - `db_query_rate`
   - `db_query_errors`
   - `db_deadlocks`
7. Active alerts table

## Notes
- `ship_operations.json` stays in place as the original sensor dashboard.
- `data_quality.json` is intentionally removed because it represented the wrong
  dashboard direction for the updated scope.
- This dashboard assumes Scope 1 database work adds the UDS schema and that the
  seeding flow populates `metric_samples` and `alerts`.
