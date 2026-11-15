"""Video walkthrough path (2026-11-15): frames sampled in the browser arrive in small batches; the backend must keep
frame order and photo-to-finding association, run model calls in parallel safely, consolidate one problem seen in many
frames into one finding, skip repeated frames, and never report partly-failed analysis as "live".

Frames are synthetic PNGs and the vision model is stubbed per image (live quality: scripts/eval_vision.py).
"""
import random
import struct
import time
import zlib

import pytest
from fastapi.testclient import TestClient

from app.backend import config
from app.backend.services import demo_cache, scans, vision
from app.backend.services.vision import Detection, FrameResult


def png(r, g, b, w=20, h=14) -> bytes:
    raw = b"".join(b"\x00" + bytes([r, g, b]) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


# A 12-second walkthrough at 1 frame/s: clean (0-2), ceiling stain (3-8, seen from slightly different spots),
# uncovered outlet (9-10), clean (11). Every frame is a distinct image.
FRAMES = [png(230, 220, 200 + k) for k in range(12)]
STAIN = set(range(3, 9))
OUTLET = {9, 10}
FAIL: set[bytes] = set()
CALLS: list[bytes] = []


def model_says(image: bytes) -> list[dict]:
    k = FRAMES.index(image) if image in FRAMES else -1
    if k in STAIN:
        return [{"violation_type": "WATER_DAMAGE_MOLD", "confidence": 0.7 + k / 100, "evidence_note": f"Ceiling stain, frame {k}"}]
    if k in OUTLET:
        return [{"violation_type": "EXPOSED_WIRING", "confidence": 0.8, "evidence_note": f"Outlet without cover, frame {k}"}]
    return []


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    d = tmp_path_factory.mktemp("videodata")
    mp = pytest.MonkeyPatch()
    mp.setattr(config, "DATA_DIR", d)
    mp.setattr(config, "SQLITE_PATH", d / "fixit.db")
    mp.setattr(config, "LOCAL_EVIDENCE_DIR", d / "evidence")
    mp.setattr(config, "DATABRICKS_HOST", "")
    mp.setattr(config, "DATABRICKS_TOKEN", "")
    mp.setattr(config, "DATABRICKS_CONFIG_PROFILE", "")
    mp.setattr(config, "VISION_CONCURRENCY", 4)

    def fake_live(image, mode, media_type="image/jpeg"):
        CALLS.append(image)
        time.sleep(random.uniform(0, 0.03))          # out-of-order completion when run in parallel
        if image in FAIL:
            raise RuntimeError("endpoint timeout")
        return FrameResult(detections=[Detection(**x) for x in model_says(image)], scene="living room")

    mp.setattr(vision, "analyze_frame_live", fake_live)
    from app.backend.main import app
    with TestClient(app) as c:
        yield c
    mp.undo()


def new_scan(client, unit):
    return client.post("/api/scans", data={"mode": "walkthrough", "address": "1234 Demo St", "unit": unit}).json()["scan_id"]


def upload_batched(client, sid, frames, size=5):
    """What Scan.tsx does: consecutive batches with frame_offset/frame_total."""
    out = []
    for off in range(0, len(frames), size):
        part = frames[off:off + size]
        r = client.post(f"/api/scans/{sid}/frames",
                        files=[("files", (f"frame-{off + i}.jpg", p, "image/png")) for i, p in enumerate(part)],
                        data={"frame_offset": str(off), "frame_total": str(len(frames))})
        assert r.status_code == 200, r.text
        out.append(r.json())
    return out


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    CALLS.clear(); FAIL.clear()
    monkeypatch.setattr(config, "DEMO_MODE", False)
    yield


def test_batched_video_is_consolidated_with_correct_photos(client):
    sid = new_scan(client, "v1")
    resps = upload_batched(client, sid, FRAMES)
    assert [len(r["frames"]) for r in resps] == [5, 5, 2]
    frames = [f for r in resps for f in r["frames"]]
    assert [f["frame_index"] for f in frames] == list(range(12))
    assert all(r["source"] == "live" and r["model"] == config.VISION_ENDPOINT for r in resps)
    ev_of = {k: f["evidence_id"] for k, f in enumerate(frames)}
    assert len(set(ev_of.values())) == 12                                     # every frame saved as its own evidence

    scan = client.get(f"/api/scans/{sid}").json()
    by_type = {v["violation_type"]: v for v in scan["violations"]}
    assert set(by_type) == {"WATER_DAMAGE_MOLD", "EXPOSED_WIRING"}            # one finding per problem, not per frame
    stain = by_type["WATER_DAMAGE_MOLD"]
    # The stain spans batches 1 and 2; the finding cites exactly frames 3-8, each note next to ITS frame.
    assert sorted(stain["evidence_ids"]) == sorted(ev_of[k] for k in STAIN)
    assert {(o["evidence_id"], o["note"]) for o in stain["observations"]} == \
        {(ev_of[k], f"Ceiling stain, frame {k}") for k in STAIN}
    assert stain["confidence"] == pytest.approx(0.78)                         # max over the frames
    assert sorted(by_type["EXPOSED_WIRING"]["evidence_ids"]) == sorted(ev_of[k] for k in OUTLET)
    assert len(scan["evidence"]) == 12


def test_parallel_calls_keep_each_detection_on_its_own_frame(client):
    for attempt in range(3):                                                    # random sleeps -> different orders
        sid = new_scan(client, f"v2-{attempt}")
        r = client.post(f"/api/scans/{sid}/frames",
                        files=[("files", (f"f{i}.png", p, "image/png")) for i, p in enumerate(FRAMES)]).json()
        for k, f in enumerate(r["frames"]):
            assert f["frame_index"] == k
            assert [d["violation_type"] for d in f["detections"]] == [x["violation_type"] for x in model_says(FRAMES[k])]
            assert all(d["evidence_id"] == f["evidence_id"] for d in f["detections"])
        assert len(CALLS) == 12 * (attempt + 1)


def test_repeated_frames_are_skipped_within_and_across_batches(client):
    sid = new_scan(client, "v3")
    still = [FRAMES[4]] * 3 + [FRAMES[5]]                                      # tenant stood still: identical frames
    r1 = upload_batched(client, sid, still, size=2)
    flat = [f for r in r1 for f in r["frames"]]
    assert [f.get("repeat", False) for f in flat] == [False, True, True, False]
    assert len(CALLS) == 2                                                      # model called once per distinct frame
    r2 = upload_batched(client, sid, [FRAMES[4]])                               # same frame again in a later upload
    assert r2[0]["frames"][0]["repeat"] and len(CALLS) == 2
    stain = next(v for v in client.get(f"/api/scans/{sid}").json()["violations"] if v["violation_type"] == "WATER_DAMAGE_MOLD")
    assert len(stain["observations"]) == 2


def test_partly_failed_analysis_is_not_reported_as_live(client):
    FAIL.update({FRAMES[0], FRAMES[4]})
    sid = new_scan(client, "v4")
    r = client.post(f"/api/scans/{sid}/frames",
                    files=[("files", (f"f{i}.png", p, "image/png")) for i, p in enumerate(FRAMES[:6])]).json()
    assert r["source"] == "partial"
    assert r["source_counts"] == {"live": 4, "none": 2}
    assert [f["source"] for f in r["frames"]] == ["none", "live", "live", "live", "none", "live"]
    assert len(client.get(f"/api/scans/{sid}").json()["evidence"]) == 6          # unanalyzed frames are still evidence


def test_all_failed_is_none_and_names_no_model(client):
    FAIL.update(FRAMES[:2])
    sid = new_scan(client, "v5")
    r = client.post(f"/api/scans/{sid}/frames",
                    files=[("files", (f"f{i}.png", p, "image/png")) for i, p in enumerate(FRAMES[:2])]).json()
    assert r["source"] == "none" and r["model"] is None and r["violations"] == []


def test_scripted_fallback_is_the_same_batched_or_not(client, monkeypatch):
    """Demo Mode, model down, no cache: scripted detections depend on the frame's position in the WHOLE upload."""
    monkeypatch.setattr(config, "DEMO_MODE", True)
    FAIL.update(FRAMES)
    one = new_scan(client, "v6a")
    single = client.post(f"/api/scans/{one}/frames",
                         files=[("files", (f"f{i}.png", p, "image/png")) for i, p in enumerate(FRAMES)]).json()
    two = new_scan(client, "v6b")
    batched = upload_batched(client, two, FRAMES)
    types = lambda frames: [[d["violation_type"] for d in f["detections"]] for f in frames]  # noqa: E731
    assert types(single["frames"]) == types([f for r in batched for f in r["frames"]])
    assert all(r["source"] == "fallback" for r in batched)
    expected = [[d["violation_type"] for d in demo_cache.scripted_detections("walkthrough", k, 12)] for k in range(12)]
    assert types(single["frames"]) == expected


@pytest.mark.parametrize("sources,expected", [
    ([], "none"), (["none"], "none"), (["live", "live"], "live"), (["live", "none"], "partial"),
    (["cache", "live"], "cache"), (["fallback", "cache"], "fallback"), (["fallback", "none"], "partial"),
])
def test_overall_source(sources, expected):
    assert scans.overall_source(sources) == expected


def test_single_photo_upload_unchanged(client):
    sid = new_scan(client, "v7")
    r = client.post(f"/api/scans/{sid}/frames", files=[("files", ("p.png", FRAMES[9], "image/png"))]).json()
    assert r["source"] == "live" and r["frames"][0]["frame_index"] == 0
    assert [v["violation_type"] for v in r["violations"]] == ["EXPOSED_WIRING"]


def test_rate_limited_model_call_is_retried(monkeypatch):
    """A video sends many frames; a 429 from the pay-per-token endpoint is retried (bounded) instead of losing the frame."""
    import httpx
    from app.backend import llm

    replies = [httpx.Response(429, headers={"retry-after": "0"}), httpx.Response(503),
               httpx.Response(200, json={"choices": [{"message": {"content": "{\"detections\": []}"}}]})]
    sent, slept = [], []
    monkeypatch.setattr(llm, "available", lambda: True)
    monkeypatch.setattr(llm, "_host", lambda: "https://example.invalid")
    monkeypatch.setattr(llm, "_auth_headers", lambda: {})
    monkeypatch.setattr(llm.time, "sleep", slept.append)
    def fake_post(url, **kw):
        sent.append(url)
        r = replies[len(sent) - 1]
        r.request = httpx.Request("POST", url)
        return r
    monkeypatch.setattr(llm.httpx, "post", fake_post)
    assert llm.chat([{"role": "user", "content": "x"}], endpoint="e") == "{\"detections\": []}"
    assert len(sent) == 3 and slept == [0.0, 2.0]

    sent.clear()
    replies[:] = [httpx.Response(429) for _ in range(10)]
    with pytest.raises(llm.LLMUnavailable):
        llm.chat([{"role": "user", "content": "x"}], endpoint="e")
    assert len(sent) == llm.RETRIES + 1                                           # bounded: gives up, frame reported "none"
