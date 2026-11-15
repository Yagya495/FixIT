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
- **Evidence levels:** *ordinance text (independently confirmed)* = read on the live official Municode page;
  *City guidance* = City of Madison web pages (helpful, not ordinance text); *interpretation* = FixIt's or the
  reviewer's reading of how a provision applies. Live check details: `docs/legal/ch27_live_check.md`.

## Summary

| FixIt issue category | Proposed section(s) | Kind | Separate legal source needed? | Status |
|---|---|---|---|---|
| Missing/disabled smoke detector (`SMOKE_DETECTOR_MISSING`) | §27.05(2)(w) | reference | **Yes** | Pending separate legal source |
| Missing CO detector near sleeping area (`CO_DETECTOR_MISSING`) | **none found in Ch. 27** | — | **Yes** | Pending separate legal source |
| Exposed wiring / missing outlet or switch cover (`EXPOSED_WIRING`) | §27.04(2)(g) | general safety and maintenance obligation (+ reference to the Wisconsin Electric Code) | No | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) |
| Water damage / suspected mold (`WATER_DAMAGE_MOLD`) | §27.05(2)(g)1., §27.05(2)(g)2. | general maintenance obligation (potentially relevant) | **Yes** | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) (mold aspect pending a separate legal source) |
| Droppings / insects / pest damage (`PEST_EVIDENCE`) | §27.07(2)(d), §27.03 | direct (single-family dwellings, with exceptions), direct (dwellings other than single-family), direct (definition) | No | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) |
| Broken/missing entry or window lock (`BROKEN_LOCK`) | §27.05(2)(h), §27.05(2)(h)3., §27.05(2)(h)4., §27.05(2)(h)6. | direct, condition (applies to rented units; Paragraph 9. = bed and breakfasts), exception (approved alternatives) | No | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) |
| Broken/cracked window or screen (`BROKEN_WINDOW`) | §27.05(2)(h), §27.04(2)(f), §27.07(2)(c) | general maintenance obligation, direct (seasonal: screens by June 1 until storm windows go in), direct (seasonal: storm windows Oct 15 - Nov 15), direct (owner responsibility for screens and storm windows) | No | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) |
| Active leak / damaged fixtures (`LEAK_PLUMBING`) | §27.05(2)(j) | direct | No | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) |
| Holes, peeling paint, damaged flooring (`DAMAGED_SURFACES`) | §27.05(2)(g)1. | general maintenance obligation, direct | No | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) |
| Blocked exit / unsafe stairs / missing handrail (`BLOCKED_EGRESS`) | §27.04(2)(d), §27.05(2)(i) | direct, reference | No | **On hold** (27.06(4) cross-reference + SPS requirements) |
| No heat (user-reported / temp evidence) (`NO_HEAT`) | §27.04(2)(h) | direct + reference, direct (exception) | No | Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name) |

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

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '43. 34.907 a. Smoke alarms not installed where required in: i. Inside every bedroom and sleeping area ii. Within 6 feet of each door leading to a bedroom or sleeping area … iii. Each floor of the building'. MGO 34.907's own text is still unread.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Hardwired or tamperproof; every bedroom or sleeping area, within six feet of bedroom entry doors, each floor incl. basements.

**Decision so far:** User: keep pending additional legal-source verification (smoke alarms, CO detectors, mold).

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Missing CO detector near sleeping area (`CO_DETECTOR_MISSING`)

> ⚠ **Separate legal-source verification required.** Chapter 27 does not itself establish the full
> requirement for this category.

**Proposed section:** none. Chapter 27 contains no provision for this category.

**Why it matches:** No match. The terms 'carbon', 'monoxide' and 'CO alarm' appear nowhere in Chapter 27 (checked in both the Databricks parse and the PDF text).

