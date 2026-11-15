# Smoke alarms, CO alarms and mold: sources outside Chapter 27 (RESEARCH NOTES, NOT VERIFIED)

> Research notes for the human reviewer, gathered 2026-11-14. **Nothing here is verified or used by the app.** Quotes
> are short excerpts read from official pages through an automated fetch; each must be re-checked on the live page
> before any citation is published. FixIt is not a lawyer and this is not legal advice.

## Sources consulted

| Source | URL | Currency shown on page |
|---|---|---|
| Wis. Stat. § 101.145 (smoke detectors, residential buildings) | https://docs.legis.wisconsin.gov/statutes/statutes/101/I/145 | 2023-24 Stats. through 2025 Wis. Act 247, published 11-4-26 |
| Wis. Stat. § 101.149 (CO detectors, residential buildings) | https://docs.legis.wisconsin.gov/statutes/statutes/101/I/149 | same |
| Wis. Stat. § 101.647 (CO detectors, dwellings) | https://docs.legis.wisconsin.gov/statutes/statutes/101/ii/647 | same |
| Wis. Stat. § 101.61(1) ("dwelling" = 1 or 2 dwelling units) | https://docs.legis.wisconsin.gov/statutes/statutes/101/II/61 | same |
| Wis. Stat. § 704.07 (landlord/tenant repair duties) | https://docs.legis.wisconsin.gov/statutes/statutes/704/07 | published 11-4-26 |
| Wis. Admin. Code ch. SPS 328 (existing 1-2 family dwellings, pre-June 1, 1980) | https://docs.legis.wisconsin.gov/code/admin_code/sps/safety_and_buildings_and_environment/326_360/328 | latest history note: Register Dec. 2011 No. 672 |
| City of Madison Fire Dept., Tenant & Owner Responsibilities (smoke alarms, MGO 34.907) | https://www.cityofmadison.com/fire/your-safety/smoke-alarms/tenant-owners-responsibilities | no date (© 1995-2026) |
| City of Madison BI, Common Code Violations: Smoke and Carbon Monoxide Alarms | https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/common-code-violations/smoke-and-carbon | no date |
| Wisconsin DHS, Tenant Landlord Issues Involving Mold | https://www.dhs.wisconsin.gov/mold/tenantlandlord.htm | last revised August 5, 2026 |
| Wis. Admin. Code ch. ATCP 134 (residential rental practices) | https://docs.legis.wisconsin.gov/code/admin_code/atcp/090/134 | searched only; no mold provision found |

**Read later on 2026-11-14 (see section 5):** MGO 34.907 and MGO 29.19/29.22 on live Municode (version Sep 1, 2026),
and Wis. Stat. § 101.645. **Still not obtained:** SPS 321.09 (the fetched URL returned 404) and SPS 362.

## 1. Smoke alarms (`SMOKE_DETECTOR_MISSING`)

- **Chapter 27** §27.05(2)(w) only incorporates other codes: MGO 34.907, SPS 362, SPS 321.09, SPS 328.02.
- **State, residential buildings** (§ 101.145; "residential building" = a public building used for sleeping or
  lodging, incl. apartment houses, rooming houses, dormitories):
  - Locations, § 101.145(4): a functional detector "in the basement and at the head of any stairway on each floor level",
    and either in each sleeping area or "within 6 feet of each sleeping area and not in a kitchen".
  - Owner installs per manufacturer (3)(a) and maintains detectors in common areas (3)(b).
  - "The occupant of a unit in a residential building shall maintain any smoke detector in that unit." (3)(c). After a
    non-owner occupant's **written notice** that a detector isn't functional, the owner must provide maintenance
    **within 5 days**.
  - Penalty (5): up to $50 per day.
- **State, 1-2 family dwellings:** § 101.645 (applied by SPS 328.03 for dwellings built before June 1, 1980): per the
  search summary, basement and each floor level, 5 days after written notice. **Not read on the official page yet.**
- **Madison** (Fire Dept. page describing MGO 34.907, "Fire Alarm and Detection Systems"; ordinance text not obtained):
  hardwired with battery backup, or a sealed 10-year battery alarm; tenant tests monthly and notifies the owner in
  writing; owner "has five days from receipt of notice to repair or replace"; no tampering; fine up to $187 for a first
  violation.
