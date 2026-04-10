# Dynamic Dashboard Prioritization

## Purpose

This document describes how the dynamic dashboards should decide which
incident deserves focus.

It separates:

1. what the dashboards do today
2. what a better prioritization model should do next

The goal is not to make the user choose what to inspect first. The goal is
that the system should surface the most relevant incident automatically when
the dashboard is opened.

## User Story Mapping

### Dashboard 1: Single Vessel Incident

Relevant user story:
- User Story 1: `DevOps engineer`

Primary question:
- What is the most important incident on this vessel right now?

### Dashboard 2: Multi-Vessel Incident

Relevant user story:
- User Story 2: `DevOps engineer`

Primary question:
- What is the most important correlated problem across the fleet right now?

## Current Behavior

### Dashboard 1

Current selection logic:
- If `explicit_context` is provided, the dashboard shows that incident.
- If automatic mode is used, the dashboard currently selects the newest active
  alert.

Implication:
- The dashboard is dynamic in how it is generated.
- It is not yet fully dynamic in the sense of always selecting the most
  important incident.

### Dashboard 2

Current selection logic:
- The dashboard looks for the strongest correlated fleet pattern from current
  fleet alerts and correlation data.

Implication:
- This is a useful first heuristic for fleet-wide incidents.
- It is still a heuristic, not a complete prioritization engine.

## Recommended Principle

The dashboards should not prioritize by recency alone.

The strongest signals should be:
- severity
- operational impact
- scope
- correlation
- persistence
- evidence strength

`recency` should be used as a secondary signal or tie-breaker.

## Dashboard 1 Priority Model

Dashboard 1 should rank incidents within one vessel.

Suggested factors:
- `severity`: critical alerts should rank above warning alerts
- `incident type`: `service_down` should rank above `high_latency`
- `application status`: `down` should rank above `degraded`
- `service criticality`: core pipeline apps should rank above peripheral apps
- `persistence`: incidents that remain unresolved should gain weight over time
- `evidence strength`: matching alerts, logs, and metrics should increase score
- `recency`: newer incidents should get a small boost, not dominate selection

Suggested interpretation:
- A critical local outage on one vessel should usually outrank a newer but less
  severe warning.
- A degraded service with strong supporting evidence can outrank a weak,
  short-lived alert spike.

## Dashboard 2 Priority Model

Dashboard 2 should rank incidents across multiple vessels.

Suggested factors:
- `severity`: critical fleet alerts should rank highest
- `fleet spread`: more affected vessels should increase priority
- `app spread`: more affected application instances should increase priority
- `correlation`: same alert type or same app failing across vessels should gain
  strong weight
- `service criticality`: shared core services should rank above lower-impact
  services
- `persistence`: recurring or long-running fleet patterns should gain weight
- `evidence strength`: repeated matching alerts and repeated recurrence should
  increase confidence
- `recency`: recent fleet patterns should get a small boost

Suggested interpretation:
- A correlated issue across several vessels should usually outrank a local issue
  on one vessel.
- A warning-level fleet incident may deserve focus if it affects many vessels
  and points to a systemic problem.

## Example Scoring Approach

An initial implementation could use a transparent rule-based score:

```text
priority_score =
  severity
  + operational_impact
  + scope
  + correlation
  + persistence
  + evidence_strength
  + small_recency_bonus
  - noise_penalty
```

This has three advantages:
- easy to explain
- easy to debug
- easy to tune during demos and evaluations

## Decision Rules

If two incidents have similar scores, the tie-breakers should be:

1. higher severity
2. larger impact scope
3. stronger correlation
4. more recent timestamp

## What This Means for the Thesis/Demo

The important distinction is:
- the dashboards are already dynamic in generation
- they are not yet fully dynamic in prioritization

That means the current prototype proves:
- incident-driven dashboard generation
- scenario-based dashboard composition
- automatic fleet-pattern focus for dashboard 2

The next maturity step is:
- explicit prioritization logic for selecting the incident that matters most

## Recommendation

For this project, the most pragmatic next step is a rule-based prioritization
model, not an opaque AI-first ranking model.

That would make the dashboard behavior:
- more defensible
- easier to present
- easier to align with operator expectations

## Priority List

### Dashboard 1: Single Vessel Incident

Priority order:
1. `critical service_down` on a vessel-critical application
2. `critical connectivity` or `reporting_stale` affecting loss of visibility
3. `high` or `warning` incidents with strong supporting evidence from alerts,
   logs, and metrics
