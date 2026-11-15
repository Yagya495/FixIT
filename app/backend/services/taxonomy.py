"""Violation taxonomy (P0-2) and seed code sections.

IMPORTANT: Section numbers are NOT guessed. Seed code sections use placeholder ids (`CH27-*`) with
verified=False. notebooks/10_parse_code.sql parses the real MGO Chapter 27 PDF, and
notebooks/20_violation_taxonomy.sql remaps `code_sections` to real section ids from the parsed text.
"""
from __future__ import annotations

from datetime import date

SEVERITIES = ("routine", "urgent", "emergency")
CATEGORIES = (
    "HEAT", "SMOKE_CO", "ELECTRICAL", "MOLD_MOISTURE", "PESTS",
    "SECURITY", "PLUMBING", "STRUCTURAL", "EGRESS", "SANITATION",
)

VIOLATION_TYPES: list[dict] = [
    {
        "type_id": "SMOKE_DETECTOR_MISSING", "name": "Missing/disabled smoke detector", "category": "SMOKE_CO",
        "visual_cues": "empty ceiling mount plate, detector covered with bag/tape, detector hanging by wires, no detector in bedroom or hallway",
        "default_severity": "urgent", "code_sections": ["CH27-SMOKE"],
        "plain_explanation": "Madison's smoke alarm ordinance (MGO 34.907) and Wisconsin law require smoke alarms in many rental buildings. Which rule applies, and where alarms must be, depends on the building (for example its age and number of units); FixIt has not verified which rule applies here. These rules generally make the tenant responsible for testing alarms inside the unit and for telling the owner in writing when one stops working. A photo cannot show whether an alarm works, or that no alarm exists elsewhere. General safety information: a missing, covered or disabled alarm is a fire-safety risk.",
        "remedy_request": "Install, replace or repair working smoke alarms wherever the applicable rules require them, and test them.",
    },
    {
        "type_id": "CO_DETECTOR_MISSING", "name": "Missing CO detector near sleeping area", "category": "SMOKE_CO",
        "visual_cues": "no carbon monoxide alarm near bedrooms in a unit with fuel-burning appliances",
        "default_severity": "urgent", "code_sections": ["PENDING-CO"],
        "plain_explanation": "Chapter 27 does not address carbon monoxide alarms. Wisconsin law requires them in many homes and apartment buildings, but whether and where depends on the building: its number of units, and whether it has fuel-burning appliances, a fuel-burning furnace, a fireplace or an attached garage. FixIt has not verified which rule applies here, and a photo cannot show whether one is required.",
        "remedy_request": "Install a working carbon monoxide alarm wherever the applicable rule requires one.",
    },
    {
        "type_id": "EXPOSED_WIRING", "name": "Exposed wiring / missing outlet or switch cover", "category": "ELECTRICAL",
        "visual_cues": "outlet or switch without cover plate, bare or taped wires, dangling fixtures, scorch marks",
        "default_severity": "urgent", "code_sections": ["CH27-ELECTRICAL"],
        "plain_explanation": "Electrical service, outlets and fixtures must be properly installed and kept in good and safe working condition. Chapter 27 does not name cover plates, and FixIt has not verified a specific legal requirement for them (the City's Common Code Violations page lists missing or damaged cover plates as a common issue). General safety information, not a Chapter 27 requirement: exposed wiring and uncovered outlets can cause shocks or fires.",
        "remedy_request": "Have a qualified electrician install cover plates and repair or enclose any exposed wiring.",
    },
    {
        "type_id": "WATER_DAMAGE_MOLD", "name": "Water damage / suspected mold", "category": "MOLD_MOISTURE",
        "visual_cues": "visible water damage: brown/yellow ceiling or wall stains, bubbling or peeling paint near water, damp areas; suspected mold: dark spotted growth",
        "default_severity": "urgent", "code_sections": ["CH27-MOISTURE", "CH27-SURFACES"],
        "plain_explanation": "Visible water damage can be a sign of a leak or moisture problem, but a stain alone does not prove an active leak, a code violation, or mold. Chapter 27 requires interior surfaces to be kept in good repair and the building to be reasonably weathertight and watertight. Chapter 27 does not mention mold, and FixIt has not verified any mold-specific legal requirement. City Building Inspection says it does not test for mold, but can require repairs when water damage is present.",
        "remedy_request": "Find and fix the source of the water and repair the damaged surfaces. If you suspect mold, ask for it to be checked and cleaned up.",
    },
    {
        "type_id": "PEST_EVIDENCE", "name": "Droppings / insects / pest damage", "category": "PESTS",
        "visual_cues": "droppings, dead insects, gnaw marks, traps, holes at baseboards",
        "default_severity": "urgent", "code_sections": ["CH27-PESTS"],
        "plain_explanation": "Signs like droppings or insects may point to an infestation, which Chapter 27 defines as the sustained presence of pests, vermin or rodents; one photo does not establish that. In any dwelling other than a single-family dwelling, extermination is the owner's responsibility. In a single-family dwelling the occupant is responsible, unless the owner failed to clean before move-in or the foundation, exterior walls, floors or roof are not kept weathertight, watertight and rodentproof. City Building Inspection says it cannot accept photos or videos as proof of pests: an inspector must see the problem.",
        "remedy_request": "Arrange pest control and seal any entry points.",
    },
    {
        "type_id": "BROKEN_LOCK", "name": "Broken/missing entry or window lock", "category": "SECURITY",
        "visual_cues": "missing deadbolt, broken latch, damaged strike plate, window without lock",
        "default_severity": "urgent", "code_sections": ["CH27-SECURITY"],
        "plain_explanation": "Door and window hardware must be kept in proper working condition. In rented units, every door into the unit needs a keyed deadbolt with at least a 1-inch throw, and basement, first- and second-story windows (and any window reachable from a balcony, fire escape or tree) need sash fasteners. Building Inspection can approve equivalent alternative locking devices. Different rules apply to lodging rooms, cooperatives and bed and breakfasts.",
        "remedy_request": "Repair or replace the broken lock(s) so all entry doors and accessible windows lock securely.",
    },
    {
        "type_id": "BROKEN_WINDOW", "name": "Broken/cracked window or screen", "category": "STRUCTURAL",
        "visual_cues": "cracked or shattered glass, missing or torn screens, boarded window",
        "default_severity": "routine", "code_sections": ["CH27-WINDOWS"],
        "plain_explanation": "Windows must be reasonably weathertight and watertight and kept in proper repair (Chapter 27 does not specifically mention cracked glass). Insect screens must be installed each year by June 1 and kept until storm windows go in; storm windows or doors go in between October 15 and November 15. The owner is responsible for screens and storm windows.",
        "remedy_request": "Replace the broken glass and repair or replace damaged screens.",
    },
    {
        "type_id": "LEAK_PLUMBING", "name": "Active leak / damaged fixtures", "category": "PLUMBING",
        "visual_cues": "dripping pipes or faucets, water pooling under a sink or around a toilet, buckets under sinks, broken toilet or faucet",
        "default_severity": "urgent", "code_sections": ["CH27-PLUMBING"],
        "plain_explanation": "Plumbing fixtures and water and waste pipes must be properly installed and kept in good working condition, free from leaks. (Roof leaks and water stains with no visible plumbing source are a different category.)",
        "remedy_request": "Repair the leak and any damaged plumbing fixtures.",
    },
    {
        "type_id": "DAMAGED_SURFACES", "name": "Holes, peeling paint, damaged flooring", "category": "STRUCTURAL",
        "visual_cues": "holes in drywall, peeling or flaking paint, torn carpet, lifted flooring",
        "default_severity": "routine", "code_sections": ["CH27-SURFACES"],
        "plain_explanation": "Interior floors, walls and ceilings must be kept clean and in good repair, and surfaces must be free from serious cracking and peeling paint (whether cracking is serious is for an inspector to judge). General safety information, not a Chapter 27 requirement: peeling paint in older buildings may contain lead.",
        "remedy_request": "Repair the damaged walls, ceilings, or flooring and repaint where needed.",
    },
    {
        "type_id": "BLOCKED_EGRESS", "name": "Blocked exit / unsafe stairs / missing handrail", "category": "EGRESS",
        "visual_cues": "three separate conditions, flag only the one you actually see: (1) blocked exit: exit door or path blocked by items, painted-shut egress window; (2) unsafe stairs: broken, loose or missing treads, sagging or damaged steps; (3) missing handrail: stairs with no handrail or a loose one. A normal staircase in good condition is not an issue",
        "default_severity": "urgent", "code_sections": ["CH27-EGRESS"],
        "plain_explanation": "These are separate conditions. Blocked exit: Chapter 27 requires direct access to at least two unobstructed means of egress, with an exception FixIt has not been able to interpret. Unsafe stairs: stairs must be safe to use and kept in proper repair. Missing handrail: Chapter 27 refers to Wisconsin's building codes (SPS) for handrails; FixIt has not verified which of them applies to this building.",
        "remedy_request": "Depending on the condition: clear the exit path, repair the stairs, or install or repair the handrail.",
    },
    {
        "type_id": "NO_HEAT", "name": "No heat (user-reported / temp evidence)", "category": "HEAT",
        "visual_cues": "thermostat showing low temperature, space heaters in use, frost on interior windows",
        "default_severity": "emergency", "code_sections": ["CH27-HEAT"],
        "plain_explanation": "A minimum temperature of 67°F must be maintained in all habitable rooms, kitchens and bathrooms, and the heating system must be kept in safe, efficient condition. A tenant may keep their own room or apartment cooler as long as it does not affect the temperature in other living areas of the building. FixIt's follow-up reminder is not a legal deadline.",
        "remedy_request": "Restore working heat as soon as possible so all habitable rooms, kitchens and bathrooms stay at 67°F or warmer.",
    },
]

