"""Anomaly / event generation
============================
Generates threshold-breach events directly from the sensor definitions in
sensors.py.  Every sensor that has anomaly_high or anomaly_low defined will
automatically produce an event when its value exceeds the threshold -- no
separate event catalogue needed.

This means:
  - No sensor can fall through the cracks: if a threshold is defined, it
    WILL produce an event and trigger an AI analysis when breached.
  - Adding a new sensor to sensors.py with thresholds is all that is needed
    to get full coverage -- no edits needed here.

Probability is controlled by the ANOMALY_PROBABILITY env var
(default 0.05 = 5% chance per sensor per cycle)."""

import random
from typing import Optional

from sensors import SENSORS, SensorConfig


# --- Descriptions per sensor ----------------------------------------------
# Human-readable cause text for each sensor, used in event details.
# If a sensor is not listed here, a generic fallback is used.
SENSOR_DESCRIPTIONS: dict[str, dict] = {

    # DG1-DG5: engine speed
    "dg1_engine_speed": {
        "high": "Engine overspeed detected. Risk of mechanical damage to DG1.",
        "low": "DG1 engine underspeed. Possible fuel supply fault or load trip.",
    },
    "dg2_engine_speed": {
        "high": "Engine overspeed detected. Risk of mechanical damage to DG2.",
        "low": "DG2 engine underspeed. Possible fuel supply fault or load trip.",
    },
    "dg3_engine_speed": {
        "high": "Engine overspeed detected. Risk of mechanical damage to DG3.",
        "low": "DG3 engine underspeed. Possible fuel supply fault or load trip.",
    },
    "dg4_engine_speed": {
        "high": "Engine overspeed detected. Risk of mechanical damage to DG4.",
        "low": "DG4 engine underspeed. Possible fuel supply fault or load trip.",
    },
    "dg5_engine_speed": {
        "high": "Engine overspeed detected. Risk of mechanical damage to DG5.",
        "low": "DG5 engine underspeed. Possible fuel supply fault or load trip.",
    },

    # DG1-DG5: power output
    "dg1_power_mw": {
        "high": "DG1 power output exceeded rated capacity. Risk of overheating and tripping.",
    },
    "dg2_power_mw": {
        "high": "DG2 power output exceeded rated capacity. Risk of overheating and tripping.",
    },
    "dg3_power_mw": {
        "high": "DG3 power output exceeded rated capacity. Risk of overheating and tripping.",
    },
    "dg4_power_mw": {
        "high": "DG4 power output exceeded rated capacity. Risk of overheating and tripping.",
    },
    "dg5_power_mw": {
        "high": "DG5 power output exceeded rated capacity. Risk of overheating and tripping.",
    },

    # DG1-DG5: fuel rack position
    "dg1_fuel_rack_pos": {
        "high": "DG1 fuel rack near maximum. Engine under very high load or governor fault.",
    },
    "dg2_fuel_rack_pos": {
        "high": "DG2 fuel rack near maximum. Engine under very high load or governor fault.",
    },
    "dg3_fuel_rack_pos": {
        "high": "DG3 fuel rack near maximum. Engine under very high load or governor fault.",
    },
    "dg4_fuel_rack_pos": {
        "high": "DG4 fuel rack near maximum. Engine under very high load or governor fault.",
    },
    "dg5_fuel_rack_pos": {
        "high": "DG5 fuel rack near maximum. Engine under very high load or governor fault.",
    },

    # DG1-DG5: charge-air temperature
    "dg1_charge_air_temp": {
        "high": "DG1 charge air temperature too high. Possible intercooler fouling or cooling water fault.",
    },
    "dg2_charge_air_temp": {
        "high": "DG2 charge air temperature too high. Possible intercooler fouling or cooling water fault.",
    },
    "dg3_charge_air_temp": {
        "high": "DG3 charge air temperature too high. Possible intercooler fouling or cooling water fault.",
    },
    "dg4_charge_air_temp": {
        "high": "DG4 charge air temperature too high. Possible intercooler fouling or cooling water fault.",
    },
    "dg5_charge_air_temp": {
        "high": "DG5 charge air temperature too high. Possible intercooler fouling or cooling water fault.",
    },

    # DG1-DG5: turbocharger speed
    "dg1_tc_speed": {
        "high": "DG1 turbocharger overspeed. Risk of TC blade failure or bearing damage.",
    },
    "dg2_tc_speed": {
        "high": "DG2 turbocharger overspeed. Risk of TC blade failure or bearing damage.",
    },
    "dg3_tc_speed": {
        "high": "DG3 turbocharger overspeed. Risk of TC blade failure or bearing damage.",
    },
    "dg4_tc_speed": {
        "high": "DG4 turbocharger overspeed. Risk of TC blade failure or bearing damage.",
    },
    "dg5_tc_speed": {
        "high": "DG5 turbocharger overspeed. Risk of TC blade failure or bearing damage.",
    },

    # DG1-DG5: cooling water inlet flow
    "dg1_cw_in_flow": {
        "low": "DG1 jacket cooling water inlet flow critically low. Possible pump failure or blockage. Risk of engine overheating.",
    },
    "dg2_cw_in_flow": {
        "low": "DG2 jacket cooling water inlet flow critically low. Possible pump failure or blockage. Risk of engine overheating.",
    },
    "dg3_cw_in_flow": {
        "low": "DG3 jacket cooling water inlet flow critically low. Possible pump failure or blockage. Risk of engine overheating.",
    },
    "dg4_cw_in_flow": {
        "low": "DG4 jacket cooling water inlet flow critically low. Possible pump failure or blockage. Risk of engine overheating.",
    },
    "dg5_cw_in_flow": {
        "low": "DG5 jacket cooling water inlet flow critically low. Possible pump failure or blockage. Risk of engine overheating.",
    },

    # Fuel system: HFO/MGO booster flows
    "hfo_booster_a_flow": {
        "high": "HFO booster A flow rate abnormally high. Possible metering fault or excess consumption.",
    },
    "hfo_booster_b_flow": {
        "high": "HFO booster B flow rate abnormally high. Possible metering fault or excess consumption.",
    },
    "mgo_booster_a_flow": {
        "high": "MGO booster A flow rate abnormally high. Possible metering fault.",
    },
    "mgo_booster_b_flow": {
        "high": "MGO booster B flow rate abnormally high. Possible metering fault.",
    },

    # Fuel tanks
    "hfo_tank_weight": {
        "low": "HFO tank level critically low. Bunkering required before next port call.",
    },
    "mgo_tank_weight": {
        "low": "MGO tank level critically low. Bunkering required before next port call.",
    },

    # HFO quality
    "hfo_fuel_temp": {
        "high": "HFO fuel temperature at booster above safe limit. Risk of fuel degradation and injector damage.",
    },
    "hfo_fuel_viscosity": {
        "high": "HFO viscosity too high at injectors. Poor atomisation and combustion efficiency. Check fuel heater.",
    },
    "hfo_density": {
        "high": "HFO density above expected range. Possible water contamination or wrong fuel grade loaded.",
    },

    # Scrubbers: FWD
    "scrubber_fwd_so2": {
        "high": "SOx emission above MARPOL Annex VI limit inside SECA zone. FWD scrubber may be malfunctioning.",
    },
    "scrubber_fwd_co2": {
        "high": "CO2 concentration above expected level in FWD scrubber circuit. Possible incomplete combustion.",
    },
    "scrubber_fwd_ph": {
        "low": "FWD scrubber wash water pH below regulatory minimum. Possible wash water pump fault.",
    },
    "scrubber_fwd_power": {
        "high": "FWD scrubber power consumption abnormally high. Possible mechanical fault.",
    },
    "scrubber_fwd_pah": {
        "high": "PAH concentration in FWD scrubber wash water above environmental limit. Check wash water treatment system.",
    },

    # Scrubbers: AFT
    "scrubber_aft_so2": {
        "high": "SOx emission above MARPOL Annex VI limit inside SECA zone. AFT scrubber may be malfunctioning.",
    },
    "scrubber_aft_co2": {
        "high": "CO2 concentration above expected level in AFT scrubber circuit. Possible incomplete combustion.",
    },
    "scrubber_aft_ph": {
        "low": "AFT scrubber wash water pH below regulatory minimum. Possible wash water pump fault.",
    },
    "scrubber_aft_power": {
        "high": "AFT scrubber power consumption abnormally high. Possible mechanical fault.",
    },
    "scrubber_aft_pah": {
        "high": "PAH concentration in AFT scrubber wash water above environmental limit. Check wash water treatment system.",
    },

    # Navigation
    "water_depth": {
        "low": "Water depth critically low. Risk of grounding. Immediate navigation action required.",
    },
    "vessel_speed": {
        "high": "Vessel speed exceeded safe limit for current conditions.",
    },

    # DG1-DG5: engine load
    "dg1_engine_load": {
        "high": "DG1 engine load above 90%. Sustained overload risk — generator may trip and shed load.",
    },
    "dg2_engine_load": {
        "high": "DG2 engine load above 90%. Sustained overload risk — generator may trip and shed load.",
    },
    "dg3_engine_load": {
        "high": "DG3 engine load above 90%. Sustained overload risk — generator may trip and shed load.",
    },
    "dg4_engine_load": {
        "high": "DG4 engine load above 90%. Sustained overload risk — generator may trip and shed load.",
    },
    "dg5_engine_load": {
        "high": "DG5 engine load above 90%. Sustained overload risk — generator may trip and shed load.",
    },

    # HFO booster C
    "hfo_booster_c_flow": {
        "high": "HFO booster C flow rate abnormally high. Possible metering fault or excess consumption.",
    },

    # HFO quality at boosters B and C
    "hfo_fuel_temp_b": {
        "high": "HFO fuel temperature at booster B above safe limit. Risk of fuel degradation and injector damage.",
    },
    "hfo_fuel_temp_c": {
        "high": "HFO fuel temperature at booster C above safe limit. Risk of fuel degradation and injector damage.",
    },
    "hfo_fuel_viscosity_b": {
        "high": "HFO viscosity too high at booster B injectors. Poor atomisation and combustion efficiency. Check fuel heater.",
    },
    "hfo_fuel_viscosity_c": {
        "high": "HFO viscosity too high at booster C injectors. Poor atomisation and combustion efficiency. Check fuel heater.",
    },
    "hfo_density_b": {
        "high": "HFO density at booster B above expected range. Possible water contamination or wrong fuel grade loaded.",
    },

    # MGO density
    "mgo_density_a": {
        "high": "MGO density at tank A above expected range. Possible wrong fuel grade or contamination.",
    },
    "mgo_density_b": {
        "high": "MGO density at tank B above expected range. Possible wrong fuel grade or contamination.",
    },

    # Scrubber sulphur content
    "scrubber_fwd_sulphur": {
        "high": "Fuel sulphur content at FWD scrubber inlet exceeded MARPOL SECA limit (0.10% m/m). Immediate reporting required.",
    },
    "scrubber_aft_sulphur": {
        "high": "Fuel sulphur content at AFT scrubber inlet exceeded MARPOL SECA limit (0.10% m/m). Immediate reporting required.",
    },

    # Lubrication oil system
    "clean_lo_flow": {
        "low": "Clean lubricating oil supply flow critically low. Possible filter blockage or pump failure. Risk of bearing damage.",
    },
    "dirty_lo_flow": {
        "high": "Dirty lubricating oil return flow abnormally high. Possible internal bypass fault or excess LO consumption.",
    },

    # Auxiliary boiler fuel flow
    "boiler_fuel_flow_a": {
        "high": "Auxiliary boiler A fuel flow above safe limit. Possible combustion control fault or uncontrolled burn.",
    },
    "boiler_fuel_flow_b": {
        "high": "Auxiliary boiler B fuel flow above safe limit. Possible combustion control fault or uncontrolled burn.",
    },

    # Emergency diesel generator
    "emdg_speed": {
        "high": "Emergency diesel generator overspeed detected during test run. Possible governor fault.",
        "low": "Emergency diesel generator underspeed during test run. Possible fuel supply fault or load issue.",
    },
}


