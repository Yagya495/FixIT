# Chapter 27 mapping review sheet (PROPOSED, NOT VERIFIED)

> **Nothing on this sheet is verified.** These are FixIt's proposed links between its issue categories and
> Madison General Ordinances Chapter 27. The app keeps showing "section number pending verification" until a
> named person approves a row (see *How to approve*). FixIt is not a lawyer and this is not legal advice.

- **Source:** docs/legal/Madison_Chapter_27.pdf (Municode export, printed 11/14/26 8:55 PM; sha256 7feae63e0b8ddbd6cddf4aa873ba88271636216f7b33e8e959f71aa8e1ff4516)
- **Official page:** https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO
- **Parsed by:** Databricks ai_parse_document -> fixit.bronze.code_sections_parsed (exported to docs/legal/ch27_parsed_sections.json)
- **Numbering:** Subsection ids are read from the inline markers in the parsed official text, e.g. '(2)' then '(h)' under 27.04. Where the ordinance's own history note repeats the id (e.g. '(Sec. 27.04(2)(h) Am. by ...)') that is noted in numbering_evidence.
- **Excerpt check:** every excerpt below was machine-checked to appear word for word in the Databricks parse and in the PDF's own text layer, on the page shown.
- **Kinds:** *direct* = Chapter 27 itself states the requirement. *reference* = Chapter 27 only says to follow
  another law or code, whose text FixIt has not reviewed.

## Summary

| FixIt issue category | Proposed section(s) | Kind | Separate legal source needed? | Status |
|---|---|---|---|---|
| Missing/disabled smoke detector (`SMOKE_DETECTOR_MISSING`) | §27.05(2)(w) | reference | **Yes** | Pending separate legal source |
| Missing CO detector near sleeping area (`CO_DETECTOR_MISSING`) | **none found in Ch. 27** | — | **Yes** | Pending separate legal source |
| Exposed wiring / missing outlet or switch cover (`EXPOSED_WIRING`) | §27.04(2)(g), §27.04(2)(g)3. | direct + reference | No | Under review |
| Water stains / visible mold (`WATER_DAMAGE_MOLD`) | §27.05(2)(g)1., §27.05(2)(g)2. | direct | **Yes** | Under review (mold aspect pending a separate legal source) |
| Droppings / insects / pest damage (`PEST_EVIDENCE`) | §27.07(2)(d), §27.03 | direct, direct (definition) | No | Under review |
| Broken/missing entry or window lock (`BROKEN_LOCK`) | §27.05(2)(h), §27.05(2)(h)3., §27.05(2)(h)4. | direct | No | Under review |
| Broken/cracked window or screen (`BROKEN_WINDOW`) | §27.05(2)(h), §27.04(2)(f), §27.07(2)(c) | direct | No | Under review |
| Active leak / damaged fixtures (`LEAK_PLUMBING`) | §27.05(2)(j) | direct | No | Approved in review; **not verified** (pending live-source check + reviewer name) |
| Holes, peeling paint, damaged flooring (`DAMAGED_SURFACES`) | §27.05(2)(g)1. | general maintenance obligation, direct | No | Approved in review; **not verified** (pending live-source check + reviewer name) |
| Blocked exit / missing handrail (`BLOCKED_EGRESS`) | §27.04(2)(d), §27.05(2)(i) | direct, reference | No | Under review |
| No heat (user-reported / temp evidence) (`NO_HEAT`) | §27.04(2)(h) | direct + reference, direct (exception) | No | Approved in review; **not verified** (pending live-source check + reviewer name) |

## Details

### Missing/disabled smoke detector (`SMOKE_DETECTOR_MISSING`)

> ⚠ **Separate legal-source verification required.** Chapter 27 does not itself establish the full
> requirement for this category.

**§27.05(2)(w)**: reference (Smoke Alarms.)

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 21
- Numbering evidence: Inline markers (2) ... (w) in the parsed text.
- Refers to (not reviewed by FixIt): MGO Sec. 34.907; Wis. Admin. Code ch. SPS 362; Wis. Admin. Code § SPS 321.09; Wis. Admin. Code § SPS 328.02

