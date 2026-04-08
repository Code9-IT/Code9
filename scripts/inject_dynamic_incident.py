#!/usr/bin/env python3
"""
inject_dynamic_incident.py
==========================
Deterministic incident injector for the dynamic-dashboard demo.

Creates a known alert + log entry + degraded metric samples for a
specific vessel/app pair so the dynamic trigger endpoint has something
concrete to act on.

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
import os
import sys
from datetime import datetime, timezone, timedelta
from uuid import uuid4

try:
    import asyncpg
except ImportError:
    print("ERROR: asyncpg is required.  pip install asyncpg")
    sys.exit(1)

# ── DB connection defaults (same env vars as the agent service) ──────────
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "maritime_telemetry")

# ── Scenario definitions ────────────────────────────────────────────────
# Each scenario maps to a deterministic vessel + app + alert combination
# that aligns with the existing seed semantics in uds_seed.sql.
SCENARIOS: dict[str, dict] = {
    "service_down": {
        "vessel_imo": "IMO9300002",
        "app_external_id": "uds-edge-parquet-sync",
        "alert_name": "ServiceDown",
        "severity": "critical",
        "alert_type": "service_down",
        "log_level": "error",
        "log_source": "application",
        "log_message": (
            "Health checks are failing and the application is unavailable. "
            "Injected for dynamic-dashboard demo."
        ),
        "description": "Service down on MV Nordic Bulk (IMO9300002) / uds-edge-parquet-sync",
    },
    "connectivity": {
        "vessel_imo": "IMO9300001",
        "app_external_id": "data-quality-processor",
        "alert_name": "ReportingStale",
        "severity": "warning",
        "alert_type": "reporting_stale",
        "log_level": "warning",
        "log_source": "sync-agent",
        "log_message": (
            "No fresh metrics received in the expected reporting window; "
            "showing last known values. Injected for dynamic-dashboard demo."
        ),
        "description": "Connectivity / stale reporting on MV Edge Aurora (IMO9300001) / data-quality-processor",
    },
    "runtime_pressure": {
        "vessel_imo": "IMO9300003",
        "app_external_id": "time-series-processor",
        "alert_name": "ResourcePressure",
        "severity": "warning",
        "alert_type": "resource_pressure",
        "log_level": "warning",
        "log_source": "runtime",
        "log_message": (
            "CPU, handle count, or database pressure is elevated. "
            "Injected for dynamic-dashboard demo."
        ),
        "description": "Runtime pressure on MV Coastal Spirit (IMO9300003) / time-series-processor",
    },
}


def _fingerprint(vessel_imo: str, app_id: str, scenario: str, ts: str) -> str:
    """Deterministic fingerprint matching the seed convention."""
    raw = f"{vessel_imo}:{app_id}:{scenario}:{ts}:dynamic-inject"
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


async def inject(scenario_key: str) -> None:
    """Insert one alert + one log entry + degraded metric samples."""
    if scenario_key not in SCENARIOS:
        print(f"Unknown scenario: {scenario_key}")
        print(f"Available: {', '.join(SCENARIOS)}")
        sys.exit(1)

    sc = SCENARIOS[scenario_key]
    now = datetime.now(timezone.utc).replace(microsecond=0)
    ts_str = now.isoformat()
    fingerprint = _fingerprint(sc["vessel_imo"], sc["app_external_id"], scenario_key, ts_str)

    conn = await asyncpg.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    try:
        loc_id, app_id = await _resolve_ids(conn, sc["vessel_imo"], sc["app_external_id"])

        # ── 1. Insert the alert ──────────────────────────────────────
        alert_id = uuid4()
        starts_at = now - timedelta(minutes=3)

        await conn.execute(
            """
            INSERT INTO alerts (
                id, uds_location_id, application_id,
                alert_name, severity, status, alert_type, fingerprint,
                labels, annotations, starts_at, ends_at, received_at
            ) VALUES (
                $1, $2, $3,
                $4, $5, 'firing', $6, $7,
                $8, $9, $10, NULL, $11
            )
            """,
            alert_id,
            loc_id,
            app_id,
            sc["alert_name"],
            sc["severity"],
            sc["alert_type"],
            fingerprint,
            {
                "imo": sc["vessel_imo"],
                "app_id": sc["app_external_id"],
                "scenario": scenario_key,
                "injected": True,
            },
            {
                "summary": f'{sc["alert_name"]} detected for {sc["app_external_id"]}',
                "injected_at": ts_str,
            },
            starts_at,
            now,
        )
        print(f"  Alert inserted:  {alert_id}  ({sc['alert_name']}, {sc['severity']})")

        # ── 2. Insert an app log ─────────────────────────────────────
        log_id = uuid4()
        await conn.execute(
            """
            INSERT INTO app_logs (
                id, uds_location_id, application_id, app_external_id,
                level, source, message, logged_at,
                alert_id, correlation_key, context
            ) VALUES (
                $1, $2, $3, $4,
                $5, $6, $7, $8,
                $9, $10, $11
            )
            """,
            log_id,
            loc_id,
            app_id,
            sc["app_external_id"],
            sc["log_level"],
            sc["log_source"],
            sc["log_message"],
            now - timedelta(minutes=2),
            alert_id,
            fingerprint,
            {
                "imo": sc["vessel_imo"],
                "app_id": sc["app_external_id"],
                "scenario": scenario_key,
                "injected": True,
            },
        )
        print(f"  Log inserted:    {log_id}")

        # ── 3. Insert degraded metric samples ────────────────────────
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
                    $9, $10, $11, $12
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
    else:
        metrics = [
            ("service_up", 1.0, "Application", "Count"),
        ]

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
                labels,
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
            print(f"  {key:20s} — {sc['description']}")
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
