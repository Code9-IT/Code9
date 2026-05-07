# Point 8 – Data Quality and Data Lineage in a Maritime Context

## Scope

This reference defines data quality and data lineage (traceability/provenance) as they apply in maritime monitoring. It explains how to assess data reliability and what the common causes of poor data quality are. Intended for RAG retrieval when the AI agent needs to evaluate whether a data source is trustworthy or explain why a value may be unreliable.

> **Note on scope**: The primary source material for this topic (IHO S-44 and S-58) focuses on maritime hydrographic, charting, and bathymetric data. The principles are applicable more broadly to vessel telemetry and operational data, but they should not be treated as a complete standard for all IAS sensor data.

---

## What Data Quality Means in a Maritime Context

Data quality describes **how suitable data is for safe and reliable use**. A practical quality model includes four core dimensions:

| Dimension | Definition |
|---|---|
| **Completeness** | Whether the required data is present and covers what it should cover (no gaps in coverage, fields, or observations) |
| **Currency** | Whether the data is up to date enough for its intended use |
| **Uncertainty** | How precise or imprecise the data is; whether measurement confidence is known and acceptable |
| **Source** | Where the data came from and whether the source is known and trustworthy |

For maritime monitoring and navigation, quality is not only about whether a value exists — it is also about whether the data is **recent enough**, **complete enough**, and **reliable enough** for the decision being made.

> Source: IHO S-44 Standards for Hydrographic Surveys, Edition 6.1.0: https://iho.int/uploads/user/pubs/standards/s-44/S-44_Edition_6.1.0.pdf

---

## What Data Lineage (Traceability) Means

**Data lineage** — also called provenance or traceability — is the ability to identify:
- what data was created or used
- what activity produced or changed it
- who created, collected, or approved it

A simple lineage model (from W3C PROV Data Model):

| Component | Role |
|---|---|
| **Entity** | The data or dataset itself |
| **Activity** | The action that created, modified, or assessed the data |
| **Agent** | The person, organization, or authority responsible |

Good lineage **improves trust** because it answers: Where did this come from? When was it collected? Who was responsible? What processes transformed it?

> Source: W3C PROV Data Model (PROV-DM): https://www.w3.org/TR/prov-dm/

---

## Practical Maritime Traceability Metadata

For maritime survey or chart data, traceability can be supported with structured metadata:

| Metadata Field | Description |
|---|---|
| Source of data | Where the data originated |
| Survey authority | The authority responsible for data collection |
| Survey date range | When data was collected |
| Data assessment | Quality review outcome |
| Quality of Survey | Overall quality classification |
| Horizontal position uncertainty | Confidence in XY position accuracy |
| Vertical uncertainty | Confidence in depth/elevation accuracy |

These fields make it possible to trace origin, timing, responsibility, and measurement confidence in a structured way.

> Source: IHO S-101 Data Classification and Encoding Guide v1.0.2: https://iho.int/uploads/user/Services%20and%20Standards/S-100WG/S-101PT7/S-101PT7_2021_06.1A_EN_S101_Data%20Classification%20and%20Encoding%20Guide_1.0.2_Clean_V1.pdf

---

## For This Project: IAS Sensor Data Lineage

For the vessel telemetry data in this system, the key lineage facts are:

| Field | Value |
|---|---|
| **Source** | IAS (Integrated Automation System) tags on a real ship |
| **Agent** | Anonymised real ship operator (dataset origin); project technical advisor (project context) |
| **Activity** | Anonymised export of 128 IAS tags → `services/generator/sensors.py` |
| **Entity** | 73 synthetic sensors driven by real IAS thresholds and tag references |
| **Currency** | Synthetic data generated in real-time by the simulator; IAS thresholds are from a real vessel |
| **Uncertainty** | Synthetic data adds Gaussian noise; thresholds are from real ship (high confidence) |

**Reference note**: the project IAS sensor catalogue is derived from anonymised real ship telemetry data.
**For RAG use**: trust `sensors.py` values as the system's actual thresholds — they reflect a real ship's alarm setpoints.

