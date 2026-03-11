# Point 2 – Sensors and What They Measure

## Scope

This file describes the industrial sensor types used in maritime monitoring systems: what each sensor type measures, how it works, and what output it provides. Intended for RAG retrieval when the AI agent needs to interpret a raw sensor value or understand what a tag is physically measuring.

> **Important**: This reference describes sensor families in general. Concrete alarm thresholds and "normal ranges" for this project come from the project IAS sensor catalogue (`services/generator/sensors.py`), not from generic sensor specs.

---

## Temperature Sensors

Three main sensor families are used in industrial temperature measurement:

| Type | Range (typical) | Strengths | Limitations |
|---|---|---|---|
| **Thermocouple** | −210 °C to 1760 °C | Wide range, robust, no external excitation | Less linear, less stable than RTD |
| **RTD (Pt100/Pt1000)** | −240 °C to 650 °C | Good linearity, high accuracy, stable | Narrower range, requires external excitation |
| **Thermistor** | −40 °C to 250 °C | Very sensitive to small changes | Limited range, poor linearity, self-heating |

**For RAG interpretation**: a temperature sensor reading outside its expected band can indicate process deviation (engine overheating, charge air cooling failure) or sensor fault. Always cross-check with related process signals before alarming.

> Source: NI – Measuring Temperature with Thermocouples, RTDs, and Thermistors: https://www.ni.com/en/shop/data-acquisition/sensor-fundamentals/measuring-temperature-with-thermocouples-rtds-and-thermistors.html
> Source: NI Sensor Whitepaper (25188_Sensor_WhitePaper_IA.pdf): https://download.ni.com/evaluation/daq/25188_Sensor_WhitePaper_IA.pdf

---

## Pressure Sensors

Industrial pressure transmitters convert pressure into an electrical signal for control systems.

**Common measurement principle**: bridge-based (strain-gauge / full-bridge) design. Small mechanical deformation under pressure is converted to a measurable voltage difference.

**One transmitter, three possible output types** (relevant for signal interpretation):
1. **Direct pressure** – output represents pressure in bar/kPa/psi
2. **Level** – pressure measured at bottom of a liquid column, converted to level height
3. **Flow (square root)** – differential pressure across an orifice or restriction, converted to volumetric flow rate via square-root extraction

> For RAG: a pressure tag can represent pressure, level, or flow depending on how the signal is configured in the IAS.

> Source: Emerson Rosemount 3051 Pressure Transmitter Reference Manual (Fieldbus protocol): https://www.emerson.com/documents/automation/reference-manual-rosemount-3051-pressure-transmitter-foundation-tm-fieldbus-protocol-en-76002.pdf

---

## Vibration Sensors (Accelerometers)

Vibration in rotating machinery is measured with **accelerometers**. These detect mechanical oscillations (acceleration in g or m/s²).

**Key points for RAG**:
- Vibration signals are typically analyzed in the **frequency domain** to identify fault signatures in rotating equipment (imbalance, misalignment, bearing wear)
- Accelerometer signals are small and sensitive to noise — amplification and signal conditioning are required before reliable use
- A single numeric vibration value is less meaningful than a trend or frequency spectrum; changes in vibration patterns indicate faults, not only absolute levels

> Source: NI Sensor Whitepaper (25188_Sensor_WhitePaper_IA.pdf): https://download.ni.com/evaluation/daq/25188_Sensor_WhitePaper_IA.pdf

---

## Flow Sensors

Flow sensors measure the rate at which a medium moves through a pipe or system.

**Electromagnetic flowmeter (magmeter)** — example type used in maritime fuel and cooling systems:
- Measures volumetric flow rate of electrically conductive liquids (water, HFO, MGO)
- Outputs: 4–20 mA continuous signal, pulse output, alarm relay, status signal
- Supports configurable **upper and lower flow alarm limits**
- Example accuracy: ±0.5% of measured value under normal flow conditions (product-specific; not a universal rule)

**For RAG**: a flow sensor provides both a continuous measured value and separate alarm/status outputs. Low flow alarms (e.g., `dg*_cw_in_flow < 5 m³/h`) indicate cooling circuit failure, not just low readings.

