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
        "plain_explanation": "Working smoke detectors are required in rental units. A missing, covered, or disabled detector is a fire-safety risk.",
        "remedy_request": "Install or replace a working smoke detector in each required location (bedrooms and hallways outside sleeping areas) and test it.",
    },
    {
        "type_id": "CO_DETECTOR_MISSING", "name": "Missing CO detector near sleeping area", "category": "SMOKE_CO",
        "visual_cues": "no carbon monoxide alarm near bedrooms in a unit with fuel-burning appliances",
        "default_severity": "urgent", "code_sections": ["PENDING-CO"],
        "plain_explanation": "Carbon monoxide alarms are generally required near sleeping areas when there are fuel-burning appliances.",
        "remedy_request": "Install a working carbon monoxide alarm near each sleeping area.",
    },
    {
        "type_id": "EXPOSED_WIRING", "name": "Exposed wiring / missing outlet or switch cover", "category": "ELECTRICAL",
        "visual_cues": "outlet or switch without cover plate, bare or taped wires, dangling fixtures, scorch marks",
        "default_severity": "urgent", "code_sections": ["CH27-ELECTRICAL"],
        "plain_explanation": "Electrical outlets, switches and wiring must be safe and covered. Exposed wiring can cause shocks or fires.",
        "remedy_request": "Have a qualified electrician install cover plates and repair or enclose any exposed wiring.",
    },
    {
        "type_id": "WATER_DAMAGE_MOLD", "name": "Water stains / visible mold", "category": "MOLD_MOISTURE",
        "visual_cues": "brown/yellow ceiling or wall stains, dark spotted growth, bubbling or peeling paint near water, damp areas",
        "default_severity": "urgent", "code_sections": ["CH27-MOISTURE", "CH27-SURFACES"],
        "plain_explanation": "Water stains and mold suggest a leak or moisture problem. Rental units must be kept free of dampness and mold growth.",
        "remedy_request": "Find and fix the source of the moisture, then professionally remove the mold and repair damaged surfaces.",
    },
    {
        "type_id": "PEST_EVIDENCE", "name": "Droppings / insects / pest damage", "category": "PESTS",
        "visual_cues": "droppings, dead insects, gnaw marks, traps, holes at baseboards",
        "default_severity": "urgent", "code_sections": ["CH27-PESTS"],
        "plain_explanation": "Rental units must be kept free of insects and rodents. Signs of pests usually mean the building needs professional extermination.",
        "remedy_request": "Arrange professional pest control and seal any entry points.",
    },
    {
        "type_id": "BROKEN_LOCK", "name": "Broken/missing entry or window lock", "category": "SECURITY",
        "visual_cues": "missing deadbolt, broken latch, damaged strike plate, window without lock",
        "default_severity": "urgent", "code_sections": ["CH27-SECURITY"],
        "plain_explanation": "Entry doors and accessible windows must lock securely.",
        "remedy_request": "Repair or replace the broken lock(s) so all entry doors and accessible windows lock securely.",
    },
    {
        "type_id": "BROKEN_WINDOW", "name": "Broken/cracked window or screen", "category": "STRUCTURAL",
        "visual_cues": "cracked or shattered glass, missing or torn screens, boarded window",
        "default_severity": "routine", "code_sections": ["CH27-WINDOWS"],
        "plain_explanation": "Windows must be weathertight and in good repair; screens are typically required in warm months.",
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
        "type_id": "BLOCKED_EGRESS", "name": "Blocked exit / missing handrail", "category": "EGRESS",
        "visual_cues": "exit door blocked by items, stairs with no handrail, painted-shut egress window",
        "default_severity": "urgent", "code_sections": ["CH27-EGRESS"],
        "plain_explanation": "Exits must be unobstructed, and stairways generally need secure handrails.",
        "remedy_request": "Clear the exit path and install or repair the handrail.",
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
     "text": "Dwellings shall be kept free of insects, rodents and other pests; the owner is responsible for extermination in multi-unit buildings."},
    {"section_id": "CH27-SECURITY", "title": "Locks on doors and windows",
     "text": "Entry doors to dwelling units shall have working locks; accessible openable windows shall have working locking devices."},
    {"section_id": "CH27-WINDOWS", "title": "Windows and screens",
     "text": "Windows shall be reasonably weathertight and watertight and kept in proper repair; insect screens are required seasonally (installed by June 1 and kept until storm windows go in)."},
    {"section_id": "CH27-PLUMBING", "title": "Plumbing fixtures",
     "text": "Plumbing fixtures and water and waste pipes shall be properly installed and maintained in good working condition, free from defects, leaks and obstructions."},
    {"section_id": "CH27-EGRESS", "title": "Exits, stairways and handrails",
     "text": "Means of egress shall be kept unobstructed; stairways shall have handrails that are firmly fastened and maintained."},
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
