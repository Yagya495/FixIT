"""Run FixIt's real AI code paths against live endpoints (no DB writes). Shows whether output is live.

  set DATABRICKS_CONFIG_PROFILE=fixit & python scripts/live_pipeline_check.py --vision <ep> --chat <ep> [image ...]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vision", required=True)
    ap.add_argument("--chat", required=True)
    ap.add_argument("images", nargs="*")
    a = ap.parse_args()
    os.environ["VISION_ENDPOINT"], os.environ["CHAT_ENDPOINT"] = a.vision, a.chat
    os.environ["DEMO_MODE"] = "false"
    from app.backend import config, llm
    from app.backend.services import calls, vision
    from scripts.dbx_check import COLORS, png

    config.VISION_ENDPOINT, config.CHAT_ENDPOINT, config.DEMO_MODE = a.vision, a.chat, False
    print("models configured:", llm.available(), "| host:", llm._host())

    imgs = [(Path(p).name, Path(p).read_bytes(), "image/png" if p.lower().endswith(".png") else "image/jpeg") for p in a.images]
    imgs = imgs or [("blank-blue.png", png(COLORS["blue"], 320, 240), "image/png")]
    for name, data, mt in imgs:
        for mode in ("walkthrough", "listing"):
            t0 = time.time()
            try:
                res = vision.analyze_frame_live(data, mode, mt)
                print(f"vision[{mode}] {name}: LIVE ok in {time.time() - t0:.1f}s scene={res.scene} "
                      f"detections={[(d.violation_type, round(d.confidence, 2)) for d in res.detections]}")
            except Exception as e:
                print(f"vision[{mode}] {name}: FAILED {type(e).__name__}: {str(e)[:200]}")

    transcript = ("AI: Hi, this is an automated AI assistant calling on behalf of your tenant at 1234 Demo St, unit 9.\n"
                  "Landlord: Hello, who's calling?\nAI: I'm calling about 3 issues. When can these repairs be completed?\n"
                  "Landlord: Look, we're busy this week. I can probably get someone out there Thursday.")
    now = datetime(2026, 11, 14, 16, 0)
    t0 = time.time()
    data, source = calls.extract(transcript, now)
    print(f"call extraction: source={source} in {time.time() - t0:.1f}s -> {data}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
