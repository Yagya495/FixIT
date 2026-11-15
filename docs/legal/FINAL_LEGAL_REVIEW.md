# FixIt Madison: consolidated legal review of the remaining categories (PREPARATION, NOT APPROVAL)

> **Status: prepared for human review on 2026-11-14. Nothing in this document is approved or verified by the
> reviewer.** No citation was activated, no reviewer field was filled, and `code_parse.py approve --apply` was not
> run. Only three citations are verified and live: plumbing §27.05(2)(j), heat §27.04(2)(h) and interior surfaces
> §27.05(2)(g)1. (approved by the named reviewer; unchanged by this review). FixIt is not a lawyer and this is not
> legal advice. A photo never establishes a code violation; only a City of Madison inspector can determine one.

## How this review was done

| Source | How it was read this session | Version shown |
|---|---|---|
| MGO Chapter 27 | Official Municode PDF export in the repo (`docs/legal/Madison_Chapter_27.pdf`, sha256 `7feae63e…e1ff4516`, unchanged). Text re-extracted independently (pypdf) and **all 26 proposed excerpts re-verified** word for word with `scripts/ch27_review_sheet.py --pdf-text`. New passages quoted below were read from the same PDF and the repo's parse. | PDF printed 11/14/26; the previous session compared it with live Municode, **version Sep 1, 2026 (current)**, `docs/legal/ch27_live_check.md` |
| Live Municode (Ch. 27, MGO 34.907, MGO 29.22) | **Not reachable by script this session** (Cloudflare challenge, HTTP 403). Not bypassed. MGO 34.907 and 29.22 quotes come from the previous session's in-browser reading (`OTHER_SOURCES_REVIEW.md` §5) and are **not re-verified** here. | Sep 1, 2026 (as recorded) |
| Wis. Stats. 101.01, 101.145, 101.149, 101.61, 101.645, 101.647, 704.07 | Official pages on docs.legis.wisconsin.gov, full text read | "2023-24 Wisconsin Statutes updated through 2025 Wis. Act 247 … (Published 11-4-26)" |
| Wis. Admin. Code SPS 320, 321.04, 321.09, 321.097, 328, 361.02, 362.0100/.0907/.1011/.1015, 366.1010, 316.001-.002; ATCP 134.04 | Official section pages on docs.legis.wisconsin.gov | "Entire code is always current" (monthly); register dates per section quoted below |
| City of Madison Building Inspection: Common Code Violations + Mold, Pests, Smoke/CO sub-pages; Fire Dept. tenant/owner smoke-alarm page; Public Health Madison & Dane County pest and home-hazard pages | Fetched 2026-11-14 | Undated (footer © 1995-2026) |

