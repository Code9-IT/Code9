"""
Anomaly / event generation
============================
Randomly produces threshold-breach events so that the Grafana
dashboards and the AI agent have something to react to during demos.

Probability is controlled by the ANOMALY_PROBABILITY env var
(default 0.05 = 5 % chance per vessel per cycle).

Burst mode is controlled by BURST_MODE env var (default false). When true,
each cycle emits 3-5 anomalies across different sensors/vessels.

TODO: add time-of-day or vessel-state weighting for more realistic patterns.
"""

import os
import random
from typing import Optional


# ─── Event type catalogue ─────────────────────────────────
# Each key maps to:
#   sensor   – which sensor triggers the event
#   kind     – 'high' or 'low' (which threshold was breached)
#   value_range – (min, max) of the anomalous reading we fabricate
EVENT_DEFINITIONS: dict = {
    "HIGH_TEMPERATURE":      {"sensor": "engine_temp",      "kind": "high", "value_range": (85, 95)},
    "HIGH_COOLANT_TEMP":     {"sensor": "coolant_temp",     "kind": "high", "value_range": (70, 80)},
    "LOW_OIL_PRESSURE":      {"sensor": "oil_pressure",     "kind": "low",  "value_range": (0.5, 2.0)},
    "HIGH_RPM":              {"sensor": "engine_rpm",       "kind": "high", "value_range": (1500, 1800)},
    "HIGH_FUEL_CONSUMPTION": {"sensor": "fuel_consumption", "kind": "high", "value_range": (45, 55)},
    "HIGH_HULL_TEMP":        {"sensor": "hull_temp",        "kind": "high", "value_range": (50, 60)},
    "HIGH_NAV_SPEED":        {"sensor": "nav_speed",        "kind": "high", "value_range": (26, 35)},
    "HIGH_RUDDER_ANGLE":     {"sensor": "rudder_angle",     "kind": "high", "value_range": (20, 35)},
    "LOW_RUDDER_ANGLE":      {"sensor": "rudder_angle",     "kind": "low",  "value_range": (-35, -20)},
}

_TRUE_VALUES = {"1", "true", "yes", "y", "on"}
BURST_MODE = os.getenv("BURST_MODE", "false").strip().lower() in _TRUE_VALUES


def _severity(event_type: str, value: float) -> str:
    """Simple rule: value in the upper quarter of the anomaly range → critical."""
    lo, hi = EVENT_DEFINITIONS[event_type]["value_range"]
    return "critical" if value >= lo + 0.75 * (hi - lo) else "warning"


def _build_anomaly(vessel_id: str, event_type: str) -> dict:
    defn = EVENT_DEFINITIONS[event_type]

    anomaly_value = round(random.uniform(*defn["value_range"]), 2)
    severity = _severity(event_type, anomaly_value)

    direction = "upper" if defn["kind"] == "high" else "lower"
    details = (
        f"Sensor '{defn['sensor']}' breached {direction} threshold. "
        f"Current value: {anomaly_value}."
    )

    return {
        "vessel_id": vessel_id,
        "sensor_name": defn["sensor"],
        "event_type": event_type,
        "severity": severity,
        "details": details,
        "telemetry_value": anomaly_value,  # the fake reading to insert
    }


def maybe_generate_anomaly(vessel_id: str, probability: float) -> Optional[dict]:
    """
    With the given *probability*, pick a random event type and
    return a dict describing it.  Returns None if no anomaly fires.

    The returned dict contains everything needed to:
      - insert a row into *events*
      - insert the anomalous telemetry point into *telemetry*
    """
    if random.random() > probability:
        return None

    event_type = random.choice(list(EVENT_DEFINITIONS.keys()))
    return _build_anomaly(vessel_id, event_type)


def _generate_burst_anomalies(vessels: list[str]) -> list[dict]:
    target = random.randint(3, 5)
    event_types = list(EVENT_DEFINITIONS.keys())

    candidates = [(vessel, event_type) for vessel in vessels for event_type in event_types]
    random.shuffle(candidates)

    selected: list[dict] = []
    used_pairs: set[tuple[str, str]] = set()

    for vessel, event_type in candidates:
        sensor = EVENT_DEFINITIONS[event_type]["sensor"]
        pair = (vessel, sensor)
        if pair in used_pairs:
            continue
        selected.append(_build_anomaly(vessel, event_type))
        used_pairs.add(pair)
        if len(selected) >= target:
            break

    return selected


def generate_anomalies_for_cycle(vessels: list[str], probability: float) -> list[dict]:
    """
    Generate anomalies for a single generator cycle.
    - If BURST_MODE is true: return 3-5 anomalies across different vessel/sensor pairs.
    - Otherwise: run per-vessel probability checks.
    """
    if BURST_MODE:
        return _generate_burst_anomalies(vessels)

    anomalies: list[dict] = []
    for vessel in vessels:
        anomaly = maybe_generate_anomaly(vessel, probability)
        if anomaly:
            anomalies.append(anomaly)
    return anomalies
