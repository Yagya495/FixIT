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


def test_no_review_means_placeholders_only():
    from app.backend.services import taxonomy
    if taxonomy.verified_review()["sections"]:
        pytest.skip("a human-approved review is present")
    assert all(s["verified"] == 0 for s in taxonomy.code_section_rows())
    assert [v["code_sections"] for v in taxonomy.taxonomy_rows()] == [v["code_sections"] for v in VIOLATION_TYPES]


def test_approved_review_applies_mapping_and_verified_flag(monkeypatch):
    from app.backend.services import taxonomy
    fake = {"mapping": {"SMOKE_DETECTOR_MISSING": ["27.99(1)"]},
            "sections": [{"section_id": "27.99(1)", "title": "Fixture", "text": "fixture text", "source_doc": "ch27.pdf",
                          "page": 4, "url": None}]}
    monkeypatch.setattr(taxonomy, "verified_review", lambda: fake)
    rows = {v["type_id"]: v for v in taxonomy.taxonomy_rows()}
    assert rows["SMOKE_DETECTOR_MISSING"]["code_sections"] == ["27.99(1)"]
    unreviewed = next(v for v in VIOLATION_TYPES if v["type_id"] == "WATER_DAMAGE_MOLD")
    assert rows["WATER_DAMAGE_MOLD"]["code_sections"] == unreviewed["code_sections"]  # keeps placeholders
    secs = {s["section_id"]: s for s in taxonomy.code_section_rows()}
    assert secs["27.99(1)"]["verified"] == 1 and secs["CH27-SMOKE"]["verified"] == 0


def test_code_match_flags_official_text():
    seed = dict(SEED_CODE_SECTIONS[0])
    parsed = {"section_id": "27.99", "title": "Smoke detectors", "text": "smoke detector required",
              "source_doc": "/Volumes/fixit/raw/code_docs/ch27.pdf", "page": 7, "url": None, "verified": 0}
    hits = {h["section_id"]: h for h in code_match.rank_sections("smoke detector", [seed, parsed], k=2)}
    assert hits["27.99"]["official_text"] is True and hits["27.99"]["verified"] is False and hits["27.99"]["page"] == 7
    assert hits["CH27-SMOKE"]["official_text"] is False


def test_eval_strips_exif_but_keeps_image_segments():
    from scripts.eval_vision import strip_jpeg_metadata
    seg = lambda m, body: bytes([0xFF, m]) + (len(body) + 2).to_bytes(2, "big") + body  # noqa: E731
    jpeg = (b"\xff\xd8" + seg(0xE0, b"JFIF\x00") + seg(0xE1, b"Exif\x00\x00GPS-SECRET") + seg(0xDB, b"\x00" * 4)
            + b"\xff\xda" + b"\x00\x0c imagedata" + b"\xff\xd9")
    out = strip_jpeg_metadata(jpeg)
    assert b"GPS-SECRET" not in out and b"JFIF" in out and out.endswith(b"imagedata\xff\xd9")
    assert strip_jpeg_metadata(b"\x89PNG....") == b"\x89PNG...."


def test_vision_parse_drops_unknown_types_keeps_rest():
    reply = ('```json\n{"detections":[{"violation_type":"SMOKE_DETECTOR_MISSING","confidence":0.8},'
             '{"violation_type":"CRACKED_CEILING_FAN","confidence":0.9}],"scene":"bedroom"}\n```')
    res = vision._parse(reply)
    assert [d.violation_type for d in res.detections] == ["SMOKE_DETECTOR_MISSING"] and res.scene == "bedroom"


def test_delta_concurrency_conflicts_are_retried_for_updates_only(monkeypatch):
    from contextlib import contextmanager
    from app.backend import config, db

    calls = {"n": 0}

    class Cur:
        def execute(self, sql, params):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("[DELTA_CONCURRENT_APPEND.ROW_LEVEL_CHANGES] Transaction conflict detected")

    @contextmanager
    def fake_cursor():
        yield Cur()

    monkeypatch.setattr(config, "DATA_BACKEND", "databricks")
    monkeypatch.setattr(db, "_cursor", fake_cursor)
    monkeypatch.setattr(db.time, "sleep", lambda s: None)
    db.execute("UPDATE {silver.deadlines} SET status = 'met' WHERE request_id = :r", {"r": "x"})
    assert calls["n"] == 2  # retried once, then succeeded
    calls["n"] = 0
    with pytest.raises(RuntimeError):  # inserts are not blindly retried
        db.execute("INSERT INTO {silver.calls} (call_id) VALUES (:c)", {"c": "x"})


def test_databricks_host_normalized():
    from app.backend import config
    assert config._normalize_host("dbc-123.cloud.databricks.com") == "https://dbc-123.cloud.databricks.com"
    assert config._normalize_host("https://x.cloud.databricks.com/") == "https://x.cloud.databricks.com"
    assert config._normalize_host("") == ""


def test_timestamp_params_bound_as_datetimes_only_on_databricks(monkeypatch):
    from app.backend import config, db
    p = {"a": "2026-11-14T16:52:42+00:00", "b": "2026-11-19T17:00", "c": "Thursday", "d": 3, "e": "2026-11-14"}
    monkeypatch.setattr(config, "DATA_BACKEND", "local")
    assert db._bind(p) == p
    monkeypatch.setattr(config, "DATA_BACKEND", "databricks")
    out = db._bind(p)
    assert isinstance(out["a"], datetime) and out["a"].utcoffset() is not None
    assert out["b"] == datetime(2026, 11, 19, 17, 0)
    assert out["c"] == "Thursday" and out["d"] == 3 and out["e"] == "2026-11-14"


def test_auto_matched_sections_never_marked_verified(monkeypatch):
    # Parsed (verified=1) sections exist but the taxonomy still points at placeholder ids: the automatic
    # fallback match must not be shown as a verified section number.
    parsed = [{"section_id": "27.99(1)", "title": "Smoke detectors", "text": "smoke detector required in each bedroom",
               "source_doc": "ch27.pdf", "page": 3, "url": None, "verified": 1}]
    monkeypatch.setattr(code_match, "_cache", parsed)
    monkeypatch.setattr(code_match, "_type_map", {})
    hits = code_match.sections_for_type("SMOKE_DETECTOR_MISSING")
    assert hits and all(h["verified"] is False for h in hits)


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
