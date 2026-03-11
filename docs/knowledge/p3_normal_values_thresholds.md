# Point 3 – Normal Operating Values and Thresholds

## Scope

This file provides the primary reference for normal operating values, warning limits, and alarm thresholds relevant to the ship systems monitored in this project. Two source layers are used:

1. **Project IAS sensor catalogue** (`services/generator/sensors.py`) — the actual alarm setpoints running in the system. Derived from real, anonymised ship IAS data (128-tag dataset).
2. **OEM and regulatory references** — Wärtsilä W20 engine manual values and IMO/ABS/IACS standards for context and validation.

> For AI event analysis: use `sensors.py` values as the definitive thresholds. OEM and regulatory values are included for cross-validation and context.

---

## Alert Priority Classification (IMO A.1021(26) and MSC.302(87))

IMO Resolution A.1021(26) (Code on Alerts and Indicators) defines four alert priorities:

| Priority | Definition |
|---|---|
| **Emergency Alarm** | Immediate danger to human life or to the ship/machinery; immediate action required |
| **Alarm** | High-priority alert; immediate attention and action needed to maintain safe navigation or operation |
| **Warning** | Precautionary; no immediate action required but condition may become hazardous if not addressed |
| **Caution** | Lowest priority; condition needs attention beyond normal monitoring but does not justify alarm/warning |

**Aggregation**: multiple individual alerts may be combined into one higher-level alert representing all of them.

> Source: IMO A.1021(26) Code on Alerts and Indicators: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.1021(26).pdf
> Source: IMO MSC.302(87) Bridge Alert Management: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf

---

## Project Alarm Thresholds (from sensors.py)

All values from `services/generator/sensors.py`, IAS tag references included. These are the actual running thresholds in the monitoring system.

### Diesel Generators DG1–DG5

| Parameter | IAS Tag(s) | Normal Value | Alarm High | Alarm Low |
|---|---|---|---|---|
| Engine speed | H09214–H09218 | 720 rpm | >742 rpm | <680 rpm |
| Engine load | (derived) | 60 % | >90 % | – |
| Power output | PD1101–PD5101 | 8 MW | >15.5 MW | – |
| Fuel rack position | DA41195R–DE41195 | 28 mm | >55 mm | – |
| Charge air temp | DA46057R | 45 °C | >120 °C | – |
| Turbocharger speed | DA45180R–DE45180 | 18,000 rpm | >22,000 rpm | – |
| Cooling water flow in | H06006/H06008/H06010/H06012/H06014 | 15 m³/h | – | <5 m³/h |

### Lubrication System

| Parameter | IAS Tag | Normal Value | Alarm High | Alarm Low |
|---|---|---|---|---|
| Clean LO flow | H06050 | (normal) | – | <3 L/min |
| Dirty LO flow | (dirty_lo_flow) | (normal) | >20 L/min | – |

### Fuel System – HFO

| Parameter | IAS Tag(s) | Normal Value | Alarm High | Alarm Low |
|---|---|---|---|---|
| HFO temperature (A/B/C) | H06086–H06088 | 90 °C | >150 °C | – |
| HFO viscosity (A/B/C) | H06168–H06170 | 15 cSt | >40 cSt | – |
| HFO density (A/B) | HFODEN1, HFODEN2 | 990 kg/m³ | >1010 kg/m³ | – |
| HFO tank weight | TK06HFO_TotalWeightTons | ~7,500 tons | – | <500 tons |
| HFO booster flow A/B | H06016, H06017 | ~2.5 m³/h | >4.8 m³/h | – |
| HFO booster flow C | H06020 | ~2.5 m³/h | >4.8 m³/h | – |

### Fuel System – MGO

| Parameter | IAS Tag(s) | Normal Value | Alarm High | Alarm Low |
|---|---|---|---|---|
| MGO density (A/B) | MGODEN1, MGODEN2 | 840 kg/m³ | >880 kg/m³ | – |
| MGO tank weight | TK06MGO_TotalWeightTons | ~2,000 tons | – | <200 tons |
| MGO booster flow A/B | H06018, H06019 | ~1.2 m³/h | >4.0 m³/h | – |

### Scrubber / Emissions

| Parameter | IAS Tag(s) | Normal | Alarm |
|---|---|---|---|
| SO₂ concentration | SC1xxx/SC2xxx | <200 ppm | >400 ppm |
| CO₂ concentration | (scrubber_*_co2) | ~5 % | >12 % |
| Exhaust scrubber pH | (scrubber_*_ph) | >6.5 | <6.0 |
| PAH (polycyclic aromatic hydrocarbons) | (scrubber_*_pah) | <25 µg/l | >50 µg/l |
| Fuel sulphur (in-use) | (scrubber_*_sulphur) | <0.10 % | ≥0.10 % |

> Note: sensors.py uses pH <6.0 as the alarm threshold. IMO MEPC.259(68) requires scrubber wash water pH ≥6.5 at 4 m from discharge port. The MEPC.259(68) standard is stricter than the coded alarm — this discrepancy should be noted in system documentation.

### Boiler

| Parameter | IAS Tag | Alarm High |
|---|---|---|
| Boiler fuel flow A | H06030 | >4.0 m³/h |
| Boiler fuel flow B | H06031 | >4.0 m³/h |

### Emergency Diesel Generator (EMDG)

| Parameter | IAS Tag | Normal | Alarm High | Alarm Low |
|---|---|---|---|---|
| EMDG speed | EMDG_SPEED | 720 rpm | >750 rpm | <680 rpm |

### Navigation

| Parameter | IAS Tag | Normal | Alarm |
|---|---|---|---|
| Water depth | DBT01 | ~80 m | <15 m |
| Vessel speed | (GPS-SOG) | ~12 kn | >25 kn |

