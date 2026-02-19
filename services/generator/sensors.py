"""
Sensor definitions and normal-value generation
================================================
Sensor catalogue derived from real ship IAS use-case data (128 tags).
We map tag codes to descriptive names and define realistic baselines,
noise levels, and anomaly thresholds based on the actual metadata ranges.

Subsystems covered:
  DG1-DG5  - engine speed, power, fuel rack, charge-air temp, turbocharger speed
  Cooling  - jacket/intercooler cooling-water inlet flow per DG
  Fuel     - HFO/MGO booster flows (A and B), HFO/MGO tank weights,
             HFO fuel temperature, viscosity, and density
  Scrubber - SO2, CO2, pH, power, PAH for both FWD and AFT scrubbers
  Nav/env  - water depth, vessel speed, GPS position (latitude, longitude)

Real IAS tag references are documented in comments where available.
All sensors sample at 10-second intervals (matching real IAS interval).

Design principle:
  Every SensorConfig with anomaly_high or anomaly_low defined will
  automatically generate an anomaly event when its value exceeds the
  threshold -- no separate event catalogue needed (see anomalies.py).
  Sensors without thresholds (latitude, longitude) appear in telemetry
  but never trigger events.
"""

import random
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SensorConfig:
    name:         str
    baseline:     float           # centre of the normal distribution
    noise_range:  float           # +/- half-width (uniform noise)
    unit:         str             # display unit
    anomaly_high: Optional[float] # upper alarm threshold (None -> no upper alarm)
    anomaly_low:  Optional[float] # lower alarm threshold (None -> no lower alarm)


