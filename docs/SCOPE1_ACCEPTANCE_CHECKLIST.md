# Scope 1 Acceptance Checklist

Last updated: 2026-03-16

Use this checklist when the group wants to verify that Scope 1 still works on a
fresh stack.

## 0. Demo prep timing

After `docker compose down -v && up -d --build`, the UDS seeder automatically
backfills 6 hours of historical data (11 seed cycles at 30-min intervals) before
starting the regular 30-minute loop. This means the Grafana time-series panels
will have chart history from the very first page load.

Watch the seeder logs to confirm backfill completes:

```bash
docker compose logs -f uds-seeder
```

You should see lines like `backfill cycle: -330m`, `backfill cycle: -300m`, etc.,
followed by `Backfill complete (11 historical cycles inserted)`.

After backfill finishes and the first live seed cycle runs, the dashboard is
ready to present.

## 1. Reset and start from a fresh DB

```bash
docker compose down -v
docker compose up -d --build
```

Then watch startup logs:

```bash
docker compose logs -f ollama-init agent generator uds-seeder
```

Expected:

- `ollama-init` pulls `llama3.2` and `nomic-embed-text`
- the agent retries RAG ingest until embeddings are available
- the generator starts inserting legacy telemetry/events
- `uds-seeder` backfills 6h of history, then starts the regular 30-min seed loop

## 2. Confirm UDS schema and reference data exist

Minimum expectation:

- `udslocations` exists
- `applications` exists
- `uds_location_application_instances` exists
- `metric_samples` exists
- `alerts` exists
- `app_logs` exists

The demo reference data should include:

- 3 vessels
- 6 applications
- 18 vessel/application link rows

## 3. Confirm seeding is active

Expected after startup settles:

- rows are inserted into `metric_samples`
- rows are inserted into `alerts`
- rows are inserted into `app_logs`
- seeded alert types are not limited to only `service_down`

Observed on the 2026-03-12 rerun:

- `metric_samples`: 468
- `alerts`: 11
- `app_logs`: 29

Those exact counts will change over time. The important part is that all three
tables receive rows on a fresh run.

## 4. Grafana acceptance

1. Open Grafana at `http://localhost:3000`
2. Open `UDS Incident Monitoring`
3. Select `IMO9300001`
4. Confirm the dashboard shows:
   - `Active Alerts`
   - `Active Incident Queue`
   - `Application Incident Board`
   - `Selected App Recent Alerts`
   - `Selected App Recent Logs`
   - time-series metric history panels
   - `Connectivity And Freshness`
5. Click `Application` or `App ID` in an incident table
6. Confirm the selected app drilldown updates on the same dashboard
7. Change `incident_window` and confirm the drilldown panels follow the new
   time slice

Pass condition:

- Grafana clearly supports alert -> app -> recent metric/log history for one
  vessel

## 5. MCP acceptance

Check that these tools return meaningful incident data for a demo vessel:

- `get_vessel_app_status`
- `get_vessel_alerts`
- `get_app_metric_history`
- `get_app_logs`

Example request:

```bash
curl -X POST http://localhost:8001/tools/call \
  -H "Content-Type: application/json" \
  -H "X-API-Key: code9-scope1-demo-key" \
  -d '{"name":"get_vessel_app_status","arguments":{"vessel_id":"IMO9300001"}}'
```

Pass condition:

- vessel status, alerts, metric history, and logs are all queryable for the
  same vessel/app context

## 6. Validation and legacy-analysis sanity check

This is a legacy-path sanity check, not the main Scope 1 proof point.

1. Open `http://localhost:8000/api/v1/validate/dashboard`
2. Run a quick validation on a recent legacy event
3. Confirm:
   - the page loads
   - quick validation completes
   - retrieved docs are shown when relevant

Optional extra signoff:

1. Queue a full analysis on a recent legacy event
2. Confirm it eventually leaves `running`
3. Only treat that path as demo-ready if it has been warmed up and checked on
   the current merge candidate

Pass condition:

- validation dashboard loads and quick validation works
- full analysis is a secondary check, not the main Scope 1 blocker

## 7. Final signoff rule

Scope 1 is good enough for demo/merge when:

- the stack starts from a fresh DB volume
- UDS schema and reference data load correctly
- seeded metrics, alerts, and logs appear
- Grafana shows incident-first vessel/app context
- MCP tools return matching incident data
- no new regression is introduced in the validation dashboard or quick analysis
