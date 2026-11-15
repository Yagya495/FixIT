"""Smoke / CO source-applicability prototype: user decisions of 2026-11-14 must hold."""
import os

os.environ["DATA_BACKEND"] = "local"
os.environ["DATABRICKS_HOST"] = ""
os.environ["DATABRICKS_TOKEN"] = ""
os.environ["DATABRICKS_CONFIG_PROFILE"] = ""

import inspect
import itertools
import json

import pytest

from app.backend.services import alarm_rules as ar

ALL_STATUSES = {ar.CONDITIONS_MET, ar.MAY_APPLY, ar.OUT_OF_SCOPE, ar.NOT_EVALUATED}


def src(result, alarm, sid):
    return next(s for s in result["alarms"][alarm] if s["source_id"] == sid)


def every_profile():
    keys = list(ar.FIELDS)
    for combo in itertools.product(*[ar.FIELDS[k] for k in keys]):
        yield dict(zip(keys, combo))


# ---- invariants over every possible combination of answers (4*4*3^5 = 3,888 profiles)
def test_invariants_for_every_profile():
    for p in every_profile():
        r = ar.evaluate(p)
        assert r["governing_rule"] is None                       # never picks a governing rule
        assert r["deadline"] == {"enabled": False, "reason": ar.DEADLINE_DISABLED_REASON}
        text = json.dumps(r).lower()
        assert "5 days" not in text and "five days" not in text  # no deadline leaks into the payload
        for alarm in ("smoke", "co"):
            ids = [s["source_id"] for s in r["alarms"][alarm]]
            assert len(ids) == len(set(ids)) == {"smoke": 4, "co": 3}[alarm]  # separate, one entry each
            for s in r["alarms"][alarm]:
                assert s["status"] in ALL_STATUSES and s["verified"] is False
                assert s["status"] != "applies"
                if s["unresolved"]:                              # unresolved scope/exceptions => never "met"
                    assert s["status"] != ar.CONDITIONS_MET


def test_deadline_display_is_hard_disabled():
    assert ar.LEGAL_DEADLINE_DISPLAY_ENABLED is False
    assert "LEGAL_DEADLINE" not in inspect.getsource(ar.normalize)  # not switchable through input


# ---- unknown building characteristics
def test_all_unknown_never_meets_conditions():
    r = ar.evaluate({})
    assert r["profile"] == {k: "unknown" for k in ar.FIELDS}
    for alarm in ("smoke", "co"):
        assert all(s["status"] in (ar.MAY_APPLY, ar.NOT_EVALUATED) for s in r["alarms"][alarm])
        assert any(s["missing"] for s in r["alarms"][alarm])


def test_invalid_values_become_unknown():
    r = ar.evaluate({"units": "12", "built": "1975", "attached_garage": True, "owner_occupied": "maybe"})
    assert r["profile"]["units"] == r["profile"]["built"] == r["profile"]["attached_garage"] == "unknown"


@pytest.mark.parametrize("units", ["1", "2"])
def test_co_dwelling_unknown_features_stay_may_apply(units):
    s = src(ar.evaluate({"units": units, "attached_garage": "no", "fireplace": "unknown",
                         "fuel_burning_appliance": "no"}), "co", "Wis. Stat. 101.647")
    assert s["status"] == ar.MAY_APPLY and "fireplace" in s["missing"]


# ---- stated scopes and exemptions
def test_mgo_34907_construction_period_and_owner_occupied():
    assert src(ar.evaluate({"built": "2009_or_later"}), "smoke", "MGO 34.907")["status"] == ar.OUT_OF_SCOPE
    occ = src(ar.evaluate({"units": "1", "owner_occupied": "yes", "built": "before_1980_06_01"}), "smoke", "MGO 34.907")
    assert occ["status"] == ar.OUT_OF_SCOPE
    unk = src(ar.evaluate({"units": "1", "owner_occupied": "unknown", "built": "1980_06_01_to_2008"}), "smoke", "MGO 34.907")
    assert unk["status"] == ar.MAY_APPLY and "whether the owner lives in the building" in unk["missing"]
    # Even with every fact known, exception (1)(e) is unresolved: never "conditions met".
    full = src(ar.evaluate({"units": "3+", "owner_occupied": "no", "built": "1980_06_01_to_2008"}), "smoke", "MGO 34.907")
    assert full["status"] == ar.MAY_APPLY and full["unresolved"]


