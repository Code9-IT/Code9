# Diesel Generator Engine Monitoring (DG1–DG5)

## Scope
Supports events from the five diesel generator engines (DG1–DG5) that provide all propulsion and hotel power on this vessel. Relevant sensors: `dg1–5_engine_speed`, `dg1–5_fuel_rack_pos`, `dg1–5_charge_air_temp`, `dg1–5_tc_speed`, `dg1–5_engine_load`, `clean_lo_flow`, `dirty_lo_flow`.

## System Role
This vessel uses diesel-electric propulsion: five 4-stroke constant-speed diesel generators supply AC power to the main switchboard, which drives electric propulsion motors and all hotel loads. The generators run at a fixed nominal speed of 720 RPM regardless of vessel speed or load. Engine load (% of rated BMEP) is the primary indicator of how hard each generator is working.

## Monitored Parameters and Alarm Thresholds

Values from project IAS sensor catalogue (`services/generator/sensors.py`), derived from real ship IAS tag data.

| Sensor | IAS Tag Reference | Normal | Alarm High | Alarm Low |
|---|---|---|---|---|
| Engine speed (DG1–5) | H09214–H09218 / DA41219R–DE41219 | 720 rpm | >742 rpm | <680 rpm |
| Fuel rack position (DG1–5) | DA41195R–DE41195 | ~28 mm | >55 mm | – |
| Charge air temperature (DG1–5) | DA46057R (DG1 ref.) | ~45 °C | >120 °C | – |
| Turbocharger speed (DG1–5) | DA45180R–DE45180 | ~18 000 rpm | >22 000 rpm | – |
| Engine load (DG1–5) | DA41xxx | ~60 % | >90 % | – |
| Clean lube oil supply flow | H06050 | ~10 L/min | – | <3 L/min |
| Dirty lube oil return flow | (return line) | ~9 L/min | >20 L/min | – |

## Causes of Common Alarms

**Engine overspeed (>742 rpm):**
- Governor failure or malfunction
- Sudden loss of electrical load (engine races when load drops)
- Fuel rack stuck open

**High fuel rack position (>55 mm):**
- Engine overloaded (too many consumers on bus)
- Fouled fuel injectors requiring more fuel for same output
- Governor compensating for reduced combustion efficiency

**High charge air temperature (>120 °C):**
- Intercooler fouled or blocked
- Insufficient cooling water flow through intercooler
- Turbocharger delivering insufficient airflow under high load

**Turbocharger overspeed (>22 000 rpm):**
- Sudden loss of exhaust back-pressure
- Bearing failure allowing rotor to accelerate

**Engine overload (>90 % load):**
- Too many electrical consumers active simultaneously
- One or more generators offline; remaining units carrying full load
- Abnormally high hotel, thruster or crane demand

**Low lube oil supply flow (<3 L/min):**
- LO filter blockage (most common cause)
- LO pump failure or wear
- Risk of bearing and cylinder damage if not corrected quickly

## How to Diagnose

1. Compare all five DG engine speeds — a single engine deviating from 720 rpm while others are stable indicates an isolated fault on that unit.
2. Check fuel rack position vs. engine load — high rack with low power output suggests combustion or injector problem.
3. Monitor charge air temp trend — sudden rise indicates intercooler or cooling water issue.
4. Compare clean vs. dirty LO flow — clean supply <3 L/min with normal return flow indicates supply-side filter blockage.

## Recommended Actions

1. **Overspeed**: Engine protection will auto-trip — do not restart until governor and fuel rack inspected.
2. **High fuel rack / overload**: Start additional generator to share load; shed non-essential consumers.
3. **High charge air temp**: Reduce engine load; inspect intercooler cooling water flow.
4. **Low LO supply flow**: Switch to standby LO filter; check pump pressure; do not run at high load.

## Cascade Risk
- Low LO supply flow → bearing damage → engine seizure (minutes)
- All DG engines overloaded → cascade trips → blackout → loss of propulsion and hotel power
- High charge air temp sustained → engine automatic de-rating or trip

## Regulations
- IMO MSC.302(87) (adopted 17 May 2010): All machinery alarms must be categorised by priority (Emergency Alarm / Alarm / Warning / Caution) and visible through the Central Alert Management system.
- Class rules: Overspeed trip, low lube oil pressure trip, and high temperature trip must be fitted, tested, and documented at each periodic survey.

## Sources
- Project IAS sensor catalogue: `services/generator/sensors.py` (tag references H09214–H09218, DA41219R–DE41219, DA41195R–DE41195, DA46057R, DA45180R–DE45180, DA41xxx, H06050)
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015): [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
- IMO MSC.302(87) – Performance Standards for Bridge Alert Management (2010): [imo.org – MSC.302(87).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302(87).pdf)
