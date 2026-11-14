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
        "default_severity": "urgent", "code_sections": ["CH27-SMOKE"],
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
        "visual_cues": "dripping pipes, water pooling, buckets under sinks, broken toilet or faucet",
        "default_severity": "urgent", "code_sections": ["CH27-PLUMBING"],
        "plain_explanation": "Plumbing fixtures must work properly and be free of leaks.",
        "remedy_request": "Repair the leak and any damaged plumbing fixtures.",
    },
    {
        "type_id": "DAMAGED_SURFACES", "name": "Holes, peeling paint, damaged flooring", "category": "STRUCTURAL",
        "visual_cues": "holes in drywall, peeling or flaking paint, torn carpet, lifted flooring, damaged stairs",
        "default_severity": "routine", "code_sections": ["CH27-SURFACES"],
        "plain_explanation": "Interior walls, ceilings and floors must be kept in good repair. Peeling paint in older buildings may involve lead.",
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
        "plain_explanation": "Rental units must have heating capable of keeping the unit at a minimum temperature during the heating season.",
        "remedy_request": "Restore working heat immediately.",
    },
]

BY_ID = {v["type_id"]: v for v in VIOLATION_TYPES}

PENDING = "Section number pending verification against parsed MGO Chapter 27"

SEED_CODE_SECTIONS: list[dict] = [
    {"section_id": "CH27-SMOKE", "title": "Smoke and carbon monoxide alarms",
     "text": "Dwelling units must have working smoke detectors in required locations, and carbon monoxide alarms where fuel-burning appliances are present."},
    {"section_id": "CH27-ELECTRICAL", "title": "Electrical systems, outlets and fixtures",
     "text": "Electrical outlets, switches, fixtures and wiring shall be maintained in safe working condition, properly installed and covered."},
    {"section_id": "CH27-MOISTURE", "title": "Dampness, leaks and mold",
     "text": "Dwellings shall be kept free of dampness, water leaks and conditions that support mold growth; sources of moisture shall be corrected."},
    {"section_id": "CH27-SURFACES", "title": "Interior walls, ceilings and floors",
     "text": "Interior walls, ceilings, floors and other surfaces shall be maintained free of holes, cracks, loose or peeling paint and in good repair."},
    {"section_id": "CH27-PESTS", "title": "Insect and rodent control",
     "text": "Dwellings shall be kept free of insects, rodents and other pests; the owner is responsible for extermination in multi-unit buildings."},
    {"section_id": "CH27-SECURITY", "title": "Locks on doors and windows",
     "text": "Entry doors to dwelling units shall have working locks; accessible openable windows shall have working locking devices."},
    {"section_id": "CH27-WINDOWS", "title": "Windows and screens",
     "text": "Windows shall be weathertight, glazed without cracks or holes, and screens provided and maintained during required months."},
    {"section_id": "CH27-PLUMBING", "title": "Plumbing fixtures",
     "text": "Plumbing fixtures shall be properly installed, maintained free of leaks and in good working order."},
    {"section_id": "CH27-EGRESS", "title": "Exits, stairways and handrails",
     "text": "Means of egress shall be kept unobstructed; stairways shall have handrails that are firmly fastened and maintained."},
    {"section_id": "CH27-HEAT", "title": "Heating facilities",
     "text": "Heating facilities shall be capable of maintaining required minimum interior temperatures in habitable rooms during the heating season."},
]
for s in SEED_CODE_SECTIONS:
    s.update({"source_doc": "seed (unverified)", "page": None, "url": None, "verified": 0})


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