def test_three_plus_units_never_meet_conditions_for_state_residential_building_statutes():
    for p in every_profile():
        if p["units"] == "3+":
            r = ar.evaluate(p)
            assert src(r, "smoke", "Wis. Stat. 101.145")["status"] == ar.MAY_APPLY
            assert src(r, "co", "Wis. Stat. 101.149")["status"] == ar.MAY_APPLY
            assert src(r, "smoke", "Wis. Stat. 101.645")["status"] == ar.OUT_OF_SCOPE
            assert src(r, "co", "Wis. Stat. 101.647")["status"] == ar.OUT_OF_SCOPE


def test_co_dwelling_exemption_and_trigger():
    none = ar.evaluate({"units": "2", "attached_garage": "no", "fireplace": "no", "fuel_burning_appliance": "no",
                        "built": "before_1980_06_01"})
    assert src(none, "co", "Wis. Stat. 101.647")["status"] == ar.OUT_OF_SCOPE
    assert src(none, "co", "SPS 328")["status"] == ar.OUT_OF_SCOPE
    garage = ar.evaluate({"units": "1", "attached_garage": "yes"})
    assert src(garage, "co", "Wis. Stat. 101.647")["status"] == ar.CONDITIONS_MET


def test_sps_328_needs_pre_june_1980_and_one_or_two_units():
    assert src(ar.evaluate({"units": "2", "built": "before_1980_06_01"}), "smoke", "SPS 328")["status"] == ar.CONDITIONS_MET
    assert src(ar.evaluate({"units": "2", "built": "1980_06_01_to_2008"}), "smoke", "SPS 328")["status"] == ar.OUT_OF_SCOPE
    assert src(ar.evaluate({"units": "3+", "built": "before_1980_06_01"}), "smoke", "SPS 328")["status"] == ar.OUT_OF_SCOPE
    assert src(ar.evaluate({"units": "2", "built": "unknown"}), "smoke", "SPS 328")["status"] == ar.MAY_APPLY


# ---- nonpersistent, tenant input only
def test_evaluate_takes_only_the_tenant_profile():
    params = list(inspect.signature(ar.evaluate).parameters)
    assert params == ["profile", "alarm_types"]           # no property id / building record input
    src_text = inspect.getsource(ar)
    assert "import db" not in src_text and "from .. import" not in src_text
    assert "import synthetic" not in src_text and "from .synthetic" not in src_text and "from . import" not in src_text


def test_endpoint_is_nonpersistent_and_ignores_extra_fields(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    from app.backend import config, db
    monkeypatch.setattr(config, "SQLITE_PATH", tmp_path / "fixit.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db._local, "sqlite", None, raising=False)
    from app.backend.main import app
    calls = []
    for name in ("execute", "insert_many"):
        monkeypatch.setattr(db, name, lambda *a, _n=name, **k: calls.append(_n))
    c = TestClient(app)
    r = c.post("/api/alarm-rules", json={"profile": {"units": "2", "attached_garage": "yes"},
                                         "property_id": "P-DEMO-1234", "alarm_types": ["co", "bogus"]})
    assert r.status_code == 200
    body = r.json()
    assert list(body["alarms"]) == ["co"] and body["deadline"]["enabled"] is False
    assert calls == []                                    # nothing written
    try:
        db._local.sqlite and db._local.sqlite.close()
    except Exception:
        pass


def test_public_building_definition_reported_not_evaluated():
    evaluate, NOT_EVALUATED, MAY_APPLY = ar.evaluate, ar.NOT_EVALUATED, ar.MAY_APPLY
    """Wis. Stat. 101.01(12) ('3 or more tenants') is surfaced, but units != tenants, so nothing is concluded."""
    for units in ("1", "2"):
        r = evaluate({"units": units})
        s145 = next(s for s in r["alarms"]["smoke"] if s["source_id"] == "Wis. Stat. 101.145")
        assert s145["status"] == NOT_EVALUATED and "101.01(12)" in " ".join(s145["reasons"] + s145["unresolved"])
    r = evaluate({"units": "3+"})
    s145 = next(s for s in r["alarms"]["smoke"] if s["source_id"] == "Wis. Stat. 101.145")
    assert s145["status"] == MAY_APPLY and any("101.01(12)" in u for u in s145["unresolved"])
