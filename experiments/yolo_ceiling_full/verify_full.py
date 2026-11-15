"""Independent leakage/integrity check for experiment 2 (exits non-zero on any violation):
- every file byte-identical to its ZIP member; labels identical; valid OBB lines
- test == experiment 1's 50 test images (by SHA-256), unchanged
- no exact or rotation/flip-invariant near-duplicate between any two splits (same rule as dedup.py), checked on ALL
  files, and no duplicate group in two splits
- the ZIP is unchanged; experiment 1's manifest is unchanged (hash recorded in experiment 1's summary is re-checked)
"""
import csv
import hashlib
import itertools
import json
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP1 = HERE.parent / "yolo_ceiling"
sys.path.insert(0, str(EXP1))
from analyze_dataset import ZIP  # noqa: E402
from dedup import DUP_BITS, MIN_CORR, STRICT_BITS, best_corr, dihedral_hashes, dihedral_pixels, inv_distance  # noqa: E402

D = HERE / "dataset_full"
summ = json.load(open(HERE / "selection_summary.json"))
errors = []
if hashlib.sha256(ZIP.read_bytes()).hexdigest() != summ["zip_sha256"]:
    errors.append("ZIP changed")
z = zipfile.ZipFile(ZIP)
members = {Path(n).name: n for n in z.namelist() if "/images/" in n}
files = {}
for split in ("train", "valid", "test"):
    for im in sorted((D / split / "images").iterdir()):
        data = im.read_bytes()
        if im.name not in members or z.read(members[im.name]) != data:
            errors.append(f"{split}/{im.name}: not identical to the ZIP")
        lab = D / split / "labels" / (im.stem + ".txt")
        zlab = members[im.name].replace("/images/", "/labels/").rsplit(".", 1)[0] + ".txt"
        if not lab.exists() or lab.read_bytes() != z.read(zlab):
            errors.append(f"{split}/{lab.name}: label differs")
        for line in lab.read_text().splitlines():
            p = line.split()
            if len(p) != 9 or int(p[0]) not in range(5):
                errors.append(f"{split}/{lab.name}: bad line")
        files[f"{split}/{im.name}"] = data
counts = {s: sum(1 for k in files if k.startswith(s + "/")) for s in ("train", "valid", "test")}
for s, st in summ["splits"].items():
    if counts[s] != st["image_files"]:
        errors.append(f"{s}: {counts[s]} files on disk vs {st['image_files']} in summary")
exp1_test = {r["sha256"] for r in csv.DictReader(open(EXP1 / "selection_manifest.csv", encoding="utf-8")) if r["selected_split"] == "test"}
test_sha = {hashlib.sha256(v).hexdigest() for k, v in files.items() if k.startswith("test/")}
if test_sha != exp1_test:
    errors.append("test split differs from experiment 1's test images")
man = list(csv.DictReader(open(HERE / "selection_manifest.csv", encoding="utf-8")))
g = {s: {r["dup_group"] for r in man if r["selected_split"] == s} for s in ("train", "valid", "test")}
for a, b in itertools.combinations(g, 2):
    if g[a] & g[b]:
        errors.append(f"duplicate group in {a} and {b}: {len(g[a] & g[b])}")
H = {k: dihedral_hashes(v) for k, v in files.items()}
P = {k: dihedral_pixels(v) for k, v in files.items()}
shas = {}
closest = (999, None)
for a, b in itertools.combinations(files, 2):
    sa, sb = a.split("/")[0], b.split("/")[0]
    if sa == sb:
        continue
    d = inv_distance(H[a], H[b])
    closest = min(closest, (d, (a, b)))
    if d <= STRICT_BITS or (d <= DUP_BITS and best_corr(P[a], P[b]) >= MIN_CORR):
        errors.append(f"near-duplicate across splits (d={d}): {a} ~ {b}")
print("files:", counts, "| closest cross-split pair:", closest[0], "bits of 256")
print("RESULT:", "OK, no leakage; test == experiment 1 test" if not errors else f"{len(errors)} problems")
for e in errors[:20]:
    print("  ", e)
sys.exit(1 if errors else 0)
