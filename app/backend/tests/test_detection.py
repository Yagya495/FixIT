"""Photo-detection honesty: alarm absence, tenant reports, evidence association, repeat uploads (2026-11-14).

The "photos" are small synthetic PNG fixtures standing in for a clean room and for alarm-related scenes; the vision
model is stubbed per image so the rules are tested deterministically (live model quality is measured separately with
scripts/eval_vision.py on real/staged photos).
"""
import os
import struct
import zlib

os.environ["DATA_BACKEND"] = "local"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABRICKS_HOST"] = ""
os.environ["DATABRICKS_TOKEN"] = ""
os.environ["DATABRICKS_CONFIG_PROFILE"] = ""

import pytest
from fastapi.testclient import TestClient

from app.backend.services import vision
from app.backend.services.vision import BASIS_TENANT, BASIS_VERIFY, BASIS_VISIBLE_ALARM, FrameResult, Detection


def png(r, g, b, w=24, h=18) -> bytes:
    raw = b"".join(b"\x00" + bytes([r, g, b]) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


CLEAN_ROOM = png(235, 225, 205)       # bedroom, ceiling visible, no alarm in frame
COVERED_ALARM = png(250, 250, 250)    # smoke alarm with a plastic bag over it
EMPTY_MOUNT = png(200, 200, 210)      # base plate on the ceiling, no alarm attached
WATER_STAIN = png(150, 110, 60)
OPEN_OUTLET = png(90, 90, 90)

# What a (sometimes over-eager) model says about each fixture.
MODEL = {
    CLEAN_ROOM: [
        {"violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.81,
         "evidence_note": "Bedroom ceiling visible with no smoke detector in frame"},
        {"violation_type": "CO_DETECTOR_MISSING", "confidence": 0.7, "evidence_note": "No CO alarm near the bedroom",
         "alarm_observation": "no_alarm_visible"},
    ],
    COVERED_ALARM: [{"violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.88,
                     "evidence_note": "Smoke alarm covered with a plastic bag", "alarm_observation": "covered_or_obstructed"}],
    EMPTY_MOUNT: [{"violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.93,
                   "evidence_note": "Round plate on the ceiling", "alarm_observation": "removed_mount_visible"}],
    WATER_STAIN: [{"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.8, "evidence_note": "Brown stain on ceiling"}],
    OPEN_OUTLET: [{"violation_type": "EXPOSED_WIRING", "confidence": 0.77, "evidence_note": "Outlet with no cover plate"}],
}
CALLS = []


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from app.backend import config
    d = tmp_path_factory.mktemp("detdata")
    config.DATA_DIR = d
    config.SQLITE_PATH = d / "fixit.db"
    config.LOCAL_EVIDENCE_DIR = d / "evidence"
    config.DATABRICKS_HOST = config.DATABRICKS_TOKEN = config.DATABRICKS_CONFIG_PROFILE = ""
    mp = pytest.MonkeyPatch()

    def fake_live(image, mode, media_type="image/jpeg"):
        CALLS.append(image)
        return FrameResult(detections=[Detection(**x) for x in MODEL.get(image, [])], scene="bedroom")

    mp.setattr(vision, "analyze_frame_live", fake_live)
    from app.backend.main import app
    with TestClient(app) as c:
        yield c
    mp.undo()


def scan(client, *photos, unit="77"):
    s = client.post("/api/scans", data={"mode": "walkthrough", "address": "1234 Demo St", "unit": unit}).json()
    r = client.post(f"/api/scans/{s['scan_id']}/frames",
                    files=[("files", (f"p{i}.png", p, "image/png")) for i, p in enumerate(photos)])
    assert r.status_code == 200, r.text
    return s["scan_id"], r.json()


# ---------------------------------------------------------------- pure rules
@pytest.mark.parametrize("note,expected", [
    ("Bedroom ceiling visible with no smoke detector in frame", None),
    ("No CO alarm near the bedroom", None),
    ("Missing smoke detector", None),
    ("Smoke detector light is off, may not work", None),       # never infer function from a still photo
    ("Smoke alarm on ceiling, looks fine", None),
    ("Ceiling is not covered and there is no alarm", None),     # negation beats a damage word
    ("Ceiling smoke detector appears covered with a plastic bag", BASIS_VISIBLE_ALARM),
    ("Detector hanging by its wires", BASIS_VISIBLE_ALARM),
    ("Empty smoke alarm base plate on the bedroom ceiling", BASIS_VERIFY),
    ("Battery compartment open and empty", BASIS_VERIFY),
])
def test_alarm_note_classification(note, expected):
    assert vision.classify_alarm_note(note) == expected


def test_screen_detection_rules():
    base = {"violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.9}
    assert vision.screen_detection({**base, "evidence_note": "x", "alarm_observation": "no_alarm_visible"}) is None
    assert vision.screen_detection({**base, "evidence_note": "x", "alarm_observation": "alarm_present"}) is None
    # Observation and note disagree ("covered" claimed, note says no alarm): trust neither.
    assert vision.screen_detection({**base, "evidence_note": "No alarm in frame",
                                    "alarm_observation": "covered_or_obstructed"}) is None
    m = vision.screen_detection({**base, "evidence_note": "Round plate", "alarm_observation": "removed_mount_visible"})
    assert m["basis"] == BASIS_VERIFY and vision.classify_alarm_note(m["evidence_note"]) == BASIS_VERIFY
    w = vision.screen_detection({"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.5, "evidence_note": "stain"})
    assert w["basis"] == "photo"


def test_verify_in_person_is_never_certain():
    d = vision.apply_threshold({"violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.99, "basis": BASIS_VERIFY})
    assert not d["certain"] and d["label"] == vision.VERIFY_LABEL


def test_prompts_and_cues_forbid_absence_findings():
    from app.backend.services.taxonomy import BY_ID
    for t in vision.ALARM_TYPES:
        cues = BY_ID[t]["visual_cues"].lower()
        assert "never report this because no" in cues and "no detector in bedroom" not in cues
    assert "NEVER report these types because no alarm appears" in vision.SYSTEM_WALKTHROUGH
    assert "missing smoke detectors on visible ceilings" not in vision.SYSTEM_LISTING
    assert "near sleeping area" not in BY_ID["CO_DETECTOR_MISSING"]["name"]


def test_scripted_listing_fallback_has_no_absence_finding():
    from app.backend.services import demo_cache
    for d in demo_cache.LISTING_SCENARIO + demo_cache.WALKTHROUGH_SCENARIO:
        assert vision.screen_detection(d) is not None, d


def test_reportable_skips_open_duplicates_and_unconfirmed_alarms():
    from app.backend.services.cases import reportable
    vio = [{"violation_type": "WATER_DAMAGE_MOLD"}, {"violation_type": "EXPOSED_WIRING"},
           {"violation_type": "SMOKE_DETECTOR_MISSING", "verify_in_person": True}]
    assert [v["violation_type"] for v in reportable(vio, {"WATER_DAMAGE_MOLD"})] == ["EXPOSED_WIRING"]


# ---------------------------------------------------------------- through the API
def test_clean_room_produces_no_alarm_finding(client):
    _, res = scan(client, CLEAN_ROOM)
    assert res["violations"] == []
    out = res["frames"][0]["screened_out"]
    assert {o["violation_type"] for o in out} == {"SMOKE_DETECTOR_MISSING", "CO_DETECTOR_MISSING"}
    assert all("can't show" in o["reason"] for o in out)


def test_visible_alarm_conditions(client):
    _, res = scan(client, COVERED_ALARM)
    (v,) = res["violations"]
    assert v["certain"] and v["bases"] == [BASIS_VISIBLE_ALARM]
    assert v["observations"][0]["evidence_id"] == res["frames"][0]["evidence_id"]

    _, res = scan(client, EMPTY_MOUNT)
    (v,) = res["violations"]
    assert not v["certain"] and v["verify_in_person"] and v["label"] == vision.VERIFY_LABEL  # despite 0.93
    assert v["observations"][0]["basis_text"] == "Needs an in-person check"


def test_tenant_report_is_preserved_and_not_tied_to_a_photo(client):
    sid, res = scan(client, CLEAN_ROOM)
    assert res["violations"] == []
    r = client.post(f"/api/scans/{sid}/manual",
                    json={"type_id": "SMOKE_DETECTOR_MISSING", "note": "Tenant reports the alarm doesn't sound when tested"})
    (v,) = r.json()["violations"]
    assert v["tenant_reported"] and v["certain"] and v["bases"] == [BASIS_TENANT]
    assert v["evidence_ids"] == [] and v["observations"][0]["evidence_id"] is None   # the clean photo isn't cited
    case = client.post("/api/cases", json={"scan_id": sid}).json()
    assert "Reported by the tenant." in case["letter_text"]


def test_each_finding_cites_its_own_photo(client):
    _, res = scan(client, WATER_STAIN, OPEN_OUTLET, EMPTY_MOUNT)
    ev = [f["evidence_id"] for f in res["frames"]]
    by_type = {v["violation_type"]: v for v in res["violations"]}
    assert by_type["WATER_DAMAGE_MOLD"]["evidence_ids"] == [ev[0]]
    assert by_type["EXPOSED_WIRING"]["evidence_ids"] == [ev[1]]
    assert by_type["SMOKE_DETECTOR_MISSING"]["evidence_ids"] == [ev[2]]
    for v in res["violations"]:
        assert [o["evidence_id"] for o in v["observations"]] == v["evidence_ids"]
    assert by_type["WATER_DAMAGE_MOLD"]["notes"] == ["Brown stain on ceiling"]


def test_repeat_upload_in_same_scan_adds_nothing(client):
    sid, first = scan(client, WATER_STAIN)
    n = len(CALLS)
    r = client.post(f"/api/scans/{sid}/frames", files=[("files", ("again.png", WATER_STAIN, "image/png"))]).json()
    assert len(CALLS) == n                                  # model not called again
    assert r["frames"][0]["repeat"] and len(r["violations"]) == 1
    assert r["violations"][0]["evidence_ids"] == first["violations"][0]["evidence_ids"]
    assert len(r["violations"][0]["observations"]) == 1


def test_second_case_does_not_duplicate_building_reports(client):
    from app.backend import db
    from app.backend.services.synthetic import unit_hash
    for _ in range(2):
        sid, _res = scan(client, WATER_STAIN, EMPTY_MOUNT, unit="88")
        client.post("/api/cases", json={"scan_id": sid})
    prop = db.q1("SELECT property_id FROM {silver.scans} WHERE scan_id = :s", {"s": sid})["property_id"]
    rows = db.q("SELECT violation_type FROM {gold.reports} WHERE property_id = :p AND unit_hash = :u AND source = 'fixit'",
                {"p": prop, "u": unit_hash(prop, "88")})
    assert [r["violation_type"] for r in rows] == ["WATER_DAMAGE_MOLD"]   # once; the unconfirmed mount not at all


def test_legacy_absence_rows_are_not_findings(client):
    from app.backend import db
    from app.backend.services import scans
    sid, _ = scan(client, WATER_STAIN)
    db.insert("silver.detections", {"detection_id": "D-legacy-1", "scan_id": sid, "evidence_id": None,
                                    "violation_type": "SMOKE_DETECTOR_MISSING", "confidence": 0.6, "bbox": None,
                                    "note": "Bedroom ceiling visible with no smoke detector in frame",
                                    "model_endpoint": "fallback", "created_at": "2026-11-01T00:00:00+00:00"})
    types = {v["violation_type"] for v in scans.rebuild_violations(sid)}
    assert types == {"WATER_DAMAGE_MOLD"}
