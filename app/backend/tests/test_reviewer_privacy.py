"""The legal reviewer's personal name must not appear in anything public: API responses and generated PDFs (letters,
evidence packet, addendum, complaint drafts) on the public demo, or any git-tracked file. Public files show the role
label "Legal Reviewer"; the approvals themselves are unchanged.

This file deliberately contains no personal name. The names to look for come from the original approval record in git
history (commit aeb7598, before the relabel) and from the owner's private, git-ignored audit record when present."""
import json
import os
import re
import subprocess
import zlib
from pathlib import Path

os.environ["DATA_BACKEND"] = "local"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABRICKS_HOST"] = ""
os.environ["DATABRICKS_TOKEN"] = ""
os.environ["DATABRICKS_CONFIG_PROFILE"] = ""  # tests must never reach a real workspace

import pytest
from fastapi.testclient import TestClient

from .test_e2e import png

ROOT = Path(__file__).resolve().parents[3]
LABEL = "Legal Reviewer"
ORIGINAL_RECORD_COMMIT = "aeb7598"  # approvals applied and deployed (2026-11-14), original reviewer field


def _git(*args: str) -> str | None:
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True,
                              encoding="utf-8").stdout
    except Exception:
        return None


def _private_names() -> set[str]:
    names: set[str] = set()
    old = _git("show", f"{ORIGINAL_RECORD_COMMIT}:app/backend/code_sections_verified.json")
    if old:
        names |= set(json.loads(old).get("reviewers", {}).values())
    audit = ROOT / ".private" / "legal_review_audit.json"
    if audit.exists():
        names |= {a["reviewer"] for a in json.loads(audit.read_text(encoding="utf-8")).get("approvals", [])}
    names = {n.strip() for n in names if n and n.strip() and n.strip().lower() != LABEL.lower()}
    # Also catch each part of a full name (e.g. a surname alone in a byline)
    return names | {p for n in names for p in n.split() if len(p) >= 4}


NAMES = _private_names()


def _pdf_text(b: bytes) -> str:
    """Raw bytes plus every inflated stream (reportlab compresses page content)."""
    parts = [b]
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", b, re.S):
        try:
            parts.append(zlib.decompress(m.group(1)))
        except zlib.error:
            pass
    return b"\n".join(parts).decode("latin-1")


def _assert_no_names(text: str, where: str):
    low = text.lower()
    hits = [n for n in NAMES if n.lower() in low]
    assert not hits, f"reviewer's personal name exposed in {where}"


# ---------------------------------------------------------------- the approvals file (always checked)
def test_public_approvals_file_uses_only_the_role_label():
    raw = json.loads((ROOT / "app" / "backend" / "code_sections_verified.json").read_text(encoding="utf-8"))
    assert set(raw["reviewers"].values()) == {LABEL}
    note = raw["reviewer_identity"]
    assert "withheld" in note and "display label" in note and "not a claim of professional or independent legal" in note
    assert "not mean the reviewer is a lawyer" in raw["review_meaning"]
    # Approvals unchanged: exactly the three verified citations
    assert raw["mapping"] == {"LEAK_PLUMBING": ["27.05(2)(j)"], "DAMAGED_SURFACES": ["27.05(2)(g)1."],
                              "NO_HEAT": ["27.04(2)(h)"]}


def test_private_audit_record_is_never_committed_or_bundled():
    if _git("rev-parse", "--git-dir") is None:
        pytest.skip("not a git checkout")
    assert _git("check-ignore", ".private/legal_review_audit.json"), ".private/ must be git-ignored"
    assert not (_git("ls-files", ".private") or "").strip()
    assert ".private" in (ROOT / ".dockerignore").read_text(encoding="utf-8").split()


