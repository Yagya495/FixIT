"""Pack the Databricks bundle: verified dataset_250 + scripts + manifest + Llama baseline + official pretrained
weights (with SHA-256) + the Ultralytics plotting font, so training needs no internet besides PyPI."""
import hashlib
import json
import os
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / "databricks" / "yolo_ceiling_bundle.zip"
weights = ["yolo26n-obb.pt", "yolo26s-obb.pt"]
font = Path(os.environ.get("APPDATA", "")) / "Ultralytics" / "Arial.ttf"
sums = {w: hashlib.sha256((HERE / w).read_bytes()).hexdigest() for w in weights}
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted((HERE / "dataset_250").rglob("*")):
        if p.is_file():
            z.write(p, Path("yolo_ceiling") / p.relative_to(HERE))
    for f in ("train_yolo.py", "evaluate.py", "selection_manifest.csv", "selection_summary.json",
              "results/llama_test_predictions.json"):
        z.write(HERE / f, Path("yolo_ceiling") / f)
    for w in weights:
        z.write(HERE / w, Path("yolo_ceiling") / "weights" / w)
    z.writestr("yolo_ceiling/weights/SHA256SUMS.json", json.dumps(sums, indent=1))
    z.write(font, "yolo_ceiling/fonts/Arial.ttf")
print(out, round(out.stat().st_size / 1e6, 1), "MB", sums)
