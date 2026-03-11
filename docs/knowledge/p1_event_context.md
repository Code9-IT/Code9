# Point 1 – Event Context and Triage Framework

## Purpose
This file helps the AI agent (Ollama) structure event responses correctly.
It covers: system dependency order, alert priority classification, and a
step-by-step triage pattern to apply to any incoming sensor event.

---

## System Dependency Order

When an event fires, understanding what depends on what matters:

1. **Fuel system** feeds engines and generators.
2. **Engines/generators** (DG1–DG5) supply all electrical power.
3. **Electrical distribution** (main switchboard + PMS) supplies navigation,
   control systems, pumps, hotel loads, and propulsion motors.
4. **Cooling system** (`dg*_cw_in_flow`) keeps engines within safe thermal range.
5. **Lubrication** (`clean_lo_flow`, `dirty_lo_flow`) protects engine bearings.
6. **Propulsion** depends on electrical power availability and propulsor condition.
7. **Navigation systems** depend on electrical power for all sensors and displays.
8. **Ballast / stability** affects the vessel's ability to operate safely.

A fault in any upstream system can cascade downward. The most critical single
point is **loss of all DG generators → blackout** (affects all downstream systems).

---

## Event Triage Pattern for Ollama

For every incoming event, answer in this order:

1. **What sensor fired, and what is its normal range?**
   (Use the sensor name to look up thresholds in the relevant knowledge file.)

2. **Which subsystem does this sensor belong to?**
   (Engine / Fuel / Cooling / Electrical / Navigation — see files in docs/knowledge/)

3. **What upstream dependency could explain the event?**
   - High charge air temp → check cooling water flow and turbocharger speed.
   - Generator overload → check how many DGs are online and total bus load.
   - Low fuel pressure → check tank level, booster flow, and filter state.

4. **What downstream system is at risk if this event is not handled?**
   - Engine CW flow low → engine will overheat → DG trip → loss of capacity.
   - DG trip → remaining DGs overloaded → possible cascade blackout.
   - Blackout → loss of propulsion, steering, navigation, and safety systems.

5. **Is this a compliance-sensitive event?**
   - Scrubber SO₂ >400 ppm, fuel sulphur ≥0.10% in SECA → MARPOL Annex VI.
   - Scrubber pH <6.0 → MEPC.259(68) (current standard requires pH ≥6.5).
   - Water depth <15 m → SOLAS Ch. V grounding-risk protocol.
   - EMDG not starting → SOLAS Ch. II-1 emergency power requirement.

6. **Is there data uncertainty that limits confidence?**
   - If sensor has not reported recently → treat as stale data event, not alarm.
   - If only one of five DGs shows anomaly → likely unit-specific fault, not systemic.

---

## Alert Priority Classification (IMO MSC.302(87))

All alerts on this vessel must be classified per IMO MSC.302(87)
(Performance Standards for Bridge Alert Management, adopted 17 May 2010):

| Priority | Definition | Example in this system |
|---|---|---|
| **Emergency Alarm** | Immediate danger to life or ship | Blackout / total power loss |
| **Alarm** | Requires immediate attention and action | DG trip, engine overspeed, low LO flow |
| **Warning** | Precautionary — not immediately hazardous | Engine load >90%, high charge air temp |
| **Caution** | Awareness required | Approaching low tank level, TC speed rising |

> Source: IMO MSC.302(87), Performance Standards for Bridge Alert Management (2010): [wwwcdn.imo.org – MSC.302(87).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf)

---

## BNWAS Escalation Logic (Navigational Watch Context)

The Bridge Navigational Watch Alarm System (BNWAS) ensures the bridge officer
is alert. Per IMO MSC.128(75):

- **Dormant period**: Officer must reset the system every 3–12 minutes.
- **Stage 1**: If not reset → audible alarm sounds on bridge **15 seconds** after visual indication.
- **Stage 2**: If still not reset → remote audible alarm at backup officer's / Master's cabin **15 seconds** after Stage 1.
- **Stage 3**: If still not reset → remote audible alarm at additional crew locations **90 seconds** after Stage 2. (May be extended up to 3 minutes on larger vessels.)

This is relevant if navigation events occur with no acknowledged response from the bridge team.

> Source: IMO MSC.128(75) – Performance Standards for a Bridge Navigational
> Watch Alarm System (BNWAS), adopted 20 May 2002.
> Direct PDF: [wwwcdn.imo.org/.../MSC.128(75).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.128%2875%29.pdf)

---

## Note on Alarm Thresholds in This System

The numeric alarm thresholds used in event detection (e.g., DG overspeed >742 rpm,
CW flow <5 m³/h) are set in `services/generator/sensors.py`. That file is derived
from an anonymised real ship IAS dataset (128 tags, with original tag codes such as
H09214–H09218, DA41195R–DE41195, etc.).

These are **project-specific thresholds**, not generic published standards.
They reflect the actual alarm setpoints of the vessel this data originates from.
For cross-validation, ranges are consistent with descriptions in:
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015) for
  general 4-stroke medium-speed diesel generator operating envelopes.
- DNV Rules for Classification of Ships, Part 4 (Rotating Machinery) for
  mandatory alarm categories — though exact setpoints remain vessel/OEM specific.

**For RAG use**: trust `sensors.py` values as the system's actual thresholds.
**For the bachelor thesis**: cite as "project IAS sensor catalogue derived from
anonymised ship telemetry data; values consistent with OEM and class society ranges."

---

## Sources
- IMO MSC.302(87) – Bridge Alert Management (2010):
  [imo.org – MSC.302(87).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf)
- IMO MSC.128(75) – BNWAS Performance Standards (2002):
  [imo.org – MSC.128(75).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.128%2875%29.pdf)
- Project IAS sensor catalogue: `services/generator/sensors.py`
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015):
  [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
