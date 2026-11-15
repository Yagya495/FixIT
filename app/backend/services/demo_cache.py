"""Demo Mode cache (P0-13). JSON files under demo/cached_outputs/.

- get/put by (namespace, key). Vision keys are image SHA-256.
- Scripted fallbacks for the stage scenario when a live call fails and the input isn't cached.
"""
from __future__ import annotations

import json
from pathlib import Path

from .. import config


def _path(ns: str, key: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)[:120]
    return config.CACHE_DIR / ns / f"{safe}.json"


def get(ns: str, key: str):
    p = _path(ns, key)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            return None
    return None


def put(ns: str, key: str, value) -> None:
    p = _path(ns, key)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2, default=str))


# ---------------------------------------------------------------- scripted scenarios
# The staged corner used on stage: covered smoke detector, fake water stain, outlet without cover.
WALKTHROUGH_SCENARIO = [
    {"violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.86, "bbox": None,
     "evidence_note": "Ceiling smoke detector appears covered with a plastic bag", "severity_hint": "urgent"},
    {"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.81, "bbox": None,
     "evidence_note": "Brown ring-shaped water stain on ceiling near the wall", "severity_hint": "urgent"},
    {"violation_type": "EXPOSED_WIRING", "confidence": 0.77, "bbox": None,
     "evidence_note": "Wall outlet with no cover plate; wiring box exposed", "severity_hint": "urgent"},
]

LISTING_SCENARIO = [
    {"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.74, "bbox": None,
     "evidence_note": "Discoloration on ceiling consistent with a past leak", "severity_hint": "urgent"},
    # Not "no smoke detector in frame": a photo can't show an alarm is missing (vision.screen_detection drops that).
    {"violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.58, "bbox": None,
     "evidence_note": "Empty smoke alarm base plate on the bedroom ceiling", "severity_hint": "urgent",
     "alarm_observation": "removed_mount_visible"},
    {"violation_type": "DAMAGED_SURFACES", "confidence": 0.66, "bbox": None,
     "evidence_note": "Peeling paint along window trim", "severity_hint": "routine"},
]


def scripted_detections(mode: str, frame_index: int, n_frames: int) -> list[dict]:
    scenario = LISTING_SCENARIO if mode == "listing" else WALKTHROUGH_SCENARIO
    if mode == "listing":
        # Spread across the photo set: stain mid-set, bedroom later, paint near the end.
        targets = {max(0, n_frames // 2): 0, max(0, n_frames - 2): 1, max(0, n_frames - 1): 2}
        idx = targets.get(frame_index)
        if n_frames == 1:
            return [dict(d) for d in scenario]
        return [dict(scenario[idx])] if idx is not None else []
    if n_frames < len(scenario):
        return [dict(d) for d in scenario[frame_index::n_frames]]
    return [dict(scenario[frame_index])] if frame_index < len(scenario) else []


SCRIPTED_CALL = [
    ("landlord", "Hello, this is Isthmus Edge Management, who's calling?"),
    ("landlord", "Okay... yeah, I think I heard about the heat. What exactly is the problem?"),
    ("landlord", "Look, we're busy this week. I can probably get someone out there Thursday."),
    ("landlord", "Yes, Thursday. Fine."),
]