> Source: Yokogawa Electromagnetic Flowmeter Technical Document (LF01E00A00-01EN): https://web-material3.yokogawa.com/LF01E00A00-01EN.us.pdf

---

## Tank Level Sensors

Tank level can be measured by **radar level sensors** (non-contact measurement).

**Working principle**:
- Uses FMCW (Frequency-Modulated Continuous Wave) radar in the 77–81 GHz / 80 GHz band
- Transmits a continuous radar signal and measures the frequency difference between transmitted and reflected signal to calculate distance to the liquid surface
- Tank level is derived from known tank dimensions minus measured distance to surface

**Practical advantages for maritime use**:
- Non-contact: sensor does not touch the medium (suitable for HFO, MGO, ballast water)
- Robust in demanding conditions: steam, condensation, temperature variation
- Not affected by medium density, viscosity, temperature, or pressure (unlike hydrostatic level sensors)

> For RAG: the `hfo_tank_weight` and `mgo_tank_weight` tags in this project are weight-based (load cells or calculated from density × volume), not radar. Radar is presented as an example of the sensor family.

> Source: IFM Radar Level Sensor LW21 product page: https://www.ifm.com/lt/en/shared/products/level/radar/radar-level-sensor-lw21

---

## RPM Sensors

RPM (speed) sensors measure rotational speed of shafts, engines, or turbochargers. Common measurement principles:
- **Inductive pickup / magnetic speed sensor**: detects passing of gear teeth or a notch on a rotating shaft; outputs pulses per revolution converted to rpm
- **Hall-effect sensor**: uses magnetic field changes to detect rotation
- **Encoder**: optical or magnetic encoder with high pulse resolution

**In this project** (`sensors.py`):
- `dg*_engine_speed`: diesel generator shaft speed (IAS tags H09214–H09218), nominal 720 rpm
- `dg*_tc_speed`: turbocharger rotor speed (IAS tags DA45180R–DE45180), nominal 18,000 rpm
- `emdg_speed`: emergency diesel generator speed (IAS tag EMDG_SPEED), nominal 720 rpm

> Note: RPM sensor technology is not covered as a standalone topic in the Point 2 source set. The values above are from `services/generator/sensors.py` (project IAS sensor catalogue derived from anonymised real ship telemetry data).

---

## Electrical Sensors (Voltage / Current)

Electrical sensors measure voltage, current, power, and power factor in distribution systems.

**In this project** (`sensors.py`):
- `dg*_power_mw`: active power output per diesel generator (IAS tags PD1101–PD5101), in MW
- `dg*_engine_load`: engine load as percentage (derived from power vs. rated power), in %

**Note**: Voltage and current transducers are standard IAS components but are not covered as a dedicated sensor type in the Point 2 source materials. Electrical sensor values in this project are documented in `services/generator/sensors.py`.

---

## Scope Limitation

This reference describes **sensor families and working principles** — not alarm limits. Specific alarm thresholds for this project are defined in `services/generator/sensors.py` (project IAS sensor catalogue, derived from anonymised real ship telemetry data, 128-tag dataset; values consistent with Wärtsilä OEM and class society ranges).

---

## Sources

- NI – Measuring Temperature with Thermocouples, RTDs, and Thermistors: https://www.ni.com/en/shop/data-acquisition/sensor-fundamentals/measuring-temperature-with-thermocouples-rtds-and-thermistors.html
- NI Sensor Whitepaper (25188_Sensor_WhitePaper_IA.pdf): https://download.ni.com/evaluation/daq/25188_Sensor_WhitePaper_IA.pdf
- Emerson Rosemount 3051 Pressure Transmitter Reference Manual (Foundation Fieldbus): https://www.emerson.com/documents/automation/reference-manual-rosemount-3051-pressure-transmitter-foundation-tm-fieldbus-protocol-en-76002.pdf
- Yokogawa Electromagnetic Flowmeter (LF01E00A00-01EN): https://web-material3.yokogawa.com/LF01E00A00-01EN.us.pdf
- IFM Radar Level Sensor LW21: https://www.ifm.com/lt/en/shared/products/level/radar/radar-level-sensor-lw21
- Project IAS sensor catalogue: `services/generator/sensors.py`
