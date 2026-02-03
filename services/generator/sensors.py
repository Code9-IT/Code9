"""
Sensor definitions and normal-value generation
================================================
Each SensorConfig describes one sensor: its typical baseline,
expected noise range, and the thresholds that count as anomalous.

The sensor list is kept short and generic on purpose
(see project guidelines – avoid deep tag hierarchies).

TODO: add more sensors as the demo evolves (e.g. rudder_angle, nav_speed).
"""

import random
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SensorConfig:
    name:          str
    baseline:      float           # centre of the normal distribution
    noise_range:   float           # ± half-width (uniform)
    unit:          str             # display unit
    anomaly_high:  Optional[float] # upper threshold (None → no upper anomaly)
    anomaly_low:   Optional[float] # lower threshold (None → no lower anomaly)


# ─── Sensor catalogue ─────────────────────────────────────
SENSORS: List[SensorConfig] = [
    SensorConfig("engine_temp",        baseline=55.0,  noise_range=10.0, unit="°C",  anomaly_high=85.0,  anomaly_low=None),
    SensorConfig("oil_pressure",       baseline=4.5,   noise_range=1.0,  unit="bar", anomaly_high=None,  anomaly_low=2.0),
    SensorConfig("engine_rpm",         baseline=900.0, noise_range=150.0,unit="RPM", anomaly_high=1500.0,anomaly_low=None),
    SensorConfig("coolant_temp",       baseline=45.0,  noise_range=8.0,  unit="°C",  anomaly_high=70.0,  anomaly_low=None),
    SensorConfig("fuel_consumption",   baseline=20.0,  noise_range=5.0,  unit="L/h", anomaly_high=45.0,  anomaly_low=None),
    SensorConfig("hull_temp",          baseline=25.0,  noise_range=5.0,  unit="°C",  anomaly_high=50.0,  anomaly_low=None),
]

# Two anonymised test vessels
VESSELS = ["vessel_001", "vessel_002"]


# ─── generation helpers ───────────────────────────────────
def generate_normal_value(sensor: SensorConfig) -> float:
    """One reading within baseline ± noise_range."""
    return round(sensor.baseline + random.uniform(-sensor.noise_range, sensor.noise_range), 2)


def generate_telemetry_batch(vessels: List[str] | None = None) -> List[dict]:
    """
    Produce one normal reading per sensor per vessel.
    Returns a list of dicts ready for executemany().
    """
    if vessels is None:
        vessels = VESSELS

    batch = []
    for vessel in vessels:
        for sensor in SENSORS:
            batch.append({
                "vessel_id":   vessel,
                "sensor_name": sensor.name,
                "value":       generate_normal_value(sensor),
            })
    return batch
