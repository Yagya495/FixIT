"""Landlord report cards (P0-10). Pure scoring + DB-backed lookups.

Grade formula (shown in UI under "How grades work"):
    score = 0.35·z(issues_per_unit) + 0.35·z(median_days_to_fix) + 0.20·z(−pct_fixed_within_30d) + 0.10·z(emergency_per_unit)
    z(x) is the standard score across all owners with ≥1 unit. Higher score = worse.
    A: score < −0.5 · B: < 0 · C: < 0.5 · D: < 1.0 · F: ≥ 1.0
Repeat-offender flag: ≥2 buildings with ≥3 issues in the last 12 months, or grade F.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timedelta

from .. import db

WEIGHTS = {"issues_per_unit": 0.35, "median_days_to_fix": 0.35, "neg_pct_fixed_30d": 0.20, "emergency_per_unit": 0.10}
GRADE_CUTS = [(-0.5, "A"), (0.0, "B"), (0.5, "C"), (1.0, "D")]

GRADE_EXPLAINER = {
    "formula": "score = 0.35·z(issues per unit, 12 mo) + 0.35·z(median days to fix) + 0.20·z(−% fixed within 30 days) + 0.10·z(emergency issues per unit)",
    "cuts": "A < −0.5 ≤ B < 0 ≤ C < 0.5 ≤ D < 1.0 ≤ F",
    "notes": "z = standard score across all owners. Higher score = worse. Built on demo (synthetic) data.",
}

OPEN = ("open", "escalated")


def grade_for(score: float) -> str:
    for cut, g in GRADE_CUTS:
        if score < cut:
            return g
    return "F"


def _z(values: list[float]) -> list[float]:
    if len(values) < 2:
        return [0.0] * len(values)
    mu = statistics.fmean(values)
    sd = statistics.pstdev(values) or 1.0
    return [(v - mu) / sd for v in values]


def _parse(ts: str | None) -> datetime | None:
    return datetime.fromisoformat(ts) if ts else None


def compute_scores(owners: list[dict], properties: list[dict], reports: list[dict], now: datetime) -> list[dict]:
    """Pure: compute gold.landlord_scores rows."""
    prop_owner = {p["property_id"]: p["owner_id"] for p in properties}
    units = defaultdict(int)
    bldgs = defaultdict(int)
    for p in properties:
        units[p["owner_id"]] += int(p["units"] or 0)
        bldgs[p["owner_id"]] += 1

    year_ago = now - timedelta(days=365)
    agg: dict[str, dict] = defaultdict(lambda: {"open": 0, "last12": 0, "fix_days": [], "fixed30": 0, "fixed_n": 0,
                                                "emerg": 0, "per_bldg": defaultdict(int)})
    for r in reports:
        oid = prop_owner.get(r["property_id"])
        if oid is None:
            continue
        a = agg[oid]
        rep = _parse(r["reported_at"])
        if r["status"] in OPEN:
            a["open"] += 1
        if rep and rep >= year_ago:
            a["last12"] += 1
            a["per_bldg"][r["property_id"]] += 1
            if r["severity"] == "emergency":
                a["emerg"] += 1
        fx = _parse(r.get("fixed_at"))
        if rep and fx:
            d = (fx - rep).total_seconds() / 86400
            a["fix_days"].append(d)
            a["fixed_n"] += 1
            a["fixed30"] += d <= 30
        elif rep and r["status"] in OPEN:
            a["fixed_n"] += 1  # unresolved counts against pct fixed

    rows = []
    for o in owners:
        oid = o["owner_id"]
        if units[oid] == 0:
            continue
        a = agg[oid]
        rows.append({
            "owner_id": oid, "buildings": bldgs[oid], "units": units[oid], "open_issues": a["open"],
            "issues_last_12mo": a["last12"], "issues_per_unit": round(a["last12"] / units[oid], 3),
            "median_days_to_fix": round(statistics.median(a["fix_days"]), 1) if a["fix_days"] else None,
            "pct_fixed_within_30d": round(a["fixed30"] / a["fixed_n"], 3) if a["fixed_n"] else None,
            "repeat_buildings": sum(1 for n in a["per_bldg"].values() if n >= 3),
            "emergency_issues": a["emerg"], "_emerg_pu": a["emerg"] / units[oid],
        })
    if not rows:
        return rows
    med_days_default = statistics.median([r["median_days_to_fix"] for r in rows if r["median_days_to_fix"] is not None] or [10])
    zs = {
        "issues_per_unit": _z([r["issues_per_unit"] for r in rows]),
        "median_days_to_fix": _z([r["median_days_to_fix"] if r["median_days_to_fix"] is not None else med_days_default for r in rows]),
        "neg_pct_fixed_30d": _z([-(r["pct_fixed_within_30d"] if r["pct_fixed_within_30d"] is not None else 1.0) for r in rows]),
        "emergency_per_unit": _z([r["_emerg_pu"] for r in rows]),
    }
    for i, r in enumerate(rows):
        s = sum(WEIGHTS[k] * zs[k][i] for k in WEIGHTS)
        r["score"] = round(s, 3)
        r["grade"] = grade_for(s)
        del r["_emerg_pu"]
    return rows


def is_repeat_offender(score_row: dict) -> bool:
    return score_row.get("grade") == "F" or (score_row.get("repeat_buildings") or 0) >= 2


# ---------------------------------------------------------------- DB lookups
def search_owners(query: str = "", limit: int = 25) -> list[dict]:
    rows = db.q(
        """SELECT o.owner_id, o.name, o.management_company, s.buildings, s.units, s.open_issues, s.issues_last_12mo,
                  s.median_days_to_fix, s.pct_fixed_within_30d, s.repeat_buildings, s.grade, s.score
           FROM {gold.owners} o JOIN {gold.landlord_scores} s ON o.owner_id = s.owner_id
           WHERE LOWER(o.name) LIKE :q OR LOWER(o.management_company) LIKE :q
           ORDER BY s.score DESC LIMIT :lim""",
        {"q": f"%{query.lower()}%", "lim": limit},
    )
    for r in rows:
        r["repeat_offender"] = is_repeat_offender(r)
    return rows


def owner_card(owner_id: str) -> dict | None:
    o = db.q1("SELECT * FROM {gold.owners} WHERE owner_id = :o", {"o": owner_id})
    if not o:
        return None
    s = db.q1("SELECT * FROM {gold.landlord_scores} WHERE owner_id = :o", {"o": owner_id}) or {}
    by_type = db.q(
        """SELECT r.violation_type, COUNT(*) AS n, SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_n
           FROM {gold.reports} r JOIN {gold.properties} p ON r.property_id = p.property_id
           WHERE p.owner_id = :o GROUP BY r.violation_type ORDER BY n DESC""",
        {"o": owner_id},
    )
    buildings = db.q(
        """SELECT p.property_id, p.address_norm, p.neighborhood, p.units, p.lat, p.lon,
                  SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_issues,
                  COUNT(r.report_id) AS total_issues
           FROM {gold.properties} p LEFT JOIN {gold.reports} r ON r.property_id = p.property_id
           WHERE p.owner_id = :o GROUP BY p.property_id, p.address_norm, p.neighborhood, p.units, p.lat, p.lon
           ORDER BY open_issues DESC""",
        {"o": owner_id},
    )
    return {**o, "scores": s, "repeat_offender": is_repeat_offender(s), "issues_by_type": by_type,
            "buildings": buildings, "grade_explainer": GRADE_EXPLAINER}


def building_page(property_id: str) -> dict | None:
    p = db.q1("SELECT * FROM {gold.properties} WHERE property_id = :p", {"p": property_id})
    if not p:
        return None
    owner = db.q1(
        """SELECT o.owner_id, o.name, o.management_company, s.grade, s.score, s.open_issues, s.median_days_to_fix
           FROM {gold.owners} o LEFT JOIN {gold.landlord_scores} s ON o.owner_id = s.owner_id WHERE o.owner_id = :o""",
        {"o": p["owner_id"]},
    )
    timeline = db.q(
        """SELECT report_id, violation_type, violation_category, severity, reported_at, fixed_at, status
           FROM {gold.reports} WHERE property_id = :p ORDER BY reported_at DESC""",
        {"p": property_id},
    )
    mix = defaultdict(int)
    for r in timeline:
        mix[r["violation_category"]] += 1
    return {**p, "owner": owner, "timeline": timeline,
            "open_issues": sum(1 for r in timeline if r["status"] in OPEN),
            "category_mix": [{"category": k, "n": v} for k, v in sorted(mix.items(), key=lambda kv: -kv[1])]}


def map_points(limit: int = 3000) -> list[dict]:
    return db.q(
        """SELECT p.property_id, p.address_norm, p.lat, p.lon, p.neighborhood, s.grade,
                  SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_issues
           FROM {gold.properties} p
           LEFT JOIN {gold.reports} r ON r.property_id = p.property_id
           LEFT JOIN {gold.landlord_scores} s ON s.owner_id = p.owner_id
           GROUP BY p.property_id, p.address_norm, p.lat, p.lon, p.neighborhood, s.grade
           LIMIT :lim""",
        {"lim": limit},
    )
