"""Scan orchestration: frames -> evidence -> detections -> deduped gold.violations."""
from __future__ import annotations

import uuid
from concurrent.futures import ThreadPoolExecutor
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


def _detection_rows(scan_id: str) -> list[dict]:
    return db.q("SELECT detection_id, evidence_id, violation_type, confidence, note, model_endpoint, created_at "
                "FROM {silver.detections} WHERE scan_id = :s ORDER BY created_at, detection_id", {"s": scan_id})


def overall_source(sources: list[str]) -> str:
    """One label for a request's frames (repeats excluded), most cautious first: no answer at all -> "none"; some frames
    unanswered -> "partial" (never reported as "live"); then scripted fallback, cache, live."""
    s = set(sources)
    if not s:
        return "none"
    if s == {"none"}:
        return "none"
    if "none" in s:
        return "partial"
    for label in ("fallback", "cache", "live"):
        if label in s:
            return label
    return sorted(s)[0]


def process_frames(scan_id: str, frames: list[tuple], frame_offset: int = 0, frame_total: int = 0) -> dict:
    """frames: (bytes, media_type, captured_at[, original_file_sha]). Returns per-frame results + deduped violations.

    frame_offset/frame_total place this request within a larger upload sent in batches. Detections are written in
    frame order. The model calls start right away and the Volume uploads run alongside them; database writes are
    batched (one statement per table per request)."""
    scan = get_scan(scan_id)
    if not scan:
        raise KeyError(scan_id)
    frames = frames[: config.MAX_FRAMES]
    total = max(frame_total, frame_offset + len(frames))

    # Which frames are new: one lookup for the whole batch (C), plus repeats within this batch.
    rows = [evidence.prepare(scan_id, f[0], f[1], f[2]) for f in frames]
    already = evidence.existing([r["evidence_id"] for r in rows])
    stored, new_rows, seen = [], [], set()
    for frame, row in zip(frames, rows):
        eid = row["evidence_id"]
        if eid in already or eid in seen:
            stored.append((frame, (already.get(eid) or row) | {"reused": True}))
        else:
            seen.add(eid)
            new_rows.append((frame, row))
            stored.append((frame, row))

    def analyze(k: int):
        frame, ev = stored[k]
        orig_sha = frame[3] if len(frame) > 3 else None
        return vision.analyze_frame(frame[0], ev["sha256"], scan["mode"], frame_offset + k, total, frame[1],
                                    alt_sha=orig_sha)

    todo = [k for k, (_, ev) in enumerate(stored) if not ev.get("reused")]
    workers = min(config.VISION_CONCURRENCY, len(todo)) or 1
    # A: model calls and Volume uploads in parallel (separate pools so uploads never take a model slot).
    with ThreadPoolExecutor(max_workers=workers) as models, ThreadPoolExecutor(max_workers=4) as uploads:
        model_jobs = {k: models.submit(analyze, k) for k in todo}
        upload_jobs = [uploads.submit(evidence.write_file, row, frame[0]) for frame, row in new_rows]
        for j in upload_jobs:
            j.result()                                     # a failed upload fails the request, as before
        # B: all new evidence rows in one statement (written before any detection that references them).
        db.insert_many("silver.evidence", [row for _, row in new_rows])
        results = {k: job.result() for k, job in model_jobs.items()}

    prior_rows = _detection_rows(scan_id) if any(ev.get("reused") for _, ev in stored) else []
    per_frame, sources, det_rows = [], [], []
    for k, (frame, ev) in enumerate(stored):
        i = frame_offset + k
        if ev.get("reused"):
            # The same photo was already analyzed in this scan (re-upload, double tap, repeated frame): don't call the
            # model again and don't add detections, so a repeat can't create duplicate or contradictory findings.
            # Earlier requests' rows plus this request's not-yet-written rows (a repeat within the same batch).
            prior = [r for r in prior_rows + det_rows if r["evidence_id"] == ev["evidence_id"]]
            per_frame.append({"evidence_id": ev["evidence_id"], "sha256": ev["sha256"], "scene": None,
                              "detections": [{"violation_type": r["violation_type"], "confidence": r["confidence"],
                                              "evidence_note": r["note"], "evidence_id": ev["evidence_id"]} for r in prior],
                              "screened_out": [], "source": "repeat", "repeat": True, "frame_index": i})
            continue
        res, source = results[k]
        sources.append(source)
        dets, screened = [], []
        for j, d in enumerate(res.detections):
            raw = d.model_dump()
            kept = vision.screen_detection(raw)
            if kept is None:
                # e.g. "no smoke detector in frame": a photo can't show an alarm is missing. Reported, never a finding.
                screened.append({"violation_type": raw["violation_type"], "evidence_note": raw.get("evidence_note", ""),
                                 "reason": "A photo can't show that an alarm is missing or whether it works."})
                continue
            dd = vision.apply_threshold(kept)
            dd.update({"evidence_id": ev["evidence_id"], "scene": res.scene})
            det_rows.append({
                # Full evidence id (hash prefix + scan suffix) + frame index: the same photo may appear in several
                # scans without colliding.
                "detection_id": f"D-{ev['evidence_id'][2:]}-{i}-{j}", "scan_id": scan_id,
                "evidence_id": ev["evidence_id"], "violation_type": d.violation_type, "confidence": d.confidence,
                "bbox": d.bbox if config.SHOW_BBOXES else None, "note": kept.get("evidence_note", ""),
                "model_endpoint": config.VISION_ENDPOINT if source == "live" else source, "created_at": _now(),
            })
            dets.append(dd)
        per_frame.append({"evidence_id": ev["evidence_id"], "sha256": ev["sha256"], "scene": res.scene,
                          "detections": dets, "screened_out": screened, "source": source, "frame_index": i})
    db.insert_many("silver.detections", det_rows)          # B: one statement, frame order preserved
    violations = rebuild_violations(scan_id, scan)
    counts = {s: sources.count(s) for s in sorted(set(sources))}
    # The UI shows where results came from; name the model only when it actually answered.
    return {"scan_id": scan_id, "frames": per_frame, "violations": violations, "source": overall_source(sources),
            "source_counts": counts, "model": config.VISION_ENDPOINT if "live" in sources else None}


