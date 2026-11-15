"""READ-ONLY analysis of the Roboflow ceiling ZIP (not modified): per-split class/instance counts, Roboflow source-photo
groups (`<source>_jpg.rf.<hash>` = variants of one photo) and near-duplicates (64-bit dHash) within and across splits.

    python experiments/yolo_ceiling/analyze_dataset.py [path/to/Ceiling.v1i.yolov8-obb.zip]
"""
import collections
import hashlib
import io
import json
import re
import sys
import zipfile
from pathlib import Path

from PIL import Image

ZIP = Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\naish\Desktop\fixit\Ceiling.v1i.yolov8-obb.zip")
NAMES = ["ceiling_crack", "ceiling_damp", "ceiling_hole", "ceiling_mold", "ceiling_stain"]
SPLITS = ["train", "valid", "test"]


def dhash(img: Image.Image, n: int = 8) -> int:
    g = img.convert("L").resize((n + 1, n), Image.LANCZOS)
    px = list(g.getdata())
    bits = 0
    for r in range(n):
        for c in range(n):
            bits = (bits << 1) | (px[r * (n + 1) + c] > px[r * (n + 1) + c + 1])
    return bits


def source_of(name: str) -> str:
    stem = Path(name).stem
    return re.sub(r"\.rf\.[0-9a-f]+$", "", stem)


def load(zip_path: Path) -> list[dict]:
    z = zipfile.ZipFile(zip_path)
    files = set(z.namelist())
    items = []
    for split in SPLITS:
        for n in sorted(f for f in files if f.startswith(f"{split}/images/") and not f.endswith("/")):
            stem = Path(n).stem
            lab = f"{split}/labels/{stem}.txt"
            text = z.read(lab).decode() if lab in files else ""
            counts = [0] * len(NAMES)
            bad = 0
            for line in text.splitlines():
                p = line.split()
                if not p:
                    continue
                if len(p) != 9 or not p[0].isdigit() or int(p[0]) >= len(NAMES):
                    bad += 1
                    continue
                counts[int(p[0])] += 1
            data = z.read(n)
            img = Image.open(io.BytesIO(data))
            items.append({"split": split, "image": n, "label": lab if lab in files else None, "stem": stem,
                          "source": source_of(n), "sha256": hashlib.sha256(data).hexdigest(), "size": img.size,
                          "dhash": dhash(img), "counts": counts, "bad_lines": bad})
    return items


if __name__ == "__main__":
    items = load(ZIP)
    print("images per split:", collections.Counter(i["split"] for i in items))
    print("missing labels:", sum(i["label"] is None for i in items), "| malformed label lines:", sum(i["bad_lines"] for i in items))
    print("image sizes:", collections.Counter(i["size"] for i in items))
    print("\nper split: images containing each class / instances")
    for s in SPLITS:
        it = [i for i in items if i["split"] == s]
        img_c = [sum(1 for i in it if i["counts"][k]) for k in range(5)]
        inst = [sum(i["counts"][k] for i in it) for k in range(5)]
        empty = sum(1 for i in it if not any(i["counts"]))
        multi = sum(1 for i in it if sum(1 for c in i["counts"] if c) > 1)
        print(f"  {s:5}: " + "  ".join(f"{NAMES[k][8:]}={img_c[k]}/{inst[k]}" for k in range(5)) + f"  empty={empty} multi-class={multi}")
    # exact duplicates
    by_sha = collections.defaultdict(list)
    for i in items:
        by_sha[i["sha256"]].append(i)
    exact = [v for v in by_sha.values() if len(v) > 1]
    print("\nexact duplicate groups:", len(exact), "| crossing splits:", sum(len({i['split'] for i in v}) > 1 for v in exact))
    # Roboflow source groups
    by_src = collections.defaultdict(list)
    for i in items:
        by_src[i["source"]].append(i)
    cross = {k: v for k, v in by_src.items() if len({i["split"] for i in v}) > 1}
    print("source photos:", len(by_src), "| with >1 variant:", sum(len(v) > 1 for v in by_src.values()),
          "| sources whose variants span splits:", len(cross))
    for k, v in list(cross.items())[:8]:
        print("   ", k[:50], sorted(collections.Counter(i["split"] for i in v).items()))
    # near duplicates across splits (dHash Hamming distance <= 6)
    pairs = []
    for a in range(len(items)):
        for b in range(a + 1, len(items)):
            x, y = items[a], items[b]
            if x["split"] != y["split"] and bin(x["dhash"] ^ y["dhash"]).count("1") <= 6:
                pairs.append((x["image"], y["image"], bin(x["dhash"] ^ y["dhash"]).count("1"), x["source"] == y["source"]))
    print("near-duplicate pairs across splits (dHash<=6):", len(pairs), "| of which same Roboflow source:", sum(p[3] for p in pairs))
    for p in pairs[:6]:
        print("   ", p)
    out = Path(__file__).parent / "dataset_analysis.json"
    json.dump({"zip_sha256": hashlib.sha256(ZIP.read_bytes()).hexdigest(), "n": len(items),
               "cross_split_sources": {k: [i["image"] for i in v] for k, v in cross.items()},
               "near_dup_pairs": pairs}, open(out, "w"), indent=1)
    print("\nwrote", out.name)
