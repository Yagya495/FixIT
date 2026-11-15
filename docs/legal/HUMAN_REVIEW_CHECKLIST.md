# Human review checklist: remaining Chapter 27 citations (ONE consolidated list)

> **Prepared 2026-11-14. Nothing here is approved.** The reviewer fills the boxes. No reviewer name is entered by FixIt
> or its assistant. The three approved mappings (plumbing §27.05(2)(j), heat §27.04(2)(h), interior surfaces
> §27.05(2)(g)1.) are not part of this list and stay unchanged. FixIt is not a lawyer; approval means "the citation and
> quoted text were checked against the official source", not that a photo shows a violation.

**Official sources**
- MGO Chapter 27 (Municode, version Sep 1, 2026): https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO
  (repo copy: `docs/legal/Madison_Chapter_27.pdf`; every excerpt below was re-checked word for word against it by
  `scripts/ch27_review_sheet.py --pdf-text`. Page numbers refer to that PDF.)
- Wisconsin Statutes ch. 101: https://docs.legis.wisconsin.gov/statutes/statutes/101 (2023-24, updated through 2025 Wis. Act 247)

**How to check each item:** open the Municode link, find the section, compare the excerpt word for word, and confirm the
subsection label (the PDF text layer drops paragraph numerals such as "3."; labels come from the repo's parse and
cross-references). Then tick one box.

**After the decisions (each step separately authorized):** fill `approved_section_ids` and the reviewer fields in
`eval/code_review.csv` for the approved rows only → `scripts/code_parse.py approve` (dry run) → `--apply` → data sync →
redeploy. Conditional items (Part B) and state law (Part C) can't go through that path yet; they need a small reviewed
code change first.

---

## Part A: the five provisional category mappings

### A1. Broken locks (`BROKEN_LOCK`): §27.05(2)(h), (h)3., (h)4.; (h)6. as a supporting reference (p. 15)
| # | Section | Exact excerpt |
|---|---|---|
| A1.1 | §27.05(2)(h) | "All door and window hardware shall be installed and maintained in proper working condition." |
| A1.2 | §27.05(2)(h) (condition) | "Except as provided in Paragraph 9. below, the following shall apply in dwelling units all or a portion thereof which are rented:" |
| A1.3 | §27.05(2)(h)3. | "All doors into each dwelling unit shall have a keyed deadbolt lock with a minimum one (1) inch throw, which is openable with a key on the exterior side of the door and a knob on the interior side of the door." / "The strike plate shall be held in place by 2½ inch screws." / "Sliding doors shall have an approved secondary locking device." |
| A1.4 | §27.05(2)(h)4. | "All basement, first, and second story windows and all other windows accessible by balconies, fire escapes, trees or other existing means shall be provided with sash fasteners." |
| A1.5 | §27.05(2)(h)6. (supporting) | "Alternative locking devices to equally resist illegal entry may be substituted with the approval of the Madison Building Inspection Division" |

**Limitations:** (h)1.-6. apply only to rented units; Paragraph 9. (bed and breakfasts), (h)7. (lodging rooms/houses)
and (h)8. (cooperatives) have their own rules. The window rule depends on story and accessibility. An alternative device
counts only with Building Inspection approval. A photo can't show whether the unit is rented or whether a device was approved.

**Proposed FixIt wording (already in `taxonomy.py`):** "Door and window hardware must be kept in proper working condition.
In rented units, every door into the unit needs a keyed deadbolt with at least a 1-inch throw, and basement, first- and
second-story windows (and any window reachable from a balcony, fire escape or tree) need sash fasteners. Building
Inspection can approve equivalent alternative locking devices. Different rules apply to lodging rooms, cooperatives and
bed and breakfasts."

- [ ] Approve A1.1-A1.4 · [ ] Approve A1.5 as supporting reference · [ ] Reject · [ ] Change: ________
- Wording: [ ] OK · [ ] Change: ________