# --- Sensor catalogue -----------------------------------------------------
SENSORS: List[SensorConfig] = [

    # -- Diesel generators DG1-DG5: engine speed ---------------------------
    # IAS tags H09214-H09218 / DA41219R-DE41219. Range 0-750 rpm.
    # Constant-speed generators cruise at exactly ~720 rpm.
    # Overspeed alarm at 742 rpm; underspeed at 680 rpm.
    SensorConfig("dg1_engine_speed",        720, 3.0, "rpm", 742.0, 680.0),
    SensorConfig("dg2_engine_speed",        720, 3.0, "rpm", 742.0, 680.0),
    SensorConfig("dg3_engine_speed",        720, 3.0, "rpm", 742.0, 680.0),
    SensorConfig("dg4_engine_speed",        720, 3.0, "rpm", 742.0, 680.0),
    SensorConfig("dg5_engine_speed",        720, 3.0, "rpm", 742.0, 680.0),

    # -- DG1-DG5: power output ---------------------------------------------
    # IAS tags PD1101_Power-PD5101_Power. Range 0-16 MW.
    # Rated capacity 16 MW; typical load 8-10 MW per DG underway.
    SensorConfig("dg1_power_mw",            8.0, 1.5, "MW", 15.5, None),
    SensorConfig("dg2_power_mw",            8.0, 1.5, "MW", 15.5, None),
    SensorConfig("dg3_power_mw",            8.0, 1.5, "MW", 15.5, None),
    SensorConfig("dg4_power_mw",            8.0, 1.5, "MW", 15.5, None),
    SensorConfig("dg5_power_mw",            8.0, 1.5, "MW", 15.5, None),

    # -- DG1-DG5: fuel rack position ---------------------------------------
    # IAS tags DA41195R-DE41195. Range 0-60 mm.
    # Normal cruising ~28 mm; high load or governor fault if >55 mm.
    SensorConfig("dg1_fuel_rack_pos",       28.0, 3.0, "mm", 55.0, None),
    SensorConfig("dg2_fuel_rack_pos",       28.0, 3.0, "mm", 55.0, None),
    SensorConfig("dg3_fuel_rack_pos",       28.0, 3.0, "mm", 55.0, None),
    SensorConfig("dg4_fuel_rack_pos",       28.0, 3.0, "mm", 55.0, None),
    SensorConfig("dg5_fuel_rack_pos",       28.0, 3.0, "mm", 55.0, None),

    # -- DG1-DG5: charge-air temperature -----------------------------------
    # IAS tag DA46057R (DG1 reference). Range 0-160 degC.
    # Normal intercooler outlet ~40-50 degC. Alarm >120 degC.
    SensorConfig("dg1_charge_air_temp",     45.0, 3.0, "degC", 120.0, None),
    SensorConfig("dg2_charge_air_temp",     45.0, 3.0, "degC", 120.0, None),
    SensorConfig("dg3_charge_air_temp",     45.0, 3.0, "degC", 120.0, None),
    SensorConfig("dg4_charge_air_temp",     45.0, 3.0, "degC", 120.0, None),
    SensorConfig("dg5_charge_air_temp",     45.0, 3.0, "degC", 120.0, None),

    # -- DG1-DG5: turbocharger speed ---------------------------------------
    # IAS tags DA45180R-DE45180. Range 0-25 000 rpm.
    # Normal ~18 000 rpm under typical load. Alarm >22 000 rpm.
    SensorConfig("dg1_tc_speed",            18000, 500.0, "rpm", 22000.0, None),
    SensorConfig("dg2_tc_speed",            18000, 500.0, "rpm", 22000.0, None),
    SensorConfig("dg3_tc_speed",            18000, 500.0, "rpm", 22000.0, None),
    SensorConfig("dg4_tc_speed",            18000, 500.0, "rpm", 22000.0, None),
    SensorConfig("dg5_tc_speed",            18000, 500.0, "rpm", 22000.0, None),

    # -- DG1-DG5: jacket cooling-water inlet flow --------------------------
    # IAS tags H06006, H06008, H06010, H06012, H06014. Range 0-30 m3/h.
    # Low-flow alarm <5 m3/h indicates cooling circuit fault or pump failure.
    SensorConfig("dg1_cw_in_flow",          15.0, 2.0, "m3/h", None, 5.0),
    SensorConfig("dg2_cw_in_flow",          15.0, 2.0, "m3/h", None, 5.0),
    SensorConfig("dg3_cw_in_flow",          15.0, 2.0, "m3/h", None, 5.0),
    SensorConfig("dg4_cw_in_flow",          15.0, 2.0, "m3/h", None, 5.0),
    SensorConfig("dg5_cw_in_flow",          15.0, 2.0, "m3/h", None, 5.0),

    # -- Fuel system: HFO booster flows ------------------------------------
    # IAS tags H06016 (booster A HFO), H06017 (booster B HFO). Range 0-5 m3/h.
    SensorConfig("hfo_booster_a_flow",      2.5, 0.3, "m3/h", 4.8, None),
    SensorConfig("hfo_booster_b_flow",      2.5, 0.3, "m3/h", 4.8, None),

    # -- Fuel system: MGO booster flows ------------------------------------
    # IAS tags H06018 (booster A MGO), H06019 (booster B MGO). Range 0-5 m3/h.
    SensorConfig("mgo_booster_a_flow",      1.2, 0.2, "m3/h", 4.0, None),
    SensorConfig("mgo_booster_b_flow",      1.2, 0.2, "m3/h", 4.0, None),

    # -- Fuel system: tank weights -----------------------------------------
    # HFO: IAS tag TK06HFO_TotalWeightTons. Range 0-10 000 tons.
    # MGO: IAS tag TK06MGO_TotalWeightTons. Range 0-10 000 tons.
    SensorConfig("hfo_tank_weight",         7500, 20.0, "tons", None, 500.0),
    SensorConfig("mgo_tank_weight",         2000, 10.0, "tons", None, 200.0),

    # -- Fuel system: HFO quality at booster --------------------------------
    # Temperature: IAS tags H06086-H06088. Range 0-200 degC.
    # HFO is heated to 90-120 degC to reduce viscosity before injection.
    # High-temp alarm at 150 degC indicates heating control fault.
    SensorConfig("hfo_fuel_temp",           90.0, 5.0, "degC", 150.0, None),

    # Viscosity: IAS tags H06168-H06170. Range 0-50 cSt.
    # Target injection viscosity ~12-18 cSt. High alarm >40 cSt
    # means fuel is too thick for proper atomisation.
    SensorConfig("hfo_fuel_viscosity",      15.0, 2.0, "cSt", 40.0, None),

    # Density: IAS tags HFODEN1/HFODEN2. Normal range ~950-1010 kg/m3.
    # Density above 1010 kg/m3 may indicate water contamination or wrong grade.
    SensorConfig("hfo_density",             990.0, 5.0, "kg/m3", 1010.0, None),

    # -- Exhaust scrubbers: FWD -------------------------------------------
    # Active when vessel is inside a SECA (Sulphur Emission Control Area).
    # IAS tags SC1xxx (FWD scrubber).
    # SO2 emissions: SC1336. MARPOL Annex VI SECA limit ~900 ppm equivalent.
    # Alarm at 400 ppm (conservative margin before regulatory breach).
    SensorConfig("scrubber_fwd_so2",        50, 10.0, "ppm", 400.0, None),
    # CO2 in exhaust: SC1335. Normal combustion 4-6%. High >12% = poor combustion.
    SensorConfig("scrubber_fwd_co2",        5.0, 0.5, "%", 12.0, None),
    # Wash-water pH: SC1109. IMO MEPC.184(59) minimum pH 6.0.
    SensorConfig("scrubber_fwd_ph",         7.5, 0.2, "pH", None, 6.0),
    # Power consumption: SC1500. Normal ~120 W. High >500 W = mechanical fault.
    SensorConfig("scrubber_fwd_power",      120, 15.0, "W", 500.0, None),
    # PAH (polycyclic aromatic hydrocarbons) in wash water: SC1108.
    # Environmental limit ~50 ug/l; above this requires bypass or port action.
    SensorConfig("scrubber_fwd_pah",        5.0, 1.0, "ug/l", 50.0, None),

    # -- Exhaust scrubbers: AFT -------------------------------------------
    # IAS tags SC2xxx (AFT scrubber) - mirrors FWD subsystem.
    SensorConfig("scrubber_aft_so2",        50, 10.0, "ppm", 400.0, None),
    SensorConfig("scrubber_aft_co2",        5.0, 0.5, "%", 12.0, None),
    SensorConfig("scrubber_aft_ph",         7.5, 0.2, "pH", None, 6.0),
    SensorConfig("scrubber_aft_power",      120, 15.0, "W", 500.0, None),
    SensorConfig("scrubber_aft_pah",        5.0, 1.0, "ug/l", 50.0, None),

    # -- Navigation / environment -----------------------------------------
    # Water depth: IAS tag DBT01. Range -500 to 500 m.
    # Grounding-risk alarm at <15 m.
    SensorConfig("water_depth",             80, 15.0, "m", None, 15.0),
    # Vessel speed (knots). ~12 kn typical cruising speed.
    # High-speed alarm >25 kn (safety limit for current conditions).
    SensorConfig("vessel_speed",            12.0, 2.0, "knots", 25.0, None),
    # GPS position in decimal degrees. No anomaly thresholds - informational only.
    # Approximate position for a vessel in the North Sea / Norwegian coast.
    SensorConfig("vessel_latitude",         59.0, 0.01, "deg", None, None),
    SensorConfig("vessel_longitude",        5.5, 0.01, "deg", None, None),

    # -- DG1-DG5: engine load ----------------------------------------------
    # IAS tags DA41xxx. Percentage of rated BMEP (brake mean effective pressure).
    # Normal cruise 50-70%. High-load alarm >90% = risk of sustained overload.
    SensorConfig("dg1_engine_load",         60.0, 5.0, "%", 90.0, None),
    SensorConfig("dg2_engine_load",         60.0, 5.0, "%", 90.0, None),
    SensorConfig("dg3_engine_load",         60.0, 5.0, "%", 90.0, None),
    SensorConfig("dg4_engine_load",         60.0, 5.0, "%", 90.0, None),
    SensorConfig("dg5_engine_load",         60.0, 5.0, "%", 90.0, None),

    # -- Fuel system: HFO booster C flow -----------------------------------
    # IAS tag H06020 (booster C HFO). Range 0-5 m3/h.
    SensorConfig("hfo_booster_c_flow",      2.5, 0.3, "m3/h", 4.8, None),

    # -- Fuel system: HFO quality at boosters B and C ----------------------
    # Mirror of booster A sensors – separate measurement points.
    SensorConfig("hfo_fuel_temp_b",         90.0, 5.0, "degC", 150.0, None),
    SensorConfig("hfo_fuel_temp_c",         90.0, 5.0, "degC", 150.0, None),
    SensorConfig("hfo_fuel_viscosity_b",    15.0, 2.0, "cSt",  40.0, None),
    SensorConfig("hfo_fuel_viscosity_c",    15.0, 2.0, "cSt",  40.0, None),
    SensorConfig("hfo_density_b",           990.0, 5.0, "kg/m3", 1010.0, None),

    # -- Fuel system: MGO density ------------------------------------------
    # IAS tags MGODEN1/MGODEN2. MGO density 820-870 kg/m3 at 15 degC.
    # Above 880 kg/m3 may indicate wrong grade or contamination.
    SensorConfig("mgo_density_a",           840.0, 5.0, "kg/m3", 880.0, None),
    SensorConfig("mgo_density_b",           840.0, 5.0, "kg/m3", 880.0, None),

    # -- Exhaust scrubbers: sulphur content --------------------------------
    # Fuel sulphur measured at scrubber inlet. MARPOL Annex VI SECA limit 0.10% m/m.
    # Alarm exactly at regulatory limit – any breach requires reporting.
    SensorConfig("scrubber_fwd_sulphur",    0.05, 0.005, "%", 0.10, None),
    SensorConfig("scrubber_aft_sulphur",    0.05, 0.005, "%", 0.10, None),

    # -- Lubrication oil system --------------------------------------------
    # Clean (supply) LO flow. IAS tag H06050. Low-flow <3 L/min = filter blockage
    # or pump failure; risk of bearing/cylinder damage.
    SensorConfig("clean_lo_flow",           10.0, 1.0, "L/min", None, 3.0),
    # Dirty (drain/return) LO flow. High >20 L/min = excess consumption or bypass.
    SensorConfig("dirty_lo_flow",           9.0, 1.0, "L/min", 20.0, None),

    # -- Auxiliary boiler: fuel flow ---------------------------------------
    # IAS tags H06030/H06031. Normal boiler fuel 0.5-2.0 m3/h.
    # High-flow alarm >4.0 m3/h suggests fault or uncontrolled burn.
    SensorConfig("boiler_fuel_flow_a",      1.0, 0.2, "m3/h", 4.0, None),
    SensorConfig("boiler_fuel_flow_b",      1.0, 0.2, "m3/h", 4.0, None),

    # -- Emergency diesel generator: speed ---------------------------------
    # IAS tag EMDG_SPEED. Runs at ~720 rpm during weekly test.
    # Overspeed alarm >750 rpm; underspeed <680 rpm during test run.
    SensorConfig("emdg_speed",              720, 5.0, "rpm", 750.0, 680.0),
]

# One anonymised test vessel (matching real-data naming convention).
VESSELS = ["vessel_001"]


# --- Generation helpers ---------------------------------------------------
def generate_normal_value(sensor: SensorConfig) -> float:
    """One reading within baseline +/- noise_range."""
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
