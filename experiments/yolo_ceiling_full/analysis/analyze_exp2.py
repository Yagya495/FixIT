"""Experiment 2 analysis. NO retraining and NO new test evaluation:
- TEST findings come only from the saved artifacts (metrics.json per-image FP/FN at conf 0.25, saved GT|prediction
  images) plus the saved Llama test predictions.
- Threshold and hybrid tuning use the 36 VALIDATION images only: best.pt inference on valid (CPU) + Llama on valid.
Run with the experiment venv (ultralytics):  experiments/yolo_ceiling/.venv/Scripts/python.exe analyze_exp2.py
"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP2 = HERE.parent
sys.path.insert(0, str(EXP2))
import evaluate as ev  # noqa: E402  (match(), gt_of(), NAMES, GROUP; DATA = dataset_full)

OUT = EXP2 / "outputs_exp2"
M = json.load(open(OUT / "results/yolo26n-obb_full/metrics.json"))
E1 = json.load(open(EXP2 / "exp1/metrics.json"))
LT = {r["image"]: r for r in json.load(open(EXP2 / "results/llama_test_predictions.json"))["results"] if r["split"] == "test"}
LG = ev.LLAMA_GROUP
GROUPS = ("surface", "moisture")


def gt_groups(classes):
    return {ev.GROUP[ev.NAMES.index(c)] for c in classes}


def llama_groups(r):
    return {LG[d["type"]] for d in r["detections"] if d["type"] in LG}


# ---------------- TEST (saved artifacts only, fixed conf 0.25) ----------------
listed = {p["image"]: p for p in M["operating_point"]["images_with_errors"]}
test_imgs = sorted(p.name for p in (ev.DATA / "test" / "images").iterdir())
per = {}
for im in test_imgs:
    gt = [ev.NAMES[c] for c, _ in ev.gt_of(ev.DATA / "test" / "images" / im)]
    if im in listed:
        per[im] = listed[im]
    else:                                   # not listed = no FP and no FN: every GT box was detected correctly
        per[im] = {"image": im, "gt": gt, "tp": len(gt), "fp": [], "fn": [], "pred_groups": sorted(gt_groups(gt)),
                   "pred_classes": sorted(set(gt))}


def image_level(pred_fn):
    out = {}
    for g in GROUPS:
        pos = [im for im in test_imgs if g in gt_groups(per[im]["gt"])]
        neg = [im for im in test_imgs if im not in pos]
        out[g] = {"recall": sum(g in pred_fn(im) for im in pos), "pos": len(pos),
                  "fp_images": sum(g in pred_fn(im) for im in neg), "neg": len(neg)}
    return out


yolo_t = lambda im: set(per[im]["pred_groups"])
llama_t = lambda im: llama_groups(LT[im])
hybrid_t = lambda im: yolo_t(im) | llama_t(im)
test_image_level = {"yolo26n_exp2": image_level(yolo_t), "llama4_maverick": image_level(llama_t),
                    "hybrid_union_conf025": image_level(hybrid_t)}
surf_pos = [im for im in test_imgs if "surface" in gt_groups(per[im]["gt"])]
yolo_only_surface = [im for im in surf_pos if "surface" in yolo_t(im) and "surface" not in llama_t(im)]
llama_only_surface = [im for im in surf_pos if "surface" in llama_t(im) and "surface" not in yolo_t(im)]
both_miss_surface = [im for im in surf_pos if "surface" not in hybrid_t(im)]
stain_imgs = [im for im in test_imgs if "ceiling_stain" in per[im]["gt"]]
stain = {name: sum("moisture" not in f(im) for im in stain_imgs) for name, f in
         (("yolo26n_exp2", yolo_t), ("llama4_maverick", llama_t), ("hybrid", hybrid_t))}

# ranking FP / FN / correct examples for the visual report
fps = sorted(((f["conf"], im, f) for im in test_imgs for f in per[im]["fp"]), key=lambda x: -x[0])
fp_by_kind = {"wrong_class": [(c, im, f["cls"], f["kind"]) for c, im, f in fps if f["kind"].startswith("wrong")][:6],
              "no_damage_there": [(c, im, f["cls"]) for c, im, f in fps if not f["kind"].startswith("wrong")][:6]}
fn_rank = []
for im in test_imgs:
    if per[im]["fn"]:
        gts = ev.gt_of(ev.DATA / "test" / "images" / im)
        area = sum(abs(float((p[1][0] - p[0][0]) * (p[3][1] - p[0][1]) - (p[1][1] - p[0][1]) * (p[3][0] - p[0][0]))) for c, p in gts if ev.NAMES[c] in per[im]["fn"])
        fn_rank.append((len(per[im]["fn"]), round(area, 4), im, per[im]["fn"], per[im]["tp"]))
fn_rank.sort(key=lambda x: (-(x[4] == 0), -x[1]))          # images with NOTHING found first, then largest missed area
correct = {}
for c in ev.NAMES:
    cand = [im for im in test_imgs if c in per[im]["gt"] and per[im]["tp"] > 0 and c in per[im]["pred_classes"]
            and c not in per[im]["fn"]]
    cand += [im for im in test_imgs if c in per[im]["gt"] and c in per[im]["pred_classes"] and im not in cand]
    correct[c] = cand[:2]

# ---------------- VALIDATION (threshold + hybrid tuning) ----------------
from ultralytics import YOLO  # noqa: E402
import torch  # noqa: E402
model = YOLO(str(OUT / "runs/yolo26n-obb_full/weights/best.pt"))
vimgs = sorted((ev.DATA / "valid" / "images").iterdir())
vpred = {}
for p in vimgs:
    r = model.predict(str(p), imgsz=640, conf=0.01, verbose=False)[0]
    vpred[p.name] = ({"cls": r.obb.cls.cpu().numpy(), "conf": r.obb.conf.cpu().numpy(), "xywhr": r.obb.xywhr.cpu()},
                     ev.gt_of(p, "valid"), r.orig_shape)
grid = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.5]
obj_curve = []
for t in grid:
    tp = fp = fn = 0
    for name, (pr, gts, shp) in vpred.items():
        k = pr["conf"] >= t
        sub = {"cls": pr["cls"][k], "conf": pr["conf"][k], "xywhr": pr["xywhr"][torch.from_numpy(k)]}
        a, b, c, _ = ev.match(sub, gts, shp[1], shp[0])
        tp += len(a); fp += len(b); fn += len(c)
    P, R = tp / max(1, tp + fp), tp / max(1, tp + fn)
    obj_curve.append({"conf": t, "tp": tp, "fp": fp, "fn": fn, "precision": round(P, 3), "recall": round(R, 3),
                      "f1": round(2 * P * R / max(1e-9, P + R), 3)})
lv_path = HERE / "llama_valid_predictions.json"
LV = {r["image"]: r for r in json.load(open(lv_path))["results"]} if lv_path.exists() else {}
vgt = {n: {ev.GROUP[c] for c, _ in g} for n, (_, g, _) in vpred.items()}


def vgroups(name, t):
    pr = vpred[name][0]
    return {ev.GROUP[int(c)] for c, s in zip(pr["cls"], pr["conf"]) if s >= t}


img_curve = []
for t in grid:
    row = {"conf": t}
    for g in GROUPS:
        pos = [n for n in vpred if g in vgt[n]]; neg = [n for n in vpred if n not in pos]
        row[f"yolo_{g}"] = f"{sum(g in vgroups(n, t) for n in pos)}/{len(pos)} | FP {sum(g in vgroups(n, t) for n in neg)}/{len(neg)}"
        if LV:
            hy = lambda n: vgroups(n, t) | llama_groups(LV[n])
            row[f"hybrid_{g}"] = f"{sum(g in hy(n) for n in pos)}/{len(pos)} | FP {sum(g in hy(n) for n in neg)}/{len(neg)}"
    img_curve.append(row)
llama_valid = None
if LV:
    llama_valid = {}
    for g in GROUPS:
        pos = [n for n in vpred if g in vgt[n]]; neg = [n for n in vpred if n not in pos]
        llama_valid[g] = f"{sum(g in llama_groups(LV[n]) for n in pos)}/{len(pos)} | FP {sum(g in llama_groups(LV[n]) for n in neg)}/{len(neg)}"
    llama_valid["errors"] = sum(1 for r in LV.values() if r["error"])

res = {"test_image_level_conf025": test_image_level, "yolo_only_surface": yolo_only_surface,
       "llama_only_surface": llama_only_surface, "both_miss_surface": both_miss_surface,
       "missed_stain_images_of": [stain, len(stain_imgs)], "top_fp": fp_by_kind, "top_fn": fn_rank[:8],
       "correct_examples": correct, "valid_object_curve": obj_curve, "valid_image_curve": img_curve,
       "llama_valid": llama_valid,
       "exp1_vs_exp2_test": {"exp1": {**E1["overall"], **{f"{k}_mAP50": v["mAP50"] for k, v in E1["per_class"].items()}},
                             "exp2": {**M["overall"], **{f"{k}_mAP50": v["mAP50"] for k, v in M["per_class"].items()}}}}
json.dump(res, open(HERE / "analysis_exp2.json", "w"), indent=1, default=str)
print(json.dumps({k: res[k] for k in ("test_image_level_conf025", "missed_stain_images_of", "yolo_only_surface",
                                      "llama_only_surface", "llama_valid")}, indent=1, default=str))
print("valid object curve:"); [print("  ", r) for r in obj_curve]
print("valid image curve:"); [print("  ", r) for r in img_curve]