# ---------------------------------------------------------------- history-free checks (always run, e.g. shallow clones)
# Any "reviewer: X", "reviewed by X", "approved by (the) X" attribution must name only these (the second is ordinance
# text: "approved by the Building Inspection Division").
_ATTRIBUTION = re.compile(r"(?i:reviewer|reviewed by|approved by|approver|signed by)\W{0,4}(?:the\s+|project's\s+)?"
                          r"\**([A-Z][a-z]+(?:[ \t]+[A-Z][a-z]+)+)")
_ALLOWED_ATTRIBUTIONS = {LABEL, "Building Inspection Division"}


def _attributions(text: str) -> set[str]:
    return {m.group(1) for m in _ATTRIBUTION.finditer(text)} - _ALLOWED_ATTRIBUTIONS


def _tracked_text_files():
    if _git("rev-parse", "--git-dir") is None:
        pytest.skip("not a git checkout")
    for f in (_git("ls-files") or "").splitlines():
        p = ROOT / f
        if not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        b = p.read_bytes()
        yield f, (_pdf_text(b) if f.lower().endswith(".pdf") else b.decode("utf-8", "ignore"))


def test_tracked_files_attribute_reviews_only_to_the_role_label():
    bad = {f: sorted(a) for f, t in _tracked_text_files() if (a := _attributions(t))}
    assert not bad, f"review attributed to a personal name: {bad}"


def test_review_csv_reviewer_column_holds_only_the_label():
    import csv
    rows = list(csv.DictReader((ROOT / "eval" / "code_review.csv").open(encoding="utf-8")))
    assert {r["reviewer"].strip() for r in rows} <= {"", LABEL}
    assert sorted(r["type_id"] for r in rows if r["reviewer"].strip()) == ["DAMAGED_SURFACES", "LEAK_PLUMBING", "NO_HEAT"]


def test_attribution_check_catches_a_personal_name():
    fake = "Jane" + " Example"  # built at runtime so this file itself passes the tracked-file scan
    assert _attributions(f"**Verified** (reviewer: {fake}, 2026-11-14)") == {fake}
    assert _attributions(f"approved by the reviewer, {fake}, on 2026-11-14") == {fake}
    assert _attributions(f"Reviewed by {fake}") == {fake}
    assert _attributions("Reviewer: **Legal Reviewer**. approved by the Building Inspection Division") == set()


# ---------------------------------------------------------------- every tracked file (name known)
def test_no_tracked_file_contains_the_reviewers_name():
    if not NAMES:
        pytest.skip("original reviewer record not available (no git history and no private audit record)")
    files = (_git("ls-files") or "").splitlines()
    assert files
    for f in files:
        p = ROOT / f
        if not p.is_file() or p.stat().st_size > 5_000_000:
            continue
        b = p.read_bytes()
        text = _pdf_text(b) if f.lower().endswith(".pdf") else b.decode("utf-8", "ignore")
        _assert_no_names(text, f)


# ---------------------------------------------------------------- public demo: responses and generated documents
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


