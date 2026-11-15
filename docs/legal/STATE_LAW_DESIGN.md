# Design: "Possibly relevant state law" for smoke and CO alarm findings (PROPOSED, DISABLED)

> Prepared 2026-11-14 at the user's request. Nothing here is active, approved or deployed. FixIt is not a lawyer and
> this is not legal advice.

## Goal
Smoke and CO findings currently cite nothing official: Chapter 27 only incorporates other codes for smoke alarms
(§27.05(2)(w)) and says nothing about CO. Wisconsin statutes are the clearest official sources, but whether one covers a
given building depends on facts FixIt usually doesn't have. The design shows them **for information**, clearly
separate from Madison ordinances, without claiming that they apply, that they govern, or that they were violated.

## Rules (user decisions, 2026-11-14)
1. Label: **"Possibly relevant state law"**. Always separate from "Possibly relevant code" (MGO).
2. Never "verified", never "applies", never "governing", never "violated" or "violation".
3. No deadline. The five-day written-notice deadline stays disabled (`alarm_rules.LEGAL_DEADLINE_DISPLAY_ENABLED`).
4. Building facts come only from the tenant (the existing smoke/CO card), never from photos or synthetic records.
5. Not shown for photo findings that only an in-person check could confirm, unless the tenant also reported the problem.
   This is a proposal for review; the prototype `payload()` doesn't yet take the finding's basis.

## Content (`app/backend/services/state_law.py`, hard-disabled)
| Finding | Citation | Excerpt (verbatim, read 2026-11-14) | Scope line shown |
|---|---|---|---|
| Smoke | Wis. Stat. § 101.145(4) | "…shall install and maintain a functional smoke detector in the basement and at the head of any stairway on each floor level of the building and shall install a functional smoke detector either in each sleeping area of each unit or elsewhere in the unit within 6 feet of each sleeping area and not in a kitchen." | Residential (public) buildings incl. apartment houses; "public building" includes use by 3 or more tenants (101.01(12)) |
| Smoke | Wis. Stat. § 101.645(3) | "The owner of a dwelling shall install a functional smoke detector in the basement of the dwelling and on each floor level except the attic or storage area of each dwelling unit." | Buildings with 1 or 2 dwelling units |
| CO | Wis. Stat. § 101.149(2)(ax)1. | "In units, outside of each separate sleeping area in the immediate vicinity of the sleeping rooms." | Only where (2)(ag)-(at) triggers apply, each with exceptions; sealed-combustion exception (5) |
| CO | Wis. Stat. § 101.647(3)(a) | "The owner of a dwelling shall install a functional carbon monoxide detector in the basement of the dwelling and on each floor level except the attic, garage, or storage area of each dwelling unit." | 1-2 unit buildings, except those with no attached garage, fireplace or fuel-burning appliance |

Source version: "2023-24 Wisconsin Statutes updated through 2025 Wis. Act 247 … (Published 11-4-26)". Each excerpt was
checked word for word against the official page text.

MGO 34.907 (Madison's smoke alarm ordinance) belongs in the **Madison** block, not this one. It isn't included because
its text couldn't be re-read this session (Municode blocks scripts) and it isn't approved.

## UI (proposed)
Under the finding's "Possibly relevant code" blocks, one gray box:

```
POSSIBLY RELEVANT STATE LAW · Wisconsin statute · not reviewed by FixIt's reviewer
Wis. Stat. § 101.645(3)  (buildings with 1 or 2 dwelling units)
"The owner of a dwelling shall install a functional smoke detector in the basement …"
Whether it covers this building depends on facts a photo can't show. FixIt doesn't decide which rule governs.
Not a finding that anything was violated.                                   Official text ↗
```

If the tenant filled in the smoke/CO card, the box can show that card's status for each source ("May apply",
"Outside the source's stated scope", …), worded exactly as the card shows it today (never "applies").

## Letters (proposed)
A separate line after the MGO line: `Possibly relevant state law (for information, not a finding): Wis. Stat. § …`.
No deadline language. The "final request" tone must not cite state law as a basis for a threat.

## Activation steps (each needs your approval)
1. Reviewer approves the statute excerpts and the wording above (they are not MGO, so they do not go through
   `code_parse.py approve`; record the approval in this file and in `FINAL_LEGAL_REVIEW.md`).
2. Code change: add the basis rule (item 5), render the box on `ViolationCard` and in letters, then flip
   `STATE_LAW_DISPLAY_ENABLED`. Tests in `test_legal_prep.py` already lock the label, `verified: false`, no governing
   rule and no deadline.
3. Redeploy (separately approved).