### A2. Windows and screens (`BROKEN_WINDOW`): §27.05(2)(h), §27.04(2)(f), §27.07(2)(c)
| # | Section (page) | Exact excerpt |
|---|---|---|
| A2.1 | §27.05(2)(h) (p. 15) | "Every window, exterior door, interior door, and basement hatchway shall be reasonably weathertight, watertight, and rodentproof and kept in proper repair." |
| A2.2 | §27.04(2)(f) (p. 7) | "All doors required for ventilation and all windows shall be protected with insect screen equivalent to not less than sixteen (16) wire mesh installed to prevent the entrance of flies, mosquitoes and other insects, annually during May before June 1 and maintained until storm windows are installed in autumn." |
| A2.3 | §27.04(2)(f) (p. 7) | "All exterior doors and windows shall have storm windows or storm doors installed or maintained to prevent excessive drafts and heat loss no earlier than October 15, but no later than November 15 annually." |
| A2.4 | §27.07(2)(c) (p. 30) | "Every owner of a residential building shall be responsible for hanging, installation, and maintenance of all screens and double or storm doors and windows whenever the same are required under the provisions of the Madison General Ordinances." |

**Limitations:** Chapter 27 never mentions glass; a cracked pane falls under "proper repair"/"weathertight" only by
interpretation. Screens and storm windows are seasonal. City guidance uses different dates (storm windows Nov 15-Apr 30,
screens Jun 1-Oct 15); FixIt follows the ordinance.

**Proposed FixIt wording (in `taxonomy.py`):** "Windows must be reasonably weathertight and watertight and kept in proper
repair (Chapter 27 does not specifically mention cracked glass). Insect screens must be installed each year by June 1 and
kept until storm windows go in; storm windows or doors go in between October 15 and November 15. The owner is responsible
for screens and storm windows."

- [ ] Approve A2.1 · [ ] Approve A2.2-A2.4 (screens/storm windows only) · [ ] Reject · [ ] Change: ________
- Wording: [ ] OK · [ ] Change: ________

### A3. Pest evidence (`PEST_EVIDENCE`): §27.07(2)(d) + §27.03 (pp. 30, 3)
| # | Section | Exact excerpt |
|---|---|---|
| A3.1 | §27.07(2)(d) | "Every occupant of a single-family dwelling shall be responsible for the extermination of any pests, vermin or rodents therein with the following exceptions: when the owner or operator has failed to clean the dwelling prior to occupancy or when the owner or operator is out of compliance with Madison General Ordinances Sec. 27.05(2)(g)2., extermination shall be the responsibility of the owner." |
| A3.2 | §27.07(2)(d) | "Whenever infestation exists in any residential dwelling other than a single-family dwelling, extermination shall be the responsibility of the owner." |
| A3.3 | §27.03 | "\"Infestation\" means the sustained presence of pests, vermin, or rodents." |

**Limitations:** "single-family dwelling" is **not defined** in §27.03 (open question for the City, see
`CITY_INQUIRY_DRAFT.md`). "Sustained presence" means one photo doesn't show an infestation. City Building Inspection
doesn't accept photos or videos as proof. No claim that rentals must be pest-free or that professional extermination is
required. Related state law (not mapped): Wis. Stat. 704.07(3)(a) (tenant-caused infestation).

**Proposed FixIt wording (in `taxonomy.py`):** "Signs like droppings or insects may point to an infestation, which Chapter
27 defines as the sustained presence of pests, vermin or rodents; one photo does not establish that. In any dwelling
other than a single-family dwelling, extermination is the owner's responsibility. In a single-family dwelling the
occupant is responsible, unless the owner failed to clean before move-in or the foundation, exterior walls, floors or
roof are not kept weathertight, watertight and rodentproof. City Building Inspection says it cannot accept photos or
videos as proof of pests: an inspector must see the problem."

- [ ] Approve A3.1-A3.3 · [ ] Approve after the City answers the definition question · [ ] Reject · [ ] Change: ________
- Wording: [ ] OK · [ ] Change: ________

### A4. Electrical hazards (`EXPOSED_WIRING`): §27.04(2)(g) (p. 7)
| # | Section | Exact excerpt |
|---|---|---|
| A4.1 | §27.04(2)(g) | "Every dwelling unit and all public and common areas in multiple dwellings shall be supplied with electrical service, outlets, and fixtures which shall be properly installed, shall be maintained in good and safe working condition, and shall be connected to a source of electric power in a manner prescribed by the Wisconsin Electric Code." |

