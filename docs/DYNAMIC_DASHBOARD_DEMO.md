# Dynamic Dashboard Demo Runbook

Short guide for repeating the dynamic-dashboard demo reliably.

## Prerequisites

- Stack is running: `docker compose up -d --build`
- UDS backfill has completed: `docker compose logs -f uds-seeder` shows "Backfill complete"
- Grafana is reachable at http://localhost:3000 (admin / code9-demo-admin)
- Agent API is reachable at http://localhost:8000/docs

## Available Scenarios

| Scenario            | Vessel           | Application                | Alert            | Severity |
|---------------------|------------------|----------------------------|------------------|----------|
| `service_down`      | IMO9300002       | uds-edge-parquet-sync      | ServiceDown      | critical |
| `connectivity`      | IMO9300001       | data-quality-processor     | ReportingStale   | warning  |
| `runtime_pressure`  | IMO9300003       | time-series-processor      | ResourcePressure | warning  |

These match the existing seed semantics in `db/seed/uds_seed.sql`.

## Primary Demo Flow

### 1. Show the baseline

Open the UDS Incident Workbench in Grafana and show the current fleet state.

### 2. Inject an incident

Run from the repo root (or from inside the `agent` container):

```bash
# From host (requires asyncpg installed locally):
python scripts/inject_dynamic_incident.py --scenario service_down

# Or from inside the agent container:
docker compose exec agent python /app/scripts/inject_dynamic_incident.py --scenario service_down
```

The script prints the exact `POST` body to use next.

### 3. Trigger the dynamic dashboard

```bash
curl -X POST http://localhost:8000/api/v1/dynamic/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "vessel_imo": "IMO9300002",
    "app_external_id": "uds-edge-parquet-sync",
    "alert_name": "ServiceDown",
    "severity": "critical",
    "mode": "explicit_context"
  }'
```

### 4. Open the generated dashboard

Navigate to: http://localhost:3000/d/maritime_dynamic_incident

The dashboard should show incident-specific panels for the vessel and application.

### 5. Drill back to static dashboards

Use the links in the generated dashboard to jump to the UDS Incident Workbench
or NOC Support dashboard for additional context.

## Fallback Flow (explicit_context without injection)

If the injection script fails or the DB is not reachable from the host, use the
trigger endpoint with `explicit_context` mode directly. The orchestrator will
fetch whatever context exists for the given vessel/app pair:

```bash
curl -X POST http://localhost:8000/api/v1/dynamic/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "vessel_imo": "IMO9300001",
    "app_external_id": "data-quality-processor",
    "alert_name": "ReportingStale",
    "severity": "warning",
    "mode": "explicit_context"
  }'
```

This works because the seed SQL already creates alerts for these vessel/app pairs.

## Connectivity Scenario Demo

```bash
python scripts/inject_dynamic_incident.py --scenario connectivity

curl -X POST http://localhost:8000/api/v1/dynamic/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "vessel_imo": "IMO9300001",
    "app_external_id": "data-quality-processor",
    "alert_name": "ReportingStale",
    "severity": "warning",
    "mode": "explicit_context"
  }'
```

## Dry-run Mode (Grafana-less Fallback)

If Grafana is unreachable on demo day, you can still produce the generated
dashboard JSON by passing `dry_run: true`:

```bash
curl -X POST http://localhost:8000/api/v1/dynamic/trigger \
  -H "Content-Type: application/json" \
  -d '{
    "vessel_imo": "IMO9300002",
    "app_external_id": "uds-edge-parquet-sync",
    "alert_name": "ServiceDown",
    "severity": "critical",
    "mode": "explicit_context",
    "dry_run": true
  }'
```

The response will include the full `dashboard_json` payload that *would* have
been written to Grafana. The orchestrator still records the run in
`dynamic_dashboard_runs` with `dry_run = TRUE` so the audit story holds.

## Checking the Runs Log

After triggering, the run should appear in the `dynamic_dashboard_runs` table:

```sql
SELECT id, created_at, scenario_key, vessel_imo, app_external_id,
       dashboard_uid, dry_run
FROM dynamic_dashboard_runs
ORDER BY created_at DESC
LIMIT 5;
```

You can also reach the same data via the API:

```bash
curl http://localhost:8000/api/v1/dynamic/status | jq
```

## Listing Available Scenarios

```bash
python scripts/inject_dynamic_incident.py --list
```

## Reset Between Demo Runs

To start completely fresh:

```bash
docker compose down -v
docker compose up -d --build
# Wait for backfill, then inject again
```

**Re-running without a full reset is safe.** Each scenario uses a stable
fingerprint, and the inject script wipes any prior injection of the same
scenario (alerts, generated logs, metric samples) before inserting a fresh
copy. So you can run:

```bash
python scripts/inject_dynamic_incident.py --scenario service_down
# ... do the demo, then inject the same scenario again ...
python scripts/inject_dynamic_incident.py --scenario service_down
```

and end up with exactly one alert/log/metric set per scenario, with fresh
timestamps. The auto-generated `app_logs` row is created by the
`trg_sync_app_log_from_alert` trigger in `db/init/003_uds.sql` -- the script
no longer inserts logs by hand.
