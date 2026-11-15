"""Listing X-Ray (P0-4): listing photos + address -> verdict, history, tour questions, addendum."""
from __future__ import annotations

from datetime import datetime, timedelta

from .. import config, db
from . import letters, scans


def building_history(property_id: str | None, now: datetime | None = None) -> dict | None:
    if not property_id:
        return None
    now = now or datetime.now()
    rows = db.q("SELECT violation_category, violation_type, severity, reported_at, fixed_at, status FROM {gold.reports} "
                "WHERE property_id = :p", {"p": property_id})
    recent = (now - timedelta(days=30)).isoformat()
    year = (now - timedelta(days=365)).isoformat()
    owner = db.q1("""SELECT o.owner_id, o.name, o.management_company, s.grade, s.score, s.open_issues, s.median_days_to_fix,
                            s.buildings, s.repeat_buildings
                     FROM {gold.properties} p JOIN {gold.owners} o ON o.owner_id = p.owner_id
                     LEFT JOIN {gold.landlord_scores} s ON s.owner_id = o.owner_id WHERE p.property_id = :p""", {"p": property_id})
    return {
        "total_reports": len(rows),
        "reports_last_12mo": sum(1 for r in rows if r["reported_at"] >= year),
        "open_issues": sum(1 for r in rows if r["status"] in ("open", "escalated")),
        "heat_reports_recent": sum(1 for r in rows if r["violation_category"] == "HEAT" and r["reported_at"] >= recent),
        "mold_reports_12mo": sum(1 for r in rows if r["violation_category"] == "MOLD_MOISTURE" and r["reported_at"] >= year),
        "owner": owner,
    }


def verdict(violations: list[dict], history: dict | None) -> dict:
    """Pure, transparent verdict rules."""
    reasons = []
    certain = [v for v in violations if v.get("certain")]
    serious = [v for v in certain if v["severity"] in ("urgent", "emergency")]
    possible = [v for v in violations if not v.get("certain")]
    for v in certain:
        reasons.append(f'Possible {v["name"].lower()} spotted in listing photos')
    for v in possible:
        reasons.append(f'Maybe: {v["name"].lower()} (low confidence — check in person)')
    grade = (history or {}).get("owner", {}) or {}
    g = grade.get("grade")
    if history:
        if history["heat_reports_recent"]:
            reasons.append(f'{history["heat_reports_recent"]} heat complaints at this building in the last 30 days')
        if history["open_issues"]:
            reasons.append(f'{history["open_issues"]} open issues on record for this building')
        if g:
            reasons.append(f"Owner report-card grade: {g}")
    bad_owner = g in ("D", "F")
    bad_history = bool(history) and (history["open_issues"] >= 3 or history["heat_reports_recent"] >= 3)
    if (serious and (bad_owner or bad_history)) or len(serious) >= 2 or (bad_owner and bad_history):
        level, label = "dont_sign", "Don't sign yet"
    elif violations or bad_owner or bad_history or g == "C":
        level, label = "ask_first", "Ask first"
    else:
        level, label = "sign", "Looks OK — still verify in person"
    if not reasons:
        reasons.append("No issues spotted in the photos and no complaint history on record")
    return {"level": level, "label": label, "reasons": reasons}


def xray(scan_id: str) -> dict:
    scan = scans.get_scan(scan_id)
    vio = scans.violations_for_scan(scan_id)
    hist = building_history(scan["property_id"])
    address = scan["address"] or "[address]"
    return {
        "scan_id": scan_id, "address": address, "property_id": scan["property_id"], "matched": bool(scan["property_id"]),
        "violations": vio, "history": hist, "verdict": verdict(vio, hist),
        "tour_questions": letters.tour_questions(vio, hist),
        "addendum": letters.lease_addendum([v for v in vio if v.get("certain")] or vio, address, scan["unit"]),
        "caveat": ("Possible issues spotted by AI in marketing photos. This is not an inspection: only a City of Madison "
                   "building inspector can determine a code violation. Verify in person. Building history is demo (synthetic) data."),
        "disclaimer": config.DISCLAIMER,
    }
