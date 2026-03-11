# Point 5 – Troubleshooting Procedures (Alarm Handling)

## Scope

This reference describes how to handle alarms in a maritime monitoring system: what an alarm is, what the first response should look like, and what an alarm evaluation checklist must contain. Intended for RAG retrieval when the AI agent needs to guide an operator through an alarm response or explain the reasoning behind an action sequence.

---

## What Is an Alarm

An alarm is an audible and/or visible indication to the operator of an equipment malfunction, process deviation, or abnormal condition that **requires a response**.

Alarm handling is primarily a **work-process and operator-response discipline**, not just a hardware or software function. The alarm system should be governed by an **alarm philosophy** defining:
- the objectives of the alarm system
- the work processes used to manage alarms
- responsibilities for operating and maintaining alarm response

Site-specific escalation paths, detailed roles, and local response procedures must be defined by internal plant/vessel documents, not inferred from generic standards.

> Source: Rockwell Automation Alarm Rationalization Whitepaper: https://literature.rockwellautomation.com/idc/groups/literature/documents/wp/proces-wp015_-en-p.pdf

---

## First Response When an Alarm Is Triggered

Follow this structured validation sequence:

1. **Check alarm validity** — confirm the alarm indicates a real malfunction, deviation, or abnormal condition (not a sensor/instrumentation fault)
2. **Determine consequence of inaction** — identify the direct consequence if no action is taken; if there is no direct consequence, the condition may not be a true alarm
3. **Confirm likely cause** — review related process measurements and system status to verify and identify the root cause
4. **Take corrective action** — perform the action needed to correct the abnormal condition; acknowledging the alarm is not the same as corrective action
5. **Act within the available response time** — corrective action must happen before the consequence occurs; if response time is too short for the operator, the response should be automated (interlock), not manual-only

> Source: Rockwell Automation Alarm Rationalization Whitepaper: https://literature.rockwellautomation.com/idc/groups/literature/documents/wp/proces-wp015_-en-p.pdf

---

## Standard Alarm Evaluation / Checklist Structure

Each alarm should be documented in a consistent format. A practical alarm record includes:

| Field | Description |
|---|---|
| **Alarm validity** | Does the alarm indicate a real abnormal condition requiring timely operator action? |
| **Consequence of inaction** | What happens if no action is taken? |
| **Cause** | The likely events or conditions this alarm uniquely identifies |
| **Confirmation** | Other measurements or conditions the operator can check to verify the alarm is real |
| **Corrective action** | The specific operator steps required to correct the condition |
| **Operator response time** | Time available from alarm activation until action is too late to prevent consequence |
| **Alarm priority** | How urgently the alarm should be addressed (critical / warning / info) |
| **Alarm classification** | Grouping by shared requirements (training, testing, reporting) |
| **Special handling** | Any suppression, routing, or handling logic |

> Source: Rockwell Automation Alarm Rationalization Whitepaper: https://literature.rockwellautomation.com/idc/groups/literature/documents/wp/proces-wp015_-en-p.pdf
> Source: Emerson DeltaV Alarm Help Datasheet: https://www.emerson.com/documents/automation/product-data-sheet-deltav-alarm-help-deltav-en-57766.pdf

---

## What Makes an Alarm Actionable

A condition should **only be treated as an alarm** if all of these are true:
- it indicates a real malfunction, deviation, or abnormal condition
- it requires a timely operator action
- there is a clear consequence if no action is taken
- there is a defined corrective action the operator can perform

If there is **no direct consequence** → treat as indicator/monitoring, not alarm.
If there is **no corrective action** → treat as indicator/monitoring, not alarm.

> Source: Rockwell Automation Alarm Rationalization Whitepaper: https://literature.rockwellautomation.com/idc/groups/literature/documents/wp/proces-wp015_-en-p.pdf

---

## Operator Access to Alarm Response Guidance

Operators must have **immediate access to approved alarm response procedures** at the time the alarm occurs. Response guidance should:
- be fast to retrieve (always available at the operator station)
- be customized to match the vessel's alarm philosophy and local operating practices
- include: classification, time to respond, consequence of inaction, short response instructions

> Source: Emerson DeltaV Alarm Help Datasheet: https://www.emerson.com/documents/automation/product-data-sheet-deltav-alarm-help-deltav-en-57766.pdf

---

## Escalation

