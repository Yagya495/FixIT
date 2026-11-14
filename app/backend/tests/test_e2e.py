"""End-to-end through the API on the local backend with DEMO_MODE fallbacks (no Databricks needed)."""
import os
import struct
import zlib

os.environ["DATA_BACKEND"] = "local"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABRICKS_HOST"] = ""
os.environ["DATABRICKS_TOKEN"] = ""

import pytest
from fastapi.testclient import TestClient


def png(r, g, b, w=32, h=24) -> bytes:
    raw = b"".join(b"\x00" + bytes([r, g, b]) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from app.backend import config
    d = tmp_path_factory.mktemp("data")
    config.DATA_DIR = d
    config.SQLITE_PATH = d / "fixit.db"
    config.LOCAL_EVIDENCE_DIR = d / "evidence"
    config.DATABRICKS_HOST = config.DATABRICKS_TOKEN = ""
    from app.backend.main import app
    with TestClient(app) as c:
        yield c


def test_full_demo_flow(client):
    # Listing X-Ray
    files = [("files", (f"p{i}.png", png(40 * i, 100, 120), "image/png")) for i in range(5)]
    r = client.post("/api/listing/xray", data={"address": "1234 Demo Street"}, files=files)
    assert r.status_code == 200, r.text
    x = r.json()
    assert x["matched"] and x["verdict"]["level"] == "dont_sign"
    assert x["history"]["heat_reports_recent"] == 6 and x["history"]["owner"]["grade"] == "D"
    assert len(x["tour_questions"]) == 5 and "ADDENDUM" in x["addendum"]
    assert client.get(f"/api/listing/{x['scan_id']}/addendum.pdf").content[:4] == b"%PDF"

    # Walkthrough scan
    s = client.post("/api/scans", data={"mode": "walkthrough", "address": "1234 Demo St", "unit": "9"}).json()
    files = [("files", (f"f{i}.png", png(200, 30 * i, 50), "image/png")) for i in range(3)]
    res = client.post(f"/api/scans/{s['scan_id']}/frames", files=files).json()
    types = {v["violation_type"] for v in res["violations"]}
    assert types == {"SMOKE_DETECTOR_MISSING", "WATER_DAMAGE_MOLD", "EXPOSED_WIRING"}
    assert all(v["code_sections"] for v in res["violations"])
    ev = res["frames"][0]["evidence_id"]
    assert client.get(f"/api/evidence/{ev}/verify").json()["intact"]

    # Case + letter
    case = client.post("/api/cases", json={"scan_id": s["scan_id"]}).json()
    rid = case["request_id"]
    assert "Chapter 27" in case["letter_text"]
    for tone in ("friendly", "final"):
        assert client.post(f"/api/cases/{rid}/letter", json={"tone": tone}).json()["tone"] == tone
    assert client.get(f"/api/cases/{rid}/packet.pdf").content[:4] == b"%PDF"
    assert client.get(f"/api/cases/{rid}/letter.pdf").content[:4] == b"%PDF"

    # Collective
    col = case["collective"]
    assert col["neighbors"]["by_category"][0]["category"] == "HEAT"
    assert col["neighbors"]["by_category"][0]["households"] == 6
    assert len(col["other_buildings"]) == 3 and sum(b["open_issues"] for b in col["other_buildings"]) == 11

    # Simulated call
    st = client.post(f"/api/cases/{rid}/call/start").json()
    assert st["transcript"][0]["text"].startswith("Hi, this is an automated AI assistant")
    script = client.get("/api/calls/demo-script").json()["lines"]
    out = None
    for line in script:
        out = client.post(f"/api/calls/{st['call_id']}/say", json={"text": line}).json()
        if out["done"]:
            break
    assert out["done"] and out["result"]["commitment_date"]
    c2 = client.get(f"/api/cases/{rid}").json()
    assert c2["deadline"]["status"] == "open"

    # Time passes -> missed -> escalate
    c3 = client.post(f"/api/cases/{rid}/simulate", json={"days": 8}).json()
    assert c3["deadline"]["status"] == "missed"
    c4 = client.post(f"/api/cases/{rid}/escalate").json()
    assert c4["deadline"]["status"] == "escalated"
    assert c4["complaint"]["fields"]["Property address"]
    assert "not submit" in c4["complaint"]["submit_note"]

    # Joint complaint
    j = client.post(f"/api/cases/{rid}/joint").json()
    assert j["units"][0] == "Unit A" and len(j["units"]) == 7
    # Unit A is dated by the real report date, not the "+8 days" simulated clock.
    assert f"first reported {case['created_at'][:10]}" in j["text"].split("Unit A:", 1)[1].split("\n", 1)[0]

    # Landlord card, building page, map, genie
    oc = client.get("/api/owners/O-DEMO").json()
    assert oc["scores"]["grade"] == "D" and len(oc["buildings"]) == 4
    assert client.get("/api/buildings/P-DEMO-1234").json()["timeline"]
    assert len(client.get("/api/city/map").json()) > 1000
    for q in client.get("/api/meta").json()["sample_questions"]:
        a = client.post("/api/genie/ask", json={"question": q}).json()
        assert a["rows"], q
    top = client.post("/api/genie/ask", json={"question": "Which owners have the most open heat issues this month?"}).json()
    assert top["rows"][0]["owner"] == "Isthmus Edge Properties (demo)"


def test_same_photo_reused_across_and_within_scans(client):
    """Rehearsals reuse the same demo photos: that must never 500 (it used to collide on detection_id)."""
    img = png(10, 200, 30)
    for _ in range(2):  # two separate scans, same bytes
        s = client.post("/api/scans", data={"mode": "walkthrough", "address": "1234 Demo St", "unit": "9"}).json()
        r = client.post(f"/api/scans/{s['scan_id']}/frames",
                        files=[("files", ("a.png", img, "image/png")), ("files", ("dup.png", img, "image/png"))])
        assert r.status_code == 200, r.text
        assert r.json()["violations"]
    x = client.post("/api/listing/xray", data={"address": "1234 Demo St"}, files=[("files", ("a.png", img, "image/png"))])
    assert x.status_code == 200, x.text
