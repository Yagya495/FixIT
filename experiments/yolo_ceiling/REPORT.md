# YOLO26-OBB ceiling-damage proof of concept (isolated experiment)

Status (2026-11-15): **dataset, scripts, notebook and the Llama baseline are complete; the real training has NOT run
yet.** No free GPU is available to this workspace (details below). No model metrics are claimed until training runs.

Nothing here touches the FixIt app, its dependencies, the Databricks deployment, tables, Genie or legal citations.
YOLO is not part of the live pipeline.

## Dataset: 150 / 50 / 50 from Roboflow "Ceiling" v1
Source: `Ceiling.v1i.yolov8-obb.zip` (500 images, 640x640, YOLO OBB labels; 300 train / 100 valid / 100 test),
license **CC BY 4.0**, universe.roboflow.com/scipublic/ceiling-y9dkm. Classes verified: ceiling_crack, ceiling_damp,
ceiling_hole, ceiling_mold, ceiling_stain. The ZIP is only read (hash checked by `verify_dataset.py`). No prompt-injection
content in its README or data.yaml.

**Duplicates.** The README says "no augmentation", but the export contains flipped/rotated copies of the same photo,
both under one Roboflow source name (`<name>_jpg.rf.<hash>`) and under different names; 103 source photos have copies in
more than one original split. A rotation/flip-invariant check (`dedup.py`: 256-bit dHash under all 8 orientations, plus
pixel correlation for borderline pairs, calibrated on the known copies and inspected visually) groups the 500 images
into **242 distinct photos**.

**Selection** (`sample_dataset.py`, seed 42): test first, then valid, then train, each only from its own original
split; least-covered-class-first sampling (multilabel aware); a duplicate group may appear in only one split.

| split | images | distinct photos | images with crack / damp / hole / mold-like / stain | instances |
|---|---|---|---|---|
| train | 150 | 115 | 36 / 40 / 40 / 54 / 40 | 81 / 103 / 75 / 253 / 86 |
| valid | 50 | 50 | 15 / 15 / 14 / 16 / 14 | 25 / 25 / 82 / 57 / 26 |
| test | 50 | 50 | 20 / 16 / 11 / 20 / 11 | 73 / 31 / 14 / 87 / 25 |

Limitations: after excluding copies of test/valid photos, the original train split has only 115 distinct photos, so 35
training images are existing rotated copies of photos already in train (none invented; none crosses splits). Holes and
stains have only 11 test images each. The only 2 unannotated images (kept as the "clean" holdout) are named
"delaminating-cracks" and likely show unlabeled damage: they are not real clean-ceiling evidence.
Files: `selection_manifest.csv` (every image: original split, SHA-256, per-class counts, duplicate group),
`selection_summary.json`; `verify_dataset.py` re-checks everything (OK; closest cross-split pair 25/256 bits, visually
different photos).

## Model, versions, licenses
- `ultralytics==8.4.196` (newest release older than two weeks; latest is 8.4.213). License **AGPL-3.0**.
- Weights `yolo26n-obb.pt` (5.9 MB) and `yolo26s-obb.pt` (21.7 MB) available from the official Ultralytics assets
  (AGPL-3.0). Fine for this experiment. **Before any integration:** serving an AGPL model inside the deployed App would
  require publishing the App's source under AGPL or an Ultralytics Enterprise license.
- Installed only in `experiments/yolo_ceiling/.venv` (not in the App's environment or requirements).

## Where training can run
- Local PC: no NVIDIA GPU. A 1-epoch smoke run (30 images, 320 px) took ~15 s of training on CPU, so the real run
  (150 images, 640 px, up to 50 epochs) would take roughly 4 h on CPU: not started, as instructed.
- Databricks (`fixit` profile, read-only checks): no clusters exist; GPU instance types are listed (g4dn, g5), but any
  GPU cluster is **new paid compute**, which needs the owner's approval. No serverless/free GPU option found.
- **Fallback prepared:** `yolo_ceiling_colab.ipynb` + `yolo_ceiling_bundle.zip` (8.4 MB, built by
  `make_colab_bundle.py`) for a free Colab T4.

## Training configuration (`train_yolo.py`)
OBB, 640 px, seed 42 (deterministic), max 50 epochs, patience 10, pretrained, batch 16 on GPUs with >= 8 GB (keeps ~10
optimizer steps per epoch on 150 images). Validation = the 50-image valid split; the test split is not used in
training. Augmentation: flips both ways and +/-10 deg rotation (a ceiling has no "up"); brightness/saturation +/-30%, **no
hue shift** (colour separates stain / mold-like discoloration / damp); mosaic 0.5, off for the last 10 epochs; **no
mixup, no copy-paste, no shear/perspective** (they create unrealistic damage). MLflow logs to `mlruns/` if installed.
Refuses a real run on CPU.

Pipeline verified locally: smoke training + `evaluate.py --split valid` (pipeline check only, not a result) produced
metrics, confusion matrix, side-by-side GT/prediction images and the clean-holdout check. The test split has not been
evaluated by any model yet.

## Evaluation (`evaluate.py`, once, on the test split)
Overall and per-class precision/recall/mAP50/mAP50-95, inference ms/image, confusion matrix, FP/FN lists at a fixed
conf 0.25 (OBB IoU 0.5 matching; FP split into "wrong class" vs "no matching damage"), GT-vs-prediction images for all
50 test images, 2 examples per class, clean holdout, and the comparison below. Display wording: "mold-like
discoloration"; a box is a visual finding, never a mold diagnosis.

## Baseline: current Llama 4 Maverick call on the same 50 test images (measured)
`compare_llama.py` ran the unchanged `vision.analyze_frame_live` (no cache, no writes); 0 errors. Image level, mapping
crack/hole -> DAMAGED_SURFACES, damp/mold-like/stain -> WATER_DAMAGE_MOLD or LEAK_PLUMBING:

| | Llama 4 Maverick |
|---|---|
| surface damage (crack/hole) images found | 15/29 (52%); false-positive images 0/21 |
| moisture (damp/mold-like/stain) images found | 27/33 (82%); false-positive images 2/17 |
| per class (images where the matching group was flagged) | crack 11/20, damp 13/16, **hole 4/11**, mold-like 17/20, **stain 7/11** |
| missed stain images | 4/11 |
| localization | a box on 29/50 images (axis-aligned, coarse) |
| latency | median 5.5 s/image locally (includes ~3 s local auth overhead) |

Weak spots: holes, cracks and a third of stains. The YOLO result will be compared on exactly these images.

## Next step
Run the Colab notebook (free T4, ~10-15 min for yolo26n) or approve a paid Databricks GPU run; then
`evaluate.py --weights runs/yolo26n-obb/weights/best.pt` once and fill in the results here.
