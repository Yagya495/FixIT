"""Independent check of dataset_250 against the ZIP and the manifest. Exits non-zero on any violation.
- exactly 150/50/50, all unique by SHA-256, every file byte-identical to the ZIP member in the SAME original split
- labels: OBB lines (class + 8 normalized coords), classes 0-4, identical to the ZIP label
- no exact or rotation/flip-invariant near-duplicate (dedup.py rule) between any two selected splits
- the ZIP's own hash is unchanged
"""
import hashlib
import itertools
import json
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from analyze_dataset import ZIP  # noqa: E402
from dedup import DUP_BITS, MIN_CORR, STRICT_BITS, best_corr, dihedral_hashes, dihedral_pixels, inv_distance  # noqa: E402

D = HERE / "dataset_250"
summ = json.load(open(HERE / "selection_summary.json"))
errors = []
z = zipfile.ZipFile(ZIP)
if hashlib.sha256(ZIP.read_bytes()).hexdigest() != summ["zip_sha256"]:
    errors.append("ZIP hash changed")
expect = {"train": 150, "valid": 50, "test": 50}
files, shas = {}, {}
for split, n in expect.items():
    imgs = sorted((D / split / "images").iterdir())
    labs = sorted((D / split / "labels").iterdir())
    if len(imgs) != n or len(labs) != n:
        errors.append(f"{split}: {len(imgs)} images / {len(labs)} labels (expected {n})")
    for im in imgs:
        data = im.read_bytes()
        member = f"{split}/images/{im.name}"                         # same original split
        if member not in z.namelist() or z.read(member) != data:
            errors.append(f"{split}/{im.name}: not identical to the ZIP file in the original {split} split")
        lab = D / split / "labels" / (im.stem + ".txt")
        if not lab.exists() or lab.read_bytes() != z.read(f"{split}/labels/{im.stem}.txt"):
            errors.append(f"{split}/{im.name}: label missing or differs from the ZIP")
        for line in lab.read_text().splitlines():
            p = line.split()
            if len(p) != 9 or int(p[0]) not in range(5) or not all(-0.01 <= float(x) <= 1.01 for x in p[1:]):
                errors.append(f"{split}/{lab.name}: bad OBB line {line[:40]}")
        sha = hashlib.sha256(data).hexdigest()
        if sha in shas:
            errors.append(f"exact duplicate: {split}/{im.name} == {shas[sha]}")
        shas[sha] = f"{split}/{im.name}"
        files[f"{split}/{im.name}"] = data
H = {k: dihedral_hashes(v) for k, v in files.items()}
P = {k: dihedral_pixels(v) for k, v in files.items()}
closest = (999, None)
for a, b in itertools.combinations(files, 2):
    if a.split("/")[0] == b.split("/")[0]:
        continue
    d = inv_distance(H[a], H[b])
    closest = min(closest, (d, (a, b)))
    if d <= STRICT_BITS or (d <= DUP_BITS and best_corr(P[a], P[b]) >= MIN_CORR):
        errors.append(f"near-duplicate across splits (d={d}): {a} ~ {b}")
print("closest cross-split pair (invariant dHash bits of 256):", closest[0])
print("RESULT:", "OK, 150/50/50 verified, no cross-split duplicates" if not errors else f"{len(errors)} problems")
for e in errors[:20]:
    print("  ", e)
sys.exit(1 if errors else 0)
