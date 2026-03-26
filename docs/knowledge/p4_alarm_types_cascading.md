# Point 4 – Alarm Types, Triggers, and Cascading Failures

## Scope

This reference supports alarm interpretation in maritime monitoring systems. It is intended for RAG retrieval when the system needs to explain:
- alarm classes and what they mean
- what actually triggers an alarm
- common failure patterns in sensor/process data
- cascading failure behavior (one fault causing multiple alarms)

---

## Alarm Classification

Use one consistent severity model across dashboards and APIs:

| Severity | Meaning | Response |
|---|---|---|
| `critical` | Immediate risk to safety, propulsion, or major equipment | Immediate operator action; escalate if unresolved |
| `warning` | Abnormal condition that can become critical if not handled | Prompt operator action and monitoring |
| `info` | Notable state change or advisory condition; low immediate risk | Awareness; follow up if persistent |

**Important**: severity must be tied to **consequence** and **available response time**, not only to how far the reading is from a threshold.

**Mapping to IMO MSC.302(87) / A.1021(26) priorities**:

| IMO Priority | Project Severity | Examples in this system |
|---|---|---|
| Emergency Alarm | `critical` | Blackout, total loss of cooling, grounding risk |
| Alarm | `critical` | DG trip, EMDG failure, engine overspeed, LO flow loss |
| Warning | `warning` | Engine load >90%, rising charge air temp, scrubber pH declining |
| Caution | `info` | Approaching low tank level, TC speed rising gradually |

> Source: IMO MSC.302(87) Bridge Alert Management: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf
> Source: IMO A.1021(26) Code on Alerts and Indicators: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.1021(26).pdf

---

## What Triggers an Alarm

Alarms must be triggered by explicit rules. Common trigger types:

1. **Absolute threshold** — high-high, high, low, low-low limits on a single signal (e.g., CW flow <5 m³/h)
2. **Deviation trigger** — difference from expected setpoint, model prediction, or paired sensor (e.g., one DG much hotter than others)
3. **Rate-of-change trigger** — signal changes too fast over time (e.g., rapid temperature rise indicates sudden cooling loss)
4. **Persistence trigger** — condition must remain abnormal for X seconds before alarm fires; avoids transient noise alarms
5. **State/event trigger** — device status change: trip, fail, communication lost, mode mismatch
6. **Data quality trigger** — missing, stale, frozen, out-of-range, or implausible sensor data
7. **Composite trigger** — multiple conditions together (e.g., low flow AND rising temperature) indicating higher-confidence diagnosis

---

## Common Failure Patterns

Patterns to recognize in sensor/process data:

| Pattern | Description |
|---|---|
| `stuck sensor` | Value flatlines despite known process changes; reading has not moved for an implausible period |
| `drifted sensor` | Gradual bias accumulation; reading slowly diverges from true value |
| `spike / noise` | Short transient excursions creating false positives; usually filtered with persistence timer |
| `intermittent comms` | Alternating normal and missing samples; check communication path, not process |
| `threshold chattering` | Rapid alarm on/off around a limit; needs deadband (hysteresis) to suppress |
| `single-point device fault` | One equipment failure drives several dependent variables abnormal simultaneously |
| `configuration error` | Wrong engineering units, swapped tag IDs, or incorrect limit values |

---

## Cascading Failures (Multi-Alarm Chains)

A cascading failure is when **one underlying fault produces a sequence of dependent alarms**. Do not treat each alarm as independent until correlation is confirmed.

### How to recognize a cascade vs. independent events:
- Close timestamp window (all alarms within seconds/minutes of each other)
- Shared subsystem tags (same DG, same circuit)
- Known dependency graph between signals
- One "first abnormal event" followed by predictable downstream alarms

### Example cascade 1: Cooling failure chain