> Source for all values above: Project IAS sensor catalogue `services/generator/sensors.py`, derived from anonymised real ship telemetry data (128 IAS tags). Values consistent with Wärtsilä W20 OEM envelope and class society ranges.

---

## OEM Reference Values (Wärtsilä W20 Four-Stroke Generator Engine)

These values are from the Wärtsilä W20 engine technical documentation. They apply to the engine type used in the DG1–DG5 units and provide cross-validation context.

### Lubrication Oil

| Parameter | Nominal | Alarm Level |
|---|---|---|
| Priming oil pressure | 80 kPa (0.8 bar) | Low alarm: 50 kPa (0.5 bar) |
| LO temperature before engine | 63 °C | High-temp alarm: 80 °C |
| LO filter differential pressure | — | Alarm: 150 kPa (1.5 bar) |

> Source: Wärtsilä W20 engine technical data (as referenced in project Docs for RAG.md, section WARTSILA_W20_LUBE_OIL_PRIMING_FILTER_TEMP)

### HT Cooling Water Circuit

| Parameter | Nominal | Alarm |
|---|---|---|
| Pressure before engine | 200 kPa + static (2.0 bar) | Low alarm: 100 kPa + static; max 350 kPa |
| Temperature before engine | ~83 °C | — |
| Temperature after engine | 91 °C | High-temp alarm: 105 °C; stop: 110 °C |
| Expansion tank pressure | 70–150 kPa | — |
| Pressure drop over engine | 50 kPa | — |
| Central cooler pressure drop max | 60 kPa | — |

> Source: Wärtsilä W20 engine technical data (section WARTSILA_W20_HT_COOLING_WATER_PRESSURE_TEMP)

### LT Cooling Water Circuit (Charge Air Cooler)

| Parameter | Nominal | Alarm |
|---|---|---|
| Pressure before charge air cooler | 200 kPa + static (2 bar) | Low alarm: 100 kPa + static; max 350 kPa |
| Temperature before charge air cooler | min 25 °C; max 38 °C | — |
| Pressure drop charge air cooler | 30 kPa | — |
| Pressure drop oil cooler | 30 kPa | — |

> Source: Wärtsilä W20 engine technical data (section WARTSILA_W20_LT_COOLING_WATER_CHARGE_AIR_LIMITS)

### Exhaust System

| Parameter | Limit |
|---|---|
| Max exhaust gas back pressure (full load) | 3 kPa |

> Source: Wärtsilä W20 engine technical data (section WARTSILA_W20_EXHAUST_BACKPRESSURE_LIMIT)

---

## Regulatory Reference: ABS Alarm Requirements

For ships ≥500 GT on international/unrestricted ocean service (ABS rules):

- **Engineers' alarm**: must be operable at the centralized propulsion machinery control station or local control position; must be audible in each engineer's cabin.
- **Propulsion machinery space alarms**: require alarm for fire, alarm for high bilge water level, and a summary alarm activated by listed machinery alarm conditions.
- **Fire alarm specifics**: must have separate visual display and a distinct sound from the summary alarm; no selector switch.

> Source: ABS Rules for Building and Classing Steel Vessels (Propulsion machinery space alarm requirements; sections ABS_ENGINEERS_ALARM_REQUIREMENT and ABS_PROPULSION_SPACE_ALARMS_SUMMARY_FIRE_BILGE in project planning document).

---

## Regulatory Reference: IACS M73 (Turbocharger Alarm Limits)

IACS Unified Requirement M73 specifies that the following must be defined for turbocharger monitoring:

- Overspeed alarm level
- Exhaust gas temperature before turbine: maximum permissible + alarm level
- Lubrication oil inlet pressure: minimum + low-pressure alarm setpoint
- Lubrication oil outlet temperature: maximum + high-temperature alarm setpoint
- Maximum permissible vibration levels (self- and externally generated)

> Alarm levels may equal permissible limits, but should not be reached at 110% engine power or approved intermittent overload beyond 110%.

> Source: IACS Unified Requirement M73 (Turbocharger monitoring requirements; section IACS_M73_TURBOCHARGER_LIMITS_TO_DEFINE in project planning document). IACS UR M73 text: https://iacs.org.uk/resolutions/unified-requirements/ur-m/

---

## How Values Vary with Operating Conditions

- **Engine speed**: constant at 720 rpm for diesel-electric generators (not variable like propulsion main engines)
- **Engine load / power**: increases with electrical demand; alarm triggers at sustained high load (>90%)
- **Charge air temperature**: increases with engine load; cooling water temperature affects it
- **Fuel viscosity**: increases if HFO temperature drops; correct viscosity is required for injection
- **Water depth**: varies with route; Norwegian coast / North Sea typical depth ~80 m; alarm <15 m = shallow water/grounding risk
- **Vessel speed**: affected by sea state, current, and propulsion settings; SOG-based alarm >25 kn

---

## Sources

- Project IAS sensor catalogue: `services/generator/sensors.py` (derived from anonymised real ship IAS data, 128 tags)
- IMO A.1021(26) Code on Alerts and Indicators: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.1021(26).pdf
- IMO MSC.302(87) Bridge Alert Management: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf
- IMO MEPC.259(68) Guidelines for Exhaust Gas Cleaning Systems: https://wwwcdn.imo.org/localresources/en/OurWork/Environment/Documents/Air%20pollution/MEPC.259(68).pdf
- Wärtsilä W20 engine technical data (via project planning document Docs for RAG.md, sections WARTSILA_W20_*)
- ABS Rules for Building and Classing Steel Vessels (propulsion and machinery space alarm requirements)
- IACS Unified Requirement M73 (Turbocharger monitoring): https://iacs.org.uk/resolutions/unified-requirements/ur-m/
