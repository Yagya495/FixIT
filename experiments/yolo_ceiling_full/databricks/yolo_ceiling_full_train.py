# Databricks notebook source
# MAGIC %md
# MAGIC # FixIt Madison: YOLO26n-OBB experiment 2 (full group-aware dataset)
# MAGIC Existing **Serverless GPU, AI Runtime v6 (A10G)** notebook compute only: no new compute, tables or Volumes; the FixIt
# MAGIC App, its data, Genie and legal citations are not touched. Experiment 1 (`fixit-yolo-ceiling/`) is not modified.
# MAGIC
# MAGIC Data: 302 training files (155 distinct photos, incl. rotated copies of training photos only), 36 validation photos,
# MAGIC and the **same 50 test images as experiment 1** (every other copy of those photos excluded), so the two models are
# MAGIC scored on identical images. Training: yolo26n-obb, 640 px, up to 100 epochs (fitted to the 30-min GPU limit
# MAGIC by the cell-6 probe), patience 15 if practical, seed 42, batch 16,
# MAGIC validation every epoch (best checkpoint = best validation fitness).
# MAGIC
# MAGIC **Order:** cells 1–5 (checks), 6 (timing probe -> epoch count; check quota), 7 (train), 8 (save), 9 (evaluate once + compare).

# COMMAND ----------

# 1. Configuration + GPU check; install ultralytics ONLY if the pinned version is missing (no restart otherwise)
import os, sys, json, subprocess, importlib.metadata as md, torch
NB_PATH = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
WS_DIR = "/Workspace" + os.path.dirname(NB_PATH)
assert torch.cuda.is_available(), "No GPU: attach this notebook to Serverless GPU (AI Runtime v6) first."
before = {"torch": torch.__version__, "cuda": torch.version.cuda, "gpu": torch.cuda.get_device_name(0),
          "gpu_mem_gb": round(torch.cuda.get_device_properties(0).total_memory / 1e9, 1)}
os.makedirs("/tmp/yolo_setup", exist_ok=True)
json.dump(before, open("/tmp/yolo_setup/before.json", "w"))
try:
    have = md.version("ultralytics")
except md.PackageNotFoundError:
    have = None
print(json.dumps(before), "| ultralytics present:", have)
if have != "8.4.196":
    cons = [f"torch=={torch.__version__}"]
    try:
        cons.append(f"torchvision=={md.version('torchvision')}")
    except md.PackageNotFoundError:
        pass
    open("/tmp/yolo_setup/constraints.txt", "w").write("\n".join(cons) + "\n")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ultralytics==8.4.196",
                           "-c", "/tmp/yolo_setup/constraints.txt"])
    print("installed ultralytics 8.4.196 (constrained to the runtime's torch); restarting Python")
    dbutils.library.restartPython()
else:
    print("ultralytics 8.4.196 already installed: no install, no restart")

# COMMAND ----------

# 2. Compatibility check: same torch as the runtime, CUDA works, torchvision NMS on GPU, OpenCV imports
import os, sys, json, torch, torchvision, cv2, ultralytics
before = json.load(open("/tmp/yolo_setup/before.json"))
assert torch.__version__ == before["torch"], f"torch changed: {before['torch']} -> {torch.__version__}"
assert torch.cuda.is_available() and ultralytics.__version__ == "8.4.196"
b = torch.tensor([[0, 0, 10, 10], [1, 1, 11, 11]], dtype=torch.float32, device="cuda")
torchvision.ops.nms(b, torch.tensor([0.9, 0.8], device="cuda"), 0.5)
print("OK | torch", torch.__version__, "| torchvision", torchvision.__version__, "| ultralytics", ultralytics.__version__,
      "| opencv", cv2.__version__, "| gpu", torch.cuda.get_device_name(0))

# COMMAND ----------