> Smoke Alarms. Smoke alarms shall be installed and maintained in accordance with Sec. 34.907, MGO and with Wis. Admin. Code ch. SPS 362, Wis. Admin. Code § SPS 321.09 and Wis. Admin. Code § SPS 328.02 which are hereby incorporated by reference.

**Why it matches:** This is the only Chapter 27 provision on smoke alarms. It requires that smoke alarms be installed and maintained, but only 'in accordance with' other codes.

**Uncertainty / missing source:** Chapter 27 does not itself say where alarms go, how many, or what counts as 'maintained'. Those rules are in MGO 34.907 and the SPS codes, which FixIt has not obtained or reviewed. Treating a covered or disabled alarm as 'not maintained' is an interpretation for an inspector.

**Decision so far:** User: keep pending additional legal-source verification (smoke alarms, CO detectors, mold).

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Missing CO detector near sleeping area (`CO_DETECTOR_MISSING`)

> ⚠ **Separate legal-source verification required.** Chapter 27 does not itself establish the full
> requirement for this category.

**Proposed section:** none. Chapter 27 contains no provision for this category.

**Why it matches:** No match. The terms 'carbon', 'monoxide' and 'CO alarm' appear nowhere in Chapter 27 (checked in both the Databricks parse and the PDF text).

**Uncertainty / missing source:** The current placeholder maps this type to CH27-SMOKE, whose summary says CO alarms are required. That is NOT supported by Chapter 27, and 27.05(2)(w) covers smoke alarms only. Possible sources to research (not verified by FixIt): MGO Chapter 34 (Fire Prevention Code), Wisconsin Statutes, Wis. Admin. Code SPS. Recommendation: keep this type unmapped to Chapter 27 and show 'legal source not yet verified'.

**Decision so far:** User: keep pending additional legal-source verification (smoke alarms, CO detectors, mold).

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Exposed wiring / missing outlet or switch cover (`EXPOSED_WIRING`)

**§27.04(2)(g)**: direct + reference (Electrical.)

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 7
- Numbering evidence: Inline markers (2) ... (g); history note '(Sec. 27.04(2)(g) Rescinded & Substituted by Ord. 4832 ...)'.
- Refers to (not reviewed by FixIt): Wisconsin Electric Code; MGO Chapter 19 (Electrical Code), per 27.04(2)(g)7.

> Every dwelling unit and all public and common areas in multiple dwellings shall be supplied with electrical service, outlets, and fixtures which shall be properly installed, shall be maintained in good and safe working condition, and shall be connected to a source of electric power in a manner prescribed by the Wisconsin Electric Code.

**§27.04(2)(g)3.**: direct + reference

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 8
- Numbering evidence: Inline marker '3.' under (g).
- Refers to (not reviewed by FixIt): NEC Article 400-A

> All cords and temporary wiring not in compliance with NEC Article 400-A, and all exposed abandoned wiring shall be removed.

**Why it matches:** 27.04(2)(g) directly requires outlets and fixtures to be properly installed and kept in good and safe working condition; (g)3. directly requires removing exposed abandoned wiring.

**Uncertainty / missing source:** A missing outlet or switch cover plate is not named. Calling it 'not properly installed / not in safe working condition' is an interpretation. 'Exposed abandoned wiring' is narrower than exposed live wiring. Installation details are in the Wisconsin Electric Code / NEC (not reviewed).

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Water stains / visible mold (`WATER_DAMAGE_MOLD`)

> ⚠ **Separate legal-source verification required.** Chapter 27 does not itself establish the full
> requirement for this category.

**§27.05(2)(g)1.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 14
- Numbering evidence: Inline markers '(g) 1.'; 27.07(2)(d) cites 'Sec. 27.05(2)(g)2.' in the same scheme.

> Every interior floor, wall and ceiling including door and window assemblies shall be kept clean and in good repair, and shall be capable of affording privacy.

**§27.05(2)(g)2.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 14
- Numbering evidence: Inline marker '2.' under (g); cited as 'Sec. 27.05(2)(g)2.' in 27.07(2)(d).

> Every foundation, exterior wall, and floor and roof shall be reasonably weathertight, watertight and rodentproof and shall be kept in proper repair and shall be capable of affording privacy.