**Uncertainty / missing source:** The current placeholder maps this type to CH27-SMOKE, whose summary says CO alarms are required. That is NOT supported by Chapter 27, and 27.05(2)(w) covers smoke alarms only. Possible sources to research (not verified by FixIt): MGO Chapter 34 (Fire Prevention Code), Wisconsin Statutes, Wis. Admin. Code SPS. Recommendation: keep this type unmapped to Chapter 27 and show 'legal source not yet verified'.

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '41. 29.19 a. Carbon Monoxide Detectors not Installed Where Required' (basement; each floor level; outside each separate sleeping area; sleeping rooms with a fuel-burning appliance). So Madison has a CO ordinance, MGO 29.19, outside Chapter 27. Its text is still unread.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). 1-2 unit dwellings: every floor; 3+ units: within 15 feet of bedroom doors in units with fuel-burning appliances.

**Decision so far:** User: keep pending additional legal-source verification (smoke alarms, CO detectors, mold).

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Exposed wiring / missing outlet or switch cover (`EXPOSED_WIRING`)

**§27.04(2)(g)**: general safety and maintenance obligation (+ reference to the Wisconsin Electric Code) (Electrical.)

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 7
- Numbering evidence: Inline markers (2) ... (g); history note '(Sec. 27.04(2)(g) Rescinded & Substituted by Ord. 4832 ...)'.
- Refers to (not reviewed by FixIt): Wisconsin Electric Code; MGO Chapter 19 (Electrical Code), per 27.04(2)(g)7.

> Every dwelling unit and all public and common areas in multiple dwellings shall be supplied with electrical service, outlets, and fixtures which shall be properly installed, shall be maintained in good and safe working condition, and shall be connected to a source of electric power in a manner prescribed by the Wisconsin Electric Code.

**Considered, NOT mapped: §27.04(2)(g)3.** (p. 8). User decision: 'exposed abandoned wiring' is narrower than a missing outlet cover or active exposed wiring; not mapped automatically.

> All cords and temporary wiring not in compliance with NEC Article 400-A, and all exposed abandoned wiring shall be removed.

**Why it matches:** 27.04(2)(g) directly requires outlets and fixtures to be properly installed and kept in good and safe working condition; (g)3. directly requires removing exposed abandoned wiring.

**Uncertainty / missing source:** A missing outlet or switch cover plate is not named. Calling it 'not properly installed / not in safe working condition' is an interpretation. 'Exposed abandoned wiring' is narrower than exposed live wiring. Installation details are in the Wisconsin Electric Code / NEC (not reviewed).

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '7. 27.04(2)(g) … a. Electrical service and wiring … vi. Exposed wires, damaged or bare, presenting shock hazard' files exposed wires under 27.04(2)(g) for abatement. The schedule does not mention cover plates.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Lists 'Missing or damaged cover plates' under Electrical, without citing a section. Recorded as City guidance; it does NOT establish that Chapter 27 expressly requires cover plates.
- *interpretation*: FixIt. Mapping a missing cover plate to 27.04(2)(g) ('properly installed … good and safe working condition') remains an interpretation; the specific electrical-code requirement is still unidentified.

**Decision so far:** PROVISIONAL: user accepted 27.04(2)(g) as a general safety and maintenance mapping (2026-11-14). (g)3. not mapped automatically. Specific electrical-code requirements (e.g. cover plates) must be identified separately before asserting they are expressly required. Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Water damage / suspected mold (`WATER_DAMAGE_MOLD`)

> ⚠ **Separate legal-source verification required.** Chapter 27 does not itself establish the full
> requirement for this category.

**§27.05(2)(g)1.**: general maintenance obligation (potentially relevant)

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 14
- Numbering evidence: Inline markers '(g) 1.'; 27.07(2)(d) cites 'Sec. 27.05(2)(g)2.' in the same scheme.

> Every interior floor, wall and ceiling including door and window assemblies shall be kept clean and in good repair, and shall be capable of affording privacy.

