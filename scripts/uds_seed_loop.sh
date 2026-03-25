#!/bin/sh
set -eu

DB_HOST="${DB_HOST:-timescaledb}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-postgres}"
DB_NAME="${DB_NAME:-maritime_telemetry}"
UDS_SEED_FILE="${UDS_SEED_FILE:-/seed/uds_seed.sql}"
UDS_SEED_INTERVAL_SECONDS="${UDS_SEED_INTERVAL_SECONDS:-1800}"
UDS_SCHEMA_RETRY_SECONDS="${UDS_SCHEMA_RETRY_SECONDS:-30}"

export PGPASSWORD="$DB_PASSWORD"

log() {
  printf '%s %s\n' "$(date -u +"%Y-%m-%dT%H:%M:%SZ")" "$*"
}

run_sql_scalar() {
  psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -tAc "$1"
}

schema_ready() {
  [ "$(run_sql_scalar "SELECT CASE WHEN to_regclass('public.udslocations') IS NOT NULL AND to_regclass('public.applications') IS NOT NULL AND to_regclass('public.metric_samples') IS NOT NULL AND to_regclass('public.alerts') IS NOT NULL AND to_regclass('public.app_logs') IS NOT NULL THEN 1 ELSE 0 END;")" = "1" ]
}

reference_data_ready() {
  [ "$(run_sql_scalar "SELECT CASE WHEN (SELECT COUNT(*) FROM udslocations WHERE imo_nr IN ('IMO9300001','IMO9300002','IMO9300003')) >= 3 AND (SELECT COUNT(*) FROM applications WHERE external_id IN ('time-series-processor','data-quality-processor','uds-topic-handler-edge','uds-edge-data-api','uds-edge-ingest-source-admin','uds-edge-parquet-sync')) >= 6 AND (SELECT COUNT(*) FROM uds_location_application_instances uai JOIN udslocations u ON u.id = uai.uds_location_id JOIN applications a ON a.id = uai.application_instance_id WHERE u.imo_nr IN ('IMO9300001','IMO9300002','IMO9300003') AND a.external_id IN ('time-series-processor','data-quality-processor','uds-topic-handler-edge','uds-edge-data-api','uds-edge-ingest-source-admin','uds-edge-parquet-sync')) >= 18 THEN 1 ELSE 0 END;")" = "1" ]
}

is_first_run() {
  [ "$(run_sql_scalar "SELECT CASE WHEN (SELECT COUNT(*) FROM metric_samples) = 0 THEN 1 ELSE 0 END;")" = "1" ]
}

run_seed() {
  psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 \
    -f "$UDS_SEED_FILE"
}

run_seed_with_offset() {
  # Replace timezone('UTC', now()) with an offset version so backfill data
  # lands at historical timestamps instead of the current time.
  sed "s/timezone('UTC', now())/timezone('UTC', now()) - interval '${1} minutes'/g" "$UDS_SEED_FILE" | \
    psql \
      -h "$DB_HOST" \
      -p "$DB_PORT" \
      -U "$DB_USER" \
      -d "$DB_NAME" \
      -v ON_ERROR_STOP=1
}

BACKFILL_DONE=0

if [ ! -f "$UDS_SEED_FILE" ]; then
  log "UDS seed file not found: $UDS_SEED_FILE"
  exit 1
fi

log "Waiting for PostgreSQL at $DB_HOST:$DB_PORT/$DB_NAME"
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  sleep 2
done
log "PostgreSQL is reachable"

while true; do
  if ! schema_ready; then
    log "UDS schema is not ready yet; waiting for Del A tables"
    sleep "$UDS_SCHEMA_RETRY_SECONDS"
    continue
  fi

  if ! reference_data_ready; then
    log "UDS reference data is not ready yet; waiting for vessels/apps/app-links"
    sleep "$UDS_SCHEMA_RETRY_SECONDS"
    continue
  fi

  # On first run with an empty DB, backfill 6 hours of history so Grafana
  # time-series panels have data from the start.
  if [ "$BACKFILL_DONE" = "0" ] && is_first_run; then
    log "Fresh database detected — backfilling 6 hours of historical data"
    for offset_minutes in 330 300 270 240 210 180 150 120 90 60 30; do
      log "  backfill cycle: -${offset_minutes}m"
      run_seed_with_offset "$offset_minutes"
    done
    log "Backfill complete (11 historical cycles inserted)"
    BACKFILL_DONE=1
  fi

  log "Running UDS seed: $UDS_SEED_FILE"
  psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 \
    -f "$UDS_SEED_FILE"

  metric_count="$(run_sql_scalar "SELECT COUNT(*) FROM metric_samples;")"
  alert_count="$(run_sql_scalar "SELECT COUNT(*) FROM alerts;")"
  log_count="$(run_sql_scalar "SELECT COUNT(*) FROM app_logs;")"
  latest_metric="$(run_sql_scalar "SELECT COALESCE(to_char(MAX(time) AT TIME ZONE 'UTC', 'YYYY-MM-DD\"T\"HH24:MI:SS\"Z\"'), 'NULL') FROM metric_samples;")"
  recent_alert_mix="$(run_sql_scalar "SELECT COALESCE(string_agg(alert_type || ':' || cnt, ', ' ORDER BY alert_type), 'none') FROM (SELECT alert_type, COUNT(*)::int AS cnt FROM alerts WHERE received_at >= NOW() - INTERVAL '1 hour' GROUP BY alert_type) t;")"
  recent_connectivity_mix="$(run_sql_scalar "SELECT COALESCE(string_agg(metric_name || ':' || affected, ', ' ORDER BY metric_name), 'none') FROM (SELECT metric_name, COUNT(DISTINCT application_instance_id)::int AS affected FROM metric_samples WHERE time >= NOW() - INTERVAL '1 hour' AND metric_name IN ('reporting_stale', 'sync_delayed') AND value > 0 GROUP BY metric_name) t;")"
  recent_log_mix="$(run_sql_scalar "SELECT COALESCE(string_agg(level || ':' || cnt, ', ' ORDER BY level), 'none') FROM (SELECT LOWER(level) AS level, COUNT(*)::int AS cnt FROM app_logs WHERE logged_at >= NOW() - INTERVAL '1 hour' GROUP BY LOWER(level)) t;")"
  log "UDS seed complete: metric_samples=$metric_count alerts=$alert_count app_logs=$log_count latest_metric=$latest_metric recent_alert_mix=$recent_alert_mix connectivity=$recent_connectivity_mix logs=$recent_log_mix"

  sleep "$UDS_SEED_INTERVAL_SECONDS"
done