---

## How Data Reliability Is Assessed

Data reliability depends on both the quality of the data and the quality of the process that produced it. Key indicators:

- whether the data is **complete** (no gaps)
- whether it is **current** enough for the intended use
- whether **uncertainty** is known and acceptable
- whether the **source** is identified and trustworthy
- whether the collection or production method was **reliable**
- whether the data has passed **validation and quality control**

Two levels of quality control:

| QC Type | Description |
|---|---|
| **A priori quality control** | Expected quality based on planned method, equipment, and process (before collection) |
| **A posteriori quality control** | Assessed quality based on actual results after collection and processing |

A reliable dataset has both documented measurement confidence and evidence it was checked after collection.

> Source: IHO S-44 Standards for Hydrographic Surveys: https://iho.int/uploads/user/pubs/standards/s-44/S-44_Edition_6.1.0.pdf

---

## Typical Causes of Poor Data Quality

| Cause | Description |
|---|---|
| **Incomplete data** | Missing coverage, missing fields, or missing observations |
| **Outdated data** | Information is too old for the intended use (stale data) |
| **High uncertainty** | Measurement precision is too weak or insufficiently documented |
| **Unknown or weak source** | Origin is unclear, undocumented, or not trustworthy |
| **Poor validation** | Data was not properly checked before use |
| **Encoding errors** | Data is stored or structured incorrectly |
| **Logical inconsistencies** | Different parts of the dataset conflict with each other |
| **Weak quality control** | Collection or processing was not adequately reviewed |

For RAG purposes, these are the core reasons why maritime data becomes unreliable or unsuitable for decision-making.

---

## Simple Rule for Trusting Maritime/IAS Data

Data is **more trustworthy** when:
- the source is known
- the collection period is known
- the responsible authority or system is identified
- uncertainty is documented
- quality has been assessed
- validation has been performed

Data is **less trustworthy** when any of these are missing, unclear, or inconsistent.

**Applied to this project**:
- `sensors.py` → high trust (real IAS data, known source, consistent with OEM ranges)
- Synthetic time-series values → medium trust (real thresholds, but noise-added)
- External regulatory references → high trust when cited with resolution number and direct IMO/class URL

---

## Optional: Practical Validation Layer

For structured data (like the IAS sensor catalogue), a validation layer should check that:
- data follows the required specification (correct units, correct field names)
- data is encoded correctly (numeric ranges, no null where required)
- data is logically consistent (alarm high > alarm low; normal value within valid range)
- obvious structural or rule-based errors are detected before use

Validation does not replace source trust or uncertainty assessment, but it catches technical defects that reduce reliability.

---

## Scope Limitation

This reference provides a compact framework for:
- defining data quality (completeness, currency, uncertainty, source)
- defining data lineage / traceability (entity, activity, agent)
- assessing data reliability
- identifying common causes of poor data quality

It does **not** define:
- internal "single source of truth" rules for this project
- data ownership or governance policies
- internal transformation pipelines
- tag-level validation logic
- system-specific acceptance thresholds

Those must be added from internal data governance documents.

---

## Sources

- IHO S-44 Standards for Hydrographic Surveys, Edition 6.1.0: https://iho.int/uploads/user/pubs/standards/s-44/S-44_Edition_6.1.0.pdf
- IHO S-58 Recommended ENC Validation Checks, Edition 6.1.0: https://iho.int/iho_pubs/standard/S-58/S-58_Edition_6.1.0_Sept18.pdf
- W3C PROV Data Model (PROV-DM): https://www.w3.org/TR/prov-dm/
- IHO S-101 Data Classification and Encoding Guide v1.0.2: https://iho.int/uploads/user/Services%20and%20Standards/S-100WG/S-101PT7/S-101PT7_2021_06.1A_EN_S101_Data%20Classification%20and%20Encoding%20Guide_1.0.2_Clean_V1.pdf
- Project IAS sensor catalogue: `services/generator/sensors.py`
