# Point 6 – Stale and Missing Sensor Data

## Scope

This reference explains what it means when a sensor stops reporting, how the system should distinguish between different loss-of-signal states, what common causes are, and how the system should behave when data is missing or stale. Intended for RAG retrieval when the AI agent needs to explain or handle missing/uncertain data.

---

## What It Means When a Sensor Stops Reporting

When a sensor stops reporting, the system must distinguish between several different states rather than treating all cases as the same fault:

| State | Meaning |
|---|---|
| **Sensor failure** | The sensor itself has failed — the device is defective |
| **No communication** | Communication to the data source is defined but not established; no last known value is available |
| **Out of service** | The data source is not operational (maintenance, manual shutdown) |
| **Last known but uncertain** | Communication has failed, but the system still shows the last value that previously had good quality; this value cannot be treated as current or reliable |

**Stale data** is distinct from missing data: a value may still exist in the system buffer, but be too old to be valid. Stale data must be detected by **checking the timestamp**, not by checking whether a numeric value exists.

> Source: OPC UA Part 8 (Data Access) – status codes and quality values: https://reference.opcfoundation.org/Core/Part8/v104/docs/6.3

---

## Standardized Device Health Status

To reduce vendor-specific diagnostic codes, use a four-state health model aligned with NAMUR NE107:

| Status | Meaning |
|---|---|
| **Check Function** | Signal is temporarily invalid, e.g., during testing or forced output |
| **Maintenance Required** | Device is still functioning but needs maintenance soon |
| **Out of Specification** | Device is operating outside allowed limits or parameters |
| **Failure** | Signal is invalid due to a fault in the sensor, instrument, or actuator |

This provides a simple, consistent way to describe whether data is valid, uncertain, or invalid without filling the system with vendor-specific diagnostic codes.

> Source: Endress+Hauser NAMUR NE107 overview: https://www.endress.com/en/support-overview/learning-center/namur-ne-107
> Source: Endress+Hauser NAMUR NE107 technical document: https://portal.endress.com/wa001/dla/5000198/9069/000/05/Ti115ren_0608.pdf

---

## Common Causes of Missing or Invalid Sensor Data

| Cause | Description |
|---|---|
| **Sensor failure** | The physical sensor has failed (e.g., thermocouple wire break, transducer damage) |
| **Communication failure** | Network, fieldbus, or serial connection to the IAS is interrupted |
| **Cable / loop fault** | Analog signal wiring is broken or signal falls outside the expected 4–20 mA range |
| **Temporary test/service state** | Signal has been intentionally put in test mode; value is not a real process measurement |
| **Out-of-spec / parameter issue** | Device is operating outside allowed limits and measurement cannot be trusted |

This covers general-level causes. Root causes specific to this system's software must be documented in internal technical documents.

---

## Practical Example: 4–20 mA Loop Fault Detection (NAMUR NE43)

For analog 4–20 mA signals, cable or loop faults can be detected using signal level thresholds:

| Signal Level | Condition |
|---|---|
| ≤ 3.8 mA | Under range (signal below minimum valid range) |
| ≥ 20.5 mA | Over range (signal above maximum valid range) |
| ≤ 3.6 mA or ≥ 21.0 mA | Open circuit (wire break or disconnected loop) |

For 1–5 V analog signals, an equivalent example:
- < 0.8 V or > 5.2 V → open circuit

> These values are a **practical example** of loop fault detection thresholds (based on NAMUR NE43 recommendation). They should be treated as a reference example, not a universal rule for all sensors in all systems.

> Source: Endress+Hauser NAMUR NE107: https://www.endress.com/en/support-overview/learning-center/namur-ne-107

---

## What the System Should Do When Data Is Missing or Stale

When data is missing or stale, the system must:

1. **Mark data quality clearly** — never present an invalid or uncertain value as if it is valid; tag with `bad`, `uncertain`, or equivalent quality flag
2. **Distinguish between "no value" and "last known value"** — if no valid last value exists, treat as missing; if a last known value is displayed, it must be marked as stale/uncertain and not treated as current
3. **Use timestamps to detect stale data** — a value may be numerically present but too old; always check the last-update timestamp against a configured freshness window
4. **Display a simple health status** — show `Failure`, `Check Function`, or `Out of Specification` alongside the process value so the operator knows whether the reading can be used
5. **Trigger a defined response for critical signals** — if missing data affects operations, monitoring, or control, trigger a defined action (alarm, fallback logic, operator notification); the exact response must be defined by internal operating rules

---

## Critical Sensors: What the System Cannot Define

This reference does **not** define which sensors are critical in this installation. That list must come from internal project documents:
- Critical tag list (CTL)
- Interlock / trip list
- Control philosophy
- SIF/SIS documentation
- Internal alarm or fallback rules

**General principle**: a sensor is critical if loss of its signal removes necessary monitoring or control of an important safety, protection, or operational function.

**For this project**, high-criticality signals (by consequence of loss) include:
- `dg*_engine_speed` — loss means DG overspeed protection is blind
- `dg*_cw_in_flow` — loss means cooling failure goes undetected
- `clean_lo_flow` — loss means bearing lubrication protection is blind
- `emdg_speed` — loss means emergency generator status is unknown
- `water_depth` — loss means grounding risk goes undetected
- `scrubber_*_so2` / `scrubber_*_ph` — loss means MARPOL compliance monitoring is disabled

---

## Optional: Sparkplug / MQTT Online/Offline State

If the system uses **Sparkplug B** over MQTT for IIoT messaging, online/offline state can be expressed at the node or host level:

- `online = true` — host/application is online
- `online = false` — host/application is offline
- `timestamp` — when the state last changed

This is useful for communication-level status in Sparkplug-based architectures. It should only be included in RAG if the project architecture actually uses Sparkplug. Do not mix this with general sensor-level logic in non-Sparkplug systems.

> Source: Sparkplug B Specification v3.0.0: https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf

---

## Scope Limitation

This reference explains:
- what missing or stale sensor data means
- general causes
- how the system should represent these states

It does **not** provide:
- the full list of critical sensors for this installation
- exact fallback logic or timeout rules for this system
- internal alarm or escalation rules

Those must be added from internal technical and operating documents.

---

## Sources

- OPC UA Specification Part 8 (Data Access, status codes / quality values): https://reference.opcfoundation.org/Core/Part8/v104/docs/6.3
- Endress+Hauser NAMUR NE107 overview: https://www.endress.com/en/support-overview/learning-center/namur-ne-107
- Endress+Hauser NAMUR NE107 technical document (Ti115ren): https://portal.endress.com/wa001/dla/5000198/9069/000/05/Ti115ren_0608.pdf
- Sparkplug B Specification v3.0.0: https://sparkplug.eclipse.org/specification/version/3.0/documents/sparkplug-specification-3.0.0.pdf
- ISA / PAS Understanding ISA-18.2: https://www.isa.org/getmedia/55b4210e-6cb2-4de4-89f8-2b5b6b46d954/PAS-Understanding-ISA-18-2.pdf
- Project IAS sensor catalogue: `services/generator/sensors.py`
