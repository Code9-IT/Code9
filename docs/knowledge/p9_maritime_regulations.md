# Point 9 – Maritime Regulations and Standards

## Scope

This reference provides regulatory and standards context for alarm and event handling, incident classification, and reporting in a maritime monitoring system. Intended for RAG retrieval when the AI agent needs to explain the regulatory basis for an alert, compliance requirement, or reporting obligation.

This is a project-oriented reference (MVP to pre-production), not a full class-approved compliance manual. Company-specific escalation contacts, class approval scope, and full legal reporting workflows must come from operator SMS and company reporting instructions.

---

## Key Regulations and Standards

### IMO Alert and Alarm Management

| Regulation | Full Title | Key Content |
|---|---|---|
| **MSC.302(87)** | Performance Standards for Bridge Alert Management (BAM), 2010 | Harmonized bridge alert handling; four alert priorities; operator response philosophy; alert state lifecycle |
| **A.1021(26)** | Code on Alerts and Indicators | Common framework for alert and indicator behavior and classification across all ship systems |
| **MSC.128(75)** | Performance Standards for BNWAS | Bridge Navigational Watch Alarm System: staged alert escalation from bridge → Master's cabin → additional crew |

### IMO Safety Management

| Regulation | Full Title | Key Content |
|---|---|---|
| **A.741(18)** | International Safety Management (ISM) Code | Safety management system, responsibilities, reporting, and continual improvement |
| **A.1188(33)** | Guidelines on Implementation of ISM Code by Administrations | Practical implementation and verification expectations for flag states and companies |
| **A.916(22)** | Recommendations on Recording of Events Related to Navigation | Navigation event recording requirements and recommended log content |
| **MSC.255(84)** | Casualty Investigation Code | Structured safety investigation; causal analysis; report content requirements |
| **MSC-MEPC.3/Circ.4/Rev.1** | Revised Harmonized Reporting Procedures | Reports required under SOLAS Regulation I/21; standardized format for reporting casualties and incidents |

### Class Society and Industry Standards

| Standard | Topic | Key Content |
|---|---|---|
| **IACS UR E22** | Computer-Based Ship Systems | Integrity, lifecycle management, testing, and robustness requirements for software-intensive ship systems |
| **IACS UR Z27** | Condition Monitoring / CBM | Condition-based maintenance expectations and use of operational data for predictive maintenance |
| **DNV Rules (Explorer)** | Classification Rules | Rule browsing for DNV-classed vessels: machinery, electrical, automation |
| **Lloyd's Register Rules** | Classification Rules | LR rules and regulations for classification of ships |

---

## Alert Priority Classification (MSC.302(87) and A.1021(26))

All alerts must be classified and presented according to four priority levels:

| Priority | Definition | Project Example |
|---|---|---|
| **Emergency Alarm** | Immediate danger to life or ship | Total blackout; flooding |
| **Alarm** | Requires immediate operator attention and action | DG trip; EMDG failure; LO flow critical |
| **Warning** | Immediate attention for precautionary reasons; not immediately hazardous | High engine load; cooling temp rising |
| **Caution** | Awareness required; outside ordinary monitoring | Approaching fuel tank low level |

**Alert states lifecycle** (MSC.302(87)):
1. `active` — condition exists and has not been acknowledged
2. `acknowledged` — operator has confirmed awareness; condition still active
3. `cleared` — condition no longer present; alarm resolved
4. (optional) `closed` — operator has confirmed resolution and closed the record

**Implementation requirement**: there must be an alarm or indication at the normal navigation position when main electrical power is interrupted (referenced in COMSAR.1/Circ.32/Rev.3 per SOLAS II-1).

---

## ISM Code Requirements (A.741(18))

The ISM Code requires every shipping company and vessel to have a Safety Management System (SMS) that includes:
- Safety and environmental protection policies
- Instructions and procedures ensuring safe operation and environmental protection
- Defined levels of authority and communication lines
- Procedures for reporting accidents and non-conformities
- Procedures for responding to emergencies
- Procedures for internal audits and management reviews

For monitoring systems: **every alarm event that is safety-relevant should be traceable** — who acknowledged it, what action was taken, when it was resolved. This supports ISM audit trails and continual improvement.

> Source: IMO A.741(18) ISM Code: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.741(18).pdf

---

## IACS UR E22: Computer-Based Systems

IACS UR E22 defines requirements for computer-based ship systems (software-intensive systems used for monitoring, control, or alarm handling):
- **Integrity**: systems must be designed to fail safely; loss of a computer-based system must not result in a more dangerous state than before
- **Lifecycle management**: software changes must follow controlled procedures
- **Testing**: systems must be type-tested and verified
- **Robustness**: systems must handle sensor failures, communication faults, and incorrect inputs without catastrophic failure

This is relevant for the monitoring agent, RAG system, and any automated alarm logic implemented in this project.