# 3. Join + verify + unpack the bundle (uploaded in <=10 MB parts) to local disk; install the bundled plotting font
import shutil, zipfile, hashlib, glob
NB_PATH = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
WS_DIR = "/Workspace" + os.path.dirname(NB_PATH)
MLFLOW_EXPERIMENT = os.path.dirname(NB_PATH) + "/yolo_ceiling_full_mlflow"
LOCAL, MAX_TRAIN_MINUTES, RUN = "/tmp/yolo_ceiling_full_work", 30, "yolo26n-obb_full"   # GPU safety limit
shutil.rmtree(LOCAL, ignore_errors=True); os.makedirs(LOCAL)
parts = sorted(glob.glob(WS_DIR + "/bundle/yolo_ceiling_full_bundle.zip.part*"))
blob = b"".join(open(p, "rb").read() for p in parts)
assert hashlib.sha256(blob).hexdigest() == open(WS_DIR + "/bundle/yolo_ceiling_full_bundle.sha256").read().strip(), \
    "bundle hash mismatch: re-upload the parts"
open(LOCAL + "/bundle.zip", "wb").write(blob)
zipfile.ZipFile(LOCAL + "/bundle.zip").extractall(LOCAL)
PKG = LOCAL + "/yolo_ceiling_full"
from ultralytics.utils import USER_CONFIG_DIR
for f in os.listdir(PKG + "/fonts"):
    shutil.copy(f"{PKG}/fonts/{f}", USER_CONFIG_DIR / f)
os.chdir(PKG); sys.path.insert(0, PKG)
print(f"bundle OK ({len(parts)} parts, {len(blob) / 1e6:.1f} MB, sha256 verified):", sorted(os.listdir(PKG)))

# COMMAND ----------

# 4. Dataset integrity + leakage checks (stops on any problem)
import csv, collections
rows = list(csv.DictReader(open(f"{PKG}/selection_manifest.csv", encoding="utf-8")))
summ = json.load(open(f"{PKG}/selection_summary.json"))
problems, sha = [], collections.defaultdict(set)
for r in rows:
    p = f"{PKG}/dataset_full/{r['selected_split']}/images/{r['image']}"
    if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != r["sha256"]:
        problems.append(f"{r['image']}: missing or hash mismatch")
    sha[r["selected_split"]].add(r["sha256"])
for s, st in summ["splits"].items():
    n = len(os.listdir(f"{PKG}/dataset_full/{s}/images"))
    if n != st["image_files"] or len(sha[s]) != st["image_files"]:
        problems.append(f"{s}: {n} files / {len(sha[s])} hashes, expected {st['image_files']}")
grp = {s: {r["dup_group"] for r in rows if r["selected_split"] == s} for s in ("train", "valid", "test")}
if grp["train"] & grp["valid"] or grp["train"] & grp["test"] or grp["valid"] & grp["test"]:
    problems.append("a photo (or a rotated/flipped copy) appears in two splits")
exp1_test = {r["sha256"] for r in csv.DictReader(open(f"{PKG}/exp1/selection_manifest.csv", encoding="utf-8"))
             if r["selected_split"] == "test"}
if sha["test"] != exp1_test:
    problems.append("test split is not identical to experiment 1's test images")
for w, h in json.load(open(f"{PKG}/weights/SHA256SUMS.json")).items():
    if hashlib.sha256(open(f"{PKG}/weights/{w}", "rb").read()).hexdigest() != h:
        problems.append(f"weights {w}: hash mismatch")
assert not problems, problems
print("OK:", {s: (st["image_files"], st["distinct_photos"]) for s, st in summ["splits"].items()},
      "(files, photos) | no cross-split photos | test == experiment 1 test | weights verified")

# COMMAND ----------

# 5. Output folder guard: experiment 2 writes ONLY to this notebook's folder (never to fixit-yolo-ceiling/)
OUT_WS = f"{WS_DIR}/outputs"
assert "fixit-yolo-ceiling-full" in WS_DIR and not os.path.exists(f"{OUT_WS}/results/{RUN}/metrics.json"), \
    "unexpected folder, or experiment 2 was already evaluated"
