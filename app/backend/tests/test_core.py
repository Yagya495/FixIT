from datetime import datetime, timedelta

import pytest

from app.backend.services import code_match, collective, deadlines, evidence, landlords, listing, properties, vision
from app.backend.services.taxonomy import SEED_CODE_SECTIONS, VIOLATION_TYPES, severity_for

MON = datetime(2026, 11, 16, 10, 0)  # a Monday


# ---------------- code matching
@pytest.mark.parametrize("issue,expected", [
    ("missing smoke detector in bedroom", "CH27-SMOKE"),
    ("no carbon monoxide alarm", "CH27-SMOKE"),
    ("outlet with no cover plate, wires showing", "CH27-ELECTRICAL"),
    ("black mold on bathroom ceiling", "CH27-MOISTURE"),
    ("mouse droppings under the sink", "CH27-PESTS"),
    ("front door deadbolt is broken", "CH27-SECURITY"),
    ("cracked window glass in living room", "CH27-WINDOWS"),
    ("kitchen faucet leaking constantly", "CH27-PLUMBING"),
    ("radiator not working, apartment is freezing cold", "CH27-HEAT"),
    ("stairs have no handrail", "CH27-EGRESS"),
    ("big hole in drywall and peeling paint", "CH27-SURFACES"),
])
def test_code_match_top3(issue, expected):
    hits = code_match.rank_sections(issue, SEED_CODE_SECTIONS, k=3)
    assert expected in [h["section_id"] for h in hits]


def test_every_taxonomy_type_matches_its_section():
    for v in VIOLATION_TYPES:
        hits = code_match.rank_sections(v["name"], SEED_CODE_SECTIONS, k=3)
        assert set(v["code_sections"]) & {h["section_id"] for h in hits}, v["type_id"]


# ---------------- deadlines
def test_default_due_windows():
    assert deadlines.default_due("urgent", MON) == MON + timedelta(hours=48)
    assert deadlines.default_due("routine", MON) == MON + timedelta(days=7)
    assert deadlines.default_due("emergency", MON) == MON + timedelta(hours=24)


@pytest.mark.parametrize("text,days", [
    ("I can probably get someone out there Thursday.", 3),
    ("Yes, Thursday. Fine.", 3),
    ("tomorrow", 1),
    ("we'll do it today", 0),
    ("in 3 days", 3),
    ("in two weeks", 14),
    ("by end of the week", 4),
    ("Monday", 7),
    ("next Tuesday", 8),
    ("next Friday", 4),
])
def test_parse_commitment_relative(text, days):
    got = deadlines.parse_commitment(text, MON)
    assert got is not None
    assert got.date() == (MON + timedelta(days=days)).date()
    assert got.hour == 17


SAT = datetime(2026, 11, 14, 16, 0)  # a Saturday (hackathon day)


@pytest.mark.parametrize("now", [MON, SAT, datetime(2026, 11, 18, 9, 0)])
def test_explicit_weekday_beats_vague_week_phrase(now):
    # The real demo-script line mentions "this week" AND "Thursday"; Thursday must win.
    got = deadlines.parse_commitment("Look, we're busy this week. I can probably get someone out there Thursday.", now)
    assert got.weekday() == 3 and 0 < (got.date() - now.date()).days <= 7
    assert deadlines.parse_commitment("this week", MON).date().isoformat() == "2026-11-20"  # vague phrase still works
    assert deadlines.parse_commitment("sometime next week", MON).date().isoformat() == "2026-11-23"


def test_scripted_call_is_coherent_and_confirms_thursday():
    from app.backend.services import calls
    from app.backend.services.demo_cache import SCRIPTED_CALL

    vs = [{"name": "Missing/disabled smoke detector", "code_sections": [{"title": "Smoke alarms", "section_id": "CH27-SMOKE"}]},
          {"name": "Water stains / visible mold", "code_sections": []}]
    call = calls.SimulatedCall("RR-test", "1234 Demo St", "9", vs)
    assert call.transcript[0]["text"].startswith("Hi, this is an automated AI assistant")
    replies = []
    for _, line in SCRIPTED_CALL:
        replies.append(call.landlord_says(line, SAT))
        if call.done:
            break
    assert not replies[0].startswith("Yes")                       # "who's calling?" isn't a yes/no question
    assert "smoke detector" in replies[1] and "busy" not in replies[1]  # "what's the problem?" gets the issues
    assert call.commitment.date().isoformat() == "2026-11-19"     # Thursday after Sat Nov 14
    assert "Thursday, November 19" in replies[-1]


def test_parse_commitment_dates_and_vague():
    assert deadlines.parse_commitment("by 11/20", MON).date().isoformat() == "2026-11-20"
    assert deadlines.parse_commitment("December 3rd", MON).date().isoformat() == "2026-12-03"
    assert deadlines.parse_commitment("by 1/5", MON).date().isoformat() == "2027-01-05"
    assert deadlines.parse_commitment("we'll get to it eventually", MON) is None
    assert deadlines.parse_commitment("I'm not going to fix that", MON) is None


def test_status_and_time_left():
    due = MON + timedelta(days=3)
    assert deadlines.status_at(due, MON) == "open"
    assert deadlines.status_at(due, MON + timedelta(days=8)) == "missed"
    assert deadlines.status_at(due, MON + timedelta(days=8), "escalated") == "escalated"
    tl = deadlines.time_left(due, MON + timedelta(days=4))
    assert tl["overdue"] and tl["days"] == 1
    assert deadlines.worst_severity(["routine", "emergency", "urgent"]) == "emergency"