def test_public_demo_outputs_do_not_expose_the_reviewer(client, monkeypatch):
    """Always runs: no review attribution to anyone but the label; plus the known names when available."""
    from app.backend import config, main
    monkeypatch.setattr(config, "PUBLIC_DEMO", True)
    monkeypatch.setattr(config, "RATE_LIMIT_POSTS", 0)
    main._POSTS.clear()
    seen: list[tuple[str, str]] = []

    def j(r, where):
        assert r.status_code == 200, (where, r.text)
        seen.append((where, r.text))
        return r.json()

    def pdf(path):
        r = client.get(path)
        assert r.status_code == 200 and r.content[:4] == b"%PDF", path
        seen.append((path, _pdf_text(r.content)))

    x = j(client.post("/api/listing/xray", data={"address": "1234 Demo St"},
                      files=[("files", ("a.png", png(1, 2, 3), "image/png"))]), "listing")
    pdf(f"/api/listing/{x['scan_id']}/addendum.pdf")
    s = j(client.post("/api/scans", data={"mode": "walkthrough", "address": "1234 Demo St", "unit": "9"}), "scan")
    j(client.post(f"/api/scans/{s['scan_id']}/frames",
                  files=[("files", (f"f{i}.png", png(200, 30 * i, 50), "image/png")) for i in range(3)]), "frames")
    # The verified citations still show (no heat -> 27.04(2)(h), verified, exact official text)
    v = j(client.post(f"/api/scans/{s['scan_id']}/manual", json={"type_id": "NO_HEAT"}), "manual")["violations"]
    heat = next(x for x in v if x["violation_type"] == "NO_HEAT")
    assert heat["code_sections"][0]["section_id"] == "27.04(2)(h)" and heat["code_sections"][0]["verified"]
    case = j(client.post("/api/cases", json={"scan_id": s["scan_id"]}), "case")
    rid = case["request_id"]
    for tone in ("friendly", "formal", "final"):
        j(client.post(f"/api/cases/{rid}/letter", json={"tone": tone}), f"letter {tone}")
        pdf(f"/api/cases/{rid}/letter.pdf")
    pdf(f"/api/cases/{rid}/packet.pdf")
    st = j(client.post(f"/api/cases/{rid}/call/start"), "call")
    for line in client.get("/api/calls/demo-script").json()["lines"]:
        if j(client.post(f"/api/calls/{st['call_id']}/say", json={"text": line}), "call line")["done"]:
            break
    j(client.post(f"/api/cases/{rid}/simulate", json={"days": 8}), "simulate")
    j(client.post(f"/api/cases/{rid}/escalate"), "complaint draft")
    j(client.post(f"/api/cases/{rid}/joint"), "joint complaint")
    j(client.get(f"/api/cases/{rid}"), "case page")
    for path in ("/api/meta", "/api/health", "/api/code/match?q=no%20heat", "/api/owners/O-DEMO",
                 "/api/buildings/P-DEMO-1234"):
        j(client.get(path), path)
    j(client.post("/api/genie/ask", json={"question": client.get("/api/meta").json()["sample_questions"][0]}), "genie")
    assert len(seen) > 20
    for where, text in seen:
        _assert_no_names(text, where)
        assert not _attributions(text), f"review attributed to a personal name in {where}"
    main._POSTS.clear()


# ---------------------------------------------------------------- approval tool keeps names private
def _code_parse():
    import importlib.util
    spec = importlib.util.spec_from_file_location("code_parse", ROOT / "scripts" / "code_parse.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_approval_tool_writes_only_the_label_publicly_and_needs_a_real_name_for_new_approvals():
    cp = _code_parse()
    prev = {"mapping": {"NO_HEAT": ["27.04(2)(h)"]}, "reviewers": {"NO_HEAT": LABEL}}
    rows = [{"type_id": "NO_HEAT", "reviewer": LABEL}, {"type_id": "LOCKS", "reviewer": "A. Person"},
            {"type_id": "PESTS", "reviewer": "Legal reviewer"}, {"type_id": "WINDOWS", "reviewer": " "}]
    # Existing approval re-applied with the label: fine. New approval with a real name: name kept privately only.
    public, entries, errors = cp.split_reviewers({"NO_HEAT": ["27.04(2)(h)"], "LOCKS": ["27.05(2)(h)"]}, rows, prev)
    assert not errors
    assert public == {"NO_HEAT": LABEL, "LOCKS": LABEL}
    assert entries == [{"type_id": "LOCKS", "section_ids": ["27.05(2)(h)"], "reviewer": "A. Person"}]
    # A new approval with only the public label, or with no reviewer, is refused (safeguard kept)
    _, _, errors = cp.split_reviewers({"PESTS": ["27.07(2)(d)"], "WINDOWS": ["27.05(2)(h)"]}, rows, prev)
    assert len(errors) == 2 and any("actual name" in e for e in errors) and any("needs a reviewer" in e for e in errors)