BY_ID = {v["type_id"]: v for v in VIOLATION_TYPES}

PENDING = "Section number pending verification against parsed MGO Chapter 27"

SEED_CODE_SECTIONS: list[dict] = [
    {"section_id": "CH27-SMOKE", "title": "Smoke alarms",
     "text": "Smoke alarms must be installed and maintained as required by the other codes Chapter 27 refers to (MGO 34.907 and Wisconsin SPS codes). FixIt has not yet verified those requirements."},
    {"section_id": "PENDING-CO", "title": "Carbon monoxide alarms",
     "text": "Chapter 27 does not address carbon monoxide alarms. FixIt has not yet verified which law applies."},
    {"section_id": "CH27-ELECTRICAL", "title": "Electrical systems, outlets and fixtures",
     "text": "Electrical service, outlets and fixtures shall be properly installed and maintained in good and safe working condition."},
    {"section_id": "CH27-MOISTURE", "title": "Water damage and watertightness",
     "text": "Interior surfaces shall be kept in good repair, and foundations, exterior walls, floors and roofs reasonably weathertight and watertight. Chapter 27 does not mention mold."},
    {"section_id": "CH27-SURFACES", "title": "Interior walls, ceilings and floors",
     "text": "Interior floors, walls and ceilings shall be kept clean and in good repair; surfaces shall be free from serious cracking, irregularities and peeling paint."},
    {"section_id": "CH27-PESTS", "title": "Insect and rodent control",
     "text": "Where an infestation (the sustained presence of pests, vermin or rodents) exists in a dwelling other than a single-family dwelling, the owner is responsible for extermination; different rules apply to single-family dwellings."},
    {"section_id": "CH27-SECURITY", "title": "Locks on doors and windows",
     "text": "Door and window hardware shall be kept in proper working condition; in rented units, doors into the unit need keyed deadbolts and lower-story or reachable windows need sash fasteners (approved alternatives allowed)."},
    {"section_id": "CH27-WINDOWS", "title": "Windows and screens",
     "text": "Windows shall be reasonably weathertight and watertight and kept in proper repair; insect screens are installed by June 1 and kept until storm windows go in (between October 15 and November 15)."},
    {"section_id": "CH27-PLUMBING", "title": "Plumbing fixtures",
     "text": "Plumbing fixtures and water and waste pipes shall be properly installed and maintained in good working condition, free from defects, leaks and obstructions."},
    {"section_id": "CH27-EGRESS", "title": "Exits, stairs and handrails",
     "text": "Each dwelling unit needs direct access to at least two unobstructed means of egress; stairs must be safe and kept in repair; handrail requirements come from the state SPS code (not yet verified by FixIt)."},
    {"section_id": "CH27-HEAT", "title": "Heating facilities",
     "text": "The heating system shall be kept in safe and efficient condition, and a minimum of 67°F shall be maintained in habitable rooms, kitchens and bathrooms. An occupant may keep their own unit cooler if it does not affect other habitable areas."},
]
for s in SEED_CODE_SECTIONS:
    s.update({"source_doc": "seed (unverified)", "page": None, "url": None, "verified": 0})


