"""Scan orchestration: frames -> evidence -> detections -> deduped gold.violations."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from .. import config, db
from . import code_match, evidence, properties, vision
from .taxonomy import BY_ID, severity_for


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def create_scan(mode: str, address: str | None, unit: str | None, user_id: str = "demo-user") -> dict:
    prop = properties.match_address(address) if address else None
    row = {"scan_id": f"S-{uuid.uuid4().hex[:10]}", "user_id": user_id,
           "property_id": prop["property_id"] if prop else None, "unit": unit, "mode": mode,
           "address": address, "created_at": _now()}
    db.insert("silver.scans", row)
    return row | {"property": prop}


def get_scan(scan_id: str) -> dict | None:
    return db.q1("SELECT * FROM {silver.scans} WHERE scan_id = :s", {"s": scan_id})


def process_frames(scan_id: str, frames: list[tuple[bytes, str, str | None]]) -> dict:
    """frames: list of (bytes, media_type, captured_at). Returns per-frame results + deduped violations."""
    scan = get_scan(scan_id)
    if not scan:
        raise KeyError(scan_id)
    frames = frames[: config.MAX_FRAMES]
    per_frame, all_dets, sources = [], [], set()
    for i, (data, media_type, captured_at) in enumerate(frames):
        ev = evidence.store(scan_id, data, media_type, captured_at)
        res, source = vision.analyze_frame(data, ev["sha256"], scan["mode"], i, len(frames), media_type)
        sources.add(source)
        dets = []
        for j, d in enumerate(res.detections):
            dd = vision.apply_threshold(d.model_dump())
            dd.update({"evidence_id": ev["evidence_id"], "scene": res.scene})
            db.insert("silver.detections", {
                "detection_id": f"D-{ev['evidence_id'][2:14]}-{j}", "scan_id": scan_id,
                "evidence_id": ev["evidence_id"], "violation_type": d.violation_type, "confidence": d.confidence,
                "bbox": d.bbox if config.SHOW_BBOXES else None, "note": d.evidence_note,
                "model_endpoint": config.VISION_ENDPOINT if source == "live" else source, "created_at": _now(),
            })
            dets.append(dd)
            all_dets.append(dd)
        per_frame.append({"evidence_id": ev["evidence_id"], "sha256": ev["sha256"], "scene": res.scene,
                          "detections": dets, "source": source})
    violations = rebuild_violations(scan_id)
    return {"scan_id": scan_id, "frames": per_frame, "violations": violations,
            "source": "live" if sources == {"live"} else ("cache" if "cache" in sources else sorted(sources)[0] if sources else "none")}


def rebuild_violations(scan_id: str) -> list[dict]:
    scan = get_scan(scan_id)
    rows = db.q("SELECT * FROM {silver.detections} WHERE scan_id = :s", {"s": scan_id})
    dets = [{"violation_type": r["violation_type"], "confidence": r["confidence"], "evidence_id": r["evidence_id"],
             "evidence_note": r["note"], "severity_hint": BY_ID[r["violation_type"]]["default_severity"]} for r in rows]
    merged = vision.dedup(dets)
    db.execute("DELETE FROM {gold.violations} WHERE scan_id = :s", {"s": scan_id})
    out = []
    for m in merged:
        t = m["violation_type"]
        tax = BY_ID[t]
        sev = severity_for(t, date.today())
        sections = code_match.sections_for_type(t)
        row = {"violation_id": f"V-{scan_id[2:]}-{t[:12]}", "scan_id": scan_id, "property_id": scan["property_id"],
               "violation_type": t, "severity": sev, "confidence": round(m["confidence"], 3),
               "code_section_ids": [s["section_id"] for s in sections], "explanation": tax["plain_explanation"],
               "evidence_ids": [e for e in m["evidence_ids"] if e], "status": "open"}
        db.insert("gold.violations", row)
        out.append(_decorate(row, sections, m["notes"]))
    return out


def _decorate(row: dict, sections: list[dict], notes: list[str]) -> dict:
    tax = BY_ID[row["violation_type"]]
    certain = row["confidence"] >= config.CONFIDENCE_THRESHOLD
    return {**row, "name": tax["name"], "category": tax["category"], "remedy": tax["remedy_request"],
            "label": tax["name"] if certain else "Possible issue — verify in person", "certain": certain,
            "code_sections": sections, "notes": [n for n in notes if n]}


def violations_for_scan(scan_id: str) -> list[dict]:
    rows = db.q("SELECT * FROM {gold.violations} WHERE scan_id = :s ORDER BY confidence DESC", {"s": scan_id})
    dets = db.q("SELECT violation_type, note FROM {silver.detections} WHERE scan_id = :s", {"s": scan_id})
    out = []
    for r in rows:
        r["code_section_ids"] = db.jl(r["code_section_ids"])
        r["evidence_ids"] = db.jl(r["evidence_ids"])
        notes = list(dict.fromkeys(d["note"] for d in dets if d["violation_type"] == r["violation_type"]))
        out.append(_decorate(r, code_match.sections_for_type(r["violation_type"]), notes))
    return out


def add_manual_violation(scan_id: str, type_id: str, note: str = "") -> list[dict]:
    """User-reported issues (e.g. NO_HEAT) that photos can't show."""
    if type_id not in BY_ID:
        raise ValueError(type_id)
    db.insert("silver.detections", {
        "detection_id": f"D-M-{uuid.uuid4().hex[:10]}", "scan_id": scan_id, "evidence_id": None,
        "violation_type": type_id, "confidence": 1.0, "bbox": None, "note": note or "Reported by tenant",
        "model_endpoint": "user", "created_at": _now()})
    return rebuild_violations(scan_id)
