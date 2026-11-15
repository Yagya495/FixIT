"""Vision pipeline (P0-3, P0-4): frame -> VLM -> validated detections -> dedup -> violations."""
from __future__ import annotations

import logging
import re
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

from .. import config, llm
from . import demo_cache
from .taxonomy import BY_ID, VIOLATION_TYPES

log = logging.getLogger("fixit.vision")


class Detection(BaseModel):
    violation_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: Optional[list[float]] = None
    evidence_note: str = ""
    severity_hint: Literal["routine", "urgent", "emergency"] = "routine"
    # Smoke/CO only: what is actually visible (see screen_detection). Anything else is ignored.
    alarm_observation: Optional[str] = None

    @field_validator("violation_type")
    @classmethod
    def known_type(cls, v: str) -> str:
        if v not in BY_ID:
            raise ValueError(f"unknown violation_type {v}")
        return v

    @field_validator("bbox")
    @classmethod
    def bbox_shape(cls, v):
        if v is not None and len(v) != 4:
            return None
        return v


class FrameResult(BaseModel):
    detections: list[Detection] = []
    scene: str = "other"


def _taxonomy_prompt() -> str:
    lines = [f'- {v["type_id"]}: {v["name"]}. Visual cues: {v["visual_cues"]}' for v in VIOLATION_TYPES if v["type_id"] != "NO_HEAT"]
    return "\n".join(lines)


SYSTEM_WALKTHROUGH = """You are a careful housing-code inspection assistant for Madison, WI rentals.
Look at the photo and report ONLY visible signs of these violation types:
{taxonomy}

Rules: only report what is visible; do not guess. Confidence reflects how sure you are it's that violation.
Smoke and carbon monoxide alarms (SMOKE_DETECTOR_MISSING, CO_DETECTOR_MISSING): report ONLY a visible problem with an
alarm or its mount, and set "alarm_observation" to one of: "covered_or_obstructed" (bag, tape, paint, cover over the
alarm), "damaged_or_hanging" (alarm visibly broken or hanging by its wires), "removed_mount_visible" (an empty base
plate or mounting bracket where an alarm was). NEVER report these types because no alarm appears in the photo: a photo
does not show the rest of the unit. You cannot tell from a photo whether an alarm works, so never claim it does or doesn't.
bbox is [x, y, w, h] as fractions of image size (0-1) if you can localize it, else null.
Reply with STRICT JSON only, no prose:
{{"detections":[{{"violation_type":"<TYPE_ID>","confidence":0.0,"bbox":null,"evidence_note":"short description","severity_hint":"routine|urgent|emergency","alarm_observation":null}}],
 "scene":"bedroom|kitchen|bathroom|hallway|exterior|other"}}
If nothing is visible, return {{"detections":[],"scene":"..."}}."""

SYSTEM_LISTING = SYSTEM_WALKTHROUGH.replace(
    "Look at the photo",
    "This is a MARKETING photo from a rental listing. Look closely for signs of problems landlords may not notice or "
    "mention (stains, covered or removed smoke alarms, damaged surfaces, exposed wiring, mold, pest evidence, "
    "broken windows or locks). Look at the photo",
)


def _parse(text: str) -> FrameResult:
    data = llm.extract_json(text)
    if isinstance(data, dict) and isinstance(data.get("detections"), list):
        # Open models sometimes invent a type id; drop that one detection instead of discarding the whole frame.
        kept = [d for d in data["detections"] if isinstance(d, dict) and d.get("violation_type") in BY_ID]
        if len(kept) != len(data["detections"]):
            log.info("vision: dropped %d detection(s) with unknown types", len(data["detections"]) - len(kept))
        data = {**data, "detections": kept}
    return FrameResult.model_validate(data)