def _anomaly_value(sensor: SensorConfig, kind: str) -> float:
    """Generate a realistic anomalous reading beyond the threshold."""
    if kind == "high" and sensor.anomaly_high is not None:
        # 10-40% above the threshold
        margin = sensor.anomaly_high * random.uniform(0.10, 0.40)
        cap    = sensor.anomaly_high + margin
        return round(random.uniform(sensor.anomaly_high, cap), 2)
    elif kind == "low" and sensor.anomaly_low is not None:
        # 10-40% below the threshold
        margin = sensor.anomaly_low * random.uniform(0.10, 0.40)
        floor  = max(0.0, sensor.anomaly_low - margin)
        return round(random.uniform(floor, sensor.anomaly_low), 2)
    return sensor.baseline


def _severity(sensor: SensorConfig, kind: str, value: float) -> str:
    """Values further from the threshold -> critical, closer -> warning."""
    if kind == "high" and sensor.anomaly_high is not None:
        margin = sensor.anomaly_high * 0.40
        return "critical" if value >= sensor.anomaly_high + 0.6 * margin else "warning"
    elif kind == "low" and sensor.anomaly_low is not None:
        margin = sensor.anomaly_low * 0.40
        return "critical" if value <= sensor.anomaly_low - 0.6 * margin else "warning"
    return "warning"


