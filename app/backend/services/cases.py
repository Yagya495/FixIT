"""Case = a repair request built from a scan. Ties together letters, calls, deadlines, complaints."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta

from .. import db
from . import collective, deadlines, evidence, letters, scans
from .synthetic import unit_hash
from .taxonomy import BY_ID


def _now() -> datetime:
    return datetime.now().replace(microsecond=0)


def case_now(request_id: str) -> datetime:
    d = db.q1("SELECT sim_offset_days FROM {silver.deadlines} WHERE request_id = :r", {"r": request_id})
    return _now() + timedelta(days=int(d["sim_offset_days"] or 0) if d else 0)


def _landlord_name(property_id: str | None) -> str:
    if not property_id:
        return "Property Manager"
    r = db.q1("SELECT o.management_company FROM {gold.properties} p JOIN {gold.owners} o ON o.owner_id = p.owner_id "
              "WHERE p.property_id = :p", {"p": property_id})
    return r["management_company"] if r else "Property Manager"


def create_case(scan_id: str, tone: str = "formal") -> dict:
    scan = scans.get_scan(scan_id)
    if not scan:
        raise KeyError(scan_id)
    vio = scans.violations_for_scan(scan_id)
    if not vio:
        raise ValueError("No violations on this scan")
    now = _now()
    sev = deadlines.worst_severity([v["severity"] for v in vio])
    fix_by = deadlines.default_due(sev, now)
    landlord = _landlord_name(scan["property_id"])
    address = scan["address"] or "[address]"
    rid = f"RR-{uuid.uuid4().hex[:10]}"
    db.insert("silver.repair_requests", {
        "request_id": rid, "user_id": scan["user_id"], "scan_id": scan_id, "property_id": scan["property_id"],
        "unit": scan["unit"], "violation_ids": [v["violation_id"] for v in vio], "tone": tone,
        "letter_text": letters.repair_letter(vio, address, scan["unit"], landlord, tone, fix_by, now),
        "sent_at": None, "created_at": now.isoformat(timespec="seconds")})
    # The tenant's own report enters the lakehouse (source=fixit) so future neighbors match against it.
    if scan["property_id"]:
        uh = unit_hash(scan["property_id"], scan["unit"] or "?")
        db.insert_many("gold.reports", [{
            "report_id": f"R-FX-{rid[3:]}-{i}", "property_id": scan["property_id"], "unit_hash": uh,
            "violation_category": BY_ID[v["violation_type"]]["category"], "violation_type": v["violation_type"],
            "severity": v["severity"], "reported_at": now.isoformat(timespec="seconds"), "fixed_at": None,
            "status": "open", "source": "fixit"} for i, v in enumerate(vio)])
    return get_case(rid)


def get_case(request_id: str) -> dict | None:
    rr = db.q1("SELECT * FROM {silver.repair_requests} WHERE request_id = :r", {"r": request_id})
    if not rr:
        return None
    scan = scans.get_scan(rr["scan_id"])
    vio = scans.violations_for_scan(rr["scan_id"])
    dl = db.q1("SELECT * FROM {silver.deadlines} WHERE request_id = :r", {"r": request_id})
    now = case_now(request_id)
    deadline = None
    if dl:
        due = datetime.fromisoformat(dl["due_date"])
        # Computed on read, never written here: a write-on-read raced the call's own deadline UPDATE and Delta rejected
        # it (DELTA_CONCURRENT_APPEND -> HTTP 500). Only terminal states (met/escalated) are stored.
        status = deadlines.status_at(due, now, dl["status"])
        deadline = {**dl, "status": status, "now": now.isoformat(timespec="seconds"),
                    "time_left": deadlines.time_left(due, now)}
    from . import calls as calls_svc  # local import avoids cycle

    complaint = db.q1("SELECT * FROM {silver.complaints} WHERE request_id = :r AND joint = 0 ORDER BY generated_at DESC",
                      {"r": request_id})
    sev = deadlines.worst_severity([v["severity"] for v in vio])
    return {
        **rr, "violation_ids": db.jl(rr["violation_ids"]), "address": scan["address"], "unit": scan["unit"],
        "landlord": _landlord_name(rr["property_id"]), "violations": vio, "severity": sev,
        "emergency": sev == "emergency", "evidence": evidence.for_scan(rr["scan_id"]),
        "calls": calls_svc.calls_for_request(request_id), "deadline": deadline,
        "complaint": json.loads(complaint["payload_json"]) if complaint else None,
        "collective": collective.match(rr["property_id"], scan["unit"], now=now),
    }


def regenerate_letter(request_id: str, tone: str) -> dict:
    c = get_case(request_id)
    due = datetime.fromisoformat(c["deadline"]["due_date"]) if c["deadline"] else deadlines.default_due(c["severity"], _now())
    text = letters.repair_letter(c["violations"], c["address"] or "[address]", c["unit"], c["landlord"], tone, due)
    db.execute("UPDATE {silver.repair_requests} SET tone = :t, letter_text = :l WHERE request_id = :r",
               {"t": tone, "l": text, "r": request_id})
    return {"tone": tone, "letter_text": text}


def mark_sent(request_id: str) -> dict:
    now = _now()
    db.execute("UPDATE {silver.repair_requests} SET sent_at = :s WHERE request_id = :r",
               {"s": now.isoformat(timespec="seconds"), "r": request_id})
    c = get_case(request_id)
    if not c["deadline"]:
        set_deadline(request_id, deadlines.default_due(c["severity"], now))
    return get_case(request_id)


def set_deadline(request_id: str, due: datetime) -> None:
    now = _now().isoformat(timespec="seconds")
    existing = db.q1("SELECT sim_offset_days FROM {silver.deadlines} WHERE request_id = :r", {"r": request_id})
    if existing:
        db.execute("UPDATE {silver.deadlines} SET due_date = :d, status = 'open', updated_at = :u WHERE request_id = :r",
                   {"d": due.isoformat(timespec="minutes"), "u": now, "r": request_id})
    else:
        db.insert("silver.deadlines", {"request_id": request_id, "due_date": due.isoformat(timespec="minutes"),
                                       "status": "open", "created_at": now, "updated_at": now, "sim_offset_days": 0})


def simulate_days(request_id: str, days: int) -> dict:
    db.execute("UPDATE {silver.deadlines} SET sim_offset_days = sim_offset_days + :d WHERE request_id = :r",
               {"d": days, "r": request_id})
    return get_case(request_id)


def mark_fixed(request_id: str) -> dict:
    db.execute("UPDATE {silver.deadlines} SET status = 'met', updated_at = :u WHERE request_id = :r",
               {"u": _now().isoformat(timespec="seconds"), "r": request_id})
    return get_case(request_id)


def escalate(request_id: str) -> dict:
    c = get_case(request_id)
    notified = [d for d in [c.get("sent_at")] + [k["created_at"] for k in c["calls"]] if d]
    commitment = next((k["commitment_date"] for k in reversed(c["calls"]) if k.get("commitment_date")), None)
    payload = letters.city_complaint({**c, "commitment_date": commitment}, c["violations"],
                                     [n[:10] for n in notified], len(c["evidence"]))
    now = case_now(request_id).isoformat(timespec="seconds")
    db.insert("silver.complaints", {"complaint_id": f"CP-{uuid.uuid4().hex[:10]}", "request_id": request_id,
                                    "payload_json": json.dumps(payload), "generated_at": now, "joint": 0, "units": []})
    db.execute("UPDATE {silver.deadlines} SET status = 'escalated', updated_at = :u WHERE request_id = :r",
               {"u": now, "r": request_id})
    return get_case(request_id)


def joint_complaint(request_id: str) -> dict:
    c = get_case(request_id)
    if not c["property_id"]:
        raise ValueError("Address not matched to a known building")
    now = case_now(request_id)
    # Neighbor households only; the tenant's own issues are prepended as Unit A.
    groups = _groups_excluding(c["property_id"], now, unit_hash(c["property_id"], c["unit"] or "?"))
    # Unit A = the tenant: dated by when they actually reported (case creation), not the simulated clock.
    reported = c["created_at"] or now.isoformat()
    groups.insert(0, {"types": ", ".join(v["name"] for v in c["violations"]), "first": reported, "last": reported})
    payload = letters.joint_complaint(c["address"], c["landlord"], groups, c["collective"]["other_buildings"])
    db.insert("silver.complaints", {"complaint_id": f"CP-{uuid.uuid4().hex[:10]}", "request_id": request_id,
                                    "payload_json": json.dumps(payload), "generated_at": now.isoformat(timespec="seconds"),
                                    "joint": 1, "units": payload["units"]})
    return payload


def _groups_excluding(property_id: str, now: datetime, exclude_hash: str) -> list[dict]:
    since = (now - timedelta(days=30)).isoformat(timespec="seconds")
    rows = db.q("SELECT unit_hash, violation_type, reported_at FROM {gold.reports} WHERE property_id = :p "
                "AND reported_at >= :s AND unit_hash <> :u ORDER BY reported_at", {"p": property_id, "s": since, "u": exclude_hash})
    g: dict[str, dict] = {}
    for r in rows:
        e = g.setdefault(r["unit_hash"], {"types": set(), "first": r["reported_at"], "last": r["reported_at"]})
        e["types"].add(BY_ID[r["violation_type"]]["name"])
        e["last"] = r["reported_at"]
    return [{"types": ", ".join(sorted(v["types"])), "first": v["first"], "last": v["last"]} for v in g.values()]


def list_cases() -> list[dict]:
    rows = db.q("""SELECT r.request_id, r.created_at, r.sent_at, s.address, s.unit, d.status, d.due_date, d.sim_offset_days
                   FROM {silver.repair_requests} r JOIN {silver.scans} s ON s.scan_id = r.scan_id
                   LEFT JOIN {silver.deadlines} d ON d.request_id = r.request_id ORDER BY r.created_at DESC""")
    for r in rows:  # same computed status as get_case
        if r.get("due_date"):
            now = _now() + timedelta(days=int(r.get("sim_offset_days") or 0))
            r["status"] = deadlines.status_at(datetime.fromisoformat(r["due_date"]), now, r["status"])
    return rows