- **Effect on FixIt:**
  - "Working smoke detectors are required in rental units" is supported by state law and MGO 34.907, **not by
    Chapter 27 itself**.
  - The remedy's locations ("bedrooms and hallways outside sleeping areas") don't match the statute's wording (basement,
    head of each stairway, each sleeping area or within 6 feet).
  - The 5-day owner deadline after written notice **is** a legal deadline (state + city), unlike FixIt's 48-hour default.

## 2. Carbon monoxide alarms (`CO_DETECTOR_MISSING`)

- **Chapter 27:** no provision.
- **Buildings with 3 or more units / lodging** (§ 101.149; "residential building" = tourist rooming house, B&B, or public
  building used for sleeping or lodging):
  - Required for units with a fuel-burning appliance (2)(ag), a fuel-burning forced-air furnace (2)(aL), fuel-burning
    appliances outside the unit (2)(ap) or an attached private garage (2)(at), each with listed exemptions.
  - Location (2)(ax): outside each separate sleeping area in the immediate vicinity of the sleeping rooms, and inside a
    sleeping room that has a fuel-burning appliance (or one in its attached bathroom).
  - Owner "shall reasonably maintain every carbon monoxide detector" (3)(a). After an occupant's written notice, the
    owner repairs or replaces **within 5 days** (3)(b).
  - Whole-building exception (5): all fuel-burning appliances are sealed-combustion units under warranty.
- **1-2 unit dwellings** (§ 101.647; "dwelling" = a building with 1 or 2 dwelling units, § 101.61(1)):
  - Owner installs a functional detector "in the basement of the dwelling" and on each floor level except attic,
    garage or storage area (3)(a).
  - Does not apply to a dwelling with "no attached garage, no fireplace, and no fuel-burning appliance" (3)(a).
  - The occupant maintains detectors in the unit; the owner repairs within 5 days of written notice (3)(b).
  - No tampering (6).
- **Madison:** no CO rule found on the city pages read. A city "Minimum Housing Standards Checklist" PDF appeared in
  search at a new URL; **not checked** (the old URL redirected).
- **Effect on FixIt:**
  - "Generally required near sleeping areas when there are fuel-burning appliances" is roughly right for 3+ unit
    buildings, but misses the forced-air furnace, attached-garage and outside-appliance triggers.
  - For 1-2 unit dwellings it's wrong: the rule there is each floor level, triggered by a garage, fireplace or
    fuel-burning appliance.
  - Which statute applies depends on the number of units. The boundary of "public building" (Wis. Stat. 101.01) was
    **not reviewed**.

## 3. Mold (mold aspect of `WATER_DAMAGE_MOLD`)

- **Chapter 27:** does not mention mold.
- **No mold-specific legal requirement found:**
  - Wis. Stat. § 704.07 does not mention mold or moisture.
  - ATCP 134 search found no mold provision.
  - DHS: "dampness and mold are typically not written into local housing ordinances."
- **General duties that may apply**, per § 704.07(2)(a):
  - "Keep in a reasonable state of repair portions of the premises over which the landlord maintains control"
  - "Make all necessary structural repairs."
  - "For a residential tenancy, comply with any local housing code applicable to the premises."
- **DHS tenant guidance:** "first contact your landlord in writing"; document the condition; contact the local building
  inspector; DATCP complaint if a verified problem isn't corrected.
- **Effect on FixIt:** keep mold as "no mold-specific requirement verified".
  - A tenant letter can cite the general repair duty (§ 704.07) and the Chapter 27 surface and watertight rules, but only
    as **possibly relevant**.
  - The remedy "have any suspected mold assessed" is reasonable guidance, not a legal requirement.

## 4. Additional findings (2026-11-14, later)

### MGO 32.04(4)(d), "Schedule of Rent Impairing Violations" (ordinance text, live Municode, version Sep 1, 2026)
Under "(4) Authorization of Rent Abatement", MGO 32.04 has a table titled "MGO Violation Description % of Rent
Abatement", indexed by code section. It sets abatement percentages; it applies through the rent-abatement process
(e.g. after an order of Building Inspection or Public Health, or a hearing examiner). It does **not** add requirements
to Chapter 27.
- **Mold:** row "12. 27.05(2)(g)1. [27.05(2)(k)] [27.05(2)(g)3.] a. Interior floor, wall, or ceiling" includes
  "vii. Mold on walls, ceilings and/or floors causing unsafe condition so that an area or room is ordered vacated…",
  "viii. Mold in the dwelling on walls, ceilings and/or floors causing documented health issues" and "ix. Mold in the
  dwelling on walls, ceilings and/or floors not causing documented health issues". Row 16 (27.05(2)(g)4.) covers mold in
  or on cabinets; row 44 covers basement "damp and mold or mildew".
  - **Interpretation:** for rent abatement, the City files mold on interior surfaces under §27.05(2)(g)1. That's useful
    context for a tenant, but it's the City's abatement classification, **not a mold-specific rule in Chapter 27**,
    whose text never says "mold". The mold aspect stays pending.
