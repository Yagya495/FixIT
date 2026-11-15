"""Exercise the deployed FixIt App's API end to end (as you, via your CLI profile's OAuth token; never printed).

  python scripts/app_smoke.py --profile fixit --url https://fixit-madison-....databricksapps.com
"""
from __future__ import annotations

import argparse
import struct
import sys
import time
import zlib

import httpx


def png(r, g, b, w=40, h=30):
    raw = b"".join(b"\x00" + bytes([r, g, b]) * w for _ in range(h))
    ch = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)  # noqa: E731
    return b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + ch(b"IDAT", zlib.compress(raw)) + ch(b"IEND", b"")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--url", required=True)
    a = ap.parse_args()
    if a.profile == "sleepsafe":
        return 2
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(profile=a.profile)
    c = httpx.Client(base_url=a.url.rstrip("/"), headers=w.config.authenticate(), timeout=120, follow_redirects=False)

    def step(name, fn):
        t0 = time.time()
        try:
            out = fn()
            print(f"PASS {name} ({time.time() - t0:.1f}s): {out}"[:400])
            return True
        except Exception as e:
            print(f"FAIL {name}: {type(e).__name__}: {str(e)[:300]}")
            return False

    def j(r):
        r.raise_for_status()
        return r.json()

    ok = step("health", lambda: j(c.get("/api/health")))
    ok &= step("UI index", lambda: (lambda r: (r.status_code, "FixIt" in r.text))(c.get("/")))
    state = {}

    def listing():
        x = j(c.post("/api/listing/xray", data={"address": "1234 Demo St"},
                     files=[("files", (f"l{i}.png", png(30 * i, 90, 140), "image/png")) for i in range(3)]))
        return x["verdict"]["label"], x["history"]["heat_reports_recent"], x["history"]["owner"]["grade"], x["source"]

    def scan():
        s = j(c.post("/api/scans", data={"mode": "walkthrough", "address": "1234 Demo St", "unit": "9"}))
        r = j(c.post(f"/api/scans/{s['scan_id']}/frames", files=[("files", ("w.png", png(200, 60, 60), "image/png"))]))
        if not r["violations"]:
            r = j(c.post(f"/api/scans/{s['scan_id']}/manual", json={"type_id": "NO_HEAT", "note": "smoke test"}))
            r["source"] = "manual"
        state["scan"], state["ev"] = s["scan_id"], (r.get("frames") or [{}])[0].get("evidence_id")
        return [v["violation_type"] for v in r["violations"]], r.get("source")

    def evidence():
        return j(c.get(f"/api/scans/{state['scan']}"))["evidence"][0]["volume_path"]

    def case():
        cs = j(c.post("/api/cases", json={"scan_id": state["scan"]}))
        state["rid"] = cs["request_id"]
        return cs["collective"]["headline"]

    def call():
        st = j(c.post(f"/api/cases/{state['rid']}/call/start"))
        out = None
        for line in j(c.get("/api/calls/demo-script"))["lines"]:
            out = j(c.post(f"/api/calls/{st['call_id']}/say", json={"text": line}))
            if out["done"]:
                break
        return out["result"]["commitment_date"], out["result"]["source"]

    def escalate():
        j(c.post(f"/api/cases/{state['rid']}/simulate", json={"days": 8}))
        return j(c.post(f"/api/cases/{state['rid']}/escalate"))["deadline"]["status"]

    def joint():
        return len(j(c.post(f"/api/cases/{state['rid']}/joint"))["units"])

    def pdf():
        return c.get(f"/api/cases/{state['rid']}/packet.pdf").content[:5]

    def genie():
        g = j(c.post("/api/genie/ask", json={"question": "Which owners have the most open heat issues this month?"}))
        return g["source"], g["rows"][:1]

    for name, fn in [("listing x-ray", listing), ("scan", scan), ("evidence in UC Volume", evidence), ("case + collective", case),
                     ("simulated call", call), ("+8 days -> escalate", escalate), ("joint complaint", joint),
                     ("evidence packet PDF", pdf), ("genie (demo mode)", genie)]:
        ok &= step(name, fn)
    print("\nALL PASSED" if ok else "\nSOME STEPS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
