"""The demo story must not depend on when the data is generated (regression: grade flipped D <-> F by time of day)."""
import os

os.environ["DATA_BACKEND"] = "local"
os.environ["DATABRICKS_HOST"] = ""
os.environ["DATABRICKS_TOKEN"] = ""
os.environ["DATABRICKS_CONFIG_PROFILE"] = ""

from datetime import datetime, timedelta

import pytest

from app.backend.services import landlords, synthetic

OPEN = ("open", "escalated")
OTHER_DEMO_BUILDINGS = ("P-DEMO-A", "P-DEMO-B", "P-DEMO-C")

# Times that used to break it (21:15 on 11-14 and noon on 11-20 gave F), plus midnight, month/year ends, a leap day,
# the US DST change, summer, and the reference instant itself.
TIMES = [
    "2026-11-14 00:00:00", "2026-11-14 09:00:00", "2026-11-14 12:00:00", "2026-11-14 17:00:00",
    "2026-11-14 21:15:00", "2026-11-14 23:59:59", "2026-11-15 09:00:00", "2026-11-20 12:00:00",
    "2026-11-01 01:30:00", "2026-11-30 23:00:00", "2026-12-31 23:59:00", "2027-02-01 03:00:00",
    "2028-02-29 12:00:00", "2026-07-04 18:30:00",
]


def story(now: datetime) -> dict:
    d = synthetic.generate(now=now)
    demo = next(r for r in landlords.compute_scores(d["owners"], d["properties"], d["reports"], now)
                if r["owner_id"] == synthetic.DEMO_OWNER_ID)
    rep = d["reports"]
    return {
        "grade": demo["grade"], "score": demo["score"],
        "heat_open_30d": sum(1 for r in rep if r["property_id"] == synthetic.DEMO_PROPERTY_ID
                             and r["violation_type"] == "NO_HEAT" and r["status"] in OPEN
                             and datetime.fromisoformat(r["reported_at"]) >= now - timedelta(days=30)),
        "heat_households": len({r["unit_hash"] for r in rep if r["report_id"].startswith("R-DEMO-HEAT")}),
        "other_open": sum(1 for r in rep if r["property_id"] in OTHER_DEMO_BUILDINGS and r["status"] in OPEN),
        "other_buildings": len({r["property_id"] for r in rep if r["property_id"] in OTHER_DEMO_BUILDINGS}),
    }


@pytest.fixture(scope="module")
def reference_story():
    return story(synthetic.REFERENCE_NOW)


@pytest.mark.parametrize("ts", TIMES)
def test_demo_story_same_at_any_time(ts, reference_story):
    s = story(datetime.fromisoformat(ts))
    assert s["heat_open_30d"] == 6 and s["heat_households"] == 6
    assert s["grade"] == "D"
    assert s["other_open"] == 11 and s["other_buildings"] == 3
    assert s == reference_story  # identical, including the exact score


def _relative(now: datetime) -> list[tuple]:
    out = []
    for r in synthetic.generate(now=now)["reports"]:
        rel = lambda f: (datetime.fromisoformat(r[f]) - now) if r[f] else None
        out.append((r["report_id"], r["property_id"], r["violation_type"], r["severity"], r["status"],
                    rel("reported_at"), rel("fixed_at")))
    return out


def test_whole_dataset_identical_relative_to_now():
    a = _relative(datetime(2026, 11, 14, 9, 0, 0))
    b = _relative(datetime(2026, 11, 14, 21, 15, 0))
    c = _relative(datetime(2027, 3, 2, 4, 5, 6))
    assert a == b == c and len(a) > 10000


def test_now_is_respected():
    now = datetime(2027, 1, 10, 8, 30, 0)
    rep = synthetic.generate(now=now)["reports"]
    assert max(datetime.fromisoformat(r["reported_at"]) for r in rep) <= now
    assert all(datetime.fromisoformat(r["fixed_at"]) <= now for r in rep if r["fixed_at"])
    assert all(r["fixed_at"] is None for r in rep if r["status"] in OPEN)


def test_demo_story_independent_of_background_size():
    """The demo owner's reports come from their own random stream: background tuning can't change them."""
    now = datetime(2026, 11, 14, 21, 15, 0)
    full = {r["report_id"]: r for r in synthetic.generate(now=now)["reports"] if r["report_id"].startswith("R-DEMO")}
    small = {r["report_id"]: r for r in synthetic.generate(now=now, n_reports=500)["reports"]
             if r["report_id"].startswith("R-DEMO")}
    assert full == small and len(full) == 6 + 8 + 11 + 9


def test_same_seed_is_deterministic_and_other_seed_differs():
    now = datetime(2026, 11, 14, 12, 0, 0)
    assert synthetic.generate(now=now) == synthetic.generate(now=now)
    assert synthetic.generate(seed=7, now=now)["reports"] != synthetic.generate(now=now)["reports"]


def test_local_seed_end_to_end_late_evening(tmp_path, monkeypatch):
    """Through the real local seeder + the listing lookup the UI uses, at the hour that used to give F."""
    from app.backend import config, db
    from app.backend.seed import seed_local
    from app.backend.services import listing

    monkeypatch.setattr(config, "SQLITE_PATH", tmp_path / "fixit.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db._local, "sqlite", None, raising=False)  # never reuse a cached connection to another DB
    now = datetime(2026, 11, 14, 21, 15, 0)
    try:
        seed_local(now=now)
        assert str(tmp_path) in db.q1("PRAGMA database_list")["file"]
        g = db.q1("SELECT grade FROM {gold.landlord_scores} WHERE owner_id = :o", {"o": synthetic.DEMO_OWNER_ID})
        assert g["grade"] == "D"
        h = listing.building_history(synthetic.DEMO_PROPERTY_ID, now)
        assert h["heat_reports_recent"] == 6 and h["owner"]["grade"] == "D"
        other = db.q1("SELECT COUNT(*) AS n FROM {gold.reports} WHERE property_id IN ('P-DEMO-A','P-DEMO-B','P-DEMO-C') "
                      "AND status IN ('open','escalated')")
        assert other["n"] == 11
    finally:
        db._local.sqlite.close()