4. `resource_pressure`, `high_latency`, or similar degradation on important
   applications
5. short-lived or weak single-signal alerts

Tie-breakers:
1. stronger evidence
2. longer persistence
3. more recent timestamp

### Dashboard 2: Multi-Vessel Incident

Priority order:
1. `critical` correlated incidents affecting multiple vessels
2. same application failing across several vessels
3. same alert type recurring across several vessels in a short time window
4. warning-level incidents with broad fleet spread and signs of systemic impact
5. isolated vessel incidents with low fleet relevance

Tie-breakers:
1. more affected vessels
2. more critical application type
3. stronger cross-vessel correlation
4. more recent timestamp

## Detailed Scoring Tables

This section proposes a transparent scoring model that could be used to rank
incidents in a deterministic way.

Important note:
- These scores are a proposed prioritization model.
- They are not the full implemented runtime logic today.
- The exact values should be tuned during evaluation and demo feedback.

### Dashboard 1 Scoring Table: Single Vessel Incident

Suggested formula:

```text
dashboard_1_score =
  severity_score
  + incident_type_score
  + operational_state_score
  + service_criticality_score
  + evidence_score
  + persistence_score
  + recency_score
  - noise_penalty
```

#### Severity Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Severity | `critical` | 50 | Highest urgency, likely requires immediate action |
| Severity | `high` | 35 | Strong operational risk, but below critical outage |
| Severity | `warning` | 20 | Important, but should not outrank major failures by itself |
| Severity | `info` | 5 | Useful context, low escalation value |

#### Incident Type Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Incident type | `service_down` | 40 | Direct application outage |
| Incident type | `connectivity_loss` | 35 | Loss of observability and possibly service reachability |
| Incident type | `reporting_stale` | 30 | Indicates broken or delayed telemetry/reporting |
| Incident type | `sync_delayed` | 25 | Impacts data freshness and downstream visibility |
| Incident type | `resource_pressure` | 20 | Serious degradation but not always full outage |
| Incident type | `high_latency` | 18 | User-visible degradation, often lower than hard outage |
| Incident type | unknown/misc | 10 | Should count, but below known high-impact patterns |

#### Operational State Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| App state | `down` | 30 | Confirmed service loss |
| App state | `degraded` | 15 | Reduced quality, but still partially functioning |
| App state | `connectivity` | 12 | Visibility or transport issue, moderate impact |
| App state | `healthy` with active alert | 5 | Alert exists, but status does not yet confirm major impact |

#### Service Criticality Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Service criticality | Core ingest/sync/data pipeline app | 20 | Central to platform data flow |
| Service criticality | Operational support app | 12 | Important but not always platform-critical |
| Service criticality | Peripheral/secondary app | 5 | Lower system-wide impact |

#### Evidence Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Evidence | Alert + logs + metrics all support same issue | 20 | Strong confidence that incident is real |
| Evidence | Alert + logs support same issue | 15 | Good confidence without full metric confirmation |
| Evidence | Alert + metrics support same issue | 12 | Good technical correlation |
| Evidence | Alert only | 5 | Weakest acceptable evidence |
| Evidence | Contradictory signals | -10 | Reduces confidence in priority |

#### Persistence Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Duration | Active for more than 15 minutes | 10 | Likely not a brief spike |
| Duration | Active for more than 1 hour | 20 | Established unresolved issue |
| Duration | Active for more than 6 hours | 30 | Long-standing unresolved incident |

#### Recency Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Recency | Started within last 5 minutes | 10 | Fresh issue, useful attention boost |
| Recency | Started within last 30 minutes | 5 | Recent, but should not dominate score |
| Recency | Older than 30 minutes | 0 | No additional recency boost |

#### Noise Penalty

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Noise | Single weak alert with no supporting log or metric | -10 | Likely low-confidence incident |
| Noise | Short-lived resolved spike | -15 | Should not outrank active unresolved incidents |
| Noise | Known noisy alert pattern | -20 | Prevents over-prioritizing repeated false positives |

#### Dashboard 1 Interpretation Examples

| Incident example | Score sketch | Expected priority |
| --- | --- | --- |
| `critical service_down` on a core sync app, app status `down`, supported by logs and metrics, active for 20 minutes | `50 + 40 + 30 + 20 + 20 + 10 + 5 = 175` | Very high |
| `warning resource_pressure` on an important app, supported by metrics only, active for 10 minutes | `20 + 20 + 15 + 12 + 12 + 0 + 5 = 84` | Medium |
| `warning high_latency` with weak support and short duration | `20 + 18 + 5 + 5 + 5 + 0 + 5 - 10 = 43` | Low |

