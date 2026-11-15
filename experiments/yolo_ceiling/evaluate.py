"""Evaluate a trained checkpoint ONCE on the held-out 50-image test split (no tuning on test), plus the clean holdout
and an image-level comparison with the existing Llama 4 Maverick call (results/llama_test_predictions.json).

    python evaluate.py --weights runs/yolo26n-obb/weights/best.pt [--conf 0.25]

Outputs in results/<run>/: metrics.json, metrics.md, confusion matrix plots, predictions/ (GT | prediction side by
side for every test image), examples/ (2 per class), clean/ (clean-holdout predictions).
Display wording: class "ceiling_mold" is shown as "mold-like discoloration". A box is a visual finding, never a
mold diagnosis.
"""
import argparse
import json
import shutil
import statistics as st
import time
from pathlib import Path

import cv2
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
DATA = HERE / "dataset_250"
NAMES = ["ceiling_crack", "ceiling_damp", "ceiling_hole", "ceiling_mold", "ceiling_stain"]
DISPLAY = {0: "crack", 1: "damp patch", 2: "hole", 3: "mold-like discoloration", 4: "stain"}
GROUP = {0: "surface", 2: "surface", 1: "moisture", 3: "moisture", 4: "moisture"}
LLAMA_GROUP = {"DAMAGED_SURFACES": "surface", "WATER_DAMAGE_MOLD": "moisture", "LEAK_PLUMBING": "moisture"}


def gt_of(img: Path, split="test"):
    lab = DATA / split / "labels" / (img.stem + ".txt")
    rows = [l.split() for l in lab.read_text().splitlines() if l.strip()] if lab.exists() else []
    return [(int(r[0]), np.array([float(x) for x in r[1:]]).reshape(4, 2)) for r in rows]


def match(pred, gts, w, h, iou_thr=0.5):
    """Greedy same-class matching with probabilistic OBB IoU. Returns (tp, fp list, fn list, ious)."""
    from ultralytics.utils.metrics import batch_probiou
    from ultralytics.utils.ops import xyxyxyxy2xywhr
    if gts:
        polys = np.stack([p * [w, h] for _, p in gts]).reshape(len(gts), 8).astype(np.float32)
        g_xywhr = xyxyxyxy2xywhr(torch.from_numpy(polys))
    used, tp, fps, ious = set(), [], [], []
    order = np.argsort(-pred["conf"]) if len(pred["conf"]) else []
    for i in order:
        c = int(pred["cls"][i])
        best, bj = 0.0, None
        if gts:
            iou = batch_probiou(pred["xywhr"][i:i + 1], g_xywhr)[0].numpy()
            for j, (gc, _) in enumerate(gts):
                if gc == c and j not in used and iou[j] > best:
                    best, bj = float(iou[j]), j
        if bj is not None and best >= iou_thr:
            used.add(bj); tp.append((c, best)); ious.append(best)
        else:
            other = None
            if gts:
                k = int(np.argmax(iou))
                other = NAMES[gts[k][0]] if iou[k] >= iou_thr and gts[k][0] != c else None
            fps.append({"cls": NAMES[c], "conf": round(float(pred["conf"][i]), 3),
                        "kind": f"wrong class (GT {other})" if other else "no matching damage"})
    fns = [NAMES[gc] for j, (gc, _) in enumerate(gts) if j not in used]
    return tp, fps, fns, ious


