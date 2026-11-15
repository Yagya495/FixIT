# YOLO26n-OBB experiment 2: full group-aware dataset

Status (2026-11-15): **trained once on the owner's Free Edition Serverless GPU and evaluated once on test; analysed
from the saved artifacts** (no retraining, no second test evaluation). Visual report: `analysis/exp2_visual_report.html`
(rebuilt by `analysis/build_report.py`).

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

## Results (single test evaluation, conf 0.25 for counts)
Training: 1.8 min on the A10G; early stop at epoch 28 (best validation epoch 13: mAP50 0.257, mAP50-95 0.140).

| same 50 test images | exp 1 | exp 2 |
|---|---|---|
| precision / recall | 0.195 / 0.231 | 0.251 / 0.264 |
| mAP50 / mAP50-95 | 0.122 / 0.053 | 0.182 / 0.089 |
| mAP50 crack / damp / hole / mold-like / stain | .108 / .187 / .085 / .207 / .025 | .211 / .225 / .141 / .209 / .126 |
| TP / FP / FN boxes | 27 / 53 / 203 | 29 / 59 / 201 |

Inference 8 ms/image on GPU. FP: 14 wrong class, 45 with no matching label. FN by class: crack 59, damp 29, hole 13,
mold-like 76, stain 24. Clean holdout: 0/2 false alarms. Training ended at the same epoch as exp 1, so the gain is
from the data, not the longer patience.

Image level (test, YOLO at 0.25; `analysis/analyze_exp2.py`):

| | surface found | surface FP images | moisture found | moisture FP images |
|---|---|---|---|---|
| YOLO exp 2 | 16/29 | 2/21 | 20/33 | 3/17 |
| Llama 4 Maverick | 15/29 | 0/21 | 27/33 | 2/17 |
| either (hybrid) | 20/29 | 2/21 | 29/33 | 5/17 |

Validation tuning (36 images; Llama run on them, 0 errors): object F1 peaks at 0.27 (conf 0.05); raising conf only
trades recall for precision. Surface hybrid at conf 0.20-0.25: 13/20 vs Llama 11/20, false-positive images 1/16 vs 0/16.

Visual review: correct crack, damp/stain, hole (0.94) and mold-like examples; real misses on obvious dark mold-like
patches (97-black-mold), large discoloration (89WATE) and an obvious hole (56-ceiling-leakage); many "errors" are
label artifacts (damp vs stain on the same patch, one loose crack box vs two tight predicted boxes, a ring stain
labelled mold). Vents and fixtures are sometimes detected as holes.

Annotation audit (`analysis/annotation_audit.py`, whole ZIP): all 2,068 boxes are axis-aligned (OBB carries no
orientation); 587 cross-class overlap pairs (382 damp + mold-like); median hole box 0.08% of the image; 84 of 195
photos with copies are labelled differently across copies (20 with different classes).

## Recommendation
- Do not integrate YOLO into the app now; Llama stays the detector.
- Next experiment: **improve the dataset**, not YOLO26s. Relabel a focused crack/hole/stain set consistently (rotated
  boxes for cracks), merge or define damp / mold-like / stain, add clean ceilings and vents/detectors/lights as
  negatives. With 155 distinct photos and noisy labels a larger model mostly fits noise; YOLO26s is a cheap side run
  only after (or alongside) the data fix.
- Also try a standard axis-aligned YOLO26 detector on the same split, since the labels have no orientation.
- A later crack/hole hybrid (YOLO at 0.25 OR Llama) is promising but must be confirmed on new photos.
- "Mold-like discoloration" is a visual description only. Ultralytics is AGPL-3.0.