**Why it matches:** Water stains on walls or ceilings are damage to interior surfaces (good repair) and may indicate the building is not watertight.

**Uncertainty / missing source:** Chapter 27 never mentions mold (0 hits for 'mold' or 'mildew'). It cannot support any statement about mold or its health effects. The placeholder CH27-MOISTURE ('conditions that support mold growth') is not supported by the text. A stain alone does not show an active leak or which surface failed.

**Decision so far:** Under review (water damage). Mold aspect: user keeps pending additional legal-source verification.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Droppings / insects / pest damage (`PEST_EVIDENCE`)

**§27.07(2)(d)**: direct

- Section title: *27.07 - FIXING THE RESPONSIBILITY OF OWNERS, OPERATORS, AND OCCUPANTS.*
- PDF page: 30
- Numbering evidence: Inline markers (2) ... (d) in 27.07.

> Whenever infestation exists in any residential dwelling other than a single-family dwelling, extermination shall be the responsibility of the owner.

**§27.03**: direct (definition) (Infestation.)

- Section title: *27.03 - RULES AND DEFINITIONS.*
- PDF page: 3
- Numbering evidence: Definition within 27.03 (definitions are not numbered).

> "Infestation" means the sustained presence of pests, vermin, or rodents.

**Why it matches:** 27.07(2)(d) places extermination on the owner in any dwelling other than a single-family dwelling; 27.03 defines infestation.

**Uncertainty / missing source:** In a single-family dwelling the occupant is responsible, with exceptions (owner failed to clean before occupancy, or owner out of compliance with 27.05(2)(g)2.). 'Sustained presence' means one photo of droppings may not show an infestation. Building type must be known.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Broken/missing entry or window lock (`BROKEN_LOCK`)

**§27.05(2)(h)**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline markers (2) ... (h); history note '(Sec. 27.05(2)(h) Am. by Ord. 7481 ...)'.

> All door and window hardware shall be installed and maintained in proper working condition.

**§27.05(2)(h)3.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline marker '3.' under (h); 27.05(2)(h)7. refers to 'Paragraphs 1., 2., 3., ... of Subdivision (h) of Subsection (2) of Section 27.05'.

> All doors into each dwelling unit shall have a keyed deadbolt lock with a minimum one (1) inch throw, which is openable with a key on the exterior side of the door and a knob on the interior side of the door.

**§27.05(2)(h)4.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline marker '4.' under (h).

> All basement, first, and second story windows and all other windows accessible by balconies, fire escapes, trees or other existing means shall be provided with sash fasteners.

**Why it matches:** 27.05(2)(h) directly requires working door and window hardware, keyed deadbolts on doors into dwelling units, and sash fasteners on accessible windows.

**Uncertainty / missing source:** Paragraphs 1.-6. apply to rented dwelling units 'Except as provided in Paragraph 9.' (bed and breakfasts). Window rules depend on the story and accessibility. The parse of paragraph 7. (lodging rooms / shared entrances) came back with lines out of order, so it is not quoted; check it on Municode if needed.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Broken/cracked window or screen (`BROKEN_WINDOW`)

**§27.05(2)(h)**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline markers (2) ... (h); history note '(Sec. 27.05(2)(h) Am. by Ord. 7481 ...)'.

> Every window, exterior door, interior door, and basement hatchway shall be reasonably weathertight, watertight, and rodentproof and kept in proper repair.

**§27.04(2)(f)**: direct

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 7
- Numbering evidence: Inline markers (2) ... (f); history note '(Sec. 27.04(2)(f) Am. by Ord. 12,349 ...)'.

> All doors required for ventilation and all windows shall be protected with insect screen equivalent to not less than sixteen (16) wire mesh installed to prevent the entrance of flies, mosquitoes and other insects, annually during May before June 1 and maintained until storm windows are installed in autumn.

**§27.07(2)(c)**: direct

- Section title: *27.07 - FIXING THE RESPONSIBILITY OF OWNERS, OPERATORS, AND OCCUPANTS.*
- PDF page: 30
- Numbering evidence: Inline markers (2) ... (c) in 27.07.