### Dashboard 2 Scoring Table: Multi-Vessel Incident

Suggested formula:

```text
dashboard_2_score =
  severity_score
  + fleet_spread_score
  + app_spread_score
  + correlation_score
  + service_criticality_score
  + persistence_score
  + evidence_score
  + recency_score
  - noise_penalty
```

#### Severity Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Severity | `critical` | 40 | Highest fleet urgency |
| Severity | `high` | 30 | Significant fleet concern |
| Severity | `warning` | 20 | Can still matter if broad or correlated |
| Severity | `info` | 5 | Low priority without spread/correlation |

#### Fleet Spread Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Vessel spread | 2 vessels affected | 20 | Confirms issue is not isolated |
| Vessel spread | 3 vessels affected | 35 | Strong multi-vessel pattern |
| Vessel spread | 4 to 5 vessels affected | 50 | Broad operational risk |
| Vessel spread | More than 5 vessels affected | 60 | Highly systemic fleet-wide issue |

#### App Spread Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| App spread | Same app on multiple vessels | 20 | Indicates shared service weakness |
| App spread | Multiple related apps affected | 25 | Indicates broader service chain issue |
| App spread | Multiple unrelated apps affected | 15 | Broad impact, but weaker causal confidence |

#### Correlation Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Correlation | Same alert type across vessels | 25 | Strong shared symptom |
| Correlation | Same app failing across vessels | 25 | Strong shared component failure |
| Correlation | Same alert type and same app across vessels | 40 | Highest confidence systemic pattern |
| Correlation | Time-window clustering within short interval | 15 | Suggests synchronized issue |

#### Service Criticality Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Service criticality | Shared core fleet service | 20 | Fleet-level operational importance |
| Service criticality | Important but not central service | 10 | Moderate systemic relevance |
| Service criticality | Peripheral service | 5 | Lower fleet consequence |

#### Persistence Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Pattern duration | Correlated pattern active for more than 15 minutes | 10 | Reduces chance of false spike |
| Pattern duration | Correlated pattern active for more than 1 hour | 20 | Persistent fleet issue |
| Pattern duration | Repeated over multiple windows | 30 | Strong evidence of systemic recurrence |

#### Evidence Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Evidence | Alerts + fleet status + cross-vessel correlation agree | 20 | Strong confidence in fleet incident |
| Evidence | Alerts + correlation agree | 15 | Good confidence |
| Evidence | Alerts only | 5 | Weakest acceptable basis |
| Evidence | Contradictory fleet signals | -10 | Reduces confidence in fleet focus |

#### Recency Score

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Recency | Pattern started within last 10 minutes | 10 | Fresh widespread issue |
| Recency | Pattern started within last 60 minutes | 5 | Recent but secondary to severity/scope |
| Recency | Older pattern | 0 | No extra recency bonus |

#### Noise Penalty

| Signal | Condition | Score | Why it matters |
| --- | --- | ---: | --- |
| Noise | Low-spread weak correlation | -10 | Prevents small patterns from dominating |
| Noise | Repeated noisy alert family | -15 | Lowers false-positive families |
| Noise | Correlation exists but low service importance | -10 | Avoids over-prioritizing low-value issues |

#### Dashboard 2 Interpretation Examples

| Incident example | Score sketch | Expected priority |
| --- | --- | --- |
| `critical` same app failing on 4 vessels, same alert type, correlated within short time window, core service | `40 + 50 + 20 + 40 + 20 + 10 + 20 + 5 = 205` | Very high |
| `warning sync_delayed` on 3 vessels, same app family, repeated pattern over 1 hour | `20 + 35 + 20 + 25 + 20 + 20 + 15 + 5 = 160` | High |
| small 2-vessel weak warning pattern with limited evidence | `20 + 20 + 15 + 15 + 5 + 0 + 5 + 5 - 10 = 75` | Medium to low |

### Final Decision Rule

If the system needs a final deterministic rule, it should:

1. calculate the score for each candidate incident
2. select the highest score
3. use tie-breakers in this order:
   - higher severity
   - larger scope
   - stronger evidence/correlation
   - longer persistence
   - more recent timestamp