def analyze_frame_live(image: bytes, mode: str, media_type: str = "image/jpeg") -> FrameResult:
    system = (SYSTEM_LISTING if mode == "listing" else SYSTEM_WALKTHROUGH).format(taxonomy=_taxonomy_prompt())
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": [{"type": "text", "text": "Analyze this photo."}, llm.image_part(image, media_type)]},
    ]
    reply = llm.chat(messages, endpoint=config.VISION_ENDPOINT, max_tokens=800, temperature=0.0)
    try:
        return _parse(reply)
    except (ValueError, ValidationError) as e:
        messages += [{"role": "assistant", "content": reply},
                     {"role": "user", "content": f"That was not valid JSON for the schema ({e}). Reply with fixed JSON only."}]
        reply = llm.chat(messages, endpoint=config.VISION_ENDPOINT, max_tokens=800, temperature=0.0)
        try:
            return _parse(reply)
        except (ValueError, ValidationError):
            return FrameResult()


def analyze_frame(image: bytes, sha256: str, mode: str, frame_index: int, n_frames: int,
                  media_type: str = "image/jpeg", alt_sha: str | None = None) -> tuple[FrameResult, str]:
    """Returns (result, source) where source ∈ live|cache|fallback|none.

    The cache is keyed by the sha of the photo file that /api/demo/warm analyzed. The browser re-encodes uploads,
    so it also sends the original file's sha (`alt_sha`), which is checked too."""
    cached = demo_cache.get("vision", f"{mode}-{sha256}")
    if cached is None and alt_sha:
        cached = demo_cache.get("vision", f"{mode}-{alt_sha}")
    if config.DEMO_MODE and cached is not None:
        # Cached demo inputs are served directly on stage: deterministic and instant.
        return FrameResult.model_validate(cached), "cache"
    try:
        res = analyze_frame_live(image, mode, media_type)
        return res, "live"
    except Exception as e:
        log.warning("vision live call failed: %s", e)
        if cached is not None:
            return FrameResult.model_validate(cached), "cache"
        if config.DEMO_MODE:
            dets = demo_cache.scripted_detections(mode, frame_index, n_frames)
            return FrameResult(detections=[Detection(**d) for d in dets]), "fallback"
        return FrameResult(), "none"


# ---------------------------------------------------------------- alarm screening (pure)
# A photo can show an alarm that is covered, damaged, hanging or removed from its mount. It cannot show that a unit has
# no alarm (the rest of the unit isn't in the frame) or whether an alarm works. Rules (user, 2026-11-14):
#   visible damage/obstruction                 -> finding, basis "visible_alarm_condition"
#   empty mount / opened battery compartment   -> basis "verify_in_person" (never shown as a certain finding)
#   "no alarm visible", "alarm present", other -> dropped (not a finding)
#   tenant-reported missing / not working      -> basis "tenant_report" (manual path, never screened out)
ALARM_TYPES = frozenset({"SMOKE_DETECTOR_MISSING", "CO_DETECTOR_MISSING"})
BASIS_PHOTO, BASIS_VISIBLE_ALARM = "photo", "visible_alarm_condition"
BASIS_VERIFY, BASIS_TENANT = "verify_in_person", "tenant_report"
BASIS_TEXT = {BASIS_PHOTO: "Seen in photo", BASIS_VISIBLE_ALARM: "Seen in photo",
              BASIS_VERIFY: "Needs an in-person check", BASIS_TENANT: "Reported by tenant"}
VERIFY_LABEL = "Possible issue — verify in person"

_OBS = {"covered_or_obstructed": (BASIS_VISIBLE_ALARM, "Alarm visibly covered or obstructed"),
        "damaged_or_hanging": (BASIS_VISIBLE_ALARM, "Alarm visibly damaged or hanging"),
        "removed_mount_visible": (BASIS_VERIFY, "Empty alarm mount or base plate visible")}
_ALARM = r"(smoke |co |carbon monoxide )?(detector|alarm)s?"
_NEG = re.compile(
    rf"\b(no {_ALARM}|without (a |an |any )?{_ALARM}|{_ALARM} (is |are )?(not|isn't|aren't) (visible|present|seen|installed)"
    rf"|not (visible )?in (the )?frame|none visible|no visible {_ALARM}|missing {_ALARM}|{_ALARM} (is |appears )?missing"
    rf"|absence of)", re.I)
_VISIBLE = re.compile(r"\b(cover(ed|ing)?|bag(ged)?|taped?|wrapped|obstruct\w*|painted over|hanging|dangling|pulled down"
                      r"|ripped|smashed|broken|cracked|damaged|melted|crushed)\b", re.I)
