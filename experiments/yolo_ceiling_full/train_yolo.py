"""EXPERIMENT 2: fine-tune pretrained YOLO26-OBB on dataset_full (302 files / 155 photos train, 36 valid). The test
split is NOT used here. Same augmentation and batch as experiment 1, so differences come from the training data.

    python train_yolo.py --model yolo26n-obb.pt            # real run (GPU; refuses CPU unless --smoke or --allow-cpu)
    python train_yolo.py --model yolo26s-obb.pt
    python train_yolo.py --smoke                           # 1 epoch, 320 px, 20% of train: pipeline check only

Pinned: ultralytics==8.4.196 (AGPL-3.0; weights from the official Ultralytics assets, AGPL-3.0).
Augmentation choices (ceiling damage must stay realistic):
  - flips both ways and small rotations: a ceiling has no "up", and the export already contains rotated copies
  - mild brightness/saturation only, NO hue shift: colour separates stain (brown) / mold-like discoloration (dark) / damp
  - mosaic at 0.5 and switched off for the last 10 epochs; NO mixup, NO copy-paste (blended/pasted damage is unrealistic)
  - no shear / perspective
"""
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "dataset_full"


def runtime_yaml() -> Path:
    """data.yaml with an absolute path (works locally, on Colab and on Databricks)."""
    src = (DATA / "data.yaml").read_text(encoding="utf-8")
    out = HERE / "runs" / "data_runtime.yaml"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(src.replace("path: .", f"path: {DATA.as_posix()}"), encoding="utf-8")
    return out


def pick_batch(device: str) -> int:
    import torch
    if device == "cpu":
        return 8
    mem_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
    # Same batch as experiment 1 (16) so the comparison isolates the training data; ~19 steps/epoch on 302 files.
    return 16 if mem_gb >= 8 else 8


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolo26n-obb.pt")
    ap.add_argument("--epochs", type=int, default=100)
    ap.add_argument("--patience", type=int, default=15)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=0, help="0 = choose from GPU memory")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--allow-cpu", action="store_true")
    ap.add_argument("--name", default="", help="run folder name (default: model name)")
    ap.add_argument("--workers", type=int, default=-1, help="dataloader workers (-1 = 2 on CPU, 4 on GPU)")
    a = ap.parse_args(argv)

    import torch
    import ultralytics
    from ultralytics import YOLO, settings

    device = "0" if torch.cuda.is_available() else "cpu"
    if device == "cpu" and not (a.smoke or a.allow_cpu):
        sys.exit("No GPU found. Use the Colab notebook (yolo_ceiling_colab.ipynb) or --smoke for a pipeline check.")
    try:
        import mlflow  # noqa: F401
        os.environ.setdefault("MLFLOW_TRACKING_URI", (HERE / "mlruns").as_uri())
        os.environ.setdefault("MLFLOW_EXPERIMENT_NAME", "yolo_ceiling_full")
        settings.update({"mlflow": True})
    except ImportError:
        settings.update({"mlflow": False})

    name = a.name or (Path(a.model).stem + ("_smoke" if a.smoke else ""))
    args = dict(
        data=str(runtime_yaml()), task="obb", imgsz=320 if a.smoke else a.imgsz,
        epochs=1 if a.smoke else a.epochs, patience=a.patience, batch=a.batch or pick_batch(device),
        device=device, seed=42, deterministic=True, pretrained=True, project=str(HERE / "runs"), name=name,
        exist_ok=True, val=True, fraction=0.2 if a.smoke else 1.0, workers=a.workers if a.workers >= 0 else (2 if device == "cpu" else 4), plots=True,
        # augmentation (see docstring)
        hsv_h=0.0, hsv_s=0.3, hsv_v=0.3, degrees=10.0, translate=0.1, scale=0.3, shear=0.0, perspective=0.0,
        flipud=0.5, fliplr=0.5, mosaic=0.5, close_mosaic=10, mixup=0.0, copy_paste=0.0,
    )
    info = {"model": a.model, "ultralytics": ultralytics.__version__, "torch": torch.__version__,
            "python": platform.python_version(), "device": device,
            "gpu": torch.cuda.get_device_name(0) if device != "cpu" else None,
            "gpu_mem_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1) if device != "cpu" else None,
            "host": "colab" if "COLAB_RELEASE_TAG" in os.environ else ("databricks" if "DATABRICKS_RUNTIME_VERSION" in os.environ else "local"),
            "args": args, "smoke": a.smoke}
    print(json.dumps({k: info[k] for k in ("model", "ultralytics", "torch", "device", "gpu", "host")}))
    if Path(a.model).exists():
        import hashlib
        info["weights_sha256"] = hashlib.sha256(Path(a.model).read_bytes()).hexdigest()
    t = time.time()
    model = YOLO(a.model)                                  # local official checkpoint, or downloaded by name
    model.train(**args)
    info["train_minutes"] = round((time.time() - t) / 60, 1)
    run_dir = HERE / "runs" / name
    info["best"] = str(run_dir / "weights" / "best.pt")
    info["completed"] = (run_dir / "weights" / "best.pt").exists()
    json.dump(info, open(run_dir / "run_info.json", "w"), indent=1)
    print("run_info:", run_dir / "run_info.json", "| best.pt exists:", info["completed"])


if __name__ == "__main__":
    main()