**§27.05(2)(g)2.**: general maintenance obligation (potentially relevant)

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 14
- Numbering evidence: Inline marker '2.' under (g); cited as 'Sec. 27.05(2)(g)2.' in 27.07(2)(d).

> Every foundation, exterior wall, and floor and roof shall be reasonably weathertight, watertight and rodentproof and shall be kept in proper repair and shall be capable of affording privacy.

**Why it matches:** Water stains on walls or ceilings are damage to interior surfaces (good repair) and may indicate the building is not watertight.

**Uncertainty / missing source:** Chapter 27 never mentions mold (0 hits for 'mold' or 'mildew'). It cannot support any statement about mold or its health effects. The placeholder CH27-MOISTURE ('conditions that support mold growth') is not supported by the text. A stain alone does not show an active leak or which surface failed.

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '12. 27.05(2)(g)1.' lists 'vii. Mold on walls, ceilings and/or floors causing unsafe condition…', 'viii. … causing documented health issues', 'ix. … not causing documented health issues' with abatement percentages; row 16 (27.05(2)(g)4.) covers mold in cabinets; row 44 covers basement 'damp and mold or mildew'.
- *interpretation*: FixIt. This is the City's classification for RENT ABATEMENT (Chapter 32, available only after the 32.04 process, e.g. an inspection order). Chapter 27's own text still does not mention mold, so it is not a mold-specific Chapter 27 rule. Mold stays pending.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Lists 'water damage' on interior surfaces; links a separate 'Mold' page (that URL returned 404 when fetched).

**Decision so far:** PROVISIONAL: user accepted 27.05(2)(g)1. and (g)2. as potentially relevant general maintenance provisions (2026-11-14). A water stain alone does not prove a leak, a code violation, or mold. Wording distinguishes visible water damage from suspected mold; mold-specific requirements stay unverified (pending additional legal-source verification). Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Droppings / insects / pest damage (`PEST_EVIDENCE`)

**§27.07(2)(d)**: direct (single-family dwellings, with exceptions)

- Section title: *27.07 - FIXING THE RESPONSIBILITY OF OWNERS, OPERATORS, AND OCCUPANTS.*
- PDF page: 30 (continues onto the next page)
- Numbering evidence: Inline markers (2) ... (d) in 27.07.

> Every occupant of a single-family dwelling shall be responsible for the extermination of any pests, vermin or rodents therein with the following exceptions: when the owner or operator has failed to clean the dwelling prior to occupancy or when the owner or operator is out of compliance with Madison General Ordinances Sec. 27.05(2)(g)2., extermination shall be the responsibility of the owner.

**§27.07(2)(d)**: direct (dwellings other than single-family)

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

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '38. 27.07(2)(d) a. Extermination of pests i. Severe infestation, whether occasional or chronic ii. Non-severe but chronic' confirms the number.

**Decision so far:** PROVISIONAL: user accepted 27.07(2)(d) with the 27.03 definition of infestation (2026-11-14). Explain single-family vs other dwellings and the stated exceptions; a photo of possible droppings does not establish a sustained infestation; no claim that rentals must be entirely pest-free or that professional extermination is legally required. Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Broken/missing entry or window lock (`BROKEN_LOCK`)

**§27.05(2)(h)**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline markers (2) ... (h); history note '(Sec. 27.05(2)(h) Am. by Ord. 7481 ...)'.

> All door and window hardware shall be installed and maintained in proper working condition.

**§27.05(2)(h)**: condition (applies to rented units; Paragraph 9. = bed and breakfasts)

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline markers (2) ... (h); history note '(Sec. 27.05(2)(h) Am. by Ord. 7481 ...)'.

> Except as provided in Paragraph 9. below, the following shall apply in dwelling units all or a portion thereof which are rented:

**§27.05(2)(h)3.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline marker '3.' under (h); 27.05(2)(h)7. refers to 'Paragraphs 1., 2., 3., ... of Subdivision (h) of Subsection (2) of Section 27.05'.

