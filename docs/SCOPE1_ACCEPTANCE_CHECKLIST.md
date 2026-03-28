# Scope 1 Acceptance Checklist

Last updated: 2026-03-28

Use this checklist when the group wants to verify that Scope 1 still works on a
fresh stack.

## 0. Demo prep timing

After `docker compose down -v` and `docker compose up -d --build`, the UDS
seeder backfills 6 hours of history before it starts the regular 30-minute seed
loop. This gives Grafana time-series panels usable history from the first page
load instead of starting with empty charts.

Watch the seeder logs to confirm backfill completes:

```bash
docker compose logs -f uds-seeder
```

Expected backfill output:

- `Fresh database detected - backfilling 6 hours of historical data`
- `backfill cycle: -330m`
- `backfill cycle: -300m`
- ...
- `Backfill complete (11 historical cycles inserted)`

After the backfill and the first live seed cycle finish, the UDS dashboards are
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
- `uds-seeder` waits for schema/reference data, backfills 6 hours, then starts
  the regular seed loop

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

## 8. Scope 2 acceptance (additional checks)

After Scope 2 changes are merged, also verify:

### Fleet overview dashboard
1. Open `Fleet Overview` dashboard in Grafana
2. Confirm fleet health cards show all 3 vessels with status
3. Confirm cross-vessel alert table shows alerts across vessels
4. Confirm correlation view highlights shared issues
5. Click a vessel and confirm drilldown navigates to UDS Incident Monitoring
   with the correct vessel pre-selected

### Scope 2 MCP tools
Check that these tools return meaningful data:

```bash
# Fleet status
curl -X POST http://localhost:8001/tools/get_fleet_status \
  -H "Content-Type: application/json" \
  -H "X-API-Key: code9-scope1-demo-key" \
  -d '{}'

# Cross-vessel correlation
curl -X POST http://localhost:8001/tools/get_cross_vessel_correlation \
  -H "Content-Type: application/json" \
  -H "X-API-Key: code9-scope1-demo-key" \
  -d '{"hours": 24}'

# Incident timeline
curl -X POST http://localhost:8001/tools/get_incident_timeline \
  -H "Content-Type: application/json" \
  -H "X-API-Key: code9-scope1-demo-key" \
  -d '{"vessel_id": "IMO9300001"}'

# Operational snapshot
curl -X POST http://localhost:8001/tools/get_operational_snapshot \
  -H "Content-Type: application/json" \
  -H "X-API-Key: code9-scope1-demo-key" \
  -d '{"vessel_id": "IMO9300001"}'
```

Pass condition:
- Fleet status shows all 3 vessels with derived status
- Cross-vessel correlation finds at least one shared issue (data-quality-processor)
- Incident timeline returns chronological events for the vessel
- Operational snapshot returns complete vessel state
