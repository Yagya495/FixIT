"""READ-ONLY: finer near-duplicate check. 16x16 dHash (256 bits) + a 32x32 grayscale correlation, for (a) variants
sharing a Roboflow source name and (b) the cross-split pairs a coarse 8x8 hash flagged. Writes contact sheets of a few
pairs to experiments/yolo_ceiling/_dupcheck/ for visual inspection."""
import io
import itertools
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from analyze_dataset import ZIP, load  # noqa: E402

OUT = Path(__file__).parent / "_dupcheck"
OUT.mkdir(exist_ok=True)
z = zipfile.ZipFile(ZIP)


def img(n):
    return Image.open(io.BytesIO(z.read(n))).convert("RGB")


def feats(n):
    g = img(n).convert("L")
    d = np.asarray(g.resize((17, 16), Image.LANCZOS), dtype=float)
    bits = (d[:, :-1] > d[:, 1:]).flatten()
    v = np.asarray(g.resize((32, 32), Image.LANCZOS), dtype=float).flatten()
    v = (v - v.mean()) / (v.std() + 1e-6)
    return bits, v


items = load(ZIP)
F = {i["image"]: feats(i["image"]) for i in items}


def sim(a, b):
    (ba, va), (bb, vb) = F[a], F[b]
    return int((ba != bb).sum()), float(np.dot(va, vb) / len(va))


by_src = {}
for i in items:
    by_src.setdefault(i["source"], []).append(i)
same = [sim(a["image"], b["image"]) + (a["image"], b["image"])
        for v in by_src.values() for a, b in itertools.combinations(v, 2)]
print("same-source variant pairs:", len(same))
print("  dHash256 distance quartiles:", np.percentile([s[0] for s in same], [0, 25, 50, 75, 100]).round(1))
print("  correlation quartiles:      ", np.percentile([s[1] for s in same], [0, 25, 50, 75, 100]).round(3))
allpairs = []
for a, b in itertools.combinations(items, 2):
    if a["source"] != b["source"]:
        d, c = sim(a["image"], b["image"])
        if d <= 40 or c >= 0.9:
            allpairs.append((d, c, a["image"], b["image"], a["split"] != b["split"]))
print("different-source pairs with dHash256<=40 or corr>=0.9:", len(allpairs),
      "| across splits:", sum(p[4] for p in allpairs))


def sheet(pairs, name):
    w = 200
    canvas = Image.new("RGB", (2 * w + 10, len(pairs) * (w + 10)), "white")
    for r, (a, b) in enumerate(pairs):
        canvas.paste(img(a).resize((w, w)), (0, r * (w + 10)))
        canvas.paste(img(b).resize((w, w)), (w + 10, r * (w + 10)))
    canvas.save(OUT / name)


same_sorted = sorted(same)
sheet([(s[2], s[3]) for s in same_sorted[:3] + same_sorted[len(same) // 2:len(same) // 2 + 3] + same_sorted[-2:]], "same_source.png")
sheet([(p[2], p[3]) for p in sorted(allpairs)[:8]], "closest_different_source.png")
json.dump({"same_source": [list(s) for s in same], "close_different_source": [list(p) for p in allpairs]},
          open(OUT / "pairs.json", "w"), indent=1)
print("closest different-source pairs:", [(p[0], round(p[1], 3), p[4]) for p in sorted(allpairs)[:8]])
print("same-source (sorted) sample:", [(s[0], round(s[1], 3)) for s in same_sorted[:3] + same_sorted[len(same)//2:len(same)//2+3] + same_sorted[-2:]])
