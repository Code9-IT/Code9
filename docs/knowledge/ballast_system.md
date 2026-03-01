# Ballast and Cargo Water System – Background Knowledge

## Scope
Background context for ballast-related events. **Note: no ballast tank level or pump sensors are present in the current sensor catalogue.** This file provides regulatory and operational context that Ollama can use if ballast-related events are reported from external sources or future sensor additions.

## System Role
The ballast system manages seawater taken onboard or discharged to maintain ship stability, trim, and structural integrity:

- **Ballast tanks**: Located in double bottom, fore peak, aft peak, and wing tanks.
- **Ballast pumps**: High-capacity pumps that fill or empty tanks (typically 2–3 pumps onboard).
- **Ballast Water Treatment System (BWTS)**: Required by IMO BWM Convention — treats ballast water to prevent transfer of invasive species between ports.
- **Tank gauging system**: Measures level in each ballast tank (ultrasonic or pressure-based sensors).

> Source: Wärtsilä Encyclopedia of Ship Technology, 2nd ed. — ballast systems.

## Key Operational Parameters (General Maritime Reference)

| Parameter | Typical Normal | Warning | Critical |
|---|---|---|---|
| Tank level | Voyage-dependent plan | Unexpected deviation | Overflow or unexpected empty |
| Trim (fore–aft difference) | Per loading plan | >1 m from plan | >2 m |
| Heel (port–starboard list) | <1° | >2° | >5° (stability concern) |
| Ballast pump motor current | Within rated amps | >rated amps (overload) | Trip point |
| BWTS UV intensity (if UV type) | Above minimum lux | Degraded | Below treatment threshold |

> Note: These are general maritime reference values from Wärtsilä Encyclopedia. No ballast sensors are active in the current project IAS catalogue.

## Regulatory Requirements

**IMO Ballast Water Management Convention (BWM Convention, 2004, in force 8 September 2017):**
- All ships must treat ballast water to the **D-2 Performance Standard** before discharge:
  - < 10 viable organisms per m³ ≥ 50 µm minimum dimension
  - < 10 viable organisms per mL between 10 and 50 µm
  - Toxicogenic Vibrio cholerae: < 1 CFU per 100 mL
  - E. coli: < 250 CFU per 100 mL
  - Intestinal Enterococci: < 100 CFU per 100 mL
- Ballast Water Record Book must be maintained and available for port state control inspection.

> Source: IMO Ballast Water Management Convention (2004), Regulation D-2: [imo.org – BWM Convention page](https://www.imo.org/en/about/conventions/pages/international-convention-for-the-control-and-management-of-ships'-ballast-water-and-sediments-(bwm).aspx)

## Common Causes of Ballast Alarms (Context)

**Unexpected tank level change:**
- Valve stuck open or closed
- Uncontrolled water ingress from adjacent compartment

**Pump overload:**
- Discharge valve partially closed → high back-pressure
- Pump running against a closed valve (immediate mechanical damage risk)
- Sea chest blocked by debris or marine growth

**BWTS fault:**
- Filter blockage before treatment unit
- UV lamp failure — intensity drops below treatment threshold
- Electrochlorination unit failure
- Flow rate outside treatment range

**Trim or heel outside limits:**
- Ballast operation not matching stability plan
- Undetected water ingress to a tank or hold

## Cascade Risk
- Undetected flooding of ballast tank or adjacent space → progressive list → severe stability loss
- BWTS failure undetected → IMO BWM Convention violation at port inspection → vessel detained

## Regulations
- IMO BWM Convention (2004, in force 2017): D-2 standard applies to all vessels. Port state control inspects BWTS records and function during port calls.
- Class rules: Tank level monitoring and automatic high-level alarms required on all ballast tanks.

## Sources
- IMO Ballast Water Management Convention (2004) – D-2 standard and overview: [imo.org – BWM Convention page](https://www.imo.org/en/about/conventions/pages/international-convention-for-the-control-and-management-of-ships'-ballast-water-and-sediments-(bwm).aspx)
- Wärtsilä Encyclopedia of Ship Technology, 2nd ed. (Jan Babicz, 2015): [wartsila.com – encyclopedia PDF](https://www.wartsila.com/docs/default-source/marine-documents/encyclopedia/wartsila-o-marine-encyclopedia.pdf)