def _event_type(sensor_name: str, kind: str) -> str:
    """Derive a readable event type string from sensor name and direction."""
    prefix = "HIGH" if kind == "high" else "LOW"
    return f"{prefix}_{sensor_name.upper()}"


def maybe_generate_anomaly(vessel_id: str, probability: float) -> Optional[dict]:
    """
    For each sensor that has a threshold defined, independently roll the
    probability of an anomaly.  Returns the first anomaly that fires, or
    None if none fire this cycle.

    Every sensor with anomaly_high or anomaly_low defined is covered --
    no sensor can be missed.
    """
    # Collect all sensors that COULD fire an anomaly
    candidates = []
    for sensor in SENSORS:
        if sensor.anomaly_high is not None:
            candidates.append((sensor, "high"))
        if sensor.anomaly_low is not None:
            candidates.append((sensor, "low"))

    # Shuffle so we do not always pick the same sensor when multiple fire
    random.shuffle(candidates)

    for sensor, kind in candidates:
        if random.random() > probability:
            continue

        value      = _anomaly_value(sensor, kind)
        severity   = _severity(sensor, kind, value)
        event_type = _event_type(sensor.name, kind)
        direction  = "upper" if kind == "high" else "lower"

        desc = SENSOR_DESCRIPTIONS.get(sensor.name, {}).get(
            kind,
            f"Sensor '{sensor.name}' breached {direction} threshold.",
        )
        details = f"{desc} Current value: {value} {sensor.unit}."

        return {
            "vessel_id":       vessel_id,
            "sensor_name":     sensor.name,
            "event_type":      event_type,
            "severity":        severity,
            "details":         details,
            "telemetry_value": value,
        }

    return None
