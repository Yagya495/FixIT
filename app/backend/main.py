"""FixIt Madison API + static frontend."""
from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import config, db, seed
from .services import (alarm_rules, calls, cases, code_match, collective, demo_cache, evidence, genie, landlords, listing,
                       pdfs, properties, scans)
from .services.taxonomy import BY_ID, EMERGENCY_GUIDANCE, VIOLATION_TYPES

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(_app):
    if config.DATA_BACKEND == "local":
        db.init_local_schema()
        seed.ensure_seeded()
    yield


app = FastAPI(title="FixIt Madison", version="0.1.0", lifespan=lifespan)


# ---------------------------------------------------------------- meta
@app.get("/api/health")
def health():
    from . import llm
    from .services import code_match as cm

    return {"ok": True, "demo_mode": config.DEMO_MODE, "backend": config.DATA_BACKEND,
            "show_bboxes": config.SHOW_BBOXES, "threshold": config.CONFIDENCE_THRESHOLD,
            # What is actually wired up, so the UI never claims more than is running (no secrets here).
            "models_configured": llm.available(), "genie_configured": bool(config.GENIE_SPACE_ID),
            "code_sections_verified": cm.verified_count()}


@app.get("/api/meta")
def meta():
    return {"disclaimer": config.DISCLAIMER, "links": config.OFFICIAL_LINKS, "taxonomy": VIOLATION_TYPES,
            "emergency_guidance": EMERGENCY_GUIDANCE, "grade_explainer": landlords.GRADE_EXPLAINER,
            "sample_questions": genie.SAMPLE_QUESTIONS, "demo_mode": config.DEMO_MODE,
            "default_windows_hours": config.DEFAULT_WINDOW_HOURS}


# ---------------------------------------------------------------- code KB
@app.get("/api/code/match")
def code_match_route(q: str):
    return {"query": q, "results": code_match.match_code(q)}


# ---------------------------------------------------------------- scans
_SHA = re.compile(r"^[0-9a-f]{64}$")


async def _read_frames(files: list[UploadFile], captured: list[str] | None, orig: list[str] | None = None):
    """(bytes, media_type, captured_at, original_file_sha|None). The original sha lets Demo Mode's cache match a
    photo even after the browser re-encoded it; evidence is still hashed on the bytes actually received."""
    out = []
    for i, f in enumerate(files):
        data = await f.read()
        if not data:
            continue
        mt = f.content_type if f.content_type in ("image/jpeg", "image/png", "image/webp") else "image/jpeg"
        o = orig[i] if orig and i < len(orig) and _SHA.match(orig[i] or "") else None
        out.append((data, mt, captured[i] if captured and i < len(captured) else None, o))
    return out


@app.post("/api/scans")
def create_scan(mode: str = Form("walkthrough"), address: str = Form(""), unit: str = Form("")):
    if mode not in ("walkthrough", "listing", "movein", "moveout"):
        raise HTTPException(400, "bad mode")
    return scans.create_scan(mode, address or None, unit or None)


@app.post("/api/scans/{scan_id}/frames")
async def add_frames(scan_id: str, files: list[UploadFile] = File(...), captured_at: list[str] | None = Form(None),
                     orig_sha: list[str] | None = Form(None), frame_offset: int = Form(0), frame_total: int = Form(0)):
    """frame_offset/frame_total: position of this batch within a larger upload (the browser sends a video's frames in
    small batches), so frame indexes stay consistent across batches."""
    frames = await _read_frames(files, captured_at, orig_sha)
    if not frames:
        raise HTTPException(400, "no images")
    try:
        return scans.process_frames(scan_id, frames, frame_offset=max(0, frame_offset), frame_total=max(0, frame_total))
    except KeyError:
        raise HTTPException(404, "scan not found")


class ManualIssue(BaseModel):
    type_id: str
    note: str = ""


@app.post("/api/scans/{scan_id}/manual")
def manual(scan_id: str, body: ManualIssue):
    if body.type_id not in BY_ID:
        raise HTTPException(400, "unknown type")
    return {"violations": scans.add_manual_violation(scan_id, body.type_id, body.note)}


@app.get("/api/scans/{scan_id}")
def get_scan(scan_id: str):
    s = scans.get_scan(scan_id)
    if not s:
        raise HTTPException(404)
    return {**s, "violations": scans.violations_for_scan(scan_id), "evidence": evidence.for_scan(scan_id)}


