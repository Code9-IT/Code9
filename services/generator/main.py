"""
Maritime Synthetic Data Generator
==================================
Continuously writes telemetry rows – and occasional anomaly events –
into TimescaleDB.  This populates the Grafana dashboards and gives
the AI agent events to analyse.

Configuration (all via env vars, see .env.example):
  GENERATE_INTERVAL_SECONDS   – seconds between write cycles (default 3)
  ANOMALY_PROBABILITY         – per-sensor probability per cycle (default 0.00008,
                                ~1 event per 8 min with 77 threshold combinations)

TODO: add a "burst" mode that fires several anomalies quickly for live demos.
"""

import os
import time

from db        import get_connection
from sensors   import generate_telemetry_batch, VESSELS
from anomalies import maybe_generate_anomaly

# ─── Configuration ───────────────────────────────────────
INTERVAL      = int(os.getenv("GENERATE_INTERVAL_SECONDS", "3"))
ANOMALY_PROB  = float(os.getenv("ANOMALY_PROBABILITY",      "0.00008"))

# ─── SQL ──────────────────────────────────────────────────
INSERT_TELEMETRY = """
    INSERT INTO telemetry (vessel_id, sensor_name, value)
    VALUES (%(vessel_id)s, %(sensor_name)s, %(value)s);
"""

INSERT_EVENT = """
    INSERT INTO events (vessel_id, sensor_name, event_type, severity, details)
    VALUES (%(vessel_id)s, %(sensor_name)s, %(event_type)s, %(severity)s, %(details)s);
"""


# ─── Main loop ────────────────────────────────────────────
def main():
    print("[generator] Starting … waiting for database …")
    conn = get_connection()
    print(f"[generator] Running – interval={INTERVAL}s, anomaly_prob={ANOMALY_PROB}")

    cycle = 0
    while True:
        try:
            with conn.cursor() as cur:
                # 1) Normal telemetry for every sensor on every vessel
                batch = generate_telemetry_batch()
                cur.executemany(INSERT_TELEMETRY, batch)

                # 2) Maybe produce an anomaly for each vessel
                for vessel in VESSELS:
                    anomaly = maybe_generate_anomaly(vessel, ANOMALY_PROB)
                    if anomaly:
                        # Insert the anomalous reading into telemetry
                        cur.execute(INSERT_TELEMETRY, {
                            "vessel_id":   anomaly["vessel_id"],
                            "sensor_name": anomaly["sensor_name"],
                            "value":       anomaly["telemetry_value"],
                        })
                        # Insert the event record
                        cur.execute(INSERT_EVENT, {
                            "vessel_id":  anomaly["vessel_id"],
                            "sensor_name":anomaly["sensor_name"],
                            "event_type": anomaly["event_type"],
                            "severity":   anomaly["severity"],
                            "details":    anomaly["details"],
                        })
                        print(f"[generator] ANOMALY → {anomaly['event_type']} on {anomaly['vessel_id']} (severity={anomaly['severity']})")

                conn.commit()

            cycle += 1
            if cycle % 20 == 0:
                print(f"[generator] … cycle {cycle}")

            time.sleep(INTERVAL)

        except Exception as exc:                    # pragma: no cover
            print(f"[generator] ERROR in cycle: {exc}")
            try:
                conn.rollback()
            except Exception:
                pass
            # conn.closed is non-zero when psycopg2 knows the connection is gone
            # (covers server-side termination, network drop, and explicit close).
            # Check this regardless of whether rollback succeeded.
            if conn.closed:
                print("[generator] Connection lost – reconnecting …")
                try:
                    conn = get_connection()
                except Exception as reconnect_exc:
                    print(f"[generator] Reconnection failed: {reconnect_exc}")
            time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