def observations(scan_id: str) -> dict[str, list[dict]]:
    """Per violation type: one entry per supporting detection, each tied to ITS photo (or none for tenant reports).

    Rows the alarm rules don't support (e.g. an 'absence' row saved before screening existed) are left out. A photo
    repeated across detections of the same type appears once."""
    out: dict[str, list[dict]] = {}
    for r in _detection_rows(scan_id):
        t = r["violation_type"]
        if t not in BY_ID:
            continue
        basis = vision.detection_basis(t, r["note"], r["model_endpoint"])
        if basis is None:
            continue
        obs = out.setdefault(t, [])
        key = (r["evidence_id"], basis, r["note"])
        if any((o["evidence_id"], o["basis"], o["note"]) == key for o in obs):
            continue
        obs.append({"evidence_id": r["evidence_id"], "note": r["note"] or "", "basis": basis,
                    "basis_text": vision.BASIS_TEXT[basis], "confidence": r["confidence"]})
    return out


def rebuild_violations(scan_id: str, scan: dict | None = None) -> list[dict]:
    scan = scan or get_scan(scan_id)
    obs_by_type = observations(scan_id)
    dets = [{"violation_type": t, "confidence": o["confidence"], "evidence_id": o["evidence_id"],
             "evidence_note": o["note"], "severity_hint": BY_ID[t]["default_severity"]}
            for t, obs in obs_by_type.items() for o in obs]
    merged = vision.dedup(dets)
    db.execute("DELETE FROM {gold.violations} WHERE scan_id = :s", {"s": scan_id})
    out, rows = [], []
    for m in merged:
        t = m["violation_type"]
        tax = BY_ID[t]
        sev = severity_for(t, date.today())
        sections = code_match.sections_for_type(t)
        row = {"violation_id": f"V-{scan_id[2:]}-{t[:12]}", "scan_id": scan_id, "property_id": scan["property_id"],
               "violation_type": t, "severity": sev, "confidence": round(m["confidence"], 3),
               "code_section_ids": [s["section_id"] for s in sections], "explanation": tax["plain_explanation"],
               "evidence_ids": [e for e in m["evidence_ids"] if e], "status": "open"}
        rows.append(row)
        out.append(_decorate(row, sections, obs_by_type[t]))
    db.insert_many("gold.violations", rows)                # B: one statement for all findings
    return out


def _decorate(row: dict, sections: list[dict], obs: list[dict]) -> dict:
    tax = BY_ID[row["violation_type"]]
    bases = sorted({o["basis"] for o in obs})
    # Only an in-person check can confirm an empty alarm mount: never a certain finding unless the tenant reported it.
    verify_only = bases == [vision.BASIS_VERIFY]
    certain = row["confidence"] >= config.CONFIDENCE_THRESHOLD and not verify_only
    return {**row, "name": tax["name"], "category": tax["category"], "remedy": tax["remedy_request"],
            "label": tax["name"] if certain else vision.VERIFY_LABEL, "certain": certain,
            "code_sections": sections, "bases": bases, "verify_in_person": verify_only,
            "tenant_reported": vision.BASIS_TENANT in bases, "observations": obs,
            # Same order as `observations`, so notes[i] describes the photo the UI shows next to it.
            "notes": [o["note"] for o in obs if o["note"]]}


def violations_for_scan(scan_id: str) -> list[dict]:
    rows = db.q("SELECT * FROM {gold.violations} WHERE scan_id = :s ORDER BY confidence DESC", {"s": scan_id})
    obs_by_type = observations(scan_id)
    out = []
    for r in rows:
        obs = obs_by_type.get(r["violation_type"])
        if not obs:  # a stored violation no detection supports any more (pre-screening alarm 'absence' row)
            continue
        r["code_section_ids"] = db.jl(r["code_section_ids"])
        r["evidence_ids"] = db.jl(r["evidence_ids"])
        out.append(_decorate(r, code_match.sections_for_type(r["violation_type"]), obs))
    return out


def add_manual_violation(scan_id: str, type_id: str, note: str = "") -> list[dict]:
    """Tenant-reported issues that photos can't show (no heat, a missing or non-working alarm). Never screened out."""
    if type_id not in BY_ID:
        raise ValueError(type_id)
    db.insert("silver.detections", {
        "detection_id": f"D-M-{uuid.uuid4().hex[:10]}", "scan_id": scan_id, "evidence_id": None,
        "violation_type": type_id, "confidence": 1.0, "bbox": None, "note": note or "Reported by tenant",
        "model_endpoint": "user", "created_at": _now()})
    return rebuild_violations(scan_id)