> All doors into each dwelling unit shall have a keyed deadbolt lock with a minimum one (1) inch throw, which is openable with a key on the exterior side of the door and a knob on the interior side of the door.

**§27.05(2)(h)3.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline marker '3.' under (h); 27.05(2)(h)7. refers to 'Paragraphs 1., 2., 3., ... of Subdivision (h) of Subsection (2) of Section 27.05'.

> The strike plate shall be held in place by 2½ inch screws.

**§27.05(2)(h)3.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline marker '3.' under (h); 27.05(2)(h)7. refers to 'Paragraphs 1., 2., 3., ... of Subdivision (h) of Subsection (2) of Section 27.05'.

> Sliding doors shall have an approved secondary locking device.

**§27.05(2)(h)4.**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline marker '4.' under (h).

> All basement, first, and second story windows and all other windows accessible by balconies, fire escapes, trees or other existing means shall be provided with sash fasteners.

**§27.05(2)(h)6.**: exception (approved alternatives)

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline marker '6.' under (h); 27.05(2)(h)7. lists 'Paragraphs 1., 2., 3., 4., 5. and 6.'

> Alternative locking devices to equally resist illegal entry may be substituted with the approval of the Madison Building Inspection Division

**Why it matches:** 27.05(2)(h) directly requires working door and window hardware, keyed deadbolts on doors into dwelling units, and sash fasteners on accessible windows.

**Uncertainty / missing source:** Paragraphs 1.-6. apply to rented dwelling units 'Except as provided in Paragraph 9.' (bed and breakfasts). Window rules depend on the story and accessibility. The parse of paragraph 7. (lodging rooms / shared entrances) came back with lines out of order, so it is not quoted; check it on Municode if needed.

**Related sources, by evidence level:**

- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Keyed deadbolt with at least a one-inch throw and 2.5-inch strike-plate screws; vent locks 1-5 inches; consistent with 27.05(2)(h).

**Decision so far:** PROVISIONAL: user accepted 27.05(2)(h), (h)3. and (h)4. (2026-11-14), subject to verifying the exact requirements and applicability. Include the rented-unit condition, approved alternative locking devices (quoted from (h)6., a supporting citation for the exception) and the window floor/access distinction. Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Broken/cracked window or screen (`BROKEN_WINDOW`)

**§27.05(2)(h)**: general maintenance obligation

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 15
- Numbering evidence: Inline markers (2) ... (h); history note '(Sec. 27.05(2)(h) Am. by Ord. 7481 ...)'.

> Every window, exterior door, interior door, and basement hatchway shall be reasonably weathertight, watertight, and rodentproof and kept in proper repair.

**§27.04(2)(f)**: direct (seasonal: screens by June 1 until storm windows go in)

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 7
- Numbering evidence: Inline markers (2) ... (f); history note '(Sec. 27.04(2)(f) Am. by Ord. 12,349 ...)'.

> All doors required for ventilation and all windows shall be protected with insect screen equivalent to not less than sixteen (16) wire mesh installed to prevent the entrance of flies, mosquitoes and other insects, annually during May before June 1 and maintained until storm windows are installed in autumn.

**§27.04(2)(f)**: direct (seasonal: storm windows Oct 15 - Nov 15)

- Section title: *27.04 - MINIMUM STANDARDS FOR BASIC EQUIPMENT, LIGHTING, VENTILATION, HEATING, AND ELECTRICAL SERVICE.*
- PDF page: 7
- Numbering evidence: Inline markers (2) ... (f); history note '(Sec. 27.04(2)(f) Am. by Ord. 12,349 ...)'.

> All exterior doors and windows shall have storm windows or storm doors installed or maintained to prevent excessive drafts and heat loss no earlier than October 15, but no later than November 15 annually.

**§27.07(2)(c)**: direct (owner responsibility for screens and storm windows)

