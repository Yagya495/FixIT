"""Conditional Chapter 27 citations (PROPOSED, INACTIVE). Pure logic, no I/O.

Some provisions are relevant only when the photographed condition AND its location make them relevant, so they must
never be attached to every finding of a category (user decisions, 2026-11-14):
  - §27.05(2)(i), stairs: only for visibly unsafe stairs, never for a blocked exit or a missing handrail by itself.
  - §27.05(2)(g)1., "A waterproof and hard surface shall be provided in spaces subject to moisture.": only for water
    damage on a surface in a wet area (shower, tub, sink, laundry).
  - §27.05(2)(k), bathroom floors "reasonably impervious to water": only for water damage on a bathroom/toilet floor.

None of these is approved. `active()` returns nothing until a human approval for that exact conditional citation exists
(`conditional` key in code_sections_verified.json, written only by a reviewed approval step that does not exist yet),
and nothing in the app calls it yet. Excerpts and conditions: docs/legal/ch27_proposed_mappings.json ("conditional").
"""
from __future__ import annotations

import re

_W = lambda *words: re.compile(r"\b(" + "|".join(words) + r")\b", re.I)  # noqa: E731

PROPOSALS: list[dict] = [
    {"id": "STAIRS_UNSAFE", "type_id": "BLOCKED_EGRESS", "section_id": "27.05(2)(i)",
     "applies_when": "the photo shows visibly unsafe stairs, steps, a porch or a balcony (broken, loose, missing, "
                     "sagging, rotted or cracked treads or structure)",
     "not_when": "a blocked exit, or a missing or loose handrail with no visible stair damage, or a normal staircase",
     "need_all": [_W("stairs?", "stairways?", "steps?", "treads?", "risers?", "porch", "balcony", "landing"),
                  _W("broken", "loose", "missing treads?", "missing steps?", "sagging", "rotted", "rotting", "cracked",
                     "damaged", "collapsed", "uneven", "splintered", "crumbling")]},
    {"id": "WET_AREA_SURFACE", "type_id": "WATER_DAMAGE_MOLD", "section_id": "27.05(2)(g)1.",
     "excerpt_note": "only the sentence 'A waterproof and hard surface shall be provided in spaces subject to moisture.'",
     "applies_when": "water damage on a wall or surface in a wet area (shower, tub, sink or laundry area)",
     "not_when": "ceiling or wall stains in rooms that are not wet areas",
     "need_all": [_W("shower", "tub", "bathtub", "sink", "backsplash", "laundry", "surround")]},
    {"id": "BATHROOM_FLOOR", "type_id": "WATER_DAMAGE_MOLD", "section_id": "27.05(2)(k)",
     "applies_when": "water damage to a bathroom or toilet-room floor",
     "not_when": "walls, ceilings, or floors outside a bathroom or toilet room",
     "need_all": [_W("floors?", "flooring", "subfloor", "tiles?"), _W("bathroom", "toilet", "water closet", "restroom")]},
]


def matching(type_id: str, observations: list[dict]) -> list[str]:
    """Conditional proposal ids whose condition is met by at least one PHOTO observation of this finding.

    Tenant reports and "verify in person" observations never trigger a conditional citation."""
    notes = [o.get("note") or "" for o in observations
             if o.get("evidence_id") and o.get("basis") in ("photo", "visible_alarm_condition")]
    return [p["id"] for p in PROPOSALS if p["type_id"] == type_id
            and any(all(rx.search(n) for rx in p["need_all"]) for n in notes)]


def active(type_id: str, observations: list[dict], approved_ids: set[str] | frozenset[str] = frozenset()) -> list[str]:
    """Section ids to show: matching AND individually approved. With no approvals (today) this is always empty."""
    by_id = {p["id"]: p for p in PROPOSALS}
    return [by_id[i]["section_id"] for i in matching(type_id, observations) if i in approved_ids]