- **Carbon monoxide:** row "41. 29.19 a. Carbon Monoxide Detectors not Installed Where Required" (basement; each floor
  level except attic, garage or storage; outside each separate sleeping area in the immediate vicinity; sleeping rooms
  with a fuel-burning appliance). **But the current MGO 29.19 is "Accrediting Standards and Tests"** (see section 5):
  the schedule's reference does not match the current code. Unresolved.
- **Smoke alarms:** row "43. 34.907 a. Smoke alarms not installed where required in: i. Inside every bedroom and sleeping
  area ii. Within 6 feet of each door leading to a bedroom or sleeping area of each unit iii. Each floor of the
  building". Consistent with MGO 34.907(1)(b)2. (section 5).
- **Electrical:** row "7. 27.04(2)(g)" includes "vi. Exposed wires, damaged or bare, presenting shock hazard". There is
  no cover-plate row.
- **Exits:** row "4. 27.04(2)(d)" covers exits blocked by stored items or furniture. **No reference to 27.06(4)**
  anywhere in the schedule, so the cross-reference stays unresolved.

### City of Madison "Common Code Violations" page (City guidance, not ordinance text)
URL: https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/common-code-violations
(undated; cites no ordinance sections; links Chapter 27 on Municode).
- **Electrical:** "Missing or damaged cover plates" is listed. **Recorded as City guidance only:** it doesn't cite a
  section, and Chapter 27 doesn't name cover plates. FixIt must not claim Chapter 27 expressly requires them.
- **Where the City's wording differs from Chapter 27** (FixIt follows the ordinance text):
  - **Heat:** "must keep at least 67°F at all times". The ordinance has an occupant exception.
  - **Windows:** storm windows "November 15 to April 30" and screens "June 1 to October 15". Chapter 27 says screens
    by June 1 until storm windows go in, and storm windows installed between Oct 15 and Nov 15.
  - **Glass:** "No broken or cracked glass". Chapter 27 doesn't name cracked glass.
  - **Handrails:** required on stairs "with more than three steps"; guardrails above 24 inches. No source is cited;
    probably from the SPS code, not reviewed.
  - **CO alarms:** every floor in 1-2 unit dwellings; within 15 feet of bedroom doors in 3+ unit buildings with
    fuel-burning appliances.
- The linked City "Mold" page URL returned 404 when fetched.

## 5. Madison ordinances vs Wisconsin statutes: smoke and CO alarms (read on official sources, 2026-11-14)

Labels: **[CONFIRMED]** = read in the current official text; **[CONDITION]** = a limit on when it applies;
**[INTERPRETATION]** = FixIt's reading; **[UNRESOLVED]** = open question. Municode version for all MGO text:
Sep 1, 2026 (current). Statutes: 2023-24 Wis. Stats. through 2025 Wis. Act 247, published 11-4-26.

### 5a. MGO 34.907, "Fire Alarm and Detection Systems" (Peter Talen Smoke Alarm Ordinance)
https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIVCH32--45_CH34FIPRCO_34.907FIALDESY

**Scope**
- [CONDITION] "Buildings built before 2009 shall comply with this section, all buildings built after 2009 shall comply
  with IFC section 907." (1)
- [CONFIRMED] "Residential building" means any building in the City used in whole or in part for sleeping or lodging,
  "including, but not limited to, any single family home, duplex, multifamily house, apartment house, rooming
  house…", excluding hospitals and nursing homes. (1)(a)

**Required alarms**
- [CONFIRMED] Power source, (1)(b)1.: all residential buildings "except owner-occupied single family homes" must have
  alarms that are hardwired with a battery backup, or powered by a "non-replaceable, non-removable battery" lasting at
  least ten years.