```
1. Cooling subsystem degradation (pump failure / valve sticking / flow restriction)
   → dg*_cw_in_flow drops below 5 m³/h         [warning]
2. Engine temperature begins to rise
   → dg*_charge_air_temp climbs above 120 °C    [warning → critical]
3. Protective logic triggers load reduction or engine shutdown
   → dg*_engine_load drops suddenly / DG trips   [critical event]
4. Remaining DGs pick up lost capacity
   → other dg*_engine_load values rise toward 90% [warning]
5. Risk: cascade blackout if remaining DGs cannot absorb load
```

### Example cascade 2: Fuel supply failure chain

```
1. Fuel filter blockage or fuel booster pump failure
   → hfo_booster_*_flow drops                   [warning]
2. Combustion instability
   → dg*_fuel_rack_pos increases (engine hunting for fuel)
   → exhaust temperature spread increases         [warning]
3. Engine protection triggers
   → DG trip or load reduction                   [critical]
```

### Example cascade 3: Power / navigation cascade

```
1. One or more DG trips
   → Total bus capacity reduced
2. Remaining DGs overloaded
   → dg*_engine_load >90%                        [warning]
3. If not resolved: cascade blackout
   → All navigation, propulsion, and safety systems lose power [Emergency Alarm]
4. EMDG must start within 45 seconds (SOLAS Ch. II-1 Reg. 42)
```

---

## How to Diagnose

Use this analysis sequence:

1. **Identify the first abnormal event** in the timestamp sequence — this is the root cause candidate
2. **Confirm trigger validity** — is this a real process issue or a sensor/instrumentation problem?
3. **Check dependency signals** — separate root cause from propagated downstream effects
4. **Classify each event**:
   - Root cause candidate
   - Consequential alarm (caused by root cause)
   - Informational side-effect
5. **Act on the initiating fault first** before addressing downstream alarms

---

## Recommended Implementation (for this project)

1. **Standard alarm schema fields**: `severity`, `state`, `trigger_type`, `trigger_rule_id`, `source_system`, `acknowledged_by`, `acknowledged_at`
2. **Correlation fields**: `correlation_id`, `parent_event_id`, `root_cause_candidate` — enable cascade grouping
3. **Noise controls**: deadband/hysteresis, persistence timers, duplicate suppression within short windows
4. **Dashboard behavior**: root-cause-first ordering; visually group correlated alarms; mark consequential alarms
5. **RAG alarm entry format**: for each alarm include meaning, trigger rule, likely causes, confirmation checks, corrective actions

---

## Scope Limitation

Alert philosophy and terminology should align with MSC.302(87) and A.1021(26). Site-specific thresholds, escalation contacts, and shutdown logic must come from operator SMS, OEM manuals, and approved procedures. This reference provides a technical troubleshooting structure, not sign-off rules.

---

## Sources

- IMO MSC.302(87) Bridge Alert Management: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf
- IMO A.1021(26) Code on Alerts and Indicators: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.1021(26).pdf
- IMO A.741(18) ISM Code: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.741(18).pdf
- Rockwell Automation Alarm Rationalization Whitepaper (PROCES-WP015-EN-P): https://literature.rockwellautomation.com/idc/groups/literature/documents/wp/proces-wp015_-en-p.pdf
- Emerson DeltaV Alarm Help Datasheet: https://www.emerson.com/documents/automation/product-data-sheet-deltav-alarm-help-deltav-en-57766.pdf
- exida Alarm Response Procedures: https://www.exida.com/blog/alarm-response-procedures-more-than-just-a-good-idea
- Yokogawa Implementing Alarm Management (PDF): https://web-material3.yokogawa.com/Implementing_alarm_management.PDF
- ISA / PAS Understanding ISA-18.2 (Alarm Management Standard): https://www.isa.org/getmedia/55b4210e-6cb2-4de4-89f8-2b5b6b46d954/PAS-Understanding-ISA-18-2.pdf
- Project IAS sensor catalogue: `services/generator/sensors.py`