- Section title: *27.07 - FIXING THE RESPONSIBILITY OF OWNERS, OPERATORS, AND OCCUPANTS.*
- PDF page: 30
- Numbering evidence: Inline markers (2) ... (c) in 27.07.

> Every owner of a residential building shall be responsible for hanging, installation, and maintenance of all screens and double or storm doors and windows whenever the same are required under the provisions of the Madison General Ordinances.

**Why it matches:** Windows must be kept in proper repair and weathertight; screens are required seasonally, and the owner is responsible for screens.

**Uncertainty / missing source:** 'Cracked glass' is not named explicitly; it falls under 'proper repair' / 'weathertight' by interpretation. The screen requirement is seasonal (by June 1 until storm windows go in), so a missing screen in winter may not be a violation.

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '6. 27.04(2)(f) [27.07(2)(c)] a. Screens' confirms the screen mapping for abatement.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Storm windows 'November 15 to April 30', screens 'June 1 to October 15', and 'No broken or cracked glass'. These differ in framing from Chapter 27 (screens by June 1 until storm windows go in; storm windows installed Oct 15 - Nov 15) and Chapter 27 does not name cracked glass. FixIt follows the ordinance text.

**Decision so far:** PROVISIONAL: user accepted 27.05(2)(h) for general window condition and repair, and 27.04(2)(f) / 27.07(2)(c) only for the screen and storm-window requirements with their seasonal dates (2026-11-14). Do not claim Chapter 27 explicitly names cracked glazing. Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Active leak / damaged fixtures (`LEAK_PLUMBING`)

**§27.05(2)(j)**: direct

- Section title: *27.05 - SAFE AND SANITARY MAINTENANCE OF PROPERTY.*
- PDF page: 17
- Numbering evidence: Inline markers (2) ... (j).

> Every plumbing fixture and water and waste pipe shall be properly installed and maintained in good working condition, free from defects, leaks, and obstructions.

**Why it matches:** Directly requires plumbing fixtures and pipes to be free from leaks and in good working condition.

**Uncertainty / missing source:** Low. Whether a given drip is a 'leak' is still an inspector's call; FixIt cannot see inside walls.

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: Live Municode, Chapter 27, version Sep 1, 2026 (checked 2026-11-14). '(j) Every plumbing fixture and water and waste pipe…' sits under 27.05(2), in order after (f)-(i); one sentence, no exceptions.
- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '30. 27.05(2)(j) [27.04(2)(a)] [27.04(2)(b)] a. Leaking Water Supply or Drain Piping…' confirms the subsection number and the plumbing scope. Applies within the rent-abatement process only.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Lists 'Fixtures improperly installed or leaking' and 'Plugged or slow drains' under Plumbing.
- *interpretation*: User decision. Citation limited to plumbing fixtures and water/waste pipes; not roof leaks or unexplained stains.

**Decision so far:** PROVISIONAL: user accepted 27.05(2)(j) as the primary mapping (2026-11-14). 27.04(2)(a) not added. Applies only to plumbing fixtures and water/waste pipes, not roof leaks or unexplained water stains. Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

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

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: Live Municode, Chapter 27, version Sep 1, 2026 (checked 2026-11-14). '(g) 1.' under 27.05(2) contains both quoted sentences; next paragraph is '2. Every foundation…'.
- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '12. 27.05(2)(g)1. … a. Interior floor, wall, or ceiling … ii. Is damaged or in such disrepair … (including but not limited to holes in floors, walls, ceilings)' confirms the number and that the City's abatement schedule files holes under (g)1.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Lists 'Holes, water damage, or peeling paint on walls, ceilings…' and damaged floors.
- *interpretation*: FixIt. 'Serious cracking' / 'peeling paint' are named in the text; holes and flooring fall under 'good repair' (interpretation, consistent with the RA schedule).

