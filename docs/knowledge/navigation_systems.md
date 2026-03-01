# Navigation Systems and Environmental Sensor Monitoring

## Scope
Supports events related to water depth, vessel speed, and GPS position. Relevant sensors: `water_depth`, `vessel_speed`, `vessel_latitude`, `vessel_longitude`. Also provides background context on bridge navigation equipment for events originating from ECDIS, AIS, or radar systems.

## Monitored Parameters and Alarm Thresholds

Values from project IAS sensor catalogue (`services/generator/sensors.py`), derived from real ship IAS tag data.

| Sensor | IAS Tag Reference | Normal | Alarm High | Alarm Low |
|---|---|---|---|---|
| Water depth | DBT01 | ~80 m | – | <15 m |
| Vessel speed | (GPS-SOG / speed log) | ~12 kn | >25 kn | – |
| Vessel latitude | (GPS) | ~59 °N | – | – |
| Vessel longitude | (GPS) | ~5.5 °E | – | – |

> `vessel_latitude` and `vessel_longitude` are informational only — no alarm thresholds defined. Approximate position: Norwegian coast / North Sea area.

## Alert Classification (MSC.302(87))

IMO MSC.302(87) defines four alert priority levels applicable to all navigation alarms:

| Priority | Definition |
|---|---|
| **Emergency Alarm** | Immediate danger to human life or to the ship — immediate action required |
| **Alarm** | Requires immediate attention and action by the bridge team |
| **Warning** | Immediate attention for preventive reasons; not immediately hazardous but may become so |
| **Caution** | Awareness of a condition requiring attention outside ordinary considerations |

> Source: IMO MSC.302(87), Performance Standards for Bridge Alert Management, adopted 17 May 2010: [wwwcdn.imo.org – MSC.302(87).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302%2887%29.pdf)

## Water Depth Alarm (<15 m)

A reading below 15 m is a **grounding-risk alarm** for a vessel of this size.

**Causes:**
- Vessel approaching shallow area not on planned route
- Outdated or incorrect electronic chart (ENC not updated)
- ECDIS safety contour incorrectly set
- Echo sounder sensor malfunction

**Immediate actions (SOLAS Ch. V):**
1. Alert officer of watch immediately — this is an **Alarm** (MSC.302(87))
2. Cross-check echo sounder with charted depth at current GPS position
3. Reduce speed
4. Alter course away from shallow area if in doubt
5. Increase radar and visual watch

## Vessel Speed Alarm (>25 kn)

A vessel speed above 25 kn exceeds the defined safety limit for current operating conditions.

**Causes:**
- Strong following sea or current assisting vessel beyond planned speed
- Speed controller or propulsion control fault
- GPS speed-over-ground measurement error

**Actions:**
1. Reduce propulsion power
2. Cross-check GPS speed vs. speed log (speed through water)
3. Apply COLREGS Rule 6 (safe speed) — especially in restricted visibility or traffic separation schemes

## Navigation Equipment Background (SOLAS Ch. V, Regulation 19)

Mandatory equipment on most commercial vessels per SOLAS:

| Equipment | Function |
|---|---|
| ECDIS | Electronic chart display — monitors route, generates safety alarms including anti-grounding |
| GPS / GNSS | Primary position source. Two independent receivers required on GMDSS vessels |
| AIS | Broadcasts own identity and position; receives other vessels. Must be on at all times in coastal areas |
| Radar / ARPA | Detects obstacles; calculates CPA and TCPA for collision avoidance |
| Echo sounder | Measures water depth below keel |
| VDR | Records navigation data for accident investigation — 12–48 h retention |

> Source: SOLAS Ch. V, Regulation 19 – Carriage requirements for shipborne navigational systems (UK Gov. PDF).

## BNWAS – Bridge Watch Alarm Escalation (MSC.128(75))

The Bridge Navigational Watch Alarm System ensures the bridge officer is alert.
Per IMO MSC.128(75) (adopted 20 May 2002):

- **Dormant period**: Officer resets system every 3–12 minutes in response to visual indication.
- **Stage 1**: If not reset → audible alarm on bridge **15 seconds** after visual indication.
- **Stage 2**: If still not reset → remote alarm at backup officer's / Master's cabin **15 seconds** after Stage 1.
- **Stage 3**: If still not reset → remote alarm at further crew locations **90 seconds** after Stage 2 (up to 3 minutes on larger vessels).

BNWAS is relevant context when a navigation alarm (e.g., water depth <15 m) fires with no bridge response.

> Source: IMO MSC.128(75), Performance Standards for a Bridge Navigational Watch Alarm System.
> Direct PDF: [wwwcdn.imo.org/.../MSC.128(75).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.128%2875%29.pdf)

## Cascade Risk
- Water depth <15 m undetected → grounding → hull breach → flooding → stability loss
- GPS failure → ECDIS loses position → route monitoring disabled → grounding risk increases
- AIS failure → loss of traffic picture → higher collision risk if radar watch not increased

## Regulations
- SOLAS Ch. V, Regulation 19: Mandatory carriage of ECDIS, AIS, radar/ARPA, echo sounder, VDR.
- IMO MSC.302(87) (2010): Navigation alarms must be categorised by priority and presented through Central Alert Management.
- COLREGS Rule 6: Safe speed must be maintained at all times.

## Sources
- Project IAS sensor catalogue: `services/generator/sensors.py` (tag references DBT01, vessel_speed)
- IMO MSC.302(87) – Performance Standards for Bridge Alert Management (2010): [imo.org – MSC.302(87).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.302(87).pdf)
- IMO MSC.128(75) – BNWAS Performance Standards (2002): [imo.org – MSC.128(75).pdf](https://wwwcdn.imo.org/localresources/en/KnowledgeCentre/IndexofIMOResolutions/MSCResolutions/MSC.128%2875%29.pdf)
- SOLAS Ch. V – Safety of Navigation (UK Government official PDF): [assets.publishing.service.gov.uk – SOLAS V](https://assets.publishing.service.gov.uk/media/5a7f0081ed915d74e33f3c6e/solas_v_on_safety_of_navigation.pdf)
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015): [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
