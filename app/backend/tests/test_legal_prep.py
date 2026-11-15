"""Legal preparation that must stay INACTIVE until the reviewer approves it (user decisions, 2026-11-14)."""
import json
import sys
from pathlib import Path

import pytest

from app.backend.services import conditional_citations as cc
from app.backend.services import state_law

ROOT = Path(__file__).resolve().parents[3]


def photo(note, ev="E-1"):
    return {"evidence_id": ev, "note": note, "basis": "photo"}


# ---------------------------------------------------------------- conditional citations
@pytest.mark.parametrize("type_id,note,expected", [
    ("BLOCKED_EGRESS", "Broken tread on the back stairs", ["STAIRS_UNSAFE"]),
    ("BLOCKED_EGRESS", "Porch steps sagging and rotted", ["STAIRS_UNSAFE"]),
    ("BLOCKED_EGRESS", "Exit door blocked by a couch", []),                  # blocked exit: never stairs
    ("BLOCKED_EGRESS", "Stairs with no handrail", []),                       # missing handrail alone: never
    ("BLOCKED_EGRESS", "Normal carpeted staircase", []),
    ("WATER_DAMAGE_MOLD", "Water damage on the tile around the shower", ["WET_AREA_SURFACE"]),
    ("WATER_DAMAGE_MOLD", "Soft, water-damaged bathroom floor near the toilet", ["BATHROOM_FLOOR"]),
    ("WATER_DAMAGE_MOLD", "Brown stain on the bedroom ceiling", []),         # not a wet area, not a bathroom floor
    ("WATER_DAMAGE_MOLD", "Water stain on the living room floor", []),
    ("DAMAGED_SURFACES", "Cracked tiles around the bathtub", []),            # other categories never trigger them
])
def test_conditional_matching(type_id, note, expected):
    assert cc.matching(type_id, [photo(note)]) == expected


def test_conditional_needs_a_photo_observation():
    tenant = {"evidence_id": None, "note": "Broken tread on the stairs", "basis": "tenant_report"}
    verify = {"evidence_id": "E-2", "note": "Broken tread on the stairs", "basis": "verify_in_person"}
    assert cc.matching("BLOCKED_EGRESS", [tenant, verify]) == []


def test_conditional_citations_are_inactive_without_approval():
    obs = [photo("Broken tread on the back stairs")]
    assert cc.active("BLOCKED_EGRESS", obs) == []                                   # today: nothing approved
    assert cc.active("BLOCKED_EGRESS", obs, {"STAIRS_UNSAFE"}) == ["27.05(2)(i)"]    # only after explicit approval
    import inspect
    from app.backend.services import code_match, scans
    for mod in (scans, code_match):                                                 # not wired into the app yet
        assert "conditional_citations" not in inspect.getsource(mod)


def test_conditional_proposals_match_the_review_json_and_cannot_be_approved_by_category():
    prop = json.loads((ROOT / "docs/legal/ch27_proposed_mappings.json").read_text(encoding="utf-8"))
    cond = {c["conditional_id"]: (p["type_id"], c["section_id"]) for p in prop["proposals"] for c in p.get("conditional", [])}
    assert cond == {p["id"]: (p["type_id"], p["section_id"]) for p in cc.PROPOSALS}
    egress = next(p for p in prop["proposals"] if p["type_id"] == "BLOCKED_EGRESS")
    assert "27.05(2)(i)" not in {i["section_id"] for i in egress["items"]}         # no longer part of the category
    sys.path.insert(0, str(ROOT / "scripts"))
    from code_parse import approved_rows
    with pytest.raises(KeyError):
        approved_rows(["27.05(2)(k)"], {"WATER_DAMAGE_MOLD"})                       # conditional: not approvable here
    with pytest.raises(KeyError):
        approved_rows(["27.05(2)(i)"], {"BLOCKED_EGRESS"})
    water = approved_rows(["27.05(2)(g)1."], {"WATER_DAMAGE_MOLD"})[0]["text"]
    assert "waterproof" not in water                                               # the conditional sentence stays out


def test_three_approved_mappings_unchanged():
    data = json.loads((ROOT / "app/backend/code_sections_verified.json").read_text(encoding="utf-8"))
    assert data["mapping"] == {"LEAK_PLUMBING": ["27.05(2)(j)"], "DAMAGED_SURFACES": ["27.05(2)(g)1."],
                               "NO_HEAT": ["27.04(2)(h)"]}
    assert "conditional" not in data


# ---------------------------------------------------------------- state law
def test_state_law_display_is_hard_disabled():
    assert state_law.STATE_LAW_DISPLAY_ENABLED is False
    assert all(state_law.payload(t) is None for t in ("SMOKE_DETECTOR_MISSING", "CO_DETECTOR_MISSING", "NO_HEAT"))


def test_state_law_design_never_claims_verified_governing_or_violated(monkeypatch):
    monkeypatch.setattr(state_law, "STATE_LAW_DISPLAY_ENABLED", True)
    for t in ("SMOKE_DETECTOR_MISSING", "CO_DETECTOR_MISSING"):
        p = state_law.payload(t)
        assert p["label"] == "Possibly relevant state law"
        assert p["governing_rule"] is None and p["deadline"] is None
        assert all(s["verified"] is False and s["kind"] == "Wisconsin statute" for s in p["sources"])
        assert all(s["citation"].startswith("Wis. Stat.") and "MGO" not in s["citation"] for s in p["sources"])
        assert all(s["url"].startswith("https://docs.legis.wisconsin.gov/") for s in p["sources"])
        shown = " ".join(p["notes"] + [s["scope"] for s in p["sources"]]).lower()
        assert "not a finding" in shown and "does not decide which rule governs" in shown
        for word in ("violates", "violated by", "verified by", "applies to this", "5 days"):
            assert word not in shown
    assert state_law.payload("NO_HEAT") is None


def test_five_day_deadline_still_disabled():
    from app.backend.services import alarm_rules
    assert alarm_rules.LEGAL_DEADLINE_DISPLAY_ENABLED is False