**Decision so far:** PROVISIONAL: user accepted 27.05(2)(g)1. for interior surfaces (2026-11-14). Keep 'serious cracking' / 'peeling paint' (direct) distinct from general 'good repair'. Damaged stairs removed from this category (stair safety handled separately under 27.05(2)(i)). Lead paint labeled general safety information, not a Chapter 27 requirement. Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.

### Blocked exit / unsafe stairs / missing handrail (`BLOCKED_EGRESS`)

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

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '4. 27.04(2)(d) [27.05(2)(i)] [27.05(2)(h)] a. Required exit … iii. Blocked by accumulation of stored items … iv. … movable furniture obstructing exit path'; row '28. 27.05(2)(i)' covers stairs and handrails/guardrails. Neither mentions 27.06(4): the cross-reference stays unresolved.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). 'Missing handrail on stairs with more than three steps'; guardrails for areas higher than 24 inches (no source cited).

**Decision so far:** ON HOLD (user, 2026-11-14): final approval waits for review of the 27.06(4) cross-reference discrepancy and the relevant Wisconsin SPS requirements (SPS 321.04, SPS 362). Category renamed 'Blocked exit / unsafe stairs / missing handrail', with the three conditions kept distinct; a photo of stairs must not trigger a blocked-exit or missing-handrail finding by itself.

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

**Related sources, by evidence level:**

- *ordinance text (independently confirmed)*: Live Municode, Chapter 27, version Sep 1, 2026 (checked 2026-11-14). '(h) Heating.' sits under 27.04(2); contains the 67°F sentence, the occupant lower-temperature exception, the Chapter 30 reference and the history note '(Sec. 27.04(2)(h) Am. by Ord. 9326, 11-13-76)'; no mention of a season.
- *ordinance text (independently confirmed)*: MGO 32.04(4)(d) 'Schedule of Rent Impairing Violations' (rent abatement), live Municode, version Sep 1, 2026. Row '9. 27.04(2)(h) a. Heat i. No heat or consistently below 55°… ii. Inadequate (55-66°)…' confirms the subsection number. Abatement percentages, not the Chapter 27 rule itself.
- *City guidance (not ordinance text)*: City of Madison 'Common Code Violations' web page (no ordinance sections cited, undated). Says heat 'must keep at least 67°F at all times'. Omits the occupant exception; FixIt follows the ordinance text.

**Decision so far:** PROVISIONAL: user accepted 27.04(2)(h) as the primary mapping (2026-11-14), including the 67°F minimum, the rooms covered (habitable rooms, kitchens and bathrooms) and the occupant exception. 27.05(2)(m) not added. Remove the unsupported 'heating season' limit; FixIt follow-up deadlines are not legal requirements. Recorded as a PROVISIONAL review decision, not a completed legal verification: needs the cross-check of exact wording, exceptions, dates and subsection numbers against the current official source, and a reviewer name supplied by the user.

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
- **CH27-PESTS** says dwellings must be "kept free of insects, rodents". Chapter 27 assigns extermination
  responsibility once an infestation (sustained presence) exists; it has no general pest-free rule.
- **CH27-SECURITY** omitted the rented-unit condition, the story/access rule for windows and approved alternatives.
- **CH27-EGRESS** says handrails must be "firmly fastened". Chapter 27 refers handrails to the SPS code.
- Category wording (explanations, remedies, names) for heat, plumbing, surfaces, locks, windows, pests, exits,
  electrical and water damage was corrected on the same branch (see the git log).

## Unresolved source discrepancies (not silently resolved)