**Evidence labels used below:** *ordinance/statute text* (read in the official text) · *City guidance* (official
City web page, not law) · *interpretation* (FixIt's reading; needs the reviewer) · *unresolved*.

**Prompt-injection check:** no instruction-like or hidden text was found in the passages read. Page content was
treated as data only.

## Summary

| # | Category (type id) | Proposed citation(s) | Recommendation |
|---|---|---|---|
| 1 | Broken locks (`BROKEN_LOCK`) | MGO §27.05(2)(h), (h)3., (h)4.; (h)6. as supporting reference | **READY FOR HUMAN REVIEW** |
| 2 | Windows and screens (`BROKEN_WINDOW`) | MGO §27.05(2)(h) (first sentence); §27.04(2)(f) (screens/storm windows, seasonal); §27.07(2)(c) | **READY FOR HUMAN REVIEW** |
| 3 | Pest evidence (`PEST_EVIDENCE`) | MGO §27.07(2)(d) + §27.03 "Infestation" | **READY FOR HUMAN REVIEW** (one open definitional question, see below) |
| 4 | Electrical hazards (`EXPOSED_WIRING`) | MGO §27.04(2)(g) (general obligation). Cover plates: none | **READY FOR HUMAN REVIEW** for §27.04(2)(g); **NO VERIFIED SOURCE** for a cover-plate requirement |
| 5 | Water damage (`WATER_DAMAGE_MOLD`, water aspect) | MGO §27.05(2)(g)1., §27.05(2)(g)2. (potentially relevant) | **READY FOR HUMAN REVIEW** |
| 6 | Exits, stairs, handrails (`BLOCKED_EGRESS`) | MGO §27.04(2)(d), §27.05(2)(i) | **NEEDS CLARIFICATION** |
| 7 | Smoke alarms (`SMOKE_DETECTOR_MISSING`) | MGO §27.05(2)(w) (reference only) → MGO 34.907; Wis. Stat. 101.145 / 101.645; SPS 328.03 | **NEEDS CLARIFICATION** |
| 8 | CO alarms (`CO_DETECTOR_MISSING`) | No Chapter 27 / Madison provision. Wis. Stat. 101.149 / 101.647; SPS 328.04 | **NEEDS CLARIFICATION** |
| 9 | Mold (`WATER_DAMAGE_MOLD`, mold aspect) | None mold-specific | **NO VERIFIED SOURCE** |

Chapter 27 link for every MGO 27.x citation:
https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO

---

## 1. Broken locks (`BROKEN_LOCK`): READY FOR HUMAN REVIEW

**Proposed citation:** §27.05(2)(h) (general hardware duty), §27.05(2)(h)3. (deadbolts), §27.05(2)(h)4. (sash
fasteners). §27.05(2)(h)6. only as a supporting reference. PDF p. 15.

**Exact excerpts (ordinance text):**
- (h): "All door and window hardware shall be installed and maintained in proper working condition."
- (h), condition: "Except as provided in Paragraph 9. below, the following shall apply in dwelling units all or a portion thereof which are rented:"
- (h)3.: "All doors into each dwelling unit shall have a keyed deadbolt lock with a minimum one (1) inch throw, which is openable with a key on the exterior side of the door and a knob on the interior side of the door." / "The strike plate shall be held in place by 2½ inch screws." / "Sliding doors shall have an approved secondary locking device."
- (h)4.: "All basement, first, and second story windows and all other windows accessible by balconies, fire escapes, trees or other existing means shall be provided with sash fasteners."
- (h)6.: "Alternative locking devices to equally resist illegal entry may be substituted with the approval of the Madison Building Inspection Division"

**Conditions and exceptions:** (h)1.-6. apply only to **rented** dwelling units, except Paragraph 9. (bed and breakfast
establishments). (h)7. extends 1.-6. to lodging rooms and adds main-entrance rules for lodging houses and shared-facility
buildings (24-hour attendant exemption); (h)8. sets rules for cooperatives. Window rule depends on story/accessibility.
Not mapped but present: (h)1. door viewer, (h)2. hinges, (h)5. vent locks on lower/accessible double-hung and sliding
windows ("one (1) to five (5) inches open").

**Current FixIt wording vs source:** accurate. Added on this branch: "Different rules apply to lodging rooms,
cooperatives and bed and breakfasts."

**Proposed FixIt wording (now in `taxonomy.py`):** "Door and window hardware must be kept in proper working condition. In
rented units, every door into the unit needs a keyed deadbolt with at least a 1-inch throw, and basement, first- and
second-story windows (and any window reachable from a balcony, fire escape or tree) need sash fasteners. Building
Inspection can approve equivalent alternative locking devices. Different rules apply to lodging rooms, cooperatives and
bed and breakfasts."

**Independently verified:** excerpts verbatim in the official PDF (this session) and live Municode (previous session).
Subsection labels: the PDF text layer drops the paragraph numerals, so "3.", "4.", "6." rest on the parsed labels and on
(h)7.'s own reference to "Paragraphs 1., 2., 3., 4., 5. and 6. of Subdivision (h) of Subsection (2) of Section 27.05".
History note "(Sec. 27.05(2)(h) Am. by Ord. 7481 …)" confirms (h). *City guidance* (Common Code Violations) matches:
deadbolt "at least a one-inch throw", strike-plate screws "at least 2.5 inches long".

**Unresolved:** none material. A photo cannot show whether a unit is rented or whether an alternative device was approved.

## 2. Windows and screens (`BROKEN_WINDOW`): READY FOR HUMAN REVIEW

**Proposed citation:** §27.05(2)(h) first sentence (p. 15); §27.04(2)(f) screens and storm windows (p. 7);
§27.07(2)(c) owner responsibility (p. 30).

**Exact excerpts (ordinance text):**
- §27.05(2)(h): "Every window, exterior door, interior door, and basement hatchway shall be reasonably weathertight, watertight, and rodentproof and kept in proper repair."
- §27.04(2)(f): "All doors required for ventilation and all windows shall be protected with insect screen equivalent to not less than sixteen (16) wire mesh installed to prevent the entrance of flies, mosquitoes and other insects, annually during May before June 1 and maintained until storm windows are installed in autumn." / "All exterior doors and windows shall have storm windows or storm doors installed or maintained to prevent excessive drafts and heat loss no earlier than October 15, but no later than November 15 annually."
- §27.07(2)(c): "Every owner of a residential building shall be responsible for hanging, installation, and maintenance of all screens and double or storm doors and windows whenever the same are required under the provisions of the Madison General Ordinances."

**Conditions:** screens are seasonal (by June 1 until storm windows go in); storm windows go in Oct 15-Nov 15. Chapter 27
does not name cracked or broken glass (0 hits for "glass"); a cracked pane falls under "proper repair"/"weathertight" only
by *interpretation*. §27.051 (energy code) separately incorporates SPS 367.05(2) for double glazing/storm windows (not
mapped).

**Current FixIt wording vs source:** accurate (says Chapter 27 "does not specifically mention cracked glass").

**City guidance differs (FixIt follows the ordinance):** "Be free of broken or cracked glass."; storm windows "from
November 15 to April 30"; screens "from June 1 to October 15".

**Independently verified:** excerpts in the PDF and live text; MGO 32.04(4)(d) row "6. 27.04(2)(f) [27.07(2)(c)] a.
Screens" (previous session). **Unresolved:** none material.

## 3. Pest evidence (`PEST_EVIDENCE`): READY FOR HUMAN REVIEW (with one open question)

**Proposed citation:** §27.07(2)(d) (p. 30) + §27.03 "Infestation" (p. 3).

**Exact excerpts (ordinance text):**
- §27.07(2)(d): "Every occupant of a single-family dwelling shall be responsible for the extermination of any pests, vermin or rodents therein with the following exceptions: when the owner or operator has failed to clean the dwelling prior to occupancy or when the owner or operator is out of compliance with Madison General Ordinances Sec. 27.05(2)(g)2., extermination shall be the responsibility of the owner. Whenever infestation exists in any residential dwelling other than a single-family dwelling, extermination shall be the responsibility of the owner."
- §27.03: "\"Infestation\" means the sustained presence of pests, vermin, or rodents." and "\"Extermination\" shall mean elimination of infestation."

**Conditions:** depends on single-family vs other dwelling; "sustained presence" means one photo may not show an
infestation. §27.05(2)(g)2. (the exception) covers foundation, exterior wall, floor and roof being "reasonably
weathertight, watertight and rodentproof".

**Related state law (statute text):** Wis. Stat. 704.07(3)(a): if the premises are damaged "including by an infestation
of insects or other pests, due to the acts or inaction of the tenant", the landlord may make the tenant repair or pay.
**City guidance:** "Housing providers need to keep buildings clear of pests, such as insects and rodents." and "We cannot
accept pictures or videos as proof of a problem. The inspector must see the problem themselves." Public Health:
"Ask your landlord to hire a pest control company."

**Corrections made:** the single-family exception now names foundation, exterior walls, floors and roof (it previously
said "the building"), and the explanation now carries the City's "photos are not accepted as proof" statement, which
matters for FixIt's evidence framing.

**Unresolved:** **"single-family dwelling" is not defined in §27.03** (it defines "Dwelling" and lists "Single-family
detached dwellings" as a type of residential building). How a rented house, or one shared by unrelated tenants, is
classified is not determined. FixIt quotes the distinction and does not decide it. The City page's "keep buildings clear
of pests" is broader than the ordinance text; FixIt keeps them distinct.

## 4. Electrical hazards (`EXPOSED_WIRING`): READY FOR HUMAN REVIEW (general obligation) / NO VERIFIED SOURCE (cover plates)

**Proposed citation:** §27.04(2)(g) (p. 7), first sentence.

**Exact excerpt (ordinance text):** "Every dwelling unit and all public and common areas in multiple dwellings shall be
supplied with electrical service, outlets, and fixtures which shall be properly installed, shall be maintained in good
and safe working condition, and shall be connected to a source of electric power in a manner prescribed by the Wisconsin
Electric Code."

**Considered, not mapped:** §27.04(2)(g)3. "… all exposed abandoned wiring shall be removed." (narrower than live exposed
wiring; user decision).

**Related (statute/rule text):** Wis. Stat. 704.07(2)(a)5.: landlord must "comply with any local housing code applicable
to the premises". ATCP 134.04(2)(b)3. (disclosure **to prospective tenants**): "the electrical wiring, outlets, fixtures
or other components of the electrical system are not in safe operating condition". SPS 316.002(1): the state electrical
code "applies to electrical wiring installations"; no SPS 316 text read mentions faceplates or cover plates. The NEC
(NFPA 70) text itself was not reviewed.

**Cover plates:** *City guidance only*: "Missing or damaged cover plates" (Common Code Violations, Electrical).
**No ordinance or statute text found that names cover plates.** FixIt must not say they are expressly required.

**Correction made:** removed "whether they are expressly required is set by the electrical code" (an unverified
assertion). It now says: "Chapter 27 does not name cover plates, and FixIt has not verified a specific legal requirement
for them (the City's Common Code Violations page lists missing or damaged cover plates as a common issue)."

**Unresolved:** whether NEC faceplate rules apply to existing rental installations (not reviewed).

## 5. Water damage (`WATER_DAMAGE_MOLD`, water aspect): READY FOR HUMAN REVIEW

**Proposed citation:** §27.05(2)(g)1. and §27.05(2)(g)2. (p. 14), as **potentially relevant general maintenance
provisions**. Note §27.05(2)(g)1. is already approved for `DAMAGED_SURFACES`; approving it here would be a separate
category mapping.

**Exact excerpts (ordinance text):**
- (g)1.: "Every interior floor, wall and ceiling including door and window assemblies shall be kept clean and in good repair, and shall be capable of affording privacy."
- (g)2.: "Every foundation, exterior wall, and floor and roof shall be reasonably weathertight, watertight and rodentproof and shall be kept in proper repair and shall be capable of affording privacy."

**Possibly relevant, not proposed (for the reviewer):** (g)1. also says "A waterproof and hard surface shall be provided in
spaces subject to moisture." §27.05(2)(k): "Every water closet compartment floor surface and bathroom floor surface shall
be properly constructed and maintained so as to be reasonably impervious to water …". Adding either would need a new
proposal entry and excerpt check.

**City guidance:** "Holes, water damage, or peeling paint on walls, ceilings, and other surfaces"; Mold page: "We can
require repairs when water damage is present."

**Conditions:** a stain does not show an active leak, which surface failed, or a violation. Roof leaks and unexplained
stains are not plumbing (§27.05(2)(j) stays limited to fixtures and pipes).

**Current FixIt wording:** accurate; City Building Inspection's statement was added (see 9).

## 6. Exits, stairways and handrails (`BLOCKED_EGRESS`): NEEDS CLARIFICATION

**Proposed citation:** §27.04(2)(d) (p. 6) and §27.05(2)(i) (p. 17).

**Exact excerpts (ordinance text):**
- §27.04(2)(d): "Every dwelling unit and lodging room shall have direct access to at least two (2) accessible unobstructed means of egress leading to a safe and open public street, alley, or court connected to a street, except as provided in Sec. 27.06(4), MGO." … "All stairways and platforms shall be protected with handrails and guardrails as specified in Wis. Admin. Code § SPS 321.04(2) or ch. SPS 362."
- §27.05(2)(i): "Every inside and outside stair, every porch, platform, balcony, and every appurtenance thereto shall be so constructed as to be safe to use and capable of supporting the load that normal use may cause to be placed thereon, and shall be kept in proper condition and repair and shall present an attractive appearance. All interior and exterior stairs, steps, porches, platforms, balconies, and every appurtenance thereto shall comply with the requirements specified in Wis. Admin. Code § SPS 321.04 and ch. SPS 362, as dictated by the type of occupancy in the building. Existing variances to the requirements specified herein may be approved by the Building Inspection Division …"

**State code read this session (rule text):**
- SPS 321.04(3)(a)1.: "A flight of stairs with more than 3 risers shall be provided with at least one handrail for the full length of the flight." (3)(a)2.: "Guards shall be provided on all open sides of stairs consisting of more than 3 risers and on all open sides of areas that are elevated more than 24 inches above the floor or exterior grade." (3)(b)1.a.: handrails "at least 30 inches, but no more than 38 inches above the nosing of the treads".
- Scope: SPS 320.03 "The effective date of chs. SPS 320, 321 … is June 1, 1980."; SPS 320.05(1) "The provisions of this code shall not apply to dwellings and dwelling units, the construction of which was commenced prior to the effective date of this code".
- SPS 361.02(1): chs. SPS 361 to 366 "apply to all public buildings and places of employment". SPS 362 modifies the IBC (e.g. 362.1011 "Stairways", 362.1015 "Guards": "more than 30 inches"); the IBC text itself was not reviewed.

**City guidance:** "Missing handrail from stairs with more than three steps"; guardrails above 24 inches. This matches SPS
321.04(3)(a); it doesn't match SPS 362.1015's 30-inch guard threshold for commercial-code buildings.

**Unresolved (why not ready):**
1. §27.06(4) cross-reference (rooms below grade, not egress): still unresolved; not guessed.
2. **New:** §27.04(2)(d) cites "SPS 321.04(2)", but in the current SPS 321.04, sub. (2) is "Details" (dimensions);
   handrails and guards are in **sub. (3)**. Possibly outdated; not interpreted.
3. Which state code applies depends on building type and age (UDC for 1-2 family dwellings begun on or after June 1,
   1980; commercial code/IBC for "public buildings"). Whether Chapter 27's incorporation extends SPS 321.04 to older
   buildings is not determined.

**Proposed FixIt wording (now in `taxonomy.py`):** "These are separate conditions. Blocked exit: Chapter 27 requires direct
access to at least two unobstructed means of egress, with an exception FixIt has not been able to interpret. Unsafe
stairs: stairs must be safe to use and kept in proper repair. Missing handrail: Chapter 27 refers to Wisconsin's building
codes (SPS) for handrails; FixIt has not verified which of them applies to this building."

**Possible split for the reviewer:** §27.05(2)(i) (unsafe stairs) is clear on its face and could be reviewed alone; the
egress and handrail parts wait on items 1-3.

## 7. Smoke alarms (`SMOKE_DETECTOR_MISSING`): NEEDS CLARIFICATION

**Chapter 27 (reference only), §27.05(2)(w), p. 21:** "Smoke alarms shall be installed and maintained in accordance with
Sec. 34.907, MGO and with Wis. Admin. Code ch. SPS 362, Wis. Admin. Code § SPS 321.09 and Wis. Admin. Code § SPS 328.02
which are hereby incorporated by reference."

**Sources and exact text:**

| Source | URL | Key text | Scope / conditions |
|---|---|---|---|
| MGO 34.907 (*previous session, browser; not re-read*) | https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIVCH32--45_CH34FIPRCO_34.907FIALDESY | (1)(b)2. alarm "in each bedroom, in every sleeping area and within six (6) feet of each door leading to a bedroom or sleeping area of each unit and on each floor of the building"; (1)(c)4. tenant maintains/tests in-unit alarms and notifies the owner in writing; owner "shall have five days from receipt of such written notice to repair and replace" | "Buildings built before 2009"; owner-occupied single family homes excluded from (1)(b); exception (1)(e); internal refs "(2)(a)/(2)(b)/(3)(h)" don't match numbering |
| Wis. Stat. 101.145 | https://docs.legis.wisconsin.gov/statutes/statutes/101/I/145 | (4) "a functional smoke detector in the basement and at the head of any stairway on each floor level of the building and … either in each sleeping area of each unit or elsewhere in the unit within 6 feet of each sleeping area and not in a kitchen"; (3)(c) occupant maintains; owner, "within 5 days after receipt of that notice", after **written notice** by a non-owner occupant or an inspecting officer | "Residential building" = "any public building which is used for sleeping or lodging purposes and includes any apartment house …" (1)(a). **New:** 101.01(12) "public building" includes use "by 3 or more tenants" |
| Wis. Stat. 101.645 | https://docs.legis.wisconsin.gov/statutes/statutes/101/II/645 | (3) "a functional smoke detector in the basement of the dwelling and on each floor level except the attic or storage area of each dwelling unit"; occupant maintains; owner 5 days after written notice | "Dwelling" = building with 1 or 2 dwelling units (101.61(1)). No construction-date limit in the statute |
| SPS 328.03 | https://docs.legis.wisconsin.gov/code/admin_code/sps/safety_and_buildings_and_environment/326_360/328 | "Smoke detectors shall be installed and maintained in accordance with s. 101.645 (3), Stats., in a dwelling, for which initial construction commenced before June 1, 1980." | 1-2 family dwellings (328.02) |
| SPS 321.09 | https://docs.legis.wisconsin.gov/code/admin_code/sps/safety_and_buildings_and_environment/320_325/321 | (1)(a) "An alarm shall be installed inside each sleeping room."; (1)(b) outside sleeping rooms "within 21 feet of the centerline of the door opening"; (2)(a) hard-wired and interconnected | UDC: 1-2 family dwellings begun on or after June 1, 1980 |
| SPS 362.0907 / IBC 907 | (SPS 362 index) | Informational notes only; IBC text not reviewed | Commercial code buildings |
| *City guidance* (Fire Dept.) | https://www.cityofmadison.com/fire/your-safety/smoke-alarms/tenant-owners-responsibilities | "The owner has five days from receipt of notice to repair or replace the inoperable alarm(s)."; "maximum fine of $187 for the first violation"; battery replaced "each time the lease is renewed or once a year" | Undated; cites "MGO 34.907(2)(a)" (numbering mismatch) |

**Overstatements corrected (on this branch, not deployed):**
- "Working smoke detectors are required in rental units" → requirement depends on the building; FixIt hasn't verified
  which rule applies.
- Remedy "bedrooms and hallways outside sleeping areas" matched **no** source → "wherever the applicable rules require them".
- Tour question "working smoke detector in each bedroom and hallway, and the CO alarm" → asks where the alarms are and
  about the building facts.

**Proposed FixIt wording (now in `taxonomy.py`):** "Madison's smoke alarm ordinance (MGO 34.907) and Wisconsin law require
smoke alarms in many rental buildings. Which rule applies, and where alarms must be, depends on the building (for example
its age and number of units); FixIt has not verified which rule applies here. These rules generally make the tenant
responsible for testing alarms inside the unit and for telling the owner in writing when one stops working. A photo cannot
show whether an alarm works, or that no alarm exists elsewhere. General safety information: a missing, covered or disabled
alarm is a fire-safety risk."

**Unresolved:** governing rule when several apply (not chosen); **new:** §27.05(2)(w) incorporates "SPS 328.02", now the
*Scope* section (smoke detectors moved to 328.03 in 2011); MGO 34.907 not re-read this session; IBC 907 not reviewed;
City battery-replacement wording ("once a year") differs from the ordinance as previously read ("as recommended by the
manufacturer, whichever … is shorter").

**Five-day written-notice deadline (stays DISABLED):** every source read gives the owner 5 days after **written** notice,
but the trigger differs: 101.145/101.645: notice that a detector "is not functional", from a non-owner occupant or an
inspecting officer; MGO 34.907: tenant's written notice that an alarm "becomes inoperable". Whether the deadline can be
shown for a given building still depends on which source applies. `LEGAL_DEADLINE_DISPLAY_ENABLED = False` is unchanged.

## 8. Carbon monoxide alarms (`CO_DETECTOR_MISSING`): NEEDS CLARIFICATION

**Chapter 27:** no provision (0 hits for "carbon"/"monoxide"). Madison: CO only via MGO 29.22's adoption of SPS 328
(previous session); the rent-abatement row "29.19" doesn't match the current code (unresolved).

| Source | URL | Key text | Scope / conditions |
|---|---|---|---|
| Wis. Stat. 101.149 | https://docs.legis.wisconsin.gov/statutes/statutes/101/I/149 | (2)(ag) "Carbon monoxide detectors shall be provided in units that contain a fuel-burning appliance."; also (aL) fuel-burning forced-air furnace, (ap) fuel-burning appliances outside units, (at) attached private garages, each with exceptions; (2)(ax)1. "In units, outside of each separate sleeping area in the immediate vicinity of the sleeping rooms."; (ax)2. in a sleeping room with a fuel-burning appliance; (3)(a) **owner** "shall reasonably maintain"; (3)(b) after occupant's written notice that a detector "is not functional or has been removed by a person other than the occupant", owner "shall repair or replace … within 5 days" | "Residential building" = tourist rooming house, B&B, or public building used for sleeping or lodging (1)(b); 101.01(12) "3 or more tenants"; (5) exception: all fuel-burning appliances sealed-combustion under warranty |
| Wis. Stat. 101.647 | https://docs.legis.wisconsin.gov/statutes/statutes/101/II/647 | (3)(a) "a functional carbon monoxide detector in the basement of the dwelling and on each floor level except the attic, garage, or storage area of each dwelling unit"; occupant maintains; "does not apply to the owner of a dwelling that has no attached garage, no fireplace, and no fuel-burning appliance"; (3)(b) owner 5 days after written notice | 1-2 unit dwellings; (1)(am) excludes tourist rooming houses; (3)(am) hard-wiring for permits on or after Feb. 1, 2011 |
| SPS 328.04 | (ch. SPS 328 link above) | CO detectors per 101.647(2), (3)(a)-(b), (6) "in a dwelling, for which initial construction commenced before June 1, 1980" | 1-2 family |
| SPS 321.097 | (ch. SPS 321 link above) | per 101.647 "in one and 2-family dwellings, for which building permit applications were made or construction commenced on or after February 1, 2011" | UDC new construction |
| SPS 366.1010(2) | (SPS 366) | buildings **changed to** include a residential building: CO alarms "in accordance with IBC section 915" | Change of occupancy only |
| *City guidance* | Common Code Violations | "on every floor of every unit in one and two dwelling units"; "within 15 feet of bedroom doors of any unit with a fuel burning appliance" | "15 feet" appears in no statute read |

**Overstatement corrected:** "generally required near sleeping areas when there are fuel-burning appliances" omitted the
furnace/garage/outside-appliance triggers and is wrong for 1-2 unit dwellings. New wording: "Chapter 27 does not address
carbon monoxide alarms. Wisconsin law requires them in many homes and apartment buildings, but whether and where depends on
the building: its number of units, and whether it has fuel-burning appliances, a fuel-burning furnace, a fireplace or an
attached garage. FixIt has not verified which rule applies here, and a photo cannot show whether one is required."

**Unresolved:** FixIt's citation model holds only MGO Chapter 27 sections; showing state statutes as "possibly relevant" would
need a design decision. A 1-2 unit building with 3+ tenants may also be a "public building" (101.01(12)); FixIt asks about
units, not tenants, and does not evaluate this (the prototype now says so). **New:** the statute page's note
"See also ss. SPS 321.095" points to automatic sprinklers; CO is SPS 321.097.

## 9. Mold (`WATER_DAMAGE_MOLD`, mold aspect): NO VERIFIED SOURCE

**Searched:** Chapter 27 (0 hits for "mold"/"mildew"/"damp"); Wis. Stat. 704.07 (no mold text); ATCP 134.04 (no mold text
in the sections read); DHS (previous session): "dampness and mold are typically not written into local housing
ordinances".

**General duties that may be relevant (statute/ordinance text):** Wis. Stat. 704.07(2)(a)1. "Keep in a reasonable state of
repair portions of the premises over which the landlord maintains control."; 3. "Make all necessary structural repairs.";
5. "For a residential tenancy, comply with any local housing code applicable to the premises."; §27.05(2)(g)1./2. (see 5).
704.07(4) (untenantability) covers casualty damage, "any condition hazardous to health", or "a substantial violation
of sub. (2) materially affecting the health or safety of the tenant"; whether a given mold condition qualifies is not
something FixIt can decide.

**City guidance:** "Building Inspection does not test for mold." "We can require repairs when water damage is present."
"We can require certain mold and mildew clean up." Public Health: "If you rent, talk to your landlord. If they won't help,
call us at 608-242-6515." MGO 32.04(4)(d) (rent abatement) files mold under §27.05(2)(g)1.: that's the City's abatement
classification, not a Chapter 27 mold rule.

**Proposed FixIt wording (now in `taxonomy.py`):** keeps "Chapter 27 does not mention mold, and FixIt has not verified any
mold-specific legal requirement." and adds "City Building Inspection says it does not test for mold, but can require
repairs when water damage is present." Remedy: "If you suspect mold, ask for it to be checked and cleaned up" (was "have
any suspected mold assessed", which read like a requirement).

---

## Detection behavior: findings (no change made; your decision)

- The vision prompt still lists "no detector in bedroom or hallway" (smoke) and "no carbon monoxide alarm near bedrooms
  in a unit with fuel-burning appliances" (CO) as visual cues. A single photo can't show that an alarm is missing from the
  unit, or whether the unit has fuel-burning appliances. One cached demo output says "Bedroom ceiling visible with no smoke
  detector in frame". **Proposal:** limit cues to visibly covered, removed or hanging alarms. Not changed, because it
  alters live detection (priority 2) and the demo.
- Pests: the City doesn't accept photos as proof. FixIt now says so; the evidence packet is still useful for the tenant's
  own records and the landlord letter.

## What was changed on `ch27-review` (local, not deployed)

| Commit | Change |
|---|---|
| `87df616` | Wording in `taxonomy.py` (smoke, CO, electrical, water/mold, pests, locks, exits); tour question in `letters.py`; alarm prototype surfaces 101.01(12) without evaluating it; Scan progress "Looking for possible issues…"; 5 new tests |
| `eb99af3` | Four new source discrepancies recorded in `ch27_proposed_mappings.json` → `CH27_REVIEW.md` (additions only) |

Not touched: the three approved categories and their seed rows; `code_sections_verified.json`; reviewer fields in
`eval/code_review.csv`; `LEGAL_DEADLINE_DISPLAY_ENABLED`; Databricks; the deployment.

## Decisions for the reviewer

1. **Approve or not, citation by citation** (READY rows): locks §27.05(2)(h)/(h)3./(h)4. (+(h)6. supporting); windows
   §27.05(2)(h)/§27.04(2)(f)/§27.07(2)(c); pests §27.07(2)(d)+§27.03; electrical §27.04(2)(g); water damage
   §27.05(2)(g)1./(g)2. Approval would mean filling `approved_section_ids` and the reviewer name in `eval/code_review.csv` for
   those rows only, then `code_parse.py approve` (dry run first), then `--apply` and a redeploy, each step separately
   authorized.
2. Exits: approve §27.05(2)(i) alone for unsafe stairs, or keep the whole category on hold.
3. Water damage: whether to propose §27.05(2)(g)1.'s "waterproof … spaces subject to moisture" sentence and/or §27.05(2)(k).
4. Smoke/CO: whether FixIt may show **state statutes** (not only MGO) as "possibly relevant" sources, which would need a
   small design change; and whether to keep the five-day deadline disabled (recommended until the governing source can be
   established for a given building).
5. Vision cues for smoke/CO absence (see "Detection behavior").
6. Whether to ask City Building Inspection (608-266-4551) about: the §27.06(4) reference, the "SPS 321.04(2)" and
   "SPS 328.02" references, and the meaning of "single-family dwelling" in §27.07(2)(d).