> Every owner of a residential building shall be responsible for hanging, installation, and maintenance of all screens and double or storm doors and windows whenever the same are required under the provisions of the Madison General Ordinances.

**Why it matches:** Windows must be kept in proper repair and weathertight; screens are required seasonally, and the owner is responsible for screens.

**Uncertainty / missing source:** 'Cracked glass' is not named explicitly; it falls under 'proper repair' / 'weathertight' by interpretation. The screen requirement is seasonal (by June 1 until storm windows go in), so a missing screen in winter may not be a violation.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Active leak / damaged fixtures (`LEAK_PLUMBING`)

**§27.05(2)(j)**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 17
- Numbering evidence: Inline markers (2) ... (j).

> Every plumbing fixture and water and waste pipe shall be properly installed and maintained in good working condition, free from defects, leaks, and obstructions.

**Why it matches:** Directly requires plumbing fixtures and pipes to be free from leaks and in good working condition.

**Uncertainty / missing source:** Low. Whether a given drip is a 'leak' is still an inspector's call; FixIt cannot see inside walls.

**Decision so far:** User approved 27.05(2)(j) as the primary mapping (2026-11-14). 27.04(2)(a) not added. Applies only to plumbing fixtures and water/waste pipes, not roof leaks or unexplained water stains. Pending: final check against the current official ordinance (Municode) and a reviewer name.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Holes, peeling paint, damaged flooring (`DAMAGED_SURFACES`)

**§27.05(2)(g)1.**: general maintenance obligation

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 14
- Numbering evidence: Inline markers '(g) 1.'.

> Every interior floor, wall and ceiling including door and window assemblies shall be kept clean and in good repair, and shall be capable of affording privacy.

**§27.05(2)(g)1.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 14
- Numbering evidence: Inline markers '(g) 1.'.

> All surfaces shall be free from serious cracking, irregularities, and peeling paint.

**Why it matches:** Directly addresses cracking and peeling paint; the same paragraph requires interior floors, walls and ceilings to be in good repair.

**Uncertainty / missing source:** 'Serious' cracking is a judgment call. Nothing here addresses lead paint; do not imply a lead hazard from this section.

**Decision so far:** User approved 27.05(2)(g)1. for interior surfaces (2026-11-14). Keep 'serious cracking' / 'peeling paint' (direct) distinct from general 'good repair'. Damaged stairs removed from this category (stair safety handled separately under 27.05(2)(i)). Lead paint labeled general safety information, not a Chapter 27 requirement. Pending: final check against the current official ordinance (Municode) and a reviewer name.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Blocked exit / missing handrail (`BLOCKED_EGRESS`)

**§27.04(2)(d)**: direct

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 6 (continues onto the next page)
- Numbering evidence: Inline markers (2) ... (d).
- Refers to (not reviewed by FixIt): MGO Sec. 27.06(4) (exception, not reviewed)

> Every dwelling unit and lodging room shall have direct access to at least two (2) accessible unobstructed means of egress leading to a safe and open public street, alley, or court connected to a street, except as provided in Sec. 27.06(4), MGO.

**§27.04(2)(d)**: reference

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 6
- Numbering evidence: Same paragraph (d).
- Refers to (not reviewed by FixIt): Wis. Admin. Code § SPS 321.04(2); Wis. Admin. Code ch. SPS 362

> All stairways and platforms shall be protected with handrails and guardrails as specified in Wis. Admin. Code § SPS 321.04(2) or ch. SPS 362.

**§27.05(2)(i)**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 17
- Numbering evidence: Inline markers (2) ... (i).
- Refers to (not reviewed by FixIt): Wis. Admin. Code § SPS 321.04 and ch. SPS 362 (stair requirements, same paragraph)

> Every inside and outside stair, every porch, platform, balcony, and every appurtenance thereto shall be so constructed as to be safe to use and capable of supporting the load that normal use may cause to be placed thereon, and shall be kept in proper condition and repair and shall present an attractive appearance.

**Why it matches:** Two unobstructed means of egress are required directly; stairs must be safe and in repair; handrail and guardrail specifics come from the SPS codes.