This reference does **not** define who an alarm should be escalated to. Escalation targets must be defined by the vessel's alarm philosophy, escalation matrix, SOPs, or callout procedures. External standards support the need for documented responsibilities and work processes, but they do not specify the actual person, team, or role.

**Exception — BNWAS bridge watch escalation** (MSC.128(75)):
- Stage 1: audible alarm on bridge 15 seconds after visual indication fails to be reset
- Stage 2: remote alarm at backup officer's/Master's cabin 15 seconds later
- Stage 3: remote alarm at additional crew locations 90 seconds later

> Source: IMO MSC.128(75) BNWAS: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.128%2875%29.pdf

---

## Project-Specific Troubleshooting Patterns

When the AI agent receives an alarm event, apply this sequence (from `p1_event_context.md`):

1. What sensor fired, and what is its normal range? (check `services/generator/sensors.py`)
2. Which subsystem does this sensor belong to? (Engine / Fuel / Cooling / Electrical / Navigation)
3. What upstream dependency could explain the event?
   - High charge air temp → check cooling water flow and TC speed
   - Generator overload → check how many DGs are online and total bus load
   - Low fuel pressure → check tank level, booster flow, filter state
4. What downstream system is at risk if this event is not handled?
5. Is this a compliance-sensitive event?
   - Scrubber SO₂ >400 ppm in SECA → MARPOL Annex VI
   - Water depth <15 m → SOLAS Ch. V grounding-risk protocol
   - EMDG not starting → SOLAS Ch. II-1 emergency power
6. Is there data uncertainty that limits confidence?
   - If sensor has not reported recently → treat as stale data event, not alarm
   - If only one of five DGs shows anomaly → likely unit-specific fault, not systemic

---

## Common Causes of Specific Alarms

| Alarm | Most Likely Causes | Confirmation Checks |
|---|---|---|
| CW flow low (`<5 m³/h`) | Cooling pump fault, valve closed/stuck, pipe obstruction | Check other DG flows; check pump status |
| Charge air temp high (`>120°C`) | Cooling failure, turbocharger problem, high ambient temp | Check CW flow, TC speed, engine load |
| TC speed high (`>22,000 rpm`) | Overloading, turbocharger surge, air filter obstruction | Check engine load, fuel rack, charge air temp |
| Engine load high (`>90%`) | Too many loads on bus, DG offline, cold weather demand | Check how many DGs are online; check bus load |
| LO flow low (`<3 L/min`) | Pump fault, filter blocked, low oil level | Check oil sump level; check pump pressure |
| HFO viscosity high (`>40 cSt`) | Fuel temperature too low, heater fault | Check HFO temperature; check heater status |
| Water depth low (`<15 m`) | Approaching shallow area, chart error, echo sounder fault | Cross-check GPS position with ENC; reduce speed |
| Vessel speed high (`>25 kn`) | Strong following sea, propulsion control fault, GPS error | Compare SOG with speed log (speed through water) |
| EMDG not starting | Fuel fault, battery fault, mechanical fault | Check EMDG fuel, battery charge, manual start attempt |

---

## Scope Limitation

This reference provides a general framework for troubleshooting and alarm handling. It supports:
- what an alarm is
- what the first response should generally look like
- what an alarm checklist should contain

It does **not** provide:
- site-specific escalation contacts for this vessel
- exact step-by-step procedures for all real alarms on this ship
- plant-specific common causes lists

Those must come from internal operating documents and OEM manuals.

---

## Sources

- Rockwell Automation Alarm Rationalization Whitepaper (PROCES-WP015-EN-P): https://literature.rockwellautomation.com/idc/groups/literature/documents/wp/proces-wp015_-en-p.pdf
- Emerson DeltaV Alarm Help Datasheet: https://www.emerson.com/documents/automation/product-data-sheet-deltav-alarm-help-deltav-en-57766.pdf
- exida Alarm Response Procedures: https://www.exida.com/blog/alarm-response-procedures-more-than-just-a-good-idea
- Yokogawa Implementing Alarm Management (PDF): https://web-material3.yokogawa.com/Implementing_alarm_management.PDF
- ISA / PAS Understanding ISA-18.2: https://www.isa.org/getmedia/55b4210e-6cb2-4de4-89f8-2b5b6b46d954/PAS-Understanding-ISA-18-2.pdf
- IMO MSC.128(75) BNWAS: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.128%2875%29.pdf
- Project IAS sensor catalogue: `services/generator/sensors.py`
