# Databricks notebook source
# MAGIC %md
# MAGIC # FixIt Madison: YOLO26-OBB ceiling-damage experiment (isolated)
# MAGIC Runs on your **existing** notebook compute: **Serverless GPU, AI Runtime v6 (A10G)**. It creates no compute, no
# MAGIC tables and no Volumes, and doesn't touch the FixIt App, its data, Genie or legal citations.
# MAGIC
# MAGIC Everything lives in this notebook's folder (`.../fixit-yolo-ceiling/`):
# MAGIC `bundle/` (the verified 150/50/50 dataset + scripts + official pretrained weights) is unpacked to
# MAGIC local disk for training; results are copied back to `outputs/` in this folder and logged to MLflow.
# MAGIC
# MAGIC **Order:** run cells 1–6 (setup + checks + a short timing probe), read the estimate, then cells 7–9 (train,
# MAGIC save, evaluate once). Cell 10 (yolo26s) is optional and off by default.

# COMMAND ----------

# 1. Configuration and GPU check (records the runtime's PyTorch so the install can't replace it)
import os, json, torch
NB_PATH = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
WS_DIR = "/Workspace" + os.path.dirname(NB_PATH)            # this notebook's folder (your workspace home)
MLFLOW_EXPERIMENT = os.path.dirname(NB_PATH) + "/yolo_ceiling_mlflow"
LOCAL = "/tmp/yolo_ceiling_work"                            # fast local disk; thrown away with the session
MAX_TRAIN_MINUTES = 30                                      # refuse the full run if the probe projects more than this
RUN_SMALL = False                                           # yolo26s-obb comparison: off unless you set True
assert torch.cuda.is_available(), "No GPU: attach this notebook to Serverless GPU (AI Runtime v6) first."
before = {"torch": torch.__version__, "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
          "gpu_mem_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)}
try:
    import torchvision; before["torchvision"] = torchvision.__version__
except ImportError:
    before["torchvision"] = None
os.makedirs("/tmp/yolo_setup", exist_ok=True)
json.dump(before, open("/tmp/yolo_setup/before.json", "w"))
with open("/tmp/yolo_setup/constraints.txt", "w") as f:       # pip may NOT change the runtime's torch/torchvision
    f.write(f"torch=={torch.__version__}\n" + (f"torchvision=={before['torchvision']}\n" if before["torchvision"] else ""))
print(json.dumps(before, indent=1)); print("bundle parts:", len([f for f in os.listdir(WS_DIR + "/bundle") if ".part" in f]))

# COMMAND ----------

# MAGIC %pip install -q ultralytics==8.4.196 -c /tmp/yolo_setup/constraints.txt

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# 3. Post-install compatibility check: same torch, CUDA still works, torchvision NMS on GPU, OpenCV imports
import json, torch, torchvision, cv2, ultralytics
before = json.load(open("/tmp/yolo_setup/before.json"))
assert torch.__version__ == before["torch"], f"torch changed: {before['torch']} -> {torch.__version__}"
assert torch.cuda.is_available()
b = torch.tensor([[0, 0, 10, 10], [1, 1, 11, 11]], dtype=torch.float32, device="cuda")
torchvision.ops.nms(b, torch.tensor([0.9, 0.8], device="cuda"), 0.5)
print("OK | torch", torch.__version__, "| torchvision", torchvision.__version__, "| ultralytics", ultralytics.__version__,
      "| opencv", cv2.__version__, "| gpu", torch.cuda.get_device_name(0))

# COMMAND ----------

# 4. Unpack the bundle to local disk; install the bundled plotting font (no internet needed)
import os, shutil, zipfile, sys
NB_PATH = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
WS_DIR = "/Workspace" + os.path.dirname(NB_PATH)
MLFLOW_EXPERIMENT = os.path.dirname(NB_PATH) + "/yolo_ceiling_mlflow"
LOCAL, MAX_TRAIN_MINUTES, RUN_SMALL = "/tmp/yolo_ceiling_work", 30, False
import hashlib, glob
shutil.rmtree(LOCAL, ignore_errors=True); os.makedirs(LOCAL)
# The workspace import API limits files to 10 MB, so the bundle was uploaded in parts: join, verify, unpack.
parts = sorted(glob.glob(WS_DIR + "/bundle/yolo_ceiling_bundle.zip.part*"))
blob = b"".join(open(p, "rb").read() for p in parts)
expected = open(WS_DIR + "/bundle/yolo_ceiling_bundle.sha256").read().strip()
assert hashlib.sha256(blob).hexdigest() == expected, "bundle hash mismatch: re-upload the parts"
open(LOCAL + "/bundle.zip", "wb").write(blob)
zipfile.ZipFile(LOCAL + "/bundle.zip").extractall(LOCAL)
print(f"bundle OK ({len(parts)} parts, {len(blob) / 1e6:.1f} MB, sha256 verified)")
PKG = LOCAL + "/yolo_ceiling"
from ultralytics.utils import USER_CONFIG_DIR
for f in os.listdir(PKG + "/fonts"):
    shutil.copy(f"{PKG}/fonts/{f}", USER_CONFIG_DIR / f)
os.chdir(PKG); sys.path.insert(0, PKG)
print(sorted(os.listdir(PKG)))

# COMMAND ----------

# 5. Leakage / integrity check against the selection manifest (stops on any problem)
import csv, hashlib, collections
rows = list(csv.DictReader(open(f"{PKG}/selection_manifest.csv", encoding="utf-8")))
want = {"train": 150, "valid": 50, "test": 50}
problems = []
by_split = collections.defaultdict(set)
for r in rows:
    p = f"{PKG}/dataset_250/{r['selected_split']}/images/{r['image']}"
    if r["selected_split"] != r["original_split"]:
        problems.append(f"{r['image']}: moved between partitions")
    if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != r["sha256"]:
        problems.append(f"{r['image']}: missing or hash mismatch")
    by_split[r["selected_split"]].add(r["sha256"])
for s, n in want.items():
    on_disk = len(os.listdir(f"{PKG}/dataset_250/{s}/images"))
    if on_disk != n or len(by_split[s]) != n:
        problems.append(f"{s}: {on_disk} files / {len(by_split[s])} manifest hashes, expected {n}")
groups = {s: {r["dup_group"] for r in rows if r["selected_split"] == s} for s in want}
if by_split["test"] & (by_split["train"] | by_split["valid"]) or groups["test"] & (groups["train"] | groups["valid"]) \
        or groups["valid"] & groups["train"]:
    problems.append("a test/valid photo (or a rotated copy of it) is also in another split")
for w, h in json.load(open(f"{PKG}/weights/SHA256SUMS.json")).items():
    if hashlib.sha256(open(f"{PKG}/weights/{w}", "rb").read()).hexdigest() != h:
        problems.append(f"weights {w}: hash mismatch")
assert not problems, problems
print("OK: 150/50/50 verified against the manifest; no cross-split duplicates; weights verified")

# COMMAND ----------

# 6. Quota/timing probe: 2 epochs on train/valid only (never the test split); projects the full-run time.
#    Free Edition limits are shown in the workspace UI, not via an API: check your remaining serverless GPU usage
#    before running cell 7. The full run is refused if the projection exceeds MAX_TRAIN_MINUTES.
import time, train_yolo
t = time.time()
train_yolo.main(["--model", "weights/yolo26n-obb.pt", "--epochs", "2", "--name", "probe_yolo26n", "--workers", "2"])
probe_min = (time.time() - t) / 60
projected = probe_min / 2 * 50 * 1.15                    # 50 epochs + ~15% for the final validation and plots
print(f"probe: {probe_min:.1f} min for 2 epochs -> projected full run <= {projected:.0f} min (early stopping may end sooner)")
FULL_RUN_OK = projected <= MAX_TRAIN_MINUTES
print("FULL_RUN_OK =", FULL_RUN_OK)

# COMMAND ----------

# 7. Train yolo26n-obb: up to 50 epochs, patience 10, 640 px, seed 42. MLflow tracks params/metrics/artifacts.
assert FULL_RUN_OK, "Projected time exceeds MAX_TRAIN_MINUTES: not starting (raise it deliberately if you accept)."
os.environ["MLFLOW_TRACKING_URI"] = "databricks"
os.environ["MLFLOW_EXPERIMENT_NAME"] = MLFLOW_EXPERIMENT
os.environ["MLFLOW_RUN"] = "yolo26n-obb_train"
train_yolo.main(["--model", "weights/yolo26n-obb.pt", "--workers", "2"])

# COMMAND ----------

# 8. Save weights, curves and run info to durable storage (this folder/outputs), before evaluation
def save(run):
    src, dst = f"{PKG}/runs/{run}", f"{WS_DIR}/outputs/runs/{run}"
    shutil.copytree(src, dst, dirs_exist_ok=True)
    print("saved", dst, sorted(os.listdir(dst)))
save("yolo26n-obb")
print(json.load(open(f"{PKG}/runs/yolo26n-obb/run_info.json")))

# COMMAND ----------

# 9. Evaluate the best checkpoint ONCE on the untouched 50-image test split; compare with Llama 4 Maverick.
#    Refuses to run again if a test result already exists (no repeated test evaluation).
import evaluate, mlflow
RUN = "yolo26n-obb"
done = f"{WS_DIR}/outputs/results/{RUN}/metrics.json"
assert not os.path.exists(done), f"Test evaluation already exists at {done}: not re-evaluating."
m = evaluate.main(["--weights", f"runs/{RUN}/weights/best.pt"])
shutil.copytree(f"{PKG}/results/{RUN}", f"{WS_DIR}/outputs/results/{RUN}", dirs_exist_ok=True)
mlflow.set_experiment(MLFLOW_EXPERIMENT)
with mlflow.start_run(run_name=f"{RUN}_test_eval"):
    mlflow.log_params({"weights": f"runs/{RUN}/weights/best.pt", "split": "test", "conf_operating": 0.25})
    mlflow.log_metrics({f"test_{k}": v for k, v in m["overall"].items()})
    for c, v in m["per_class"].items():
        mlflow.log_metrics({f"test_{c}_{k}": v[k] for k in ("precision", "recall", "mAP50", "mAP50-95")})
    mlflow.log_metrics({"test_fp_conf025": m["operating_point"]["false_positives"],
                        "test_fn_conf025": m["operating_point"]["false_negatives"]})
    mlflow.log_artifacts(f"{PKG}/results/{RUN}", artifact_path="test_eval")
print(open(f"{PKG}/results/{RUN}/metrics.md").read())
displayHTML("".join(f'<img src="data:image/jpeg;base64,{__import__("base64").b64encode(open(f"{PKG}/results/{RUN}/examples/{f}","rb").read()).decode()}" width="640"><br>{f}<br>'
                    for f in sorted(os.listdir(f"{PKG}/results/{RUN}/examples"))))

# COMMAND ----------

# 10. OPTIONAL second experiment: yolo26s-obb (off by default; set RUN_SMALL = True deliberately to run it).
#     Same data/settings; probe first; its own single test evaluation.
if RUN_SMALL:
    t = time.time()
    train_yolo.main(["--model", "weights/yolo26s-obb.pt", "--epochs", "2", "--name", "probe_yolo26s", "--workers", "2"])
    proj_s = (time.time() - t) / 60 / 2 * 50 * 1.15
    assert proj_s <= MAX_TRAIN_MINUTES, f"yolo26s projected {proj_s:.0f} min > {MAX_TRAIN_MINUTES}"
    os.environ["MLFLOW_RUN"] = "yolo26s-obb_train"
    train_yolo.main(["--model", "weights/yolo26s-obb.pt", "--workers", "2"])
    save("yolo26s-obb")
    assert not os.path.exists(f"{WS_DIR}/outputs/results/yolo26s-obb/metrics.json")
    ms = evaluate.main(["--weights", "runs/yolo26s-obb/weights/best.pt"])
    shutil.copytree(f"{PKG}/results/yolo26s-obb", f"{WS_DIR}/outputs/results/yolo26s-obb", dirs_exist_ok=True)
    print(open(f"{PKG}/results/yolo26s-obb/metrics.md").read())
else:
    print("yolo26s-obb not run (RUN_SMALL = False).")