**Uncertainty / missing source:** The handrail sentence sits in a passage about exterior stairways and exit platforms, and the actual handrail specs are in SPS (not reviewed). Whether furniture temporarily blocking a door makes an exit 'obstructed' is an inspector's call. Exception 27.06(4) not reviewed.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### No heat (user-reported / temp evidence) (`NO_HEAT`)

**§27.04(2)(h)**: direct + reference (Heating.)

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 9
- Numbering evidence: Inline markers (2) ... (h); history note '(Sec. 27.04(2)(h) Am. by Ord. 9326 ...)'.
- Refers to (not reviewed by FixIt): MGO Chapter 30 (Heating, Ventilating and Air Conditioning Code); Sec. 30.03(1) and 30.04(4)(d) for the heating system itself

> A minimum temperature of sixty-seven degrees Fahrenheit (67°) shall be maintained in all habitable rooms, kitchens and bathrooms.

**§27.04(2)(h)**: direct (exception)

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 9
- Numbering evidence: Same paragraph (h).

> The occupant of a room or an apartment may maintain a lesser temperature than is specified above as long as it does not affect the temperature in other habitable areas of the building.

**Considered, NOT mapped: §27.05(2)(m)** (p. 18). User decision: concerns removing/shutting off/discontinuing a required service, not every heating failure. Not added automatically.

> No owner, operator or occupant shall cause any service, facility, equipment, or utility which is required under this ordinance to be removed from or shut off from or discontinued for any occupied dwelling, dwelling unit or lodging room let or occupied by them except for such temporary interruption as may be necessary while actual repairs are in process, or during temporary emergencies when discontinuance of service is approved by an authorized inspector.

**Why it matches:** 27.04(2)(h) directly sets the 67°F minimum in habitable rooms, kitchens and bathrooms; 27.05(2)(m) prohibits shutting off required services except for repairs or approved emergencies.

**Uncertainty / missing source:** The occupant may keep a lower temperature if it doesn't affect other units. Chapter 27 sets no repair response time: FixIt's 24h/48h/7-day follow-up windows are FixIt defaults, not from this ordinance. The history note says 'Ord. 9326, 11-13-76' here but '11-13-87' elsewhere (an inconsistency in the source, quoted as-is).

**Decision so far:** User approved 27.04(2)(h) as the primary mapping (2026-11-14), including the 67°F minimum, the rooms covered (habitable rooms, kitchens and bathrooms) and the occupant exception. 27.05(2)(m) not added. Remove the unsupported 'heating season' limit; FixIt follow-up deadlines are not legal requirements. Pending: final check against the current official ordinance (Municode) and a reviewer name.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

## Problems found in the current placeholder summaries

These FixIt summaries are shown in the deployed app today, labeled "plain-language summary, not official text".
Corrected on git branch `ch27-review` (not deployed yet):

- **CH27-SMOKE** says carbon monoxide alarms are required. Chapter 27 does not mention carbon monoxide.
- **CH27-MOISTURE** mentions "conditions that support mold growth". Chapter 27 does not mention mold.
- **CH27-ELECTRICAL** says outlets must be "covered". Chapter 27 does not mention cover plates.
- **CH27-WINDOWS** says windows must be "glazed without cracks or holes". Chapter 27 says "proper repair" and
  "weathertight"; screens are required seasonally.
- **CH27-HEAT** gives no temperature. Chapter 27 sets 67°F in habitable rooms, kitchens and bathrooms.

## Parse defects (do not quote these passages from the parse)

- §27.05(2)(h)7. (lodging rooms / shared entrances): lines came back out of order.
- §27.05(2)(x) (storm sewers): the forfeiture sentence lost words ("not twenty-five dollars").

## How to approve

1. Read each excerpt against the official text on Municode (link above).
2. In `eval/code_review.csv`, fill `approved_section_ids` (e.g. `27.04(2)(h)`) and `reviewer` for rows you approve.
   Leave a row blank to keep the placeholder. Leave `CO_DETECTOR_MISSING` blank unless a separate source is verified.
3. Run `python scripts/code_parse.py approve --profile fixit --warehouse <id>` (dry run) and check the plan.
   Only then run it with `--apply`. Until then nothing in the app changes.