def side_by_side(img_path: Path, result, gts, out: Path):
    im = cv2.imread(str(img_path))
    h, w = im.shape[:2]
    left = im.copy()
    for c, p in gts:
        pts = (p * [w, h]).astype(np.int32)
        cv2.polylines(left, [pts], True, (0, 200, 0), 2)
        cv2.putText(left, DISPLAY[c], tuple(pts[0]), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 0), 1)
    result.names = DISPLAY                                    # display wording on the prediction panel
    right = result.plot(line_width=2, font_size=12)
    cv2.putText(left, "ground truth", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)
    cv2.putText(right, "YOLO26 prediction", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imwrite(str(out), np.hstack([left, right]))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--conf", type=float, default=0.25, help="operating threshold for FP/FN lists (fixed, not tuned)")
    ap.add_argument("--split", default="test", choices=["test", "valid"],
                    help="'valid' only for pipeline checks; the reported result is the single test evaluation")
    a = ap.parse_args(argv)
    from ultralytics import YOLO
    w = Path(a.weights).resolve()
    run = w.parent.parent.name
    out = HERE / "results" / (run if a.split == "test" else f"{run}_{a.split}_pipelinecheck")
    out.mkdir(parents=True, exist_ok=True)
    info = json.load(open(w.parent.parent / "run_info.json")) if (w.parent.parent / "run_info.json").exists() else {}
    model = YOLO(str(w))
    yaml = HERE / "runs" / "data_runtime.yaml"
    if not yaml.exists():
        yaml.write_text((DATA / "data.yaml").read_text().replace("path: .", f"path: {DATA.as_posix()}"))

    # 1) standard metrics, ONE pass over the test split
    m = model.val(data=str(yaml), split="val" if a.split == "valid" else "test", imgsz=640, batch=8, conf=0.001, iou=0.7, plots=True,
                  project=str(out), name="val_test", exist_ok=True, verbose=False)
    box = m.box
    per_class = {}
    for k, ci in enumerate(m.ap_class_index):
        per_class[NAMES[int(ci)]] = {"display": DISPLAY[int(ci)], "precision": round(float(box.p[k]), 3),
                                     "recall": round(float(box.r[k]), 3), "mAP50": round(float(box.ap50[k]), 3),
                                     "mAP50-95": round(float(box.ap[k]), 3)}
    metrics = {"run": run, "weights": str(w), "train_info": {k: info.get(k) for k in ("device", "gpu", "host", "ultralytics", "train_minutes", "smoke")},
               "split": a.split, "images": 50, "overall": {"precision": round(float(box.mp), 3), "recall": round(float(box.mr), 3),
                                              "mAP50": round(float(box.map50), 3), "mAP50-95": round(float(box.map), 3)},
               "per_class": per_class, "speed_ms_per_image": {k: round(v, 1) for k, v in m.speed.items()},
               "confusion_matrix": {"labels": NAMES + ["background"], "matrix": m.confusion_matrix.matrix.astype(int).tolist()}}

    # 2) FP / FN lists at a fixed operating threshold + prediction images
    for sub in ("predictions", "examples", "clean"):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir()
    imgs = sorted((DATA / a.split / "images").iterdir())
    per_image, all_ious, t_inf = [], [], []
    examples = {k: 0 for k in range(5)}
    for img in imgs:
        t = time.perf_counter()
        r = model.predict(str(img), imgsz=640, conf=a.conf, verbose=False)[0]
        t_inf.append((time.perf_counter() - t) * 1000)
        pred = {"cls": r.obb.cls.cpu().numpy(), "conf": r.obb.conf.cpu().numpy(), "xywhr": r.obb.xywhr.cpu()}
        gts = gt_of(img, a.split)
        tp, fps, fns, ious = match(pred, gts, r.orig_shape[1], r.orig_shape[0])
        all_ious += ious
        per_image.append({"image": img.name, "gt": [NAMES[c] for c, _ in gts], "tp": len(tp), "fp": fps, "fn": fns,
                          "pred_groups": sorted({GROUP[int(c)] for c in pred["cls"]}),
                          "pred_classes": sorted({NAMES[int(c)] for c in pred["cls"]})})
        side_by_side(img, r, gts, out / "predictions" / f"{img.stem}.jpg")
        for c in {c for c, _ in gts}:
            if examples[c] < 2:
                examples[c] += 1
                shutil.copy(out / "predictions" / f"{img.stem}.jpg", out / "examples" / f"{NAMES[c]}_{examples[c]}.jpg")
    n_tp = sum(p["tp"] for p in per_image)
    n_fp = sum(len(p["fp"]) for p in per_image)
    n_fn = sum(len(p["fn"]) for p in per_image)
    metrics["operating_point"] = {
        "conf": a.conf, "iou_match": 0.5, "true_positives": n_tp, "false_positives": n_fp, "false_negatives": n_fn,
        "precision": round(n_tp / max(1, n_tp + n_fp), 3), "recall": round(n_tp / max(1, n_tp + n_fn), 3),
        "mean_iou_of_matches": round(float(np.mean(all_ious)), 3) if all_ious else None,
        "fp_by_kind": {k: sum(1 for p in per_image for f in p["fp"] if f["kind"].startswith(k)) for k in ("wrong class", "no matching")},
        "fn_by_class": {n: sum(p["fn"].count(n) for p in per_image) for n in NAMES},
        "predict_ms_per_image_median": round(st.median(t_inf[1:] or t_inf), 1),
        "images_with_errors": [p for p in per_image if p["fp"] or p["fn"]][:50]}

    # 3) clean holdout (no annotations, not used for training/tuning)
    clean = []
    for img in sorted((DATA / "clean_holdout" / "images").iterdir()):
        r = model.predict(str(img), imgsz=640, conf=a.conf, verbose=False)[0]
        r.names = DISPLAY
        cv2.imwrite(str(out / "clean" / img.name), r.plot())
        clean.append({"image": img.name, "detections": [DISPLAY[int(c)] for c in r.obb.cls.cpu().numpy()]})
    metrics["clean_holdout"] = {"images": len(clean), "images_with_any_detection": sum(1 for c in clean if c["detections"]),
                                "detail": clean, "note": "only 2 unannotated images exist in the dataset: weak evidence"}

    # 4) image-level comparison with Llama 4 Maverick (same test images)
    lp = HERE / "results" / "llama_test_predictions.json"
    if lp.exists() and a.split == "test":
        L = {r["image"]: r for r in json.load(open(lp))["results"] if r["split"] == "test"}
        Y = {p["image"]: p for p in per_image}
        cmp = {}
        for name, getg in (("yolo26", lambda im: set(Y[im]["pred_groups"])),
                           ("llama4_maverick", lambda im: {LLAMA_GROUP[d["type"]] for d in L[im]["detections"] if d["type"] in LLAMA_GROUP})):
            row = {}
            for g in ("surface", "moisture"):
                pos = [im for im in Y if g in {GROUP[NAMES.index(c)] for c in Y[im]["gt"]}]
                neg = [im for im in Y if im not in pos]
                hit = sum(1 for im in pos if g in getg(im))
                fp = sum(1 for im in neg if g in getg(im))
                row[g] = {"image_recall": f"{hit}/{len(pos)}", "false_positive_images": f"{fp}/{len(neg)}"}
            stains = [im for im in Y if "ceiling_stain" in Y[im]["gt"]]
            row["missed_stain_images"] = sum(1 for im in stains if "moisture" not in getg(im))
            row["stain_images"] = len(stains)
            cmp[name] = row
        lat = [r["seconds"] for r in L.values() if not r["error"]]
        cmp["llama4_maverick"]["seconds_per_image_median"] = round(st.median(lat), 2) if lat else None
        cmp["llama4_maverick"]["errors"] = sum(1 for r in L.values() if r["error"])
        cmp["llama4_maverick"]["images_with_a_bbox"] = sum(1 for r in L.values() if any(d.get("bbox") for d in r["detections"]))
        cmp["yolo26"]["ms_per_image_median"] = metrics["operating_point"]["predict_ms_per_image_median"]
        cmp["yolo26"]["mean_iou_of_matched_boxes"] = metrics["operating_point"]["mean_iou_of_matches"]
        cmp["mapping"] = "crack/hole -> DAMAGED_SURFACES; damp/mold-like/stain -> WATER_DAMAGE_MOLD or LEAK_PLUMBING"
        metrics["vs_llama"] = cmp

    json.dump(metrics, open(out / "metrics.json", "w"), indent=1)
    title = "evaluated once" if a.split == "test" else "PIPELINE CHECK ONLY"
    md = [f"# {run}: {a.split}-set results (50 images, {title})\n",
          f"Trained on: {metrics['train_info']}\n",
          "| overall | value |\n|---|---|"] + [f"| {k} | {v} |" for k, v in metrics["overall"].items()]
    md += ["\n| class | precision | recall | mAP50 | mAP50-95 |\n|---|---|---|---|---|"]
    md += [f"| {v['display']} | {v['precision']} | {v['recall']} | {v['mAP50']} | {v['mAP50-95']} |" for v in per_class.values()]
    md += [f"\nSpeed (ms/image): {metrics['speed_ms_per_image']}",
           f"\nOperating point conf={a.conf}: {json.dumps({k: v for k, v in metrics['operating_point'].items() if k != 'images_with_errors'})}",
           f"\nClean holdout: {metrics['clean_holdout']['images_with_any_detection']}/{metrics['clean_holdout']['images']} images with a detection"]
    if "vs_llama" in metrics:
        md += ["\n## vs Llama 4 Maverick (image level)\n```json", json.dumps(metrics["vs_llama"], indent=1), "```"]
    (out / "metrics.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    return metrics


if __name__ == "__main__":
    main()
