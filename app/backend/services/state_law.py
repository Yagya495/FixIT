"""'Possibly relevant state law' for smoke and CO alarm findings (DESIGN PROTOTYPE, DISABLED). Pure, no I/O.

User decision (2026-11-14): Wisconsin statutes may appear as clearly labeled "Possibly relevant state law", SEPARATE
from Madison ordinances; never as verified, automatically governing, or violated. The five-day written-notice deadline
stays disabled (alarm_rules.LEGAL_DEADLINE_DISPLAY_ENABLED). Design: docs/legal/STATE_LAW_DESIGN.md.

Excerpts were read word for word on docs.legis.wisconsin.gov on 2026-11-14 ("2023-24 Wisconsin Statutes updated
through 2025 Wis. Act 247 ... (Published 11-4-26)"). They have NOT been approved by FixIt's reviewer.
"""
from __future__ import annotations

# Hard-coded off (not an env var): showing state law in the app needs the reviewer's approval and a reviewed change.
STATE_LAW_DISPLAY_ENABLED = False

LABEL = "Possibly relevant state law"
VERSION = "Wis. Stats. 2023-24, updated through 2025 Wis. Act 247 (published 11-4-26); read 2026-11-14"
NOTES = (
    "Wisconsin statute, shown for information. Not reviewed or approved by FixIt's reviewer.",
    "Whether it covers this building depends on facts a photo can't show (number of units or tenants, fuel-burning "
    "appliances, attached garage). FixIt does not decide which rule governs.",
    "Not a finding that anything was violated. Only an inspector or a court can decide that.",
)
_BASE = "https://docs.legis.wisconsin.gov/statutes/statutes/101/"

SOURCES: dict[str, list[dict]] = {
    "SMOKE_DETECTOR_MISSING": [
        {"citation": "Wis. Stat. § 101.145(4)", "url": _BASE + "I/145",
         "scope": "\"Residential building\": a public building used for sleeping or lodging, including apartment houses "
                  "(101.145(1)(a)); a \"public building\" includes one used by 3 or more tenants (101.01(12)).",
         "excerpt": "The owner of a residential building the initial construction of which is commenced before, on or "
                    "after May 23, 1978, shall install and maintain a functional smoke detector in the basement and at "
                    "the head of any stairway on each floor level of the building and shall install a functional smoke "
                    "detector either in each sleeping area of each unit or elsewhere in the unit within 6 feet of each "
                    "sleeping area and not in a kitchen."},
        {"citation": "Wis. Stat. § 101.645(3)", "url": _BASE + "II/645",
         "scope": "\"Dwelling\": a building with 1 or 2 dwelling units (101.61(1)).",
         "excerpt": "The owner of a dwelling shall install a functional smoke detector in the basement of the dwelling "
                    "and on each floor level except the attic or storage area of each dwelling unit."},
    ],
    "CO_DETECTOR_MISSING": [
        {"citation": "Wis. Stat. § 101.149(2)(ax)1.", "url": _BASE + "I/149",
         "scope": "Residential buildings (tourist rooming houses, bed and breakfasts, public buildings used for sleeping "
                  "or lodging), only where 101.149(2)(ag)-(at) require detectors (fuel-burning appliance, fuel-burning "
                  "forced-air furnace, fuel-burning appliances outside the unit, attached garage), each with exceptions; "
                  "101.149(5) exempts buildings whose fuel-burning appliances are all sealed-combustion under warranty.",
         "excerpt": "In units, outside of each separate sleeping area in the immediate vicinity of the sleeping rooms."},
        {"citation": "Wis. Stat. § 101.647(3)(a)", "url": _BASE + "II/647",
         "scope": "Buildings with 1 or 2 dwelling units; not a dwelling with no attached garage, no fireplace and no "
                  "fuel-burning appliance.",
         "excerpt": "The owner of a dwelling shall install a functional carbon monoxide detector in the basement of the "
                    "dwelling and on each floor level except the attic, garage, or storage area of each dwelling unit."},
    ],
}


def payload(type_id: str) -> dict | None:
    """The block the UI/letters would show, or None (always None while the feature is disabled)."""
    if not STATE_LAW_DISPLAY_ENABLED or type_id not in SOURCES:
        return None
    return {"label": LABEL, "version": VERSION, "notes": list(NOTES), "governing_rule": None, "deadline": None,
            "sources": [{**s, "kind": "Wisconsin statute", "verified": False} for s in SOURCES[type_id]]}
