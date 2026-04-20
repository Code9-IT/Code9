#!/usr/bin/env python3
"""
inject_dynamic_incident.py
==========================
Deterministic incident injector for the dynamic-dashboard demo.

Creates a known alert + degraded metric samples for a specific vessel/app
pair so the dynamic trigger endpoint has something concrete to act on.
The corresponding ``app_logs`` row is created automatically by the
``trg_sync_app_log_from_alert`` trigger defined in
``db/init/003_uds.sql`` -- the script no longer inserts logs by hand.

Reruns are safe: each scenario uses a stable fingerprint so a previous
injection of the same scenario is wiped first (alerts, generated logs,
metric samples), then re-inserted with fresh timestamps.

Usage:
    python scripts/inject_dynamic_incident.py --scenario service_down
    python scripts/inject_dynamic_incident.py --scenario connectivity
    python scripts/inject_dynamic_incident.py --scenario runtime_pressure
    python scripts/inject_dynamic_incident.py --list

Runs against the same PostgreSQL database used by the rest of the stack.
Uses asyncpg with parameterized queries only.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from uuid import uuid4

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg is required.  pip install asyncpg")
    sys.exit(1)

# DB connection defaults (same env vars as the agent service)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "maritime_telemetry")

# Scenario definitions
# Each scenario maps to a deterministic vessel + app + alert combination
# that aligns with the existing seed semantics in uds_seed.sql.
SCENARIOS: dict[str, dict] = {
    "service_down": {
        "vessel_imo": "IMO9300002",
        "app_external_id": "uds-edge-parquet-sync",
        "alert_name": "ServiceDown",
        "severity": "critical",
        "alert_type": "service_down",
        "summary": (
            "Health checks are failing and uds-edge-parquet-sync is "
            "unavailable on MV Edge Borealis. Injected for dynamic-"
            "dashboard demo."
        ),
        "description": "Service down on MV Edge Borealis (IMO9300002) / uds-edge-parquet-sync",
    },
    "connectivity": {
        "vessel_imo": "IMO9300001",
        "app_external_id": "data-quality-processor",
        "alert_name": "ReportingStale",
        "severity": "warning",
        "alert_type": "reporting_stale",
        "summary": (
            "data-quality-processor on MV Edge Aurora has not reported "
            "fresh metrics in the expected window; showing last known "
            "values. Injected for dynamic-dashboard demo."
        ),
        "description": "Connectivity / stale reporting on MV Edge Aurora (IMO9300001) / data-quality-processor",
    },
    "runtime_pressure": {
        "vessel_imo": "IMO9300003",
        "app_external_id": "time-series-processor",
        "alert_name": "ResourcePressure",
        "severity": "warning",
        "alert_type": "resource_pressure",
        "summary": (
            "CPU, memory, and request latency are elevated on time-"
            "series-processor on MT Nordic Fjord. Injected for dynamic-"
            "dashboard demo."
        ),
        "description": "Runtime pressure on MT Nordic Fjord (IMO9300003) / time-series-processor",
    },
    "propulsion_anomaly": {
        "vessel_imo": "IMO9300001",
        "app_external_id": "time-series-processor",
        "alert_name": "SeverePropulsionAnomaly",
        "severity": "critical",
        "alert_type": "propulsion_anomaly",
        "summary": (
            "CRITICAL — Multiple propulsion-related signals on MV Edge Aurora "
            "are showing simultaneous extreme deviations. Shaft vibration has "
            "spiked to dangerous levels (>20 mm/s vs normal 2-3 mm/s), "
            "propulsion power has dropped sharply, vessel speed is falling "
            "despite engines compensating at high load, and stern tube "
            "temperature is rising rapidly. This pattern is consistent with "
            "severe physical obstruction or impact damage to the propeller "
            "assembly. The AI agent has identified this as a rare multi-signal "
            "anomaly that requires immediate investigation by the chief "
            "engineer. This is NOT a routine alarm — the simultaneous failure "
            "pattern across vibration, power, speed, and temperature channels "
            "indicates a structural propulsion event."
        ),
        "description": (
            "Severe propulsion anomaly on MV Edge Aurora (IMO9300001) — "
            "simultaneous extreme deviations across shaft vibration, "
            "propulsion power, vessel speed, and stern tube temperature"
        ),
    },
}


def _fingerprint(vessel_imo: str, app_id: str, scenario: str) -> str:
    """Stable fingerprint per scenario so reruns wipe and replace cleanly."""
    raw = f"{vessel_imo}:{app_id}:{scenario}:dynamic-inject"
    return hashlib.md5(raw.encode()).hexdigest()


async def _resolve_ids(
    conn: asyncpg.Connection,
    vessel_imo: str,
    app_external_id: str,
) -> tuple[str, str]:
    """Look up the UDS location UUID and application UUID."""
    loc_id = await conn.fetchval(
        "SELECT id FROM udslocations WHERE imo_nr = $1", vessel_imo
    )
    if loc_id is None:
        raise SystemExit(f"Vessel {vessel_imo} not found in udslocations")

    app_id = await conn.fetchval(
        "SELECT id FROM applications WHERE external_id = $1", app_external_id
    )
    if app_id is None:
        raise SystemExit(f"Application {app_external_id} not found in applications")

    return loc_id, app_id


async def _wipe_previous(
    conn: asyncpg.Connection,
    sc: dict,
    scenario_key: str,
    fingerprint: str,
) -> None:
    """Remove any prior injection of this scenario.

    Order matters because of FK + UNIQUE constraints:
      1. app_logs (FK to alerts via alert_id)
      2. metric_samples (no FK but tagged with labels)
      3. alerts (parent row)
    """
    await conn.execute(
        "DELETE FROM app_logs WHERE correlation_key = $1",
        fingerprint,
    )
    await conn.execute(
        """
        DELETE FROM metric_samples
        WHERE imo_nr = $1
          AND app_id = $2
          AND labels ->> 'source' = 'dynamic_inject'
          AND labels ->> 'scenario' = $3
        """,
        sc["vessel_imo"],
        sc["app_external_id"],
        scenario_key,
    )
    await conn.execute(
        "DELETE FROM alerts WHERE fingerprint = $1",
        fingerprint,
    )


async def inject(scenario_key: str) -> None:
    """Insert one alert (which auto-creates a log) + degraded metric samples."""
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}")
        print(f"Available: {', '.join(SCENARIOS)}")
        sys.exit(1)

    sc = SCENARIOS[scenario_key]
    now = datetime.now(timezone.utc).replace(microsecond=0)
    ts_str = now.isoformat()
    fingerprint = _fingerprint(sc["vessel_imo"], sc["app_external_id"], scenario_key)

    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    try:
        loc_id, app_id = await _resolve_ids(conn, sc["vessel_imo"], sc["app_external_id"])

        # 0. Wipe any prior injection so reruns are deterministic
        await _wipe_previous(conn, sc, scenario_key, fingerprint)

        # 1. Insert the alert. The trg_sync_app_log_from_alert trigger
        #    automatically creates a matching app_logs row using
        #    annotations.summary as the user-facing message.
        alert_id = uuid4()
        starts_at = now - timedelta(minutes=3)

        labels = {
            "imo": sc["vessel_imo"],
            "app_id": sc["app_external_id"],
            "scenario": scenario_key,
            "injected": True,
        }
        annotations = {
            "summary": sc["summary"],
            "injected_at": ts_str,
        }

        await conn.execute(
            """
            INSERT INTO alerts (
                id, uds_location_id, application_id,
                alert_name, severity, status, alert_type, fingerprint,
                labels, annotations, starts_at, ends_at, received_at
            ) VALUES (
                $1, $2, $3,
                $4, $5, 'firing', $6, $7,
                $8::jsonb, $9::jsonb, $10, NULL, $11
            )
            """,
            alert_id,
            loc_id,
            app_id,
            sc["alert_name"],
            sc["severity"],
            sc["alert_type"],
            fingerprint,
            json.dumps(labels),
            json.dumps(annotations),
            starts_at,
            now,
        )
        print(f"  Alert inserted:  {alert_id}  ({sc['alert_name']}, {sc['severity']})")
        print("  Log inserted:    auto-generated by trg_sync_app_log_from_alert")

        # 2. Insert degraded metric samples
        sync_id = uuid4()
        metric_rows = _build_metric_rows(sc, scenario_key, sync_id, now, loc_id, app_id)
        inserted = 0
        for row in metric_rows:
            await conn.execute(
                """
                INSERT INTO metric_samples (
                    sync_id, app_id, metric_name, time,
                    application_instance_id, value, min_value, max_value,
                    metric_type, metric_unit, imo_nr, labels
                ) VALUES (
                    $1, $2, $3, $4,
                    $5, $6, $7, $8,
                    $9, $10, $11, $12::jsonb
                )
                ON CONFLICT DO NOTHING
                """,
                *row,
            )
            inserted += 1
        print(f"  Metrics inserted: {inserted} samples")

        print()
        print(f"Scenario '{scenario_key}' injected successfully.")
        print(f"  Vessel:      {sc['vessel_imo']}")
        print(f"  Application: {sc['app_external_id']}")
        print(f"  Alert:       {sc['alert_name']} ({sc['severity']})")
        print(f"  Fingerprint: {fingerprint}")
        print()
        print("Next step: call POST /api/v1/dynamic/trigger with:")
        print(f'  {{"vessel_imo": "{sc["vessel_imo"]}", '
              f'"app_external_id": "{sc["app_external_id"]}", '
              f'"alert_name": "{sc["alert_name"]}", '
              f'"severity": "{sc["severity"]}", '
              f'"source_alert_fingerprint": "{fingerprint}", '
              f'"mode": "explicit_context"}}')

    finally:
        await conn.close()


def _build_metric_rows(
    sc: dict,
    scenario_key: str,
    sync_id,
    now: datetime,
    loc_id,
    app_id,
) -> list[tuple]:
    """Build degraded metric sample tuples matching uds_seed.sql patterns."""
    import random
    random.seed(f"{sc['vessel_imo']}:{sc['app_external_id']}:{scenario_key}")

    labels = {
        "app_id": sc["app_external_id"],
        "imo": sc["vessel_imo"],
        "source": "dynamic_inject",
        "scenario": scenario_key,
        "injected": True,
    }
    labels_json = json.dumps(labels)

    # Core metrics that matter for each scenario
    if scenario_key == "service_down":
        metrics = [
            ("service_up", 0.0, "Application", "Count"),
            ("health_check_status", 0.0, "Application", "Count"),
            ("http_error_rate_5xx", 35.0 + random.random() * 30, "Application", "Percent"),
            ("process_cpu_usage", 85.0 + random.random() * 12, "Application", "Percent"),
            ("process_uptime_seconds", 90.0 + random.random() * 200, "Application", "Seconds"),
        ]
    elif scenario_key == "connectivity":
        metrics = [
            ("service_up", 1.0, "Application", "Count"),
            ("reporting_stale", 1.0, "Connectivity", "Count"),
            ("last_sync_age_seconds", 2800.0 + random.random() * 1800, "Connectivity", "Seconds"),
            ("process_cpu_usage", 12.0 + random.random() * 20, "Application", "Percent"),
        ]
    elif scenario_key == "runtime_pressure":
        metrics = [
            ("service_up", 1.0, "Application", "Count"),
            ("process_cpu_usage", 72.0 + random.random() * 18, "Application", "Percent"),
            ("process_memory_bytes", 850000000.0 + random.random() * 800000000, "Application", "Bytes"),
            ("http_request_duration_p95", 1.2 + random.random() * 1.5, "Application", "Seconds"),
            ("http_error_rate_5xx", 5.0 + random.random() * 8, "Application", "Percent"),
        ]
    elif scenario_key == "propulsion_anomaly":
        metrics = None  # handled separately below with time-evolving values
    else:
        metrics = [
            ("service_up", 1.0, "Application", "Count"),
        ]

    # --- Propulsion anomaly: realistic time-evolving sensor traces --------
    if scenario_key == "propulsion_anomaly":
        rows = []
        # Build 12 samples over the last hour: first 4 normal, then
        # escalating to extreme.  This gives the time-series chart a
        # visible "moment of impact" curve.
        sample_times = [now - timedelta(minutes=m) for m in reversed(range(0, 60, 5))]
        impact_index = 4  # sample 5 of 12 is when the event starts

        # (metric_name, normal, peak, unit, metric_type)
        propulsion_metrics = [
            ("shaft_vibration_mm_s",     2.5,   22.0,  "mm/s",    "Gauge"),
            ("propulsion_power_kw",   8000.0, 2200.0,  "kW",      "Gauge"),
            ("vessel_speed_knots",      18.0,    7.5,  "knots",   "Gauge"),
            ("engine_load_pct",         58.0,   94.0,  "Percent", "Gauge"),
            ("propeller_rpm",          120.0,   45.0,  "RPM",     "Gauge"),
            ("stern_tube_temp_c",       45.0,   82.0,  "Celsius", "Gauge"),
        ]

        for mi, (metric_name, normal, peak, unit, metric_type) in enumerate(propulsion_metrics):
            for ti, t in enumerate(sample_times):
                if ti < impact_index:
                    # Normal readings with small jitter
                    value = normal * (1.0 + (random.random() - 0.5) * 0.04)
                else:
                    # Escalate toward peak over the remaining samples
                    progress = (ti - impact_index) / max(1, len(sample_times) - impact_index - 1)
                    value = normal + (peak - normal) * min(1.0, progress * 1.1)
                    value *= (1.0 + (random.random() - 0.5) * 0.06)

                rows.append((
                    sync_id,
                    sc["app_external_id"],
                    metric_name,
                    t,
                    app_id,
                    float(value),
                    None,
                    None,
                    metric_type,
                    unit,
                    sc["vessel_imo"],
                    labels_json,
                ))
        return rows

    rows = []
    times = [now - timedelta(minutes=m) for m in [20, 10, 0]]
    for metric_name, base_value, metric_type, metric_unit in metrics:
        for t in times:
            jitter = random.random() * 0.08
            value = max(0.0, base_value * (1.0 + (random.random() - 0.5) * 0.1))
            min_val = max(0.0, value * (1.0 - jitter)) if metric_type != "Count" else None
            max_val = max(0.0, value * (1.0 + jitter)) if metric_type != "Count" else None
            rows.append((
                sync_id,
                sc["app_external_id"],
                metric_name,
                t,
                app_id,
                value,
                min_val,
                max_val,
                metric_type,
                metric_unit,
                sc["vessel_imo"],
                labels_json,
            ))

    return rows


def main():
    parser = argparse.ArgumentParser(
        description="Inject a deterministic incident for dynamic-dashboard demo"
    )
    parser.add_argument(
        "--scenario",
        choices=list(SCENARIOS.keys()),
        help="Scenario to inject",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit",
    )
    args = parser.parse_args()

    if args.list:
        print("Available scenarios:")
        for key, sc in SCENARIOS.items():
            print(f"  {key:20s} -- {sc['description']}")
        sys.exit(0)

    if not args.scenario:
        parser.print_help()
        sys.exit(1)

    print(f"Injecting scenario: {args.scenario}")
    print(f"  {SCENARIOS[args.scenario]['description']}")
    print()
    asyncio.run(inject(args.scenario))


if __name__ == "__main__":
    main()
