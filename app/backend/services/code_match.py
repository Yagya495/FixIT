"""match_code(issue_description) -> top-3 code sections (P0-1).

Order of attempts:
  1. Databricks Vector Search (Delta Sync index on silver.code_chunks) when DATA_BACKEND=databricks.
  2. Local BM25 over silver.code_sections, boosted by taxonomy keyword hints. No external deps.
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .. import config, db
from .taxonomy import BY_ID, VIOLATION_TYPES

_TOKEN = re.compile(r"[a-z0-9]+")
STOP = set("a an the of in on at to for and or is are be with without by from this that it its as my our no not".split())

# Synonym expansion so short user phrases hit the right section.
SYNONYMS = {
    "smoke": ["detector", "alarm", "fire"], "detector": ["alarm", "smoke"], "co": ["carbon", "monoxide", "alarm"],
    "carbon": ["monoxide", "alarm"], "outlet": ["electrical", "switch", "cover", "wiring"],
    "wire": ["wiring", "electrical"], "wires": ["wiring", "electrical"], "wiring": ["electrical"],
    "mold": ["moisture", "dampness", "mildew"], "mildew": ["mold", "moisture"], "stain": ["water", "leak", "moisture"],
    "water": ["leak", "moisture", "dampness"], "damp": ["dampness", "moisture"], "leak": ["leaks", "plumbing", "water"],
    "leaking": ["leak", "plumbing"], "drip": ["leak", "plumbing"], "faucet": ["plumbing", "fixture"],
    "toilet": ["plumbing", "fixture"], "sink": ["plumbing", "fixture"], "pipe": ["plumbing"],
    "mice": ["rodent", "rodents", "pests"], "mouse": ["rodent", "rodents", "pests"], "rats": ["rodent", "rodents"],
    "roach": ["insect", "insects", "pests"], "roaches": ["insect", "insects", "pests"], "cockroach": ["insects", "pests"],
    "bugs": ["insects", "pests"], "bedbugs": ["insects", "pests"], "droppings": ["rodent", "pests"],
    "lock": ["locks", "locking", "doors"], "deadbolt": ["lock", "locks"], "door": ["doors", "locks"],
    "window": ["windows", "glazed", "screens"], "glass": ["window", "glazed"], "screen": ["screens", "windows"],
    "cracked": ["cracks", "window"], "hole": ["holes", "walls"], "paint": ["peeling", "walls", "surfaces"],
    "peeling": ["paint", "surfaces"], "floor": ["floors"], "ceiling": ["ceilings"], "wall": ["walls"],
    "heat": ["heating", "temperature"], "cold": ["heating", "temperature"], "furnace": ["heating"],
    "radiator": ["heating"], "heater": ["heating"], "exit": ["egress", "exits"], "handrail": ["handrails", "stairways"],
    "stairs": ["stairways", "handrails"], "blocked": ["egress", "unobstructed"], "bedroom": ["sleeping"],
}


def tokenize(text: str) -> list[str]:
    toks = [t for t in _TOKEN.findall((text or "").lower()) if t not in STOP]
    out = list(toks)
    for t in toks:
        out.extend(SYNONYMS.get(t, []))
    return out


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.4, b: float = 0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.avgdl = sum(map(len, docs)) / max(1, len(docs))
        df = Counter(t for d in docs for t in set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [Counter(d) for d in docs]

    def score(self, query: list[str], i: int) -> float:
        tf, dl = self.tf[i], len(self.docs[i])
        s = 0.0
        for t in query:
            if t in tf:
                f = tf[t]
                s += self.idf.get(t, 0) * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
        return s


def _section_doc(s: dict) -> list[str]:
    hints = []
    for v in VIOLATION_TYPES:
        if s["section_id"] in v["code_sections"]:
            hints.append(f'{v["name"]} {v["visual_cues"]}')
    return tokenize(f'{s["title"]} {s["title"]} {s["text"]} {" ".join(hints)}')


def rank_sections(issue: str, sections: list[dict], k: int = 3) -> list[dict]:
    """Pure BM25 ranking — unit-tested."""
    if not sections:
        return []
    bm = BM25([_section_doc(s) for s in sections])
    qt = tokenize(issue)
    scored = sorted(((bm.score(qt, i), i) for i in range(len(sections))), reverse=True)[:k]
    top = scored[0][0] or 1.0
    out = []
    for sc, i in scored:
        s = sections[i]
        out.append({"section_id": s["section_id"], "title": s["title"], "snippet": (s["text"] or "")[:400],
                    "url": s.get("url") or config.OFFICIAL_LINKS["chapter_27"], "score": round(sc / top, 3),
                    "verified": bool(s.get("verified"))})
    return out


_cache: list[dict] | None = None


def _sections() -> list[dict]:
    global _cache
    if _cache is None:
        _cache = db.q("SELECT section_id, title, text, source_doc, page, url, verified FROM {silver.code_sections}")
    return _cache


def reset_cache() -> None:
    global _cache, _type_map
    _cache = None
    _type_map = None


def _vector_search(issue: str, k: int) -> list[dict]:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    res = w.vector_search_indexes.query_index(
        index_name=config.VECTOR_INDEX, columns=["chunk_id", "section_id", "text", "source_doc", "page"],
        query_text=issue, num_results=k * 3,
    )
    rows = res.result.data_array or []
    out, seen = [], set()
    for r in rows:
        chunk_id, section_id, text, source_doc, page, score = r[0], r[1], r[2], r[3], r[4], r[-1]
        if section_id in seen:
            continue
        seen.add(section_id)
        sec = next((s for s in _sections() if s["section_id"] == section_id), {})
        out.append({"section_id": section_id, "title": sec.get("title", section_id), "snippet": text[:400],
                    "url": sec.get("url") or config.OFFICIAL_LINKS["chapter_27"], "score": round(float(score), 3),
                    "verified": True})
        if len(out) == k:
            break
    return out


def match_code(issue: str, k: int = 3) -> list[dict]:
    if config.DATA_BACKEND == "databricks":
        try:
            hits = _vector_search(issue, k)
            if hits:
                return hits
        except Exception:
            pass
    return rank_sections(issue, _sections(), k)


_type_map: dict[str, list[str]] | None = None


def _type_sections(type_id: str) -> list[str]:
    """Section ids per type from ref.violation_types (remapped after parsing), falling back to taxonomy.py."""
    global _type_map
    if _type_map is None:
        try:
            _type_map = {r["type_id"]: db.jl(r["code_sections"]) or [] for r in
                         db.q("SELECT type_id, code_sections FROM {ref.violation_types}")}
        except Exception:
            _type_map = {}
    return _type_map.get(type_id) or BY_ID[type_id]["code_sections"]


def sections_for_type(type_id: str) -> list[dict]:
    """Taxonomy-mapped sections first (authoritative), then fill from match_code."""
    v = BY_ID.get(type_id)
    if not v:
        return []
    by_id = {s["section_id"]: s for s in _sections()}
    out = []
    for sid in _type_sections(type_id):
        s = by_id.get(sid)
        if s:
            out.append({"section_id": sid, "title": s["title"], "snippet": (s["text"] or "")[:400],
                        "url": s.get("url") or config.OFFICIAL_LINKS["chapter_27"], "score": 1.0,
                        "verified": bool(s.get("verified"))})
    if not out:
        out = match_code(f'{v["name"]} {v["plain_explanation"]}')[:2]
    return out