@app.get("/api/evidence/{evidence_id}/image")
def evidence_image(evidence_id: str):
    e = evidence.get(evidence_id)
    if not e:
        raise HTTPException(404)
    return Response(evidence.read(e["volume_path"]), media_type=e["media_type"],
                    headers={"Cache-Control": "max-age=86400"})


@app.get("/api/evidence/{evidence_id}/verify")
def evidence_verify(evidence_id: str):
    return {"evidence_id": evidence_id, "intact": evidence.verify(evidence_id)}


# ---------------------------------------------------------------- listing x-ray
@app.post("/api/listing/xray")
async def listing_xray(address: str = Form(...), unit: str = Form(""), files: list[UploadFile] = File(...),
                       orig_sha: list[str] | None = Form(None)):
    scan = scans.create_scan("listing", address, unit or None)
    frames = await _read_frames(files, None, orig_sha)
    if not frames:
        raise HTTPException(400, "no images")
    res = scans.process_frames(scan["scan_id"], frames)
    return {**listing.xray(scan["scan_id"]), "frames": res["frames"], "source": res["source"], "model": res["model"]}


@app.get("/api/listing/{scan_id}/addendum.pdf")
def addendum_pdf(scan_id: str):
    x = listing.xray(scan_id)
    return Response(pdfs.text_pdf("Lease Addendum — Repairs Before Move-in", x["addendum"]), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="addendum-{scan_id}.pdf"'})


# ---------------------------------------------------------------- cases
class CaseCreate(BaseModel):
    scan_id: str
    tone: str = "formal"


@app.post("/api/cases")
def create_case(body: CaseCreate):
    try:
        return cases.create_case(body.scan_id, body.tone)
    except (KeyError, ValueError) as e:
        raise HTTPException(400, str(e))


@app.get("/api/cases")
def list_cases():
    return cases.list_cases()


def _case_or_404(rid: str):
    c = cases.get_case(rid)
    if not c:
        raise HTTPException(404, "case not found")
    return c


@app.get("/api/cases/{rid}")
def get_case(rid: str):
    return _case_or_404(rid)


class Tone(BaseModel):
    tone: str


@app.post("/api/cases/{rid}/letter")
def letter(rid: str, body: Tone):
    _case_or_404(rid)
    return cases.regenerate_letter(rid, body.tone)


@app.post("/api/cases/{rid}/send")
def send(rid: str):
    _case_or_404(rid)
    return cases.mark_sent(rid)


@app.get("/api/cases/{rid}/letter.pdf")
def letter_pdf(rid: str):
    c = _case_or_404(rid)
    return Response(pdfs.text_pdf("Repair Request", c["letter_text"]), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="repair-request-{rid}.pdf"'})


@app.get("/api/cases/{rid}/packet.pdf")
def packet_pdf(rid: str):
    c = _case_or_404(rid)
    return Response(pdfs.evidence_packet(c), media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="evidence-packet-{rid}.pdf"'})


class Days(BaseModel):
    days: int = 8


@app.post("/api/cases/{rid}/simulate")
def simulate(rid: str, body: Days):
    _case_or_404(rid)
    return cases.simulate_days(rid, body.days)


@app.post("/api/cases/{rid}/fixed")
def fixed(rid: str):
    _case_or_404(rid)
    return cases.mark_fixed(rid)


@app.post("/api/cases/{rid}/escalate")
def escalate(rid: str):
    _case_or_404(rid)
    return cases.escalate(rid)


@app.post("/api/cases/{rid}/joint")
def joint(rid: str):
    _case_or_404(rid)
    try:
        return cases.joint_complaint(rid)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---------------------------------------------------------------- simulated call
@app.post("/api/cases/{rid}/call/start")
def call_start(rid: str):
    c = _case_or_404(rid)
    call = calls.SimulatedCall(rid, c["address"] or "[address]", c["unit"], c["violations"])
    calls.ACTIVE[call.call_id] = call
    return {"call_id": call.call_id, "transcript": call.transcript, "done": call.done}


class Say(BaseModel):
    text: str


@app.post("/api/calls/{call_id}/say")
def call_say(call_id: str, body: Say):
    call = calls.ACTIVE.get(call_id)
    if not call:
        raise HTTPException(404, "call not found")
    reply = call.landlord_says(body.text, cases.case_now(call.request_id))
    out = {"call_id": call_id, "reply": reply, "transcript": call.transcript, "done": call.done}
    if call.done:
        out["result"] = _finish(call)
    return out


@app.get("/api/calls/demo-script")
def call_script():
    return {"lines": [t for _, t in demo_cache.SCRIPTED_CALL]}


@app.post("/api/calls/{call_id}/end")
def call_end(call_id: str):
    call = calls.ACTIVE.get(call_id)
    if not call:
        raise HTTPException(404)
    call.state = "closed"
    return {"result": _finish(call), "transcript": call.transcript, "done": True}


def _finish(call: calls.SimulatedCall) -> dict:
    calls.ACTIVE.pop(call.call_id, None)
    now = cases.case_now(call.request_id)
    res = calls.save_call(call, now=now)
    c = cases.get_case(call.request_id)
    if res.get("commitment_date"):
        cases.set_deadline(call.request_id, datetime.fromisoformat(res["commitment_date"]))
    elif not c["deadline"]:
        from .services import deadlines

        cases.set_deadline(call.request_id, deadlines.default_due(c["severity"], now))
    return res


# ---------------------------------------------------------------- collective / landlords / city
@app.get("/api/collective/{property_id}")
def collective_route(property_id: str, unit: str = ""):
    return collective.match(property_id, unit or None)


@app.get("/api/properties/search")
def prop_search(q: str):
    return properties.search(q)


@app.get("/api/owners")
def owners(q: str = "", limit: int = 25):
    return landlords.search_owners(q, limit)


@app.get("/api/owners/{owner_id}")
def owner(owner_id: str):
    c = landlords.owner_card(owner_id)
    if not c:
        raise HTTPException(404)
    return c


@app.get("/api/buildings/{property_id}")
def building(property_id: str):
    b = landlords.building_page(property_id)
    if not b:
        raise HTTPException(404)
    return b


@app.get("/api/city/map")
def city_map():
    return landlords.map_points()


class Question(BaseModel):
    question: str


@app.post("/api/genie/ask")
def genie_ask(body: Question):
    return genie.ask(body.question)


# ---------------------------------------------------------------- smoke / CO source applicability (prototype)
class AlarmRulesRequest(BaseModel):
    profile: dict = {}
    alarm_types: list[str] = ["smoke", "co"]


@app.post("/api/alarm-rules")
def alarm_rules_eval(body: AlarmRulesRequest):
    """Nonpersistent: reads only the tenant-entered profile (no property id, no DB access, nothing stored)."""
    return alarm_rules.evaluate(body.profile, [t for t in body.alarm_types if t in ("smoke", "co")])


# ---------------------------------------------------------------- demo
@app.post("/api/demo/reset")
def demo_reset():
    if config.DATA_BACKEND != "local":
        raise HTTPException(400, "reset only supported on local backend; rerun notebooks/05 on Databricks")
    counts = seed.seed_local()
    code_match.reset_cache()
    calls.ACTIVE.clear()
    return {"ok": True, "counts": counts}


@app.post("/api/demo/warm")
def demo_warm():
    """Run live vision on demo/demo_inputs and save results to the cache (call before going on stage)."""
    from .services import vision

    out = []
    for mode, folder in (("listing", "listing"), ("walkthrough", "walkthrough")):
        d = config.DEMO_DIR / "demo_inputs" / folder
        files = sorted(p for p in d.glob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png"))
        for p in files:
            data = p.read_bytes()
            sha = evidence.sha256_bytes(data)
            try:
                res = vision.analyze_frame_live(data, mode, "image/png" if p.suffix.lower() == ".png" else "image/jpeg")
                demo_cache.put("vision", f"{mode}-{sha}", res.model_dump())
                out.append({"file": p.name, "mode": mode, "detections": len(res.detections), "ok": True})
            except Exception as e:
                out.append({"file": p.name, "mode": mode, "ok": False, "error": str(e)[:200]})
    gen = genie.warm() if config.GENIE_SPACE_ID else []
    return {"warmed": out, "genie": gen}


# ---------------------------------------------------------------- frontend
if config.STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=config.STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        f = config.STATIC_DIR / path
        if path and f.is_file():
            return FileResponse(f)
        return FileResponse(config.STATIC_DIR / "index.html")
else:
    @app.get("/")
    def root():
        return JSONResponse({"msg": "Frontend not built. Run `make build` or use the Vite dev server on :5173."})
