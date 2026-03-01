# Point 10 – Maritime Event Analysis and Reporting

## Scope

This reference supports incident classification, root cause analysis, and reporting in a maritime monitoring system. Intended for RAG retrieval when the AI agent needs to explain what type of event has occurred, how to analyze it, or what a report should contain.

---

## Purpose of a Maritime Safety Investigation

A maritime safety investigation is conducted to understand:
1. **What happened**
2. **Why it happened**
3. **How similar events can be prevented in the future**

Its purpose is **prevention, not blame or liability**. The investigation should collect evidence, analyze the event, identify causal factors, and produce findings or safety recommendations that reduce future risk.

> Source: IMO MSC.255(84) Casualty Investigation Code: https://wwwcdn.imo.org/localresources/en/OurWork/MSAS/Documents/Res.MSC.255%2884%29CasualtyIinvestigationCode.pdf

---

## Key Definitions

| Term | Definition |
|---|---|
| **Marine casualty** | An event or sequence of events directly connected with ship operations resulting in serious consequences: death, serious injury, loss of person from ship, loss or abandonment of a ship, material damage to a ship, or serious environmental harm |
| **Marine incident** | An event or sequence of events directly connected with ship operations that is **not** a marine casualty, but endangered — or if not corrected would endanger — the ship, people, or the environment |
| **Near-miss** | A sequence of events and/or conditions that **could have resulted in loss**, but the loss was avoided only because the chain of events was interrupted by chance or by timely intervention |

**These terms are not interchangeable**:
- A marine incident involves actual endangerment without reaching casualty severity
- A near-miss is a no-loss event that still had real loss potential

> Source: IMO MSC.255(84) Casualty Investigation Code

---

## Difference Between Incident, Near-Miss, and Alarm

| Concept | In this system |
|---|---|
| **Alarm** | A control-system or IAS signal indicating an abnormal condition requiring operator response. An alarm is not the same as an incident. |
| **Near-miss** | An operational event that could have caused loss, but did not. Higher threshold than an alarm — requires actual endangerment potential, not just a sensor threshold crossing. |
| **Incident** | An event that actually endangered safety, operations, or the environment. Requires investigation and corrective action. |

**Rule**: a single alarm crossing a threshold is usually not a near-miss. A near-miss typically involves multiple alarms, operator inaction or delayed action, and a situation that came close to causing real harm.

---

## How a Maritime Event Should Be Analyzed

Follow this seven-step investigation sequence:

**Step 1 – Decide whether the event requires analysis**
Determine if the event is serious enough, likely enough to recur, or important enough to justify a full investigation.

**Step 2 – Initiate the investigation**
Define who is responsible, the scope, and required resources.

**Step 3 – Gather and preserve data**
Collect from: people (interviews), documents (logs, SMS), electronic data (IAS records, RAG event log), physical evidence, location/position data, photos, charts, recordings, and all other relevant evidence.

**Step 4 – Analyze the data**
Reconstruct what happened, in what order, under what conditions. Identify what is known, what is missing, and what needs clarification.

**Step 5 – Identify causal factors and root causes**
Determine the actions, omissions, events, or conditions without which the event would not have happened (or would not have been as serious). Go deeper than the most obvious explanation.

**Step 6 – Develop recommendations**
Address identified causal factors; aim to prevent recurrence by improving procedures, systems, equipment, or practices.

**Step 7 – Complete the report and archive the case**
Document the event, analysis, and recommended actions. Store in a way that supports later review and trend analysis.

> Source: ABS Root Cause Analysis Guidance (Investigation of Marine Incidents): https://ww2.eagle.org/content/dam/eagle/rules-and-guides/current/other/142_investigationofmarineincidents/ii_rca_guidance_e-feb14.pdf
> Source: IMO MSC.255(84) Casualty Investigation Code

---

## Root Cause Analysis in Maritime Context

Root cause analysis (RCA) goes beyond the immediate or apparent cause.

| Type | Focus |
|---|---|
| **Apparent Cause Analysis (ACA)** | The visible or immediate causes — what seems to have triggered the event |
| **Root Cause Analysis (RCA)** | The deeper underlying causes — why the event became possible in the first place |

A strong maritime RCA examines:
- Equipment failures and design factors
- Procedures that were absent, inadequate, or not followed
- Human factors (decision-making, fatigue, communication, supervision)
- Organizational/management factors (training, maintenance policy, workload)
- System safeguards that failed or were not in place

A simple internal cause grouping (useful for tag-based categorization):
1. **Human factors**
2. **System / procedure factors**
3. **Equipment / design factors**
4. **Other / external factors**

> Source: ABS Root Cause Analysis Guidance: https://ww2.eagle.org/content/dam/eagle/rules-and-guides/current/other/142_investigationofmarineincidents/ii_rca_guidance_e-feb14.pdf

---

## What Should Be Included in an Event Report

A good maritime event report includes:

