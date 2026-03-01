# Fuel Oil and Exhaust Scrubber System Monitoring

## Scope
Supports events related to HFO and MGO fuel delivery, tank levels, fuel quality, exhaust gas scrubbers, and boiler fuel. Relevant sensors: `hfo_booster_a/b/c_flow`, `mgo_booster_a/b_flow`, `hfo_tank_weight`, `mgo_tank_weight`, `hfo_fuel_temp`, `hfo_fuel_viscosity`, `hfo_density`, `mgo_density_a/b`, `scrubber_fwd/aft_so2/co2/ph/power/pah/sulphur`, `boiler_fuel_flow_a/b`.

## System Role
Heavy fuel oil (HFO) is the primary fuel for the diesel generators at sea. Marine gas oil (MGO) is used in port or emission-controlled areas. HFO must be heated to reduce viscosity for injection. Exhaust gas scrubbers remove sulphur from engine exhaust gases when operating in a Sulphur Emission Control Area (SECA), allowing HFO use while complying with MARPOL Annex VI limits.

## Monitored Parameters and Alarm Thresholds

Values from project IAS sensor catalogue (`services/generator/sensors.py`), derived from real ship IAS tag data.

| Sensor | IAS Tag Reference | Normal | Alarm High | Alarm Low |
|---|---|---|---|---|
| HFO booster flow A/B | H06016, H06017 | ~2.5 m³/h | >4.8 m³/h | – |
| HFO booster flow C | H06020 | ~2.5 m³/h | >4.8 m³/h | – |
| MGO booster flow A/B | H06018, H06019 | ~1.2 m³/h | >4.0 m³/h | – |
| HFO tank weight | TK06HFO_TotalWeightTons | ~7 500 tons | – | <500 tons |
| MGO tank weight | TK06MGO_TotalWeightTons | ~2 000 tons | – | <200 tons |
| HFO fuel temperature (A/B/C) | H06086–H06088 | ~90 °C | >150 °C | – |
| HFO fuel viscosity (A/B/C) | H06168–H06170 | ~15 cSt | >40 cSt | – |
| HFO density (A/B) | HFODEN1, HFODEN2 | ~990 kg/m³ | >1 010 kg/m³ | – |
| MGO density (A/B) | MGODEN1, MGODEN2 | ~840 kg/m³ | >880 kg/m³ | – |
| Scrubber SO₂ (FWD/AFT) | SC1336 / SC2336 | ~50 ppm | >400 ppm | – |
| Scrubber CO₂ (FWD/AFT) | SC1335 / SC2335 | ~5 % | >12 % | – |
| Scrubber wash-water pH (FWD/AFT) | SC1109 / SC2109 | ~7.5 | – | <6.0 |
| Scrubber power (FWD/AFT) | SC1500 / SC2500 | ~120 W | >500 W | – |
| Scrubber PAH (FWD/AFT) | SC1108 / SC2108 | ~5 µg/l | >50 µg/l | – |
| Fuel sulphur at scrubber inlet (FWD/AFT) | (scrubber inlet) | ~0.05 % | ≥0.10 % | – |
| Boiler fuel flow A/B | H06030, H06031 | ~1.0 m³/h | >4.0 m³/h | – |

## Regulatory Limits (MARPOL Annex VI)

- **Global sulphur cap**: max 0.50 % m/m from 1 January 2020 (Regulation 14, MARPOL Annex VI).
- **SECA sulphur limit**: max 0.10 % m/m from 1 January 2015 (Baltic Sea and North Sea are SECAs).
- **Scrubber wash-water pH**: minimum 6.5 measured at 4 m from discharge point per IMO MEPC.259(68) (2015 Guidelines for Exhaust Gas Cleaning Systems). Note: the project alarm threshold is set at 6.0, which corresponds to the earlier MEPC.184(59) (2009) guideline.

> Source: MARPOL Annex VI, Regulation 14 (directly verified from IMO official page); MEPC.259(68) (confirmed from USCG/IMO search results).

## Causes of Common Alarms

**High HFO booster flow (>4.8 m³/h):**
- Valve stuck open or control system fault
- High fuel demand from multiple generators at full load

**Low HFO or MGO tank weight:**
- Normal consumption during long voyage without bunkering
- Unexpected consumption: leak in fuel lines or injector dripping

**High HFO temperature (>150 °C):**
- Heater thermostat fault — fuel overheated
- Too-thin fuel reduces lubrication of injection pump plungers

**High HFO viscosity (>40 cSt):**
- Heater failure — fuel too cold; cannot be properly atomised at injection
- Results in black smoke, misfiring, and reduced engine output

**Scrubber SO₂ alarm (>400 ppm):**
- Scrubber wash-water flow insufficient
- Scrubber bypass valve open
- Using high-sulphur fuel without effective scrubbing

**Scrubber pH alarm (<6.0):**
- Wash-water alkalinity depleted (seawater buffering capacity exhausted)
- Excessive sulphur load from high-sulphur fuel
- Circulation pump failure

**Fuel sulphur at scrubber inlet ≥ 0.10 %:**
- Direct MARPOL Annex VI SECA violation — requires immediate reporting
- Wrong fuel loaded or fuel transfer error

**High boiler fuel flow (>4.0 m³/h):**
- Boiler control valve stuck open
- Uncontrolled combustion in boiler — fire risk

## Recommended Actions

1. **High HFO viscosity**: Check heater temperature and thermostat; reduce engine load until viscosity normalises.
2. **Low tank level**: Transfer fuel from storage; check transfer pump; verify no leak.
3. **Scrubber SO₂ alarm**: Check wash-water flow rate; inspect scrubber pump; switch to low-sulphur fuel (MGO) if scrubber cannot be restored.
4. **Scrubber pH alarm**: Increase wash-water flow rate; check pump; log fault — may need to switch to MGO.
5. **Fuel sulphur ≥ 0.10 % (SECA)**: Mandatory to log and report to flag state; switch to compliant fuel immediately.

## Cascade Risk
- HFO viscosity too high → poor atomisation → injector fouling → engine power loss
- Scrubber failure in SECA → regulatory violation → port state control detention
- Low MGO level → forced switch to HFO in port/SECA → compliance breach

## Sources
- Project IAS sensor catalogue: `services/generator/sensors.py` (tag references H06016–H06020, H06086–H06088, H06168–H06170, HFODEN1/2, MGODEN1/2, SC1xxx/SC2xxx, H06030/H06031, TK06HFO/MGO)
- MARPOL Annex VI, Regulation 14 – Sulphur Oxide Emissions (IMO): [imo.org – SOx Regulation 14](https://www.imo.org/en/ourwork/environment/pages/sulphur-oxides-(sox)-%E2%80%93-regulation-14.aspx)
- IMO MEPC.259(68) – 2015 Guidelines for Exhaust Gas Cleaning Systems: [imo.org – MEPC.259(68).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MEPCDocuments/MEPC.259(68).pdf)
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015): [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