def verified_review() -> dict:
    """Human-approved Chapter 27 sections + type mapping written by `scripts/code_parse.py approve` (empty if none)."""
    import json
    from pathlib import Path

    p = Path(__file__).resolve().parents[1] / "code_sections_verified.json"
    if not p.exists():
        return {"mapping": {}, "sections": []}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {"mapping": data.get("mapping", {}), "sections": data.get("sections", [])}


def taxonomy_rows() -> list[dict]:
    """VIOLATION_TYPES with any human-approved section mapping applied (placeholders otherwise)."""
    mapping = verified_review()["mapping"]
    return [{**v, "code_sections": mapping.get(v["type_id"], v["code_sections"])} for v in VIOLATION_TYPES]


def code_section_rows() -> list[dict]:
    """Unverified seed summaries + human-approved official sections."""
    return [dict(s) for s in SEED_CODE_SECTIONS] + [{**s, "verified": 1} for s in verified_review()["sections"]]


def severity_for(type_id: str, on: date | None = None, live_or_sparking: bool = False) -> str:
    """Seasonal / contextual severity adjustments from the taxonomy table."""
    on = on or date.today()
    base = BY_ID.get(type_id, {}).get("default_severity", "routine")
    heating_season = on.month >= 10 or on.month <= 5
    if type_id == "NO_HEAT":
        return "emergency" if heating_season else "urgent"
    if type_id == "BROKEN_WINDOW" and (on.month >= 11 or on.month <= 3):
        return "urgent"
    if type_id == "EXPOSED_WIRING" and live_or_sparking:
        return "emergency"
    return base


EMERGENCY_GUIDANCE = (
    "This may be an emergency. If anyone is in immediate danger (fire, gas smell, sparking wires), call 911. "
    "Otherwise call City of Madison Building Inspection now at 608-266-4551."
)