_VERIFY = re.compile(r"\b(base ?plate|mount(ing)?( plate| bracket)?|bracket|battery (compartment|door) (is )?(open|empty)"
                     r"|open battery|battery removed|disconnected)\b", re.I)


def classify_alarm_note(note: str) -> str | None:
    """Basis implied by an alarm note, or None if it shows no visible alarm problem (pure, tested).

    Negations ("no detector", "not in frame") override damage words, so "ceiling not covered, no alarm" is dropped.
    An empty mount or opened battery compartment needs an in-person check; it never proves anything by itself."""
    n = note or ""
    if _NEG.search(n):
        return BASIS_VERIFY if _VERIFY.search(n) else None
    if _VISIBLE.search(n):
        return BASIS_VISIBLE_ALARM
    return BASIS_VERIFY if _VERIFY.search(n) else None


def screen_detection(det: dict) -> dict | None:
    """Apply the alarm rules to one PHOTO detection. Returns it with `basis` (alarm notes made self-describing so a
    stored row can be re-screened from its note), or None when the photo doesn't support it."""
    d = dict(det)
    d.pop("alarm_observation", None)
    if det["violation_type"] not in ALARM_TYPES:
        return d | {"basis": BASIS_PHOTO}
    note = (det.get("evidence_note") or "").strip()
    obs = det.get("alarm_observation")
    if obs in _OBS:
        basis, prefix = _OBS[obs]
        if classify_alarm_note(note) != basis:
            note = f"{prefix}: {note}" if note else prefix
            if classify_alarm_note(note) != basis:  # the note contradicts the observation (e.g. "no alarm"): drop
                return None
        return d | {"evidence_note": note, "basis": basis}
    if obs:  # "no_alarm_visible", "alarm_present" or anything unexpected
        return None
    basis = classify_alarm_note(note)
    return d | {"basis": basis} if basis else None


def detection_basis(violation_type: str, note: str | None, model_endpoint: str | None) -> str | None:
    """Basis of a stored detection row; None = unsupported (e.g. an alarm 'absence' row saved before screening)."""
    if model_endpoint == "user":
        return BASIS_TENANT
    if violation_type not in ALARM_TYPES:
        return BASIS_PHOTO
    return classify_alarm_note(note or "")


# ---------------------------------------------------------------- pure helpers
def apply_threshold(det: dict, threshold: float = config.CONFIDENCE_THRESHOLD) -> dict:
    d = dict(det)
    d["certain"] = d["confidence"] >= threshold and d.get("basis") != BASIS_VERIFY
    d["label"] = BY_ID[d["violation_type"]]["name"] if d["certain"] else VERIFY_LABEL
    return d


def dedup(detections: list[dict]) -> list[dict]:
    """Merge detections of the same type within a scan into one violation.

    Input rows: {violation_type, confidence, evidence_id, evidence_note, severity_hint, scene?}
    Output: one row per type with max confidence, all evidence_ids (ordered, unique), notes, worst severity.
    """
    order = {"routine": 0, "urgent": 1, "emergency": 2}
    merged: dict[str, dict] = {}
    for d in detections:
        t = d["violation_type"]
        m = merged.get(t)
        if m is None:
            merged[t] = {"violation_type": t, "confidence": d["confidence"], "evidence_ids": [d["evidence_id"]],
                         "notes": [d.get("evidence_note", "")], "severity_hint": d.get("severity_hint", "routine"),
                         "scenes": [d.get("scene")] if d.get("scene") else []}
            continue
        m["confidence"] = max(m["confidence"], d["confidence"])
        if d["evidence_id"] not in m["evidence_ids"]:
            m["evidence_ids"].append(d["evidence_id"])
        if d.get("evidence_note") and d["evidence_note"] not in m["notes"]:
            m["notes"].append(d["evidence_note"])
        if order.get(d.get("severity_hint", "routine"), 0) > order.get(m["severity_hint"], 0):
            m["severity_hint"] = d["severity_hint"]
        if d.get("scene") and d["scene"] not in m["scenes"]:
            m["scenes"].append(d["scene"])
    return sorted(merged.values(), key=lambda m: -m["confidence"])
