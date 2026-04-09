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

## Checking the Runs Log

After triggering, the run should appear in the `dynamic_dashboard_runs` table:

```sql
SELECT id, created_at, scenario_key, vessel_imo, app_external_id, dashboard_uid
FROM dynamic_dashboard_runs
ORDER BY created_at DESC
LIMIT 5;
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

To re-inject without a full reset, just run the inject script again. The alert
insert uses `ON CONFLICT DO NOTHING`-style unique fingerprints, so duplicate
runs are safe and will produce new alerts with fresh timestamps.
