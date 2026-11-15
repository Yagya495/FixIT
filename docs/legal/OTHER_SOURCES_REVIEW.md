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

**Not obtained:** the text of **MGO 34.907** itself (Municode blocks scripts; needs a browser check), **SPS 321.09** (the
fetched URL returned 404) and **SPS 362**. These are the sections Chapter 27 §27.05(2)(w) incorporates.

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

## Open questions for the reviewer

1. Read MGO 34.907 on Municode: smoke (and any CO) requirements for rentals, and whether it differs from state law.
2. Read SPS 321.09, SPS 362 and § 101.645 on the official pages, or decide they're out of scope for an existing-rental
   tool.
3. Decide whether FixIt should show the legal 5-day deadline after written notice for smoke and CO alarms, separately
   from FixIt's own reminders.
4. Decide whether CO wording should depend on building size (1-2 units vs 3+), which FixIt may not know.
