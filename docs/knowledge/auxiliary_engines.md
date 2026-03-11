# Generator Power Output and Emergency Diesel Generator (EMDG)

## Scope
Supports events related to electrical power output from the five diesel generators (DG1–DG5) and the emergency diesel generator (EMDG). Relevant sensors: `dg1–5_power_mw`, `dg1–5_engine_load`, `emdg_speed`.

## System Role
Each diesel generator is coupled to an alternator producing 3-phase AC power. Five generators run in parallel on the main switchboard, sharing load proportionally. Rated capacity per generator is 16 MW. Typical cruise load is 8–10 MW per unit. The Power Management System (PMS) automatically starts or stops generators based on total bus demand.

The Emergency Diesel Generator (EMDG) is a separate, independent unit required by SOLAS. It starts automatically on main power loss and supplies essential systems: emergency lighting, navigation lights, steering, fire detection, and communications.

## Monitored Parameters and Alarm Thresholds

Values from project IAS sensor catalogue (`services/generator/sensors.py`), derived from real ship IAS tag data.

| Sensor | IAS Tag Reference | Normal | Alarm High | Alarm Low |
|---|---|---|---|---|
| DG power output (DG1–5) | PD1101_Power – PD5101_Power | ~8 MW | >15.5 MW | – |
| DG engine load (DG1–5) | DA41xxx | ~60 % | >90 % | – |
| EMDG speed | EMDG_SPEED | 720 rpm | >750 rpm | <680 rpm |

> DG rated capacity: 16 MW per unit. Alarm at 15.5 MW = ~97 % of rated capacity, indicating near-maximum loading.

## Causes of Power and Load Alarms

**DG overpower / overload (>15.5 MW or >90 % load):**
- Too many large consumers online simultaneously (bow thruster, cranes, hotel)
- One or more parallel generators have tripped offline
- PMS failed to start a standby generator when load increased
- Unexpected step load from large motor start

**Generator trip (loss of one unit from bus):**
- Overcurrent protection operated
- Engine-side fault: overspeed, low LO pressure, high temperature (see main_engine.md)
- Differential protection – internal alternator fault
- Manual isolation for maintenance

**Cascade to blackout:**
- One generator trips → remaining units overloaded → second trip → total blackout
- Blackout = loss of all propulsion, hotel, and navigation loads

**EMDG overspeed (>750 rpm) or underspeed (<680 rpm):**
- Governor malfunction during weekly test run
- Fuel supply issue (air in fuel line after long standby)
- Bearing wear or mechanical fault

## How to Diagnose

1. Check individual DG power outputs — one unit above 15.5 MW while others are normal indicates PMS load-sharing fault or a generator offline.
2. Compare total bus load vs. online generating capacity — if total demand exceeds capacity, overload cascade is imminent.
3. On EMDG alarm: check whether alarm occurred during scheduled weekly test (normal). If outside test period, investigate fuel supply and governor.

## Recommended Actions

1. **DG overload**: Start standby generator via PMS or manual; shed non-critical loads (HVAC, galley, non-essential hotel loads).
2. **Generator trip**: PMS should auto-start standby — confirm this occurred; investigate trip cause before restart.
3. **Blackout**: EMDG should auto-start and restore emergency bus within 45 seconds (SOLAS requirement); restore main generators in sequence; reconnect loads gradually.
4. **EMDG alarm during test**: Stop test; inspect governor and fuel supply before scheduling next test.

## Cascade Risk
- DG trip → remaining units overloaded → cascade blackout
- Blackout → loss of steering, propulsion, navigation lights, bilge pumps
- EMDG failure on standby undetected → no emergency power when needed

## Regulations
- SOLAS Ch. II-1, Regulation 42 (passenger ships) / Regulation 43 (cargo ships): Emergency generator must start automatically and restore power within 45 seconds of main power loss. Minimum fuel: 18 hours (cargo) / 36 hours (passenger ships).
- IMO MSC.302(87) (2010): Generator alarms are classified as Alarm (immediate attention required). Blackout event = Emergency Alarm (immediate danger to ship).
- Class rules: All generator protective trips (overcurrent, overspeed, differential) must be tested at periodic survey intervals.

## Sources
- Project IAS sensor catalogue: `services/generator/sensors.py` (tag references PD1101_Power–PD5101_Power, DA41xxx, EMDG_SPEED)
- SOLAS Ch. II-1, Regulation 42/43 – Emergency source of electrical power (18h/36h capacity and 45-second start requirement): cited and confirmed via IMO COMSAR.1/Circ.32/Rev.3: [wwwcdn.imo.org – COMSAR.1/Circ.32/Rev.3](https://wwwcdn.imo.org/localresources/en/OurWork/Safety/Documents/IMO%20Documents%20related%20to/COMSAR.1-Circ.32-Rev.3.pdf)
- IMO MSC.302(87) – Performance Standards for Bridge Alert Management (2010): [imo.org – MSC.302(87).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302(87).pdf)
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015): [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
