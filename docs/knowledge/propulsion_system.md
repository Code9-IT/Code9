# Propulsion System – Background Knowledge

## Scope
Background context for propulsion-related events. **Note: this vessel uses diesel-electric propulsion — no direct propulsion shaft sensors are present in the current sensor catalogue.** Propulsion faults typically manifest as generator load changes (see `main_engine.md` and `auxiliary_engines.md`) or speed/depth anomalies (see `navigation_systems.md`).

## System Role
This vessel uses a diesel-electric propulsion arrangement:
- DG1–DG5 generate electrical power (see `main_engine.md`)
- Electric motors receive power from the main switchboard and drive the propeller shafts
- There is no mechanical gearbox coupling engines directly to propellers
- Vessel speed is controlled by varying motor power; engines run at constant 720 RPM

This is the standard arrangement for large passenger ferries. The primary advantage is operational flexibility: any combination of generators can supply propulsion and hotel loads simultaneously.

> Source: Wärtsilä Encyclopedia of Ship Technology, 2nd ed. — diesel-electric propulsion.

## Propulsion-Related Alarm Patterns (Indirect Indicators)

No propulsion shaft sensors exist in the current sensor catalogue, but these indirect patterns can indicate propulsion problems:

| Indirect Indicator | Sensor | Likely Propulsion Issue |
|---|---|---|
| Sudden DG engine load increase | `dg_engine_load` >90 % | Propulsion motor demand spike; thruster engagement |
| Vessel speed drops without reduced load | `vessel_speed` | Propeller fouling or propulsion motor fault |
| Vessel speed above 25 kn | `vessel_speed` >25 kn | Overspeed / sea-state control fault |
| Water depth drops toward 15 m | `water_depth` <15 m | Shallow water — grounding risk to propeller |

## Common Propulsion Fault Types (Context)

**Propeller fouling:**
- Marine growth (barnacles, algae) increases resistance → higher engine load for same speed
- Resolved at dry-dock cleaning

**Electric motor fault:**
- Motor drive inverter fault
- Insulation failure (detected by earth fault protection relays)
- Overtemperature on motor windings

**CPP system fault (if Controllable Pitch Propeller):**
- Hydraulic pressure loss → pitch cannot be adjusted
- Pitch feedback mismatch → ordered vs. actual pitch different

## Regulations
- Class rules: shaft alignment and bearing clearance measurements required at dry-dock intervals.
- CPP systems: backup manual pitch control required.
- SOLAS Ch. V, Regulation 20: Voyage data recorder (VDR) must log propulsion commands.

## Sources
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015) – diesel-electric propulsion: [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
- SOLAS Ch. V (UK Gov. official PDF): [assets.publishing.service.gov.uk – SOLAS V](https://assets.publishing.service.gov.uk/media/5a7f0081ed915d74e33f3c6e/solas_v_on_safety_of_navigation.pdf)
