# YOLO26n-OBB experiment 2: full group-aware dataset

Status (2026-11-15): **dataset built and verified; notebook and bundle uploaded to the workspace folder
`fixit-yolo-ceiling-full/`. Training has NOT run yet** (it runs in the owner's existing Serverless GPU notebook
session; see "How to run"). No accuracy is claimed until it runs.

Isolated: no change to the FixIt App, its Llama pipeline, App tables/Volumes, legal citations, synthetic data or Genie.
Experiment 1 (`experiments/yolo_ceiling/`, workspace `fixit-yolo-ceiling/`) is unchanged and was not rerun.

## Dataset audit (`sample_full.py`, seed 42; ZIP only read)
- Images examined: **500** (300/100/100 in Roboflow's original partitions), all 640x640 with OBB labels, 5 classes.
- Distinct photographs: **242** (rotated/flipped/near-duplicate copies grouped by `experiments/yolo_ceiling/dedup.py`,
  the same rule as experiment 1: Roboflow source name, or rotation/flip-invariant 256-bit dHash <= 15 bits, or <= 30
  bits with best-orientation pixel correlation >= 0.85).

| split | image files | distinct photos | photos with crack / damp / hole / mold-like / stain |
|---|---|---|---|
| train | 302 | 155 | 48 / 38 / 28 / 59 / 32 |
| valid | 36 | 36 | 11 / 12 / 12 / 12 / 11 |
| test | 50 | 50 | 20 / 16 / 11 / 20 / 11 |

Excluded (all 500 files accounted for):
- 74 files (44 photos): other rotated/flipped copies of the **50 test photos**, so no test photo reaches training in
  any form.
- 36 files (28 photos): extra copies of validation photos (validation keeps one image per photo).
- 2 files (1 photo): the only unannotated images; named "delaminating-cracks" and likely unlabeled damage, so unsafe
  as background; kept as the (weak) clean holdout.

Design choices:
- **Test = exactly experiment 1's 50 test images** (verified by SHA-256). Both models are scored on identical images,
  so differences come from training, not from evaluation-set composition; the Llama 4 Maverick baseline on those
  images remains valid.
- Trade-off: a fresh 70/15/15 split would give ~169 training photos instead of 155 (+9%). Not material, so the
  comparable split was kept and no alternative was trained.
- Experiment 1's validation photos may train here (they were used only for checkpoint selection, never for the
  final evaluation).
- Split is ~64/15/21 by photos (test is larger than 15% because it is experiment 1's test set).

Leakage checks (`verify_full.py`): every file byte-identical to the ZIP; labels identical; no duplicate group in two
splits; no rotation/flip-invariant near-duplicate between any two splits across all 388 files (closest pair 19/256 bits;
the four closest pairs inspected visually: different photos); test == experiment 1's test set; ZIP unchanged.
Experiment 1's own verifier still passes.

## Training setup (`train_yolo.py`, notebook `databricks/yolo_ceiling_full_train.py`)
yolo26n-obb (official pretrained weights, SHA-256 checked), OBB, 640 px, up to **100 epochs, patience 15**, seed 42,
deterministic, batch 16, validation every epoch, best checkpoint by validation fitness. Augmentation identical to
experiment 1 (flips, +/-10 deg, brightness/saturation, no hue shift, mosaic 0.5 with close_mosaic 10, no
mixup/copy-paste/shear/perspective). Ultralytics 8.4.196, installed only if missing, constrained to the runtime's torch.
Hardware: the owner's existing Free Edition Serverless GPU (AI Runtime v6, NVIDIA A10G). No compute created.

Note for the comparison: besides the data, epochs/patience changed (50/10 -> 100/15, as requested). Experiment 1
stopped by patience at epoch 28 (best epoch 18), so part of any gain may come from the longer patience.

## Experiment 1 (for reference, measured on the same 50 test images)
Trained 1.4 min on the A10G, 28 epochs (early stop; best val mAP50 0.206 at epoch 18).
Test: precision 0.195, recall 0.231, mAP50 0.122, mAP50-95 0.053. Per class mAP50: crack 0.108, damp 0.187,
hole 0.085, mold-like 0.207, stain 0.025. At conf 0.25: 27 TP, 53 FP, 203 FN. Image level vs Llama 4 Maverick:
surface damage 11/29 vs 15/29, moisture 21/33 vs 27/33, missed stain images 8/11 vs 4/11. Inference 8 ms/image (GPU)
vs ~5.5 s/image for Llama. Experiment 1 did not beat Llama.

## How to run (owner, existing notebook session)
Workspace -> Users -> (you) -> `fixit-yolo-ceiling-full` -> `yolo_ceiling_full_train`; attach Serverless GPU (AI v6);
run cells 1-5 (checks), 6 (probe: projected minutes; check quota), 7 (train), 8 (save to `outputs/` + MLflow),
9 (single test evaluation + comparison table). Outputs: `fixit-yolo-ceiling-full/outputs/` and MLflow experiment
`fixit-yolo-ceiling-full/yolo_ceiling_full_mlflow`.

## Results
_Pending the training run._ To be filled from cell 9 (overall/per-class metrics, confusion matrix, FP/FN, speed,
training duration, comparison with experiment 1 and Llama, recommendation).
