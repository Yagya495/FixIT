"""Hardening for a public, anonymous deployment: static-file confinement, upload limits, rate limiting, and the
PUBLIC_DEMO mode (no Databricks, no live models, per-browser case lists, demo admin endpoints disabled)."""
import os

os.environ["DATA_BACKEND"] = "local"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABRICKS_HOST"] = ""
os.environ["DATABRICKS_TOKEN"] = ""
os.environ["DATABRICKS_CONFIG_PROFILE"] = ""  # tests must never reach a real workspace

import pytest
from fastapi.testclient import TestClient

from .test_e2e import png


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    from app.backend import config
    d = tmp_path_factory.mktemp("data")
    config.DATA_DIR = d
    config.SQLITE_PATH = d / "fixit.db"
    config.LOCAL_EVIDENCE_DIR = d / "evidence"
    config.DATABRICKS_HOST = config.DATABRICKS_TOKEN = config.DATABRICKS_CONFIG_PROFILE = ""
    from app.backend.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture
def public(monkeypatch):
    from app.backend import config, main
    monkeypatch.setattr(config, "PUBLIC_DEMO", True)
    monkeypatch.setattr(config, "RATE_LIMIT_POSTS", 0)
    main._POSTS.clear()
    return config


def _walkthrough(c, n=2):
    s = c.post("/api/scans", data={"mode": "walkthrough", "address": "1234 Demo St", "unit": "9"}).json()
    files = [("files", (f"f{i}.png", png(200, 30 * i, 50), "image/png")) for i in range(n)]
    r = c.post(f"/api/scans/{s['scan_id']}/frames", files=files)
    assert r.status_code == 200, r.text
    return s["scan_id"], r.json()


# ---------------------------------------------------------------- static files (all modes)
@pytest.mark.parametrize("path", [
    "/..%2f..%2fbackend%2fconfig.py", "/%2e%2e/%2e%2e/backend/config.py", "/..%5c..%5cbackend%5cconfig.py",
    "/%2e%2e/%2e%2e/%2e%2e/README.md",
])
def test_spa_route_cannot_read_files_outside_the_frontend(client, path):
    from app.backend import config
    if not config.STATIC_DIR.exists():
        pytest.skip("frontend not built")
    r = client.get(path)
    assert "Central configuration" not in r.text and "FixIt Madison**" not in r.text
    assert r.headers["content-type"].startswith("text/html")  # falls back to index.html


def test_spa_route_still_serves_frontend_files(client):
    from app.backend import config
    if not config.STATIC_DIR.exists():
        pytest.skip("frontend not built")
    assert client.get("/").headers["content-type"].startswith("text/html")
    assert client.get("/cases/RR-unknown").headers["content-type"].startswith("text/html")


# ---------------------------------------------------------------- upload limits (all modes)
def test_oversized_image_rejected(client, monkeypatch):
    from app.backend import config
    monkeypatch.setattr(config, "MAX_UPLOAD_BYTES", 1000)
    s = client.post("/api/scans", data={"mode": "walkthrough"}).json()
    big = png(1, 2, 3, w=200, h=200) + b"\0" * 2000
    r = client.post(f"/api/scans/{s['scan_id']}/frames", files=[("files", ("big.png", big, "image/png"))])
    assert r.status_code == 413


def test_too_many_files_rejected(client, monkeypatch):
    from app.backend import config
    monkeypatch.setattr(config, "MAX_FILES_PER_REQUEST", 2)
    s = client.post("/api/scans", data={"mode": "walkthrough"}).json()
    files = [("files", (f"f{i}.png", png(9, 9, i), "image/png")) for i in range(3)]
    assert client.post(f"/api/scans/{s['scan_id']}/frames", files=files).status_code == 413


# ---------------------------------------------------------------- rate limit
def test_rate_limit_applies_to_api_posts_only(client, monkeypatch):
    from app.backend import config, main
    monkeypatch.setattr(config, "RATE_LIMIT_POSTS", 3)
    main._POSTS.clear()
    codes = [client.post("/api/scans", data={"mode": "walkthrough"}).status_code for _ in range(5)]
    assert codes == [200, 200, 200, 429, 429]
    assert client.get("/api/health").status_code == 200  # reads are not limited
    main._POSTS.clear()


