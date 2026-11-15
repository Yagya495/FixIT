"""Pack what Colab needs into yolo_ceiling_bundle.zip (dataset_250 + scripts + Llama predictions, if present)."""
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
out = HERE / "yolo_ceiling_bundle.zip"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for p in (HERE / "dataset_250").rglob("*"):
        if p.is_file():
            z.write(p, Path("yolo_ceiling") / p.relative_to(HERE))
    for f in ("train_yolo.py", "evaluate.py", "selection_manifest.csv", "selection_summary.json",
              "results/llama_test_predictions.json"):
        if (HERE / f).exists():
            z.write(HERE / f, Path("yolo_ceiling") / f)
print(out, round(out.stat().st_size / 1e6, 1), "MB")
