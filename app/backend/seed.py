"""Seed the local SQLite backend: taxonomy, seed code sections, synthetic data, landlord scores.

Usage:  python -m app.backend.seed          (from repo root)
"""
from __future__ import annotations

from datetime import datetime

from . import config, db
from .services import landlords, synthetic
from .services.taxonomy import code_section_rows, taxonomy_rows


def seed_local(now: datetime | None = None, keep_code_sections: bool = True) -> dict:
    assert config.DATA_BACKEND == "local", "seed_local only targets the local SQLite backend"
    now = now or datetime.now().replace(microsecond=0)
    existing_sections = db.q("SELECT * FROM {silver.code_sections}") if keep_code_sections and _has_table() else []
    db.init_local_schema(drop=True)

    db.insert_many("ref.violation_types", taxonomy_rows())  # placeholders unless a human approved a mapping
    rows = {s["section_id"]: s for s in code_section_rows()}
    for s in existing_sections:  # keep anything verified that was loaded earlier
        if s.get("verified"):
            rows.setdefault(s["section_id"], s)
    db.insert_many("silver.code_sections", list(rows.values()))

    data = synthetic.generate(now=now)
    db.insert_many("gold.owners", data["owners"])
    db.insert_many("gold.properties", data["properties"])
    db.insert_many("gold.reports", data["reports"])
    scores = landlords.compute_scores(data["owners"], data["properties"], data["reports"], now)
    db.insert_many("gold.landlord_scores", scores)
    return {k: len(v) for k, v in data.items()} | {"landlord_scores": len(scores)}


def _has_table() -> bool:
    try:
        db.q("SELECT 1 FROM {silver.code_sections} LIMIT 1")
        return True
    except Exception:
        return False


def ensure_seeded() -> None:
    if config.DATA_BACKEND == "local" and db.table_count("gold.properties") == 0:
        seed_local()


if __name__ == "__main__":
    print(seed_local())
