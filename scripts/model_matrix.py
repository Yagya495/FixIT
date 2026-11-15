"""Test many serving endpoints at once (chat nonce, N random-color vision trials, embeddings). Never prints secrets.

  python scripts/model_matrix.py --profile fixit --chat a,b --vision a,b,c --embed x,y --trials 3
"""
from __future__ import annotations

import argparse
import base64
import json
import random
import secrets
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dbx_check import COLORS, REFUSED_PROFILES, invoke, png  # noqa: E402


def text_of(resp: dict) -> str:
    c = resp["choices"][0]["message"]["content"]
    if isinstance(c, list):  # some models return parts (e.g. reasoning + text)
        c = " ".join(p.get("text", "") for p in c if isinstance(p, dict) and p.get("type", "text") == "text")
    return (c or "").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--chat", default="")
    ap.add_argument("--vision", default="")
    ap.add_argument("--embed", default="")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.profile in REFUSED_PROFILES:
        print("refused profile")
        return 2
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(profile=a.profile)
    out: dict = {"chat": {}, "vision": {}, "embed": {}}
    for ep in filter(None, a.chat.split(",")):
        nonce = secrets.token_hex(3)
        t0 = time.time()
        try:
            r = invoke(w, ep, {"messages": [{"role": "user", "content": f"Reply with exactly this code and nothing else: {nonce}"}],
                               "max_tokens": 200, "temperature": 0})
            t = text_of(r)
            ok = nonce in t
            out["chat"][ep] = {"pass": ok, "secs": round(time.time() - t0, 1), "reply": t[:60]}
        except Exception as e:
            out["chat"][ep] = {"pass": False, "error": str(e)[:160]}
        print("chat  ", ep, out["chat"][ep])
    for ep in filter(None, a.vision.split(",")):
        trials = []
        for _ in range(a.trials):
            color = random.choice(list(COLORS))
            b64 = base64.b64encode(png(COLORS[color])).decode()
            t0 = time.time()
            try:
                r = invoke(w, ep, {"messages": [{"role": "user", "content": [
                    {"type": "text", "text": "What single color fills this image? Answer with one word from: red, green, blue, yellow."},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
                    "max_tokens": 200, "temperature": 0})
                t = text_of(r).lower()
                trials.append({"expected": color, "got": t[:30], "pass": color in t, "secs": round(time.time() - t0, 1)})
            except Exception as e:
                trials.append({"expected": color, "error": str(e)[:160], "pass": False})
                break
        out["vision"][ep] = {"passed": sum(t["pass"] for t in trials), "of": len(trials), "trials": trials}
        print("vision", ep, f'{out["vision"][ep]["passed"]}/{len(trials)}', trials)
    for ep in filter(None, a.embed.split(",")):
        try:
            r = invoke(w, ep, {"input": ["smoke detector missing in bedroom"]})
            vec = r["data"][0]["embedding"]
            out["embed"][ep] = {"pass": bool(vec), "dims": len(vec)}
        except Exception as e:
            out["embed"][ep] = {"pass": False, "error": str(e)[:160]}
        print("embed ", ep, out["embed"][ep])
    if a.json:
        Path(a.json).write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