def test_rate_limit_is_per_client(client, monkeypatch):
    from app.backend import config, main
    monkeypatch.setattr(config, "RATE_LIMIT_POSTS", 1)
    main._POSTS.clear()
    a = {"x-forwarded-for": "203.0.113.1"}
    b = {"x-forwarded-for": "203.0.113.2"}
    assert client.post("/api/scans", data={"mode": "walkthrough"}, headers=a).status_code == 200
    assert client.post("/api/scans", data={"mode": "walkthrough"}, headers=a).status_code == 429
    assert client.post("/api/scans", data={"mode": "walkthrough"}, headers=b).status_code == 200
    main._POSTS.clear()


# ---------------------------------------------------------------- PUBLIC_DEMO
def test_public_demo_never_calls_live_models(client, public, monkeypatch):
    from app.backend import llm
    from app.backend.services import vision

    def boom(*a, **k):
        raise AssertionError("live model called on the public demo")
    monkeypatch.setattr(vision, "analyze_frame_live", boom)
    monkeypatch.setattr(llm.httpx, "post", boom)
    assert llm.available() is False
    with pytest.raises(llm.LLMUnavailable):
        llm._auth_headers()
    _, res = _walkthrough(client)
    assert {f["source"] for f in res["frames"]} == {"fallback"}  # labeled "Demo script" in the UI
    assert res["violations"]


def test_public_demo_health_flags(client, public, monkeypatch):
    monkeypatch.setattr(public, "LIVE_APP_URL", "https://example.invalid/app")
    h = client.get("/api/health").json()
    assert h["public_demo"] is True and h["models_configured"] is False and h["genie_configured"] is False
    assert h["live_app_url"] == "https://example.invalid/app"


def test_private_deployment_does_not_advertise_public_fields(client):
    h = client.get("/api/health").json()
    assert h["public_demo"] is False and h["live_app_url"] == ""


def test_public_demo_disables_admin_endpoints(client, public):
    assert client.post("/api/demo/reset").status_code == 403
    assert client.post("/api/demo/warm").status_code == 403


def test_public_demo_case_list_is_per_browser(client, public):
    scan_id, _ = _walkthrough(client)
    case = client.post("/api/cases", json={"scan_id": scan_id}).json()
    sid = client.cookies.get("fixit_sid")
    assert sid
    assert [c["request_id"] for c in client.get("/api/cases").json()] == [case["request_id"]]
    # A different visitor (new cookie) sees none of it
    with TestClient(client.app) as other:
        assert other.get("/api/cases").json() == []
        assert other.cookies.get("fixit_sid") not in (None, sid)
    # The case itself still opens by its link (unguessable id), e.g. when shared with a teammate
    assert client.get(f"/api/cases/{case['request_id']}").status_code == 200


def test_public_demo_genie_answers_sample_questions_without_genie(client, public):
    from app.backend.services import genie
    q = genie.SAMPLE_QUESTIONS[0]
    a = client.post("/api/genie/ask", json={"question": q}).json()
    assert a["source"] != "genie" and a["rows"]


def test_public_demo_forces_safe_config(monkeypatch):
    """Importing config with PUBLIC_DEMO=true clears every Databricks setting even if they are set."""
    import importlib
    from app.backend import config
    for k, v in {"PUBLIC_DEMO": "true", "DATA_BACKEND": "databricks", "DEMO_MODE": "false",
                 "DATABRICKS_HOST": "https://x.invalid", "DATABRICKS_TOKEN": "dapi-not-a-real-token",
                 "DATABRICKS_WAREHOUSE_ID": "w", "GENIE_SPACE_ID": "g"}.items():
        monkeypatch.setenv(k, v)
    saved = dict(vars(config))
    try:
        c = importlib.reload(config)
        assert c.PUBLIC_DEMO and c.DEMO_MODE and c.DATA_BACKEND == "local"
        assert not (c.DATABRICKS_HOST or c.DATABRICKS_TOKEN or c.DATABRICKS_WAREHOUSE_ID or c.GENIE_SPACE_ID)
        assert c.RATE_LIMIT_POSTS > 0 and c.MAX_UPLOAD_BYTES == 8 * 1024 * 1024
    finally:
        vars(config).clear()
        vars(config).update(saved)  # exact prior state (other modules' test paths included)