**Limitations:** a general safety and maintenance duty only. §27.04(2)(g)3. ("exposed abandoned wiring") is **not**
mapped (narrower). **No verified legal source names cover plates**; only City guidance lists them. The electrical code
(NEC/SPS 316) text wasn't reviewed.

**Proposed FixIt wording (in `taxonomy.py`):** "Electrical service, outlets and fixtures must be properly installed and
kept in good and safe working condition. Chapter 27 does not name cover plates, and FixIt has not verified a specific
legal requirement for them (the City's Common Code Violations page lists missing or damaged cover plates as a common
issue). General safety information, not a Chapter 27 requirement: exposed wiring and uncovered outlets can cause shocks
or fires."

- [ ] Approve A4.1 as a general obligation · [ ] Reject · [ ] Change: ________
- Wording: [ ] OK · [ ] Change: ________

### A5. Water damage (`WATER_DAMAGE_MOLD`, water aspect): §27.05(2)(g)1., (g)2. (p. 14)
| # | Section | Exact excerpt |
|---|---|---|
| A5.1 | §27.05(2)(g)1. | "Every interior floor, wall and ceiling including door and window assemblies shall be kept clean and in good repair, and shall be capable of affording privacy." |
| A5.2 | §27.05(2)(g)2. | "Every foundation, exterior wall, and floor and roof shall be reasonably weathertight, watertight and rodentproof and shall be kept in proper repair and shall be capable of affording privacy." |

**Limitations:** "potentially relevant" general maintenance provisions. A stain does not show an active leak, which
surface failed, a violation, or mold. Not plumbing (§27.05(2)(j) stays limited to fixtures and pipes). §27.05(2)(g)1. is
already approved for `DAMAGED_SURFACES`; approving it here is a separate mapping. Mold: no verified source (stays unmapped).

**Proposed FixIt wording (in `taxonomy.py`):** "Visible water damage can be a sign of a leak or moisture problem, but a
stain alone does not prove an active leak, a code violation, or mold. Chapter 27 requires interior surfaces to be kept in
good repair and the building to be reasonably weathertight and watertight. Chapter 27 does not mention mold, and FixIt
has not verified any mold-specific legal requirement. City Building Inspection says it does not test for mold, but can
require repairs when water damage is present."

- [ ] Approve A5.1 · [ ] Approve A5.2 · [ ] Reject · [ ] Change: ________
- Wording: [ ] OK · [ ] Change: ________

---

## Part B: conditional citations (never attached to a whole category)
Code: `app/backend/services/conditional_citations.py` (inactive). They apply only when a **photo** observation of the
finding matches the condition. Tenant reports and "verify in person" observations never trigger them.

### B1. Unsafe stairs: §27.05(2)(i) (p. 17), finding `BLOCKED_EGRESS`, id `STAIRS_UNSAFE`
> "Every inside and outside stair, every porch, platform, balcony, and every appurtenance thereto shall be so constructed
> as to be safe to use and capable of supporting the load that normal use may cause to be placed thereon, and shall be
> kept in proper condition and repair and shall present an attractive appearance."

- **Applies only when:** the photo shows visibly unsafe stairs, steps, a porch or a balcony (broken, loose, missing,
  sagging, rotted or cracked treads or structure).
- **Never when:** a blocked exit; a missing or loose handrail with no visible stair damage; a normal staircase.
- **Limitations:** the rest of the exits category (§27.04(2)(d)) stays on hold (the §27.06(4) and SPS 321.04(2)
  references). "Attractive appearance" is not something FixIt should cite or comment on.
- **Proposed wording:** "Chapter 27 requires stairs, porches, platforms and balconies to be safe to use and kept in proper
  condition and repair. The photo appears to show stair damage; an inspector must confirm it."

- [ ] Approve as a separate conditional citation · [ ] Keep on hold · [ ] Change: ________

### B2. Wet-area surfaces: §27.05(2)(g)1., second part (p. 14), finding `WATER_DAMAGE_MOLD`, id `WET_AREA_SURFACE`
> "A waterproof and hard surface shall be provided in spaces subject to moisture."

