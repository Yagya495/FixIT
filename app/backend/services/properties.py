"""Address normalization + fuzzy property matching."""
from __future__ import annotations

import difflib
import re

from .. import db

SUFFIX = {"STREET": "ST", "AVENUE": "AVE", "BOULEVARD": "BLVD", "DRIVE": "DR", "ROAD": "RD", "LANE": "LN",
          "COURT": "CT", "PLACE": "PL", "TERRACE": "TER", "PARKWAY": "PKWY", "CIRCLE": "CIR"}
DIRS = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}
UNIT_RE = re.compile(r"\b(APT|UNIT|STE|SUITE|#)\s*\w+\b")


def normalize_address(addr: str) -> str:
    a = (addr or "").upper()
    a = a.split(",")[0]  # drop city/state/zip
    a = UNIT_RE.sub("", a)
    a = re.sub(r"[^A-Z0-9 ]", " ", a)
    words = [DIRS.get(w, SUFFIX.get(w, w)) for w in a.split()]
    return " ".join(words)


def best_match(query: str, candidates: list[str], cutoff: float = 0.82) -> str | None:
    """Pure fuzzy match on normalized addresses. House number must match exactly."""
    qn = normalize_address(query)
    if not qn:
        return None
    if qn in candidates:
        return qn
    num = qn.split()[0]
    same_num = [c for c in candidates if c.split()[0] == num]
    m = difflib.get_close_matches(qn, same_num, n=1, cutoff=cutoff)
    return m[0] if m else None


def match_address(address: str) -> dict | None:
    qn = normalize_address(address)
    if not qn:
        return None
    num = qn.split()[0]
    rows = db.q("SELECT * FROM {gold.properties} WHERE address_norm LIKE :p", {"p": f"{num} %"})
    by_addr = {r["address_norm"]: r for r in rows}
    hit = best_match(address, list(by_addr))
    return by_addr.get(hit) if hit else None


def search(query: str, limit: int = 10) -> list[dict]:
    qn = normalize_address(query)
    return db.q(
        """SELECT p.property_id, p.address_norm, p.neighborhood, p.units, o.name AS owner_name
           FROM {gold.properties} p JOIN {gold.owners} o ON o.owner_id = p.owner_id
           WHERE p.address_norm LIKE :q ORDER BY p.address_norm LIMIT :lim""",
        {"q": f"%{qn}%", "lim": limit},
    )