# ---------------- evidence hashing
def test_sha256_stable_and_ids():
    h = evidence.sha256_bytes(b"hello")
    assert h == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert evidence.evidence_id_for(h, "S-abcdef1234").startswith("E-2cf24dba5fb0a30e")
    assert evidence.storage_path(h, "image/jpeg").endswith(f"/{h[:2]}/{h}.jpg")


# ---------------- vision helpers
def test_dedup_merges_same_type():
    dets = [
        {"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.7, "evidence_id": "E1", "evidence_note": "stain", "severity_hint": "urgent"},
        {"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.9, "evidence_id": "E2", "evidence_note": "stain 2", "severity_hint": "urgent"},
        {"violation_type": "EXPOSED_WIRING", "confidence": 0.8, "evidence_id": "E2", "evidence_note": "outlet", "severity_hint": "emergency"},
        {"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.5, "evidence_id": "E1", "evidence_note": "stain", "severity_hint": "routine"},
    ]
    out = vision.dedup(dets)
    assert [o["violation_type"] for o in out] == ["WATER_DAMAGE_MOLD", "EXPOSED_WIRING"]
    assert out[0]["confidence"] == 0.9 and out[0]["evidence_ids"] == ["E1", "E2"]
    assert out[0]["notes"] == ["stain", "stain 2"]


def test_threshold_labels():
    d = vision.apply_threshold({"violation_type": "PEST_EVIDENCE", "confidence": 0.4}, 0.6)
    assert not d["certain"] and "verify in person" in d["label"]


def test_detection_schema_rejects_unknown_type():
    with pytest.raises(Exception):
        vision.Detection(violation_type="ALIENS", confidence=0.9)


def test_severity_seasonal():
    from datetime import date
    assert severity_for("NO_HEAT", date(2026, 1, 10)) == "emergency"
    assert severity_for("NO_HEAT", date(2026, 7, 10)) == "urgent"
    assert severity_for("BROKEN_WINDOW", date(2026, 12, 1)) == "urgent"
    assert severity_for("BROKEN_WINDOW", date(2026, 6, 1)) == "routine"


# ---------------- addresses
def test_normalize_and_match_address():
    assert properties.normalize_address("1234 Demo Street, Apt 5, Madison WI 53703") == "1234 DEMO ST"
    assert properties.normalize_address("415 West Mifflin St.") == "415 W MIFFLIN ST"
    cands = ["1234 DEMO ST", "1243 DEMO ST", "415 W MIFFLIN ST"]
    assert properties.best_match("1234 demo st", cands) == "1234 DEMO ST"
    assert properties.best_match("415 W Miflin Street", cands) == "415 W MIFFLIN ST"
    assert properties.best_match("999 DEMO ST", cands) is None


# ---------------- collective
def test_summarize_neighbors_excludes_me():
    reps = [
        {"unit_hash": "me", "violation_category": "HEAT"},
        {"unit_hash": "a", "violation_category": "HEAT"},
        {"unit_hash": "a", "violation_category": "HEAT"},
        {"unit_hash": "b", "violation_category": "HEAT"},
        {"unit_hash": "c", "violation_category": "PESTS"},
    ]
    s = collective.summarize_neighbors(reps, "me")
    assert s["households"] == 3 and s["reports"] == 4
    assert s["by_category"][0] == {"category": "HEAT", "households": 2}


# ---------------- scoring
def test_grade_cuts():
    assert [landlords.grade_for(x) for x in (-1, -0.2, 0.2, 0.7, 1.5)] == ["A", "B", "C", "D", "F"]


def test_compute_scores_ranks_bad_owner_worse():
    now = datetime(2026, 11, 1)
    owners = [{"owner_id": "good"}, {"owner_id": "bad"}, {"owner_id": "mid"}]
    props = [{"property_id": "g1", "owner_id": "good", "units": 10}, {"property_id": "b1", "owner_id": "bad", "units": 10},
             {"property_id": "m1", "owner_id": "mid", "units": 10}]

    def rep(pid, days_ago, fix_days, sev="urgent"):
        d = now - timedelta(days=days_ago)
        return {"property_id": pid, "reported_at": d.isoformat(), "severity": sev,
                "fixed_at": (d + timedelta(days=fix_days)).isoformat() if fix_days is not None else None,
                "status": "fixed" if fix_days is not None else "open"}

    reports = [rep("g1", 100, 3), rep("m1", 100, 15), rep("m1", 50, 15)] + \
              [rep("b1", 30 * k + 5, 60, "emergency") for k in range(6)] + [rep("b1", 2, None)]
    rows = {r["owner_id"]: r for r in landlords.compute_scores(owners, props, reports, now)}
    assert rows["bad"]["score"] > rows["mid"]["score"] > rows["good"]["score"]
    assert rows["bad"]["open_issues"] == 1 and rows["bad"]["repeat_buildings"] == 1


# ---------------- listing verdict
def test_verdict_rules():
    v = [{"name": "Water stains / visible mold", "severity": "urgent", "certain": True}]
    bad_hist = {"heat_reports_recent": 6, "open_issues": 9, "owner": {"grade": "D"}}
    assert listing.verdict(v, bad_hist)["level"] == "dont_sign"
    assert listing.verdict(v, {"heat_reports_recent": 0, "open_issues": 0, "owner": {"grade": "A"}})["level"] == "ask_first"
    assert listing.verdict([], {"heat_reports_recent": 0, "open_issues": 0, "owner": {"grade": "A"}})["level"] == "sign"