> Source: IACS UR E22 page: https://iacs.org.uk/resolutions/unified-requirements/ur-e/ur-e22-rev2-cln-2

---

## IACS UR Z27: Condition-Based Maintenance

IACS UR Z27 covers the use of operational data for condition monitoring and predictive maintenance (CBM):
- Operational data may be used to supplement or replace fixed-interval maintenance
- CBM systems should be validated; their recommendations should be traceable
- Data gaps or sensor failures reduce CBM confidence and must be flagged

This is relevant when the monitoring system uses sensor trends (e.g., rising TC speed, declining CW flow) to predict future maintenance needs.

> Source: IACS UR Z27 page: https://iacs.org.uk/resolutions/unified-requirements/ur-z/ur-z27-new

---

## Compliance-Sensitive Alarm Events

Certain alarm conditions in this project trigger specific regulatory obligations:

| Event | Regulation | Obligation |
|---|---|---|
| Scrubber SO₂ >400 ppm | MARPOL Annex VI Reg. 14 | May indicate fuel sulphur non-compliance if scrubber is not functioning |
| Scrubber pH <6.0 | MEPC.259(68) | Wash water discharge standard: pH must be ≥6.5 at 4 m from discharge |
| Fuel sulphur ≥0.10% in SECA | MARPOL Annex VI Reg. 14 | Violation if vessel is in an Emission Control Area (ECA) |
| Water depth <15 m | SOLAS Ch. V, Reg. 19 | Grounding-risk alarm; SOLAS requires immediate bridge action |
| EMDG not starting | SOLAS Ch. II-1, Reg. 42/43 | Emergency generator must start and carry load within 45 seconds |
| Navigation alarm with no bridge response | MSC.128(75) | BNWAS escalation must be functioning: 15s → +15s → +90s |

---

## Recommended Alarm Event Logging Schema

For ISM-aligned, audit-ready event logging, each alarm event record should include:

```
event_id          (unique identifier)
vessel_id
source_system     (sensor / IAS / RAG / manual)
sensor_name       (IAS tag)
measured_value
threshold_value
unit
severity          (critical / warning / info)
state             (active / acknowledged / cleared)
created_at_utc
updated_at_utc
acknowledged_by
acknowledged_at_utc
suspected_cause
recommended_actions
actual_actions
data_quality_flag (good / uncertain / stale / bad)
```

---

## Scope Limitation

This reference gives a compliant structure and minimum content expectations. It does **not** define:
- company-specific escalation contacts
- class approval scope for this specific system
- full legal reporting workflow for a specific flag state

Those details must come from operator SMS procedures, class documentation, and company reporting instructions.

---

## Sources

- IMO MSC.302(87) Bridge Alert Management: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf
- IMO A.1021(26) Code on Alerts and Indicators: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.1021(26).pdf
- IMO MSC.128(75) BNWAS: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.128%2875%29.pdf
- IMO A.741(18) ISM Code: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.741(18).pdf
- IMO A.1188(33) ISM Implementation Guidelines: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.1188(33).pdf
- IACS UR E22 Computer-Based Systems: https://iacs.org.uk/resolutions/unified-requirements/ur-e/ur-e22-rev2-cln-2
- IACS UR Z27 Condition Monitoring: https://iacs.org.uk/resolutions/unified-requirements/ur-z/ur-z27-new
- IMO A.916(22) Recording of Navigation Events: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/AssemblyDocuments/A.916(22).pdf
- IMO MSC.255(84) Casualty Investigation Code: https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.255(84).pdf
- IMO MSC-MEPC.3/Circ.4/Rev.1 Harmonized Reporting: https://wwwcdn.imo.org/localresources/en/OurWork/MSAS/Documents/MSC-MEPC3/MSC-MEPC.3-Circ.4%20Rev%201%20%20Revised%20harmonized%20reporting%20procedures%20-%20Reports%20required%20under%20SOLAS%20regulations%20I21.pdf
- DNV Rules and Standards Explorer: https://standards.dnv.com/explorer
- Lloyd's Register Rules for Classification of Ships: https://www.lr.org/en/knowledge/lloyds-register-rules/rules-and-regulations-for-the-classification-of-ships/
- MARPOL Annex VI Regulation 14 (sulphur limits): https://www.imo.org/en/ourwork/environment/pages/sulphur-oxides-%28sox%29-%E2%80%93-regulation-14.aspx
- IMO MEPC.259(68) Exhaust Gas Cleaning System Guidelines: https://wwwcdn.imo.org/localresources/en/OurWork/Environment/Documents/Air%20pollution/MEPC.259(68).pdf
- IMO COMSAR.1/Circ.32/Rev.3 (Emergency source of power): https://wwwcdn.imo.org/localresources/en/OurWork/Safety/Documents/IMO%20Documents%20related%20to/COMSAR.1-Circ.32-Rev.3.pdf
