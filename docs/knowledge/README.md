# Knowledge Base Authoring Guide

This folder contains curated maritime reference notes used by the RAG system (pgvector + Ollama).

**Note**: This README is excluded from RAG ingest by the ingest script. All other `.md` files in this folder are ingested.

---

## Goal

Each file should be focused on one operational topic and written for retrieval quality, not as a full report. Keep files factual, source-backed, and structured for similarity search.

## Recommended file format

```md
# Title

## Scope
Short description of what event/sensor patterns this note supports.

## Causes
- ...

## How to diagnose
- ...

## Recommended actions
1. ...

## Limits / regulations
- ...

## Sources
- Source title: https://...
```

## Writing rules

- Keep each file short and focused (roughly 400–800 words per file).
- One theme per file (e.g., scrubber emissions, lubrication, fuel quality).
- Use trusted primary sources: IMO, class societies (DNV/ABS/IACS), OEM manuals, standards bodies.
- Summarise relevant points; do not paste raw documents.
- Do not include prompt-like instructions to the AI — only domain facts and procedures.
- Always include source links at the end.

---

## Current Knowledge Files

### Point 1 – Ship Systems (operational domain)
| File | Contents |
|---|---|
| `main_engine.md` | DG1–DG5 engine internals: speed, fuel rack, charge air, TC, LO flow |
| `auxiliary_engines.md` | DG power output, engine load, EMDG, SOLAS emergency power |
| `fuel_system.md` | HFO/MGO booster flows, tanks, quality, scrubbers, MARPOL |
| `cooling_system.md` | Jacket cooling water flow per DG, HT/LT circuit context |
| `electrical_system.md` | PMS, bus load, MSC.302(87) alert priorities, emergency generator |
| `propulsion_system.md` | Diesel-electric propulsion context (no direct propulsion sensors) |
| `ballast_system.md` | BWM Convention D-2 context (no ballast sensors in current dataset) |
| `navigation_systems.md` | Water depth, vessel speed, SOLAS V, BNWAS escalation |
| `p1_event_context.md` | 6-step event triage pattern, system dependency map, alert classification |

### Points 2–10 – Cross-system knowledge
| File | Contents |
|---|---|
| `p2_sensors_what_they_measure.md` | Sensor types: temperature, pressure, vibration, flow, level, RPM |
| `p3_normal_values_thresholds.md` | Full alarm threshold tables (all IAS tags) + OEM reference values |
| `p4_alarm_types_cascading.md` | Alarm classification, trigger types, failure patterns, cascade chains |
| `p5_troubleshooting_procedures.md` | First response, alarm evaluation checklist, common causes per alarm |
| `p6_stale_missing_sensor_data.md` | Sensor loss states, NAMUR NE107 health model, system behavior |
| `p8_data_quality_lineage.md` | Data quality dimensions, lineage model, traceability metadata |
| `p9_maritime_regulations.md` | Regulatory reference table (MSC.302, A.741, IACS UR E22/Z27, etc.) |
| `p10_incident_analysis_reporting.md` | Marine casualty/incident/near-miss, RCA, event report structure |
