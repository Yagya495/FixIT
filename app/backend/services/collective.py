"""'You're not alone' collective match (P0-9)."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

from .. import db
from .synthetic import unit_hash
from .taxonomy import BY_ID


def summarize_neighbors(reports: list[dict], my_unit_hash: str | None) -> dict:
    """Pure: given same-building reports, count other households + categories."""
    others = [r for r in reports if r["unit_hash"] != my_unit_hash]
    households = {r["unit_hash"] for r in others}
    by_cat: dict[str, set] = defaultdict(set)
    for r in others:
        by_cat[r["violation_category"]].add(r["unit_hash"])
    cats = sorted(({"category": c, "households": len(h)} for c, h in by_cat.items()), key=lambda x: -x["households"])
    return {"households": len(households), "reports": len(others), "by_category": cats}


def match(property_id: str | None, unit: str | None, now: datetime | None = None, days: int = 30) -> dict:
    if not property_id:
        return {"matched": False, "reason": "Address not found in FixIt data"}
    now = now or datetime.now()
    since = (now - timedelta(days=days)).isoformat(timespec="seconds")
    my_hash = unit_hash(property_id, unit) if unit else None
    same = db.q(
        """SELECT report_id, unit_hash, violation_category, violation_type, severity, reported_at, status
           FROM {gold.reports} WHERE property_id = :p AND reported_at >= :since""",
        {"p": property_id, "since": since},
    )
    neighbors = summarize_neighbors(same, my_hash)
    prop = db.q1("SELECT p.*, o.name AS owner_name FROM {gold.properties} p JOIN {gold.owners} o ON o.owner_id = p.owner_id "
                 "WHERE p.property_id = :p", {"p": property_id})
    others = db.q(
        """SELECT p.property_id, p.address_norm, p.neighborhood,
                  SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_issues
           FROM {gold.properties} p LEFT JOIN {gold.reports} r ON r.property_id = p.property_id
           WHERE p.owner_id = :o AND p.property_id <> :p
           GROUP BY p.property_id, p.address_norm, p.neighborhood
           HAVING SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) > 0
           ORDER BY open_issues DESC""",
        {"o": prop["owner_id"], "p": property_id},
    ) if prop else []
    top = neighbors["by_category"][0] if neighbors["by_category"] else None
    headline = None
    if top:
        headline = (f'{top["households"]} other household{"s" if top["households"] != 1 else ""} in your building '
                    f'reported {top["category"].replace("_", " ")} issues in the last {days} days.')
    owner_line = None
    if others:
        n_open = sum(int(b["open_issues"]) for b in others)
        owner_line = f"This owner's {len(others)} other building{'s' if len(others) != 1 else ''} have {n_open} open issues."
    return {"matched": bool(top or others), "property_id": property_id, "address": prop["address_norm"] if prop else None,
            "owner_name": prop["owner_name"] if prop else None, "neighbors": neighbors, "other_buildings": others,
            "headline": headline, "owner_line": owner_line, "synthetic_note": "Neighbor reports are simulated (synthetic demo data)."}