- [CONFIRMED] Locations, (1)(b)2.: owners of residential buildings (except owner-occupied single family homes) "shall
  install and maintain a smoke alarm in each bedroom, in every sleeping area and within six (6) feet of each door
  leading to a bedroom or sleeping area of each unit and on each floor of the building". This doesn't apply to hotels
  and motels.

**Maintenance and repair**
- [CONFIRMED] The owner replaces the backup battery "each time the lease is renewed or as recommended by the
  manufacturer, whichever time period is shorter", and replaces any battery that can't power the alarm. (1)(c)1.
- [CONFIRMED] The owner gives tenants the manufacturer's maintenance and testing instructions (1)(c)2., and maintains and
  tests alarms in common areas (1)(c)3.
- [CONFIRMED] Tenant duty and **repair deadline**, (1)(c)4.: "The tenant shall be responsible for maintaining and
  testing … smoke alarms that are within the dwelling unit during the term of the tenancy. The tenant shall be
  responsible for notifying the owner in writing if a smoke alarm becomes inoperable. The owner shall have five days
  from receipt of such written notice to repair and replace the inoperable alarm(s)."
- [CONFIRMED] No tampering (1)(c)5.; owner and tenant sign a smoke-alarm document per MGO 32.06(4) (1)(c)7.; no alarm in
  service more than ten years unless the manufacturer says otherwise (1)(c)8.
- [CONFIRMED] Fire safety education materials at each new lease and at least every 12 months. (2)

**Exception**
- [CONDITION] (1)(e): "This ordinance does not apply to any buildings that have smoke detectors installed as required by
  other codes, ordinances, or standards and located in locations specified in sub. (2)(b)."

**Open questions**
- [UNRESOLVED] Internal references "sub. (2)(a)", "sub. (2)(b)" and "sub. (3)(h)" don't match the current numbering,
  where alarm types are (1)(b)1. and locations (1)(b)2. Possibly outdated cross-references; not interpreted.
- [UNRESOLVED] No penalty clause in 34.907 itself. The "$187" figure comes only from the Fire Department web page.

### 5b. Carbon monoxide in Madison ordinances
- [CONFIRMED] **MGO 29.19 is "Accrediting Standards and Tests"** (current text), not carbon monoxide.
- [CONFIRMED] "Carbon monoxide" appears in Chapter 29 only in **MGO 29.22 "Adoption by Reference"**, which adopts Wis.
  Admin. Code chapters including "SPS 328 (Smoke Detectors and Carbon Monoxide Detectors)".
- [CONFIRMED] Chapter 34 mentions carbon monoxide only in a permit-exception list ("carbon monoxide detection (IFC 915)")
  and in a list of state codes.
- [UNRESOLVED] The MGO 32.04(4)(d) rent-abatement row "41. 29.19 a. Carbon Monoxide Detectors not Installed Where
  Required" points to a section that is now about accrediting standards. Possibly an outdated reference; not
  interpreted. Whether Chapter 34's IFC adoption applies IFC 915 (CO) to existing rentals was not reviewed.
- [INTERPRETATION] For existing rentals, CO requirements come from state law (5c), adopted locally through MGO 29.22 /
  SPS 328 for 1-2 family dwellings built before June 1, 1980.

### 5c. Wisconsin statutes (official text) compared with Madison

**Smoke alarms**

| | MGO 34.907 (pre-2009 buildings) | Wis. Stat. § 101.145 (residential buildings, i.e. public buildings used for sleeping/lodging incl. apartment houses) | Wis. Stat. § 101.645 (dwellings; SPS 328 for 1-2 family built before 6/1/1980) |
|---|---|---|---|
| Locations | each bedroom; every sleeping area; within 6 ft of each bedroom/sleeping-area door; each floor | basement and head of any stairway on each floor; each sleeping area or within 6 ft of it, not in a kitchen (4) | basement and each floor level except attic/storage (3) |
| In-unit maintenance | tenant maintains and tests | occupant maintains (3)(c) | occupant maintains (3) |
| Owner deadline after written notice | **5 days** ((1)(c)4.) | **5 days** ((3)(c)) | **5 days** ((3)) |
| Other | owner replaces batteries at lease renewal; 10-year life; owner-occupied single family homes excluded from (1)(b) | penalty up to $50/day (5) | no penalty clause; annotation: negligence per se |

**Carbon monoxide alarms**