| Section | Content |
|---|---|
| **Summary** | Short description of the event |
| **Identification** | Vessel, location, date/time UTC, involved parties |
| **Narrative** | What happened, in sequence |
| **Timeline** | UTC timestamps of events, alarm acknowledgments, actions taken |
| **Evidence** | Documents, logs, IAS data, interviews, recordings, physical findings used |
| **Analysis** | Causal factors, dependency chain, what went wrong |
| **Findings / conclusions** | Summary of what the analysis determined |
| **Safety issues identified** | Systemic or procedural weaknesses revealed |
| **Recommendations** | Corrective and preventive actions (CAPA) |
| **Appendices** | Only if directly useful to understanding the analysis |

The report should include enough detail for safety issues to be understood and acted on, without irrelevant content.

> Source: IMO MSC.255(84) Casualty Investigation Code: https://wwwcdn.imo.org/localresources/en/OurWork/MSAS/Documents/Res.MSC.255%2884%29CasualtyIinvestigationCode.pdf
> Source: IMO MSC-MEPC.7/Circ.7 (Guidance on Near-Miss Reporting, 2008): https://wwwcdn.imo.org/localresources/en/OurWork/HumanElement/Documents/MSC-MEPC7%20Circulars/7.pdf
> Supporting reference: Martecma Marine Casualty Report Internal Investigation Guidelines (industry practice guide): https://martecma.com/wp-content/uploads/2023/02/Marine_Casualty_Report_Internal_Investigation_Guidelines_06Aug13-clean.pdf

---

## Near-Miss Reporting and Investigation

Near-misses should be reported and investigated because they share the same underlying causes as actual losses. Investigating near-misses helps improve safety before a more serious event occurs.

**Minimum near-miss review captures**:
- Who and what was involved
- What happened, where, when, and in what sequence
- What the potential losses could have been
- How severe those losses could have been
- How likely the chain of events is to happen again

If the near-miss was likely to recur or could have had severe consequences: investigate more deeply rather than treating as a minor note.

> Source: IMO MSC-MEPC.7/Circ.7 (Reporting of Near-Misses): https://wwwcdn.imo.org/localresources/en/OurWork/HumanElement/Documents/MSC-MEPC7%20Circulars/7.pdf

---

## Just Culture and Reporting

Near-miss and event reporting works better when people can report safety-relevant information without fear of automatic punishment. A "just culture" supports:
- Open reporting of errors, near-misses, and unsafe conditions
- Separation of honest mistakes (to be learned from) and unacceptable behavior (to be addressed separately)

**For this monitoring system**: the event log and alarm history should encourage learning, not blame assignment. All event records should be treated as improvement opportunities.

---

## Recommended Implementation (for this project)

1. **Unified event model** with severity (`critical` / `warning` / `info`) and state lifecycle (`active` → `acknowledged` → `cleared`)
2. **Mandatory event fields**: `event_id`, `vessel_id`, `source_system`, `sensor_name`, `measured_value`, `threshold_value`, `unit`, `severity`, `state`, `created_at_utc`, `updated_at_utc`, `acknowledged_by`, `acknowledged_at_utc`, `suspected_cause`, `recommended_actions`, `actual_actions`
3. **Incident classification field**: `event_type` = `alarm` / `near_miss` / `incident`
4. **Data quality linkage**: tag alarms with `data_quality_flag` to distinguish process events from instrumentation errors
5. **ISM alignment**: map each resolved event to follow-up owner and corrective action; retain auditable history

---

## Scope Limitation

This reference provides a compact framework for:
- analyzing maritime events
- distinguishing incident, near-miss, and alarm
- structuring event reports
- applying root cause analysis

It does **not** define:
- company-specific report templates or approval workflows
- internal severity thresholds for this project
- company-specific CAPA processes
- specific escalation contacts

Those must come from internal operating procedures.

---

## Sources

- IMO MSC.255(84) Casualty Investigation Code: https://wwwcdn.imo.org/localresources/en/OurWork/MSAS/Documents/Res.MSC.255%2884%29CasualtyIinvestigationCode.pdf
- Martecma Marine Casualty Report Internal Investigation Guidelines (industry practice guide, secondary): https://martecma.com/wp-content/uploads/2023/02/Marine_Casualty_Report_Internal_Investigation_Guidelines_06Aug13-clean.pdf
- IMO MSC-MEPC.7/Circ.7 (Near-Miss Reporting Guidelines): https://wwwcdn.imo.org/localresources/en/OurWork/HumanElement/Documents/MSC-MEPC7%20Circulars/7.pdf
- ABS Root Cause Analysis Guidance (Investigation of Marine Incidents): https://ww2.eagle.org/content/dam/eagle/rules-and-guides/current/other/142_investigationofmarineincidents/ii_rca_guidance_e-feb14.pdf
- IMO A.741(18) ISM Code: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.741(18).pdf
