"""Run the unchanged app Llama 4 Maverick vision call on experiment 2's 36 VALIDATION images (for threshold/hybrid
tuning without touching the test set). Read-only use of app code; no DB, no Databricks writes, no cache.
Run with the APP venv."""
import json, os, sys, time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", "fixit"); os.environ["DEMO_MODE"] = "false"
sys.path.insert(0, str(REPO))
from app.backend import config  # noqa: E402
from app.backend.services import vision  # noqa: E402
D = HERE.parent / "dataset_full" / "valid" / "images"


def one(p):
    t = time.perf_counter()
    try:
        res = vision.analyze_frame_live(p.read_bytes(), "walkthrough", "image/jpeg")
        dets = []
        for d in res.detections:
            raw = d.model_dump()
            if vision.screen_detection(raw) is not None:
                dets.append({"type": d.violation_type, "confidence": d.confidence, "bbox": d.bbox})
        err = None
    except Exception as e:
        dets, err = [], f"{type(e).__name__}: {str(e)[:100]}"
    return {"image": p.name, "seconds": round(time.perf_counter() - t, 2), "detections": dets, "error": err}


with ThreadPoolExecutor(max_workers=config.VISION_CONCURRENCY) as pool:
    out = list(pool.map(one, sorted(D.iterdir())))
json.dump({"endpoint": config.VISION_ENDPOINT, "results": out}, open(HERE / "llama_valid_predictions.json", "w"), indent=1)
print("done", len(out), "errors", sum(1 for r in out if r["error"]))
