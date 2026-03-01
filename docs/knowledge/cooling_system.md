# Engine Cooling Water System Monitoring

## Scope
Supports events related to jacket cooling water flow for diesel generators DG1–DG5. Relevant sensor: `dg1_cw_in_flow` through `dg5_cw_in_flow`. A low-flow alarm indicates cooling circuit fault or pump failure for that specific generator.

## System Role
Each diesel generator has a dedicated freshwater cooling circuit (jacket water circuit) that removes heat from cylinder liners, cylinder heads, and pistons. Cooled freshwater is pumped through the engine and then through a heat exchanger where it transfers heat to the low-temperature (LT) circuit or sea water. The system prevents engine overheating.

Most modern vessels use a central cooling arrangement with two circuits:
- **HT circuit (High Temperature)**: Freshwater directly cooling the engine. Typical operating temperature: 70–85 °C.
- **LT circuit (Low Temperature)**: Freshwater cooling the HT circuit, lube oil cooler, and charge air cooler. Cooled in turn by seawater via a central cooler. Seawater does not contact engine components directly.

> Source: Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (system description).

## Monitored Parameters and Alarm Thresholds

Values from project IAS sensor catalogue (`services/generator/sensors.py`), derived from real ship IAS tag data.

| Sensor | IAS Tag Reference | Normal | Alarm High | Alarm Low |
|---|---|---|---|---|
| Cooling water inlet flow (DG1) | H06006 | ~15 m³/h | – | <5 m³/h |
| Cooling water inlet flow (DG2) | H06008 | ~15 m³/h | – | <5 m³/h |
| Cooling water inlet flow (DG3) | H06010 | ~15 m³/h | – | <5 m³/h |
| Cooling water inlet flow (DG4) | H06012 | ~15 m³/h | – | <5 m³/h |
| Cooling water inlet flow (DG5) | H06014 | ~15 m³/h | – | <5 m³/h |

> Sensor range: 0–30 m³/h. Low-flow alarm at <5 m³/h indicates a cooling circuit fault that requires immediate investigation to prevent engine overheating.

## Causes of Low Cooling Water Flow Alarm (<5 m³/h)

- **Freshwater pump failure**: Most critical cause — flow drops to near zero rapidly.
- **Thermostat stuck in closed position**: Restricts flow through the cooler; engine temperature rises.
- **Air in the cooling circuit**: Air pockets reduce effective flow; typically follows maintenance work.
- **Blocked strainer or filter in cooling circuit**: Gradual flow reduction.
- **Pipe leak or burst hose**: Flow drops; coolant level in expansion tank falls.
- **Pump cavitation**: Occurs if suction pressure drops; pump runs but delivers little flow.

## How to Diagnose

1. Check which DG unit has low flow — a single unit affected indicates a localised pump or circuit fault; multiple units affected simultaneously suggests a common cause (seawater side, central cooler).
2. Check if the freshwater pump for that DG is running — confirm pump pressure.
3. Check expansion tank level — low level combined with low flow suggests a leak.
4. Compare inlet and outlet temperatures if available — small temperature difference with low flow = poor flow, not a temperature problem yet.

## Recommended Actions

1. **Low CW flow alarm**: Reduce load on affected DG immediately; switch to standby cooling pump if available.
2. **Check pump**: Verify pump is running and developing pressure; prime if necessary.
3. **Check expansion tank**: Top up if low; locate and repair any visible leak.
4. **If flow cannot be restored**: Take affected DG offline before engine temperature rises to trip point; distribute load to remaining generators.
5. **Do not restart after low-flow trip** until root cause is identified and corrected.

## Cascade Risk
- Low cooling water flow → engine jacket overheats → automatic engine trip within minutes
- Engine trip → power reduction on bus → risk of overload on remaining DGs (see auxiliary_engines.md)
- Multiple DG cooling failures simultaneously → blackout

## Regulations
- SOLAS and class rules require automatic engine shutdown on high jacket water temperature.
- Class rules: freshwater chemistry (pH, inhibitor concentration) must be checked monthly; expansion tanks must be fitted with low-level alarms.

## Sources
- Project IAS sensor catalogue: `services/generator/sensors.py` (tag references H06006, H06008, H06010, H06012, H06014)
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015) – central cooling system description: [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
