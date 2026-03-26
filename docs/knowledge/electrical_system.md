# Electrical Power Management System Monitoring

## Scope
Supports events related to the ship's electrical power generation and distribution. Overlaps with `auxiliary_engines.md` (DG power) and `main_engine.md` (engine load). This file focuses on the Power Management System (PMS) logic, blackout scenarios, and alert classification.

## System Role
The ship's electrical system consists of:
- **Generators** (DG1–DG5, each up to 16 MW): Produce 3-phase AC power fed to the main switchboard (MSB).
- **Main Switchboard (MSB)**: Central distribution point connecting all generators and distributing power to consumers.
- **Power Management System (PMS)**: Automatically manages generator start/stop, load sharing, blackout prevention, and synchronisation.
- **Emergency Generator (EMDG)**: Mandatory backup per SOLAS — starts automatically on blackout, supplies critical systems only.

> Source: Wärtsilä Encyclopedia of Ship Technology, 2nd ed. — electrical system overview.

## Monitored Parameters and Alarm Thresholds

Values from project IAS sensor catalogue (`services/generator/sensors.py`), derived from real ship IAS tag data.

| Sensor | IAS Tag Reference | Normal | Alarm High | Alarm Low |
|---|---|---|---|---|
| DG power output (DG1–5) | PD1101_Power – PD5101_Power | ~8 MW | >15.5 MW | – |
| DG engine load (DG1–5) | DA41xxx | ~60 % | >90 % | – |
| EMDG speed | EMDG_SPEED | 720 rpm | >750 rpm | <680 rpm |

## PMS Functions (Normal Operation)
1. Monitors total electrical load vs. online generating capacity at all times.
2. Auto-starts standby generator when load approaches capacity limit (~80–85 % of online capacity).
3. Auto-stops a generator when load drops sufficiently (typically <40 % of capacity per running unit).
4. Load-shares between running generators proportionally.
5. Prevents large motor starts (bow thruster, cranes) if insufficient capacity is online.
6. Auto-restores power sequence after blackout.
7. Synchronises incoming generator to busbar before closing circuit breaker.

## Alert Classification (MSC.302(87))

IMO MSC.302(87) defines four alert priorities. For electrical events:

| Situation | Alert Priority |
|---|---|
| Blackout (total power loss) | **Emergency Alarm** – immediate danger to ship |
| Generator trip (one unit offline) | **Alarm** – immediate attention and action required |
| Generator overload approaching limit | **Warning** – precautionary attention required |
| Standby generator ready but not started | **Caution** – awareness required |

> Source: IMO MSC.302(87), Performance Standards for Bridge Alert Management, adopted 17 May 2010.

## Causes of Electrical Alarms

**Overload (>15.5 MW per DG / >90 % load):**
- Unexpected large load start without PMS pre-approval
- Generator trip reducing available capacity
- PMS failure to start standby generator

**Generator trip:**
- Overcurrent protection — consumers drawing more than rated current
- Engine-side fault (overspeed, low LO pressure, high temperature — see main_engine.md)
- Differential protection — internal alternator fault

**Blackout (total power loss):**
- Cascade: first generator trips → remaining generators overloaded → cascade trip → blackout
- Common-mode fault (shared fuel supply, shared cooling system failure)
- SOLAS requires EMDG to restore emergency bus within 45 seconds

**EMDG fails to start:**
- Fuel supply fault (air in fuel, low fuel level)
- Battery discharged (starting battery not maintained)
- Governor or mechanical fault

## How to Diagnose

1. Check which generators are online and their individual load percentages.
2. On overload: identify which consumer caused the load increase (large motor start, thruster demand).
3. On blackout: verify EMDG started and emergency bus energised within 45 seconds; then proceed with main generator restoration sequence.
4. Check MSB trip indicators — trip cause is displayed on MSB panel for each generator.

## Recommended Actions

1. **Overload**: Start standby generator; shed non-critical loads (HVAC, galley, hotel non-essential).
2. **Generator trip**: Confirm PMS started standby; investigate trip cause; do not restart without clearing fault.
3. **Blackout recovery**: Verify EMDG online → start first main generator → synchronise and close → reconnect loads gradually → start additional generators as needed.
4. **EMDG alarm**: Investigate during next test; check fuel supply, batteries, and governor.

## Cascade Risk
- One DG trip → bus overloaded → cascade trip → blackout
- Blackout → loss of steering, propulsion motors, navigation lights, bilge pumps, fire detection (all on emergency bus after EMDG starts)
- Synchronisation failure → circuit breaker refuses to close → generator cannot be reconnected

## Regulations
- SOLAS Ch. II-1, Regulation 42/43: Emergency generator must restore power within 45 seconds; must supply emergency lighting, navigation lights, fire detection, watertight door indicators, communications for minimum 18 h (cargo) / 36 h (passenger ships).
- IMO MSC.302(87) (2010): Electrical alarms must be categorised and presented through Central Alert Management.
- Class rules: Generator protective relays (overcurrent, differential, reverse power) must be tested at each periodic survey.

## Sources
- Project IAS sensor catalogue: `services/generator/sensors.py` (tag references PD1101_Power–PD5101_Power, DA41xxx, EMDG_SPEED)
- SOLAS Ch. II-1, Regulation 42/43 (emergency generator requirements cited via IMO circular): [wwwcdn.imo.org – COMSAR.1/Circ.32/Rev.3](https://wwwcdn.imo.org/localresources/en/OurWork/Safety/Documents/IMO%20Documents%20related%20to/COMSAR.1-Circ.32-Rev.3.pdf)
- IMO MSC.302(87) – Performance Standards for Bridge Alert Management (2010): [imo.org – MSC.302(87).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302(87).pdf)
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015): [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