- **Applies only when:** water damage on a wall or surface in a wet area (shower, tub, sink or laundry area).
- **Never when:** ceiling or wall stains in rooms that aren't wet areas.
- **Limitations:** a photo can't show whether a surface is "waterproof and hard". "Spaces subject to moisture" isn't
  defined. The approved `DAMAGED_SURFACES` mapping quotes other sentences of (g)1. and is unaffected.
- **Proposed wording:** "In spaces subject to moisture, such as around a shower or tub, Chapter 27 requires a waterproof and
  hard surface. The photo shows possible water damage in such a space; it doesn't show the cause."

- [ ] Approve as conditional · [ ] Reject · [ ] Change: ________

### B3. Bathroom floors: §27.05(2)(k) (p. 17), finding `WATER_DAMAGE_MOLD`, id `BATHROOM_FLOOR`
> "Every water closet compartment floor surface and bathroom floor surface shall be properly constructed and maintained so
> as to be reasonably impervious to water and so as to permit such floor to be easily kept in clean and sanitary
> condition."

- **Applies only when:** water damage to a bathroom or toilet-room floor.
- **Never when:** walls, ceilings, or floors outside a bathroom or toilet room.
- **Limitations:** a photo can't show whether the floor is "reasonably impervious to water"; discoloration may be cosmetic.
- **Proposed wording:** "Chapter 27 requires bathroom and toilet-room floors to be maintained so they are reasonably
  impervious to water and easy to keep clean. The photo shows possible water damage to a bathroom floor."

- [ ] Approve as conditional · [ ] Reject · [ ] Change: ________

---

## Part C: "Possibly relevant state law" (smoke and CO; for information, never a finding)
Design: `STATE_LAW_DESIGN.md`. Code: `app/backend/services/state_law.py` (hard-disabled). Excerpts verified word for word
against docs.legis.wisconsin.gov on 2026-11-14. Never shown as verified, governing or violated; no deadline.

| # | Citation | Link | Excerpt |
|---|---|---|---|
| C1 | Wis. Stat. § 101.145(4) | https://docs.legis.wisconsin.gov/statutes/statutes/101/I/145 | "The owner of a residential building the initial construction of which is commenced before, on or after May 23, 1978, shall install and maintain a functional smoke detector in the basement and at the head of any stairway on each floor level of the building and shall install a functional smoke detector either in each sleeping area of each unit or elsewhere in the unit within 6 feet of each sleeping area and not in a kitchen." |
| C2 | Wis. Stat. § 101.645(3) | https://docs.legis.wisconsin.gov/statutes/statutes/101/II/645 | "The owner of a dwelling shall install a functional smoke detector in the basement of the dwelling and on each floor level except the attic or storage area of each dwelling unit." |
| C3 | Wis. Stat. § 101.149(2)(ax)1. | https://docs.legis.wisconsin.gov/statutes/statutes/101/I/149 | "In units, outside of each separate sleeping area in the immediate vicinity of the sleeping rooms." |
| C4 | Wis. Stat. § 101.647(3)(a) | https://docs.legis.wisconsin.gov/statutes/statutes/101/II/647 | "The owner of a dwelling shall install a functional carbon monoxide detector in the basement of the dwelling and on each floor level except the attic, garage, or storage area of each dwelling unit." |

**Limitations:** coverage depends on the number of units/tenants (101.01(12), 101.61(1)), fuel-burning appliances and an
attached garage, with exceptions (101.149(5)). MGO 34.907 (Madison's ordinance) wasn't re-read this session and is not in
this block. The relationship between MGO 34.907, §27.05(2)(w)'s SPS references and these statutes is unresolved.

- [ ] Approve showing C1-C4 as "Possibly relevant state law" with the design's labels · [ ] Reject · [ ] Change: ________
- Five-day deadline: stays disabled (no decision requested).

---

## Not in this checklist (still unresolved, no approval possible yet)
- Exits (§27.04(2)(d)): the §27.06(4) cross-reference and the "SPS 321.04(2)" handrail reference (see `CITY_INQUIRY_DRAFT.md`).
- Smoke (§27.05(2)(w)): reference only; cites "SPS 328.02" (now the Scope section; smoke alarms are in 328.03).
- CO: no Madison or Chapter 27 provision found.
- Mold: no mold-specific source. Cover plates: City guidance only.

Reviewer (name and date, filled by the reviewer only): ____________________