os.makedirs(OUT_WS, exist_ok=True)
print("outputs ->", OUT_WS.split("/fixit-yolo-ceiling-full")[-1] or "/", "| MLflow ->", MLFLOW_EXPERIMENT.split("/")[-1])

# COMMAND ----------

# 6. Timing probe v2 (train/valid only; the test split is never touched). 5 epochs from the pretrained checkpoint into
#    a throwaway run folder. Uses Ultralytics' per-epoch cumulative training time (results.csv "time") to separate:
#      fixed overhead = setup (model, data scan/cache) + final best.pt validation/plots
#      first-epoch extra (warm-up, cuDNN autotune) and steady-state seconds per epoch.
#    Then picks the largest epoch count <= 100 that fits MAX_TRAIN_MINUTES with buffers. Free Edition GPU quota is shown
#    in the workspace UI only: check it before cell 7.
import time, math, statistics, csv as _csv, torch
PROBE = "probe_timing"
shutil.rmtree(f"{PKG}/runs/{PROBE}", ignore_errors=True)
torch.cuda.reset_peak_memory_stats()
t0 = time.time()
train_yolo.main(["--model", "weights/yolo26n-obb.pt", "--epochs", "5", "--patience", "15", "--name", PROBE, "--workers", "2"])
wall = time.time() - t0
peak_gb = torch.cuda.max_memory_allocated() / 1e9
pinfo = json.load(open(f"{PKG}/runs/{PROBE}/run_info.json"))
assert pinfo["device"] != "cpu" and pinfo["gpu"] and peak_gb > 0.2,     f"GPU NOT used: device={pinfo['device']} gpu={pinfo['gpu']} peak={peak_gb:.2f} GB"
r = [{k.strip(): v for k, v in x.items()} for x in _csv.DictReader(open(f"{PKG}/runs/{PROBE}/results.csv"))]
cum = [float(x["time"]) for x in r]                       # seconds since the training loop started, per epoch
deltas = [b - a for a, b in zip(cum, cum[1:])]
steady = statistics.median(deltas)                        # s/epoch incl. per-epoch validation
first_extra = max(0.0, cum[0] - steady)
overhead = wall - cum[-1]                                 # setup + final validation/plots (paid once)
# Buffers: probe epochs run without mosaic (close_mosaic=10 > 5 epochs) and epoch times vary -> x1.3 per epoch;
# fixed costs x1.2; only 85% of the budget is planned.
budget_s = MAX_TRAIN_MINUTES * 60 * 0.85
fixed_s = (overhead + first_extra) * 1.2
EPOCHS = int(min(100, math.floor((budget_s - fixed_s) / (steady * 1.3))))
assert EPOCHS >= 30, f"only {EPOCHS} epochs fit in {MAX_TRAIN_MINUTES} min: not a meaningful run; stopping"
PATIENCE = 15 if EPOCHS >= 45 else max(8, EPOCHS // 3)
HARD_STOP_MIN = MAX_TRAIN_MINUTES - (overhead * 1.2) / 60 - 1   # end the epoch loop in time for the final validation
planned = (fixed_s + EPOCHS * steady * 1.3) / 60
print(f"GPU check OK: {pinfo['gpu']}, peak {peak_gb:.1f} GB allocated during the probe")
print(f"probe wall {wall:.0f}s | fixed overhead {overhead:.0f}s | first-epoch extra {first_extra:.0f}s | "
      f"steady {steady:.1f}s/epoch (median of {len(deltas)})")
print(f"-> EPOCHS = {EPOCHS} (max 100), PATIENCE = {PATIENCE}, planned <= {planned:.1f} min incl. buffers, "
      f"hard stop of the epoch loop at {HARD_STOP_MIN:.1f} min | budget {MAX_TRAIN_MINUTES} min")
FULL_RUN_OK = planned <= MAX_TRAIN_MINUTES
print("FULL_RUN_OK =", FULL_RUN_OK)

# COMMAND ----------

# 7. Train FROM THE ORIGINAL PRETRAINED CHECKPOINT (never from the probe): EPOCHS / PATIENCE from cell 6, 640 px,
#    seed 42, batch 16, validation every epoch; best checkpoint = best validation fitness. A backstop callback ends the
#    epoch loop if wall time reaches HARD_STOP_MIN (best.pt so far is kept and validated). MLflow via Ultralytics.
assert FULL_RUN_OK and "EPOCHS" in globals(), "Run cell 6 first (and it must report FULL_RUN_OK = True)."
sums = json.load(open(f"{PKG}/weights/SHA256SUMS.json"))
assert hashlib.sha256(open(f"{PKG}/weights/yolo26n-obb.pt", "rb").read()).hexdigest() == sums["yolo26n-obb.pt"],     "pretrained checkpoint changed"
from ultralytics.utils.callbacks import base as _cb
HARD_STOPPED = {"hit": False, "epoch": None}
def _hard_stop(trainer):
    if time.time() - trainer.train_time_start > HARD_STOP_MIN * 60 and not trainer.stop:
        HARD_STOPPED.update(hit=True, epoch=trainer.epoch + 1)
        print(f"[hard stop] {HARD_STOP_MIN:.1f} min reached after epoch {trainer.epoch + 1}: ending training")
        trainer.stop = True
_cb.default_callbacks["on_fit_epoch_end"] = [f for f in _cb.default_callbacks["on_fit_epoch_end"]
                                             if getattr(f, "__name__", "") != "_hard_stop"] + [_hard_stop]
shutil.rmtree(f"{PKG}/runs/{RUN}", ignore_errors=True)       # fresh run folder; nothing resumed
os.environ["MLFLOW_TRACKING_URI"] = "databricks"
os.environ["MLFLOW_EXPERIMENT_NAME"] = MLFLOW_EXPERIMENT
os.environ["MLFLOW_RUN"] = f"{RUN}_train"
t0 = time.time()
train_yolo.main(["--model", "weights/yolo26n-obb.pt", "--epochs", str(EPOCHS), "--patience", str(PATIENCE),
                 "--name", RUN, "--workers", "2"])
TRAIN_MIN = round((time.time() - t0) / 60, 2)
print("training wall time:", TRAIN_MIN, "min | hard stop:", HARD_STOPPED)

# COMMAND ----------

# 8. Durable storage BEFORE evaluation: weights, curves, run info, manifest -> outputs/ and MLflow artifacts
import mlflow
shutil.copytree(f"{PKG}/runs/{RUN}", f"{OUT_WS}/runs/{RUN}", dirs_exist_ok=True)
for f in ("selection_manifest.csv", "selection_summary.json"):
    shutil.copy(f"{PKG}/{f}", f"{OUT_WS}/{f}")
info = json.load(open(f"{PKG}/runs/{RUN}/run_info.json"))
import csv as _csv
res = [{k.strip(): v for k, v in r.items()} for r in _csv.DictReader(open(f"{PKG}/runs/{RUN}/results.csv"))]
best = max(res, key=lambda r: 0.1 * float(r["metrics/mAP50(B)"]) + 0.9 * float(r["metrics/mAP50-95(B)"]))
mlflow.set_experiment(MLFLOW_EXPERIMENT)
with mlflow.start_run(run_name=f"{RUN}_artifacts"):
    mlflow.log_params({"model": "yolo26n-obb", "imgsz": 640, "epochs_max": EPOCHS, "patience": PATIENCE, "seed": 42, "batch": 16,
                       "budget_minutes": MAX_TRAIN_MINUTES, "probe_steady_s_per_epoch": round(steady, 2),
                       "probe_fixed_overhead_s": round(overhead, 1), "hard_stop_hit": HARD_STOPPED["hit"],
                       "train_files": 302, "train_photos": 155, "valid_photos": 36, "test_images": 50,
                       "gpu": info.get("gpu"), "ultralytics": info.get("ultralytics")})
    mlflow.log_metrics({"train_minutes": TRAIN_MIN, "epochs_run": len(res), "best_epoch": int(best["epoch"]),
                        "best_val_mAP50": float(best["metrics/mAP50(B)"]), "best_val_mAP50_95": float(best["metrics/mAP50-95(B)"])})
    mlflow.log_artifacts(f"{PKG}/runs/{RUN}", artifact_path="train_run")      # best.pt, last.pt, curves, results.csv
    mlflow.log_artifact(f"{PKG}/selection_manifest.csv")
print("saved:", sorted(os.listdir(f"{OUT_WS}/runs/{RUN}")), "| epochs run", len(res), "| best epoch", best["epoch"])

# COMMAND ----------

# 9. Evaluate the best checkpoint ONCE on the untouched test split; compare with experiment 1 and Llama 4 Maverick
import evaluate
assert not os.path.exists(f"{OUT_WS}/results/{RUN}/metrics.json"), "already evaluated: not re-evaluating"
m = evaluate.main(["--weights", f"runs/{RUN}/weights/best.pt"])
shutil.copytree(f"{PKG}/results/{RUN}", f"{OUT_WS}/results/{RUN}", dirs_exist_ok=True)
with mlflow.start_run(run_name=f"{RUN}_test_eval"):
    mlflow.log_metrics({f"test_{k}": v for k, v in m["overall"].items()})
    for c, v in m["per_class"].items():
        mlflow.log_metrics({f"test_{c}_{k}": v[k] for k in ("precision", "recall", "mAP50", "mAP50-95")})
    op = m["operating_point"]
    mlflow.log_metrics({"test_fp_conf025": op["false_positives"], "test_fn_conf025": op["false_negatives"],
                        "train_minutes": TRAIN_MIN})
    mlflow.log_artifacts(f"{PKG}/results/{RUN}", artifact_path="test_eval")
e1 = json.load(open(f"{PKG}/exp1/metrics.json"))
lines = ["| metric (same 50 test images) | exp 1 (115 photos) | exp 2 (155 photos) |", "|---|---|---|"]
lines += [f"| {k} | {e1['overall'][k]} | {m['overall'][k]} |" for k in m["overall"]]
for c in m["per_class"]:
    for k in ("recall", "mAP50"):
        lines.append(f"| {m['per_class'][c]['display']} {k} | {e1['per_class'].get(c, {}).get(k)} | {m['per_class'][c][k]} |")
for k in ("true_positives", "false_positives", "false_negatives", "recall", "precision"):
    lines.append(f"| conf 0.25 {k} | {e1['operating_point'][k]} | {op[k]} |")
v1, v2 = e1["vs_llama"], m["vs_llama"]
for g in ("surface", "moisture"):
    lines.append(f"| {g} image recall (Llama {v2['llama4_maverick'][g]['image_recall']}) | {v1['yolo26'][g]['image_recall']} | {v2['yolo26'][g]['image_recall']} |")
lines.append(f"| missed stain images of 11 (Llama {v2['llama4_maverick']['missed_stain_images']}) | {v1['yolo26']['missed_stain_images']} | {v2['yolo26']['missed_stain_images']} |")
lines.append(f"| training minutes | {e1['train_info']['train_minutes']} | {TRAIN_MIN} |")
print("\n".join(lines))
print("\n" + open(f"{PKG}/results/{RUN}/metrics.md").read())
displayHTML("".join(f'<img src="data:image/jpeg;base64,{__import__("base64").b64encode(open(f"{PKG}/results/{RUN}/examples/{f}","rb").read()).decode()}" width="640"><br>{f}<br>'
                    for f in sorted(os.listdir(f"{PKG}/results/{RUN}/examples"))))
