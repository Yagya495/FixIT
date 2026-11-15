"""Annotation-quality audit of the whole Roboflow ceiling ZIP (read-only). Polygons rasterized at 160x160.
- box size: whole-image boxes (>= 60% of the image) and tiny boxes (< 0.2%)
- same-class near-duplicate boxes (mask IoU >= 0.7) and cross-class overlap (>= 50% of the smaller box covered by a
  box of another class: the same region labelled two ways, e.g. damp + stain + mold-like)
- label consistency between copies of the SAME photo (duplicate groups): class-count vectors that differ
Writes annotation_audit.json.
"""
import collections
import itertools
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
EXP1 = HERE.parents[1] / "yolo_ceiling"
sys.path.insert(0, str(EXP1))
from analyze_dataset import NAMES, ZIP, load  # noqa: E402
from dedup import DUP_BITS, groups  # noqa: E402

S = 160


def masks(text):
    out = []
    for line in text.splitlines():
        p = line.split()
        if len(p) != 9:
            continue
        pts = [(float(p[1 + 2 * i]) * S, float(p[2 + 2 * i]) * S) for i in range(4)]
        im = Image.new("1", (S, S), 0)
        ImageDraw.Draw(im).polygon(pts, fill=1)
        out.append((int(p[0]), np.asarray(im, dtype=bool)))
    return out


items = load(ZIP)
z = zipfile.ZipFile(ZIP)
gid, _, _ = groups(items, ZIP, threshold=DUP_BITS)
stats = collections.Counter()
per_class_area = collections.defaultdict(list)
examples = collections.defaultdict(list)
for it in items:
    if not it["label"]:
        continue
    ms = masks(z.read(it["label"]).decode())
    for c, m in ms:
        a = m.mean()
        per_class_area[NAMES[c]].append(a)
        stats["boxes"] += 1
        if a >= 0.6:
            stats["whole_image_boxes"] += 1; examples["whole_image"].append(Path(it["image"]).name)
        if a < 0.002:
            stats["tiny_boxes"] += 1
    for (c1, m1), (c2, m2) in itertools.combinations(ms, 2):
        inter = (m1 & m2).sum()
        if not inter:
            continue
        if c1 == c2 and inter / max(1, (m1 | m2).sum()) >= 0.7:
            stats["same_class_duplicate_pairs"] += 1; examples["same_class_dup"].append(Path(it["image"]).name)
        if c1 != c2 and inter / max(1, min(m1.sum(), m2.sum())) >= 0.5:
            stats["cross_class_overlap_pairs"] += 1
            key = "+".join(sorted((NAMES[c1][8:], NAMES[c2][8:])))
            stats[f"overlap:{key}"] += 1
            examples["cross_class"].append(Path(it["image"]).name)
# consistency among copies of the same photo
by_g = collections.defaultdict(list)
for it in items:
    by_g[gid[it["image"]]].append(it)
multi = [v for v in by_g.values() if len(v) > 1]
incons = [v for v in multi if len({tuple(i["counts"]) for i in v}) > 1]
incons_cls = [v for v in multi if len({tuple(bool(x) for x in i["counts"]) for i in v}) > 1]
res = {"images": len(items), "boxes": stats["boxes"],
       "whole_image_boxes": stats["whole_image_boxes"], "tiny_boxes": stats["tiny_boxes"],
       "same_class_duplicate_pairs": stats["same_class_duplicate_pairs"],
       "cross_class_overlap_pairs": stats["cross_class_overlap_pairs"],
       "cross_class_overlap_by_pair": {k[8:]: v for k, v in stats.items() if k.startswith("overlap:")},
       "median_box_area_pct_by_class": {k: round(100 * float(np.median(v)), 2) for k, v in per_class_area.items()},
       "boxes_by_class": {k: len(v) for k, v in per_class_area.items()},
       "photos_with_copies": len(multi),
       "copies_with_different_box_counts": len(incons),
       "copies_with_different_class_sets": len(incons_cls),
       "examples": {k: sorted(set(v))[:12] for k, v in examples.items()},
       "inconsistent_copy_examples": [[Path(i["image"]).name for i in v][:3] for v in incons_cls[:8]]}
json.dump(res, open(HERE / "annotation_audit.json", "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if k not in ("examples", "inconsistent_copy_examples")}, indent=1))