- **27.04(2)(d) (p. 6)** (open): The egress rule says 'except as provided in Sec. 27.06(4), MGO', but 27.06(4) in this document (p. 29) is about habitable rooms below grade and says nothing about egress. Possibly an outdated cross-reference. Check the current official source; do not resolve it silently. INVESTIGATED 2026-11-14: identical wording on live Municode (Sep 1, 2026) and in the oldest structured version available (Feb 7, 2018); the rent-abatement schedule's exit row does not mention 27.06(4). The reason for the reference cannot be determined from the available official text and is not guessed. Next step: ask Building Inspection or obtain the amending ordinances (Ord. 9326, 1987; Ord. 12,349, 1999).
- **27.04(2)(h) history note (p. 9)** (open (cosmetic)): 'Ord. 9326, 11-13-76' here; the same ordinance is dated '11-13-87' elsewhere in Chapter 27. Quoted as written; does not change the requirement.
- **MGO 32.04(4)(d) row 41 (rent abatement)** (open): Cites '29.19' for carbon monoxide detectors, but the current MGO 29.19 is 'Accrediting Standards and Tests'. CO appears in Chapter 29 only via 29.22 (adoption of SPS 328). Not interpreted.
- **MGO 34.907 internal references** (open (outside Ch. 27)): Refers to 'sub. (2)(a)', 'sub. (2)(b)' and 'sub. (3)(h)' for alarm requirements that are now numbered (1)(b)1./(1)(b)2. Not interpreted.

## Parse defects, corrected from the PDF's own text layer

ai_parse_document lost words at these page breaks. The raw parse (`ch27_parsed_sections.json`) is kept unmodified;
the correct text is in `docs/legal/ch27_parse_corrections.json`. Neither passage is used in a mapping.

- **§27.05(2)(h)7.** (PDF pp. 15, 16; lines out of order and words missing across the page break): > Paragraphs 1., 2., 3., 4., 5. and 6. of Subdivision (h) of Subsection (2) of Section 27.05 shall also apply in lodging rooms, except as provided in Paragraph 9. below. In addition, the main entrance door into all lodging houses and into all residential buildings with two or more dwelling units or lodging rooms where occupants of the separate dwelling units or lodging rooms share common bathroom or kitchen facilities shall be equipped with a positive locking guarded latch lock and with an approved self-closing device. An approved guard plate shall be affixed to the exterior side of the door if the Director of the Building Inspection Division determines such a device is necessary to provide adequate security against illegal entry. All other doors into said buildings shall be equipped with a deadbolt lock complying with Paragraph 3 of this Subdivision. If any door locking mechanism in said buildings utilize passwords or passcodes of any type, including but not limited to digital locks, radio-frequency or RFID locks, or electronic keypads, the passwords or passcodes must be changed at least on a yearly basis. In cases where said buildings have an attendant or attendants responsible for the security of the building on duty twenty-four (24) hours a day, they shall be exempt from the main entrance door-locking and self-closing requirements.
- **§27.05(2)(x)** (PDF pp. 21, 22; words 'less than' and 'violation;' lost across the page break): > Private and Building Storm Sewers. Every private storm sewer and building storm sewer shall be properly installed and maintained in good working condition, free from defects, leaks and obstructions. Any person who violates this subsection shall be subject to a forfeiture of not less than twenty-five dollars ($25) nor more than two hundred dollars ($200) per day for each and every violation; each day of violation shall constitute a separate offense.

## How to approve

1. Read each excerpt against the current official text on Municode (link above).
2. In `eval/code_review.csv`, fill `approved_section_ids` (e.g. `27.04(2)(h)`) and `reviewer` **only** for rows the
   reviewer personally checked against the official source and explicitly approved. Reviewer: **Naisha Chadha**.
   Every other reviewer field stays blank. Leave `CO_DETECTOR_MISSING` blank unless a separate source is verified.

   **What a reviewer approval means:** the ordinance citation and quoted text were checked against the official
   source. It does **not** mean the reviewer is a lawyer or a City inspector, and it does **not** mean that an
   AI-detected condition is a confirmed legal violation.

3. Run `python scripts/code_parse.py approve --profile fixit --warehouse <id>` (dry run) and check the plan.
   Only then run it with `--apply`. Until then nothing in the app changes.
