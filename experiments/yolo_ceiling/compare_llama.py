"""Run the EXISTING Llama 4 Maverick vision call (app/backend/services/vision.analyze_frame_live, unchanged) on the 50
held-out TEST images and the clean holdout. Read-only use of app code: no database, no Databricks writes, no cache.
Run with the APP venv (it has the app's dependencies):

    PATH=<databricks cli>:$PATH .venv/Scripts/python.exe experiments/yolo_ceiling/compare_llama.py

Image-level mapping (Llama has no ceiling-specific classes):
  ceiling_crack, ceiling_hole                 -> DAMAGED_SURFACES
  ceiling_damp, ceiling_mold, ceiling_stain   -> WATER_DAMAGE_MOLD (LEAK_PLUMBING also accepted)
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).parent
REPO = HERE.parent.parent
os.environ.setdefault("DATABRICKS_CONFIG_PROFILE", "fixit")
os.environ["DEMO_MODE"] = "false"
sys.path.insert(0, str(REPO))
from app.backend import config  # noqa: E402
from app.backend.services import vision  # noqa: E402

NAMES = ["ceiling_crack", "ceiling_damp", "ceiling_hole", "ceiling_mold", "ceiling_stain"]
GROUP_OF_CLASS = {0: "surface", 2: "surface", 1: "moisture", 3: "moisture", 4: "moisture"}
GROUP_OF_TYPE = {"DAMAGED_SURFACES": "surface", "WATER_DAMAGE_MOLD": "moisture", "LEAK_PLUMBING": "moisture"}
D = HERE / "dataset_250"


def gt(label: Path) -> list[tuple[int, list[float]]]:
    out = []
    for line in label.read_text().splitlines():
        p = line.split()
        if p:
            out.append((int(p[0]), [float(x) for x in p[1:]]))
    return out


def run_one(img: Path):
    t = time.perf_counter()
    try:
        res = vision.analyze_frame_live(img.read_bytes(), "walkthrough", "image/jpeg")
        dets, err = [], None
        for d in res.detections:
            raw = d.model_dump()
            kept = vision.screen_detection(raw)
            if kept is None:
                continue
            dets.append({"type": d.violation_type, "confidence": d.confidence, "bbox": d.bbox,
                         "note": raw.get("evidence_note", ""), "certain": d.confidence >= config.CONFIDENCE_THRESHOLD})
    except Exception as e:  # recorded, never silently dropped
        dets, err = [], f"{type(e).__name__}: {str(e)[:120]}"
    return {"image": img.name, "seconds": round(time.perf_counter() - t, 2), "detections": dets, "error": err}


def main():
    items = [("test", p) for p in sorted((D / "test" / "images").iterdir())] + \
            [("clean", p) for p in sorted((D / "clean_holdout" / "images").iterdir())]
    with ThreadPoolExecutor(max_workers=config.VISION_CONCURRENCY) as pool:
        results = list(pool.map(lambda sp: run_one(sp[1]) | {"split": sp[0]}, items))
    for r in results:
        if r["split"] == "test":
            r["gt"] = [{"cls": c, "poly": poly} for c, poly in gt(D / "test" / "labels" / (Path(r["image"]).stem + ".txt"))]
    out = HERE / "results" / "llama_test_predictions.json"
    out.parent.mkdir(exist_ok=True)
    json.dump({"endpoint": config.VISION_ENDPOINT, "confidence_threshold": config.CONFIDENCE_THRESHOLD,
               "results": results}, open(out, "w"), indent=1)
    print("wrote", out, "| errors:", sum(1 for r in results if r["error"]))


if __name__ == "__main__":
    main()