| | Wis. Stat. § 101.149 (residential buildings) | Wis. Stat. § 101.647 (dwellings = 1 or 2 units, § 101.61(1)) |
|---|---|---|
| When required | units with a fuel-burning appliance, a fuel-burning forced-air furnace, fuel-burning appliances outside the unit, or an attached garage, each with listed exemptions (2)(ag)-(at); none if all appliances are sealed-combustion under warranty (5) | basement and each floor level except attic, garage, storage (3)(a); not required with "no attached garage, no fireplace, and no fuel-burning appliance" |
| Location | outside each separate sleeping area "in the immediate vicinity"; inside a sleeping room with a fuel-burning appliance (2)(ax) | basement + each floor level |
| Maintenance | owner "shall reasonably maintain" (3)(a) | occupant maintains in the unit (3)(a) |
| Owner deadline after written notice | **5 days** (3)(b) | **5 days** (3)(b) |
| Other | tampering penalties (8)(c); correction orders, $50/day after (8)(a) | tampering prohibited (6) |

- [INTERPRETATION] Every source read gives the owner **5 days after the tenant's written notice** for a non-working smoke
  alarm (MGO 34.907; §§ 101.145, 101.645) or CO alarm (§§ 101.149, 101.647). That's a statutory or ordinance deadline,
  unlike FixIt's own reminders. It requires written notice.
- [INTERPRETATION] Smoke-alarm locations differ between MGO 34.907 (each bedroom, within 6 ft of bedroom doors, each
  floor) and the state statutes. For a pre-2009 Madison rental, MGO 34.907 is the more specific local rule.
- [UNRESOLVED] How state and city rules interact (e.g. which governs when both apply) was not reviewed; not legal advice.
- [CONFIRMED, City guidance only] The City's Common Code Violations page describes CO alarms as every floor in 1-2 unit
  dwellings and within 15 feet of bedroom doors in 3+ unit buildings. "15 feet" doesn't appear in § 101.149, which says
  "immediate vicinity". Source unidentified.

## 6. The §27.06(4) exit cross-reference (investigated; UNRESOLVED)
- [CONFIRMED] Live text (Sep 1, 2026): §27.04(2)(d) requires two accessible unobstructed means of egress "except as
  provided in Sec. 27.06(4), MGO." It's the only reference to 27.06(4) in Chapter 27.
- [CONFIRMED] §27.06(4) (live): "No habitable room, kitchen or bathroom shall have its floor level below the alley, court,
  yard, or street grade … except when meeting the requirements of Wis. Adm. Code ch. SPS 362 or chs. SPS 320-325 …
  unless said room or rooms have been previously approved by the Building Inspection Division prior to May 17, 1983."
  It doesn't mention egress or exits.
- [CONFIRMED] Same wording in the oldest structured Municode version available (Feb 7, 2018, "Revision 1"). The Aug 2017
  archive's document no longer exists on Municode ("BlobNotFound"). Versions available: 105, from 08/13/2017 to
  09/01/2026.
- [CONFIRMED] The rent-abatement schedule's exit row ("4. 27.04(2)(d)") doesn't mention 27.06(4).
- [CONFIRMED] History notes: §27.04(2)(d) "Am. by Ord. 9326, 11-13-87; Ord. 13,124, 8-28-02; ORD-08-00109, 10-7-08;
  ORD-12-00035, 3-28-12"; §27.06(4) "Am. by Ord. 12,349, 3-30-99; Ord. 13,124, 8-28-02; ORD-08-00109, 10-7-08".
- [UNRESOLVED] Why the exit rule points to 27.06(4) can't be determined from the available official text. **Not
  guessed.** Possible next steps (not done): ask City of Madison Building Inspection (608-266-4551), or obtain the text
  of the amending ordinances (e.g. Ord. 9326 of 1987, Ord. 12,349 of 1999) from the City Clerk / Legistar. Exits stay on
  hold.

## Open questions for the reviewer

1. ~~Read MGO 34.907 and MGO 29.19~~ Done (section 5). New: the 29.19 reference in the rent-abatement schedule, and
   34.907's internal sub-references, don't match the current numbering.
2. Read SPS 321.09 and SPS 362 on the official pages, or decide they're out of scope for an existing-rental tool.
3. Decide whether FixIt should show the legal 5-day deadline after written notice for smoke and CO alarms, separately
   from FixIt's own reminders.
4. Decide whether CO wording should depend on building size (1-2 units vs 3+), which FixIt may not know.
