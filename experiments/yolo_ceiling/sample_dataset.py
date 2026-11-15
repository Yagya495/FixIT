"""Reproducible 150/50/50 subset of the Roboflow ceiling-damage OBB dataset (seed 42). The ZIP is only read.

Rules (owner, 2026-11-15):
- train only from original train, valid only from original valid, test only from original test; 250 images, the other
  250 unused; no image invented, duplicated or moved between partitions.
- multilabel-aware class coverage: greedy "least-covered class first" (an image counts for every class it contains),
  random choice among eligible images with numpy seed 42.
- duplicates: the export contains flipped/rotated copies of one photo (same Roboflow source name, and also under other
  names). Images are grouped by source name OR rotation/flip-invariant dHash distance <= DUP_BITS (dedup.py); a group
  may appear in only ONE selected split, at most once per split. Test is selected first, so nothing that looks like
  a test image can enter train or valid.
- images without annotations are not sampled; if they don't share a group with train/valid they are kept aside for
  the separate clean-ceiling check.

    python experiments/yolo_ceiling/sample_dataset.py [zip]
"""
import collections
import csv
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from analyze_dataset import NAMES, ZIP, load  # noqa: E402
from dedup import groups  # noqa: E402

SEED = 42
DUP_BITS = 30                                      # see dedup.py (strict 15 bits, or 30 bits + correlation >= 0.85)
TARGET = {"test": 50, "valid": 50, "train": 150}       # selection order: test, valid, train
ORIG = {"train": "train", "valid": "valid", "test": "test"}
OUT = HERE / "dataset_250"


def select(cands: list[dict], n: int, rng: np.random.Generator, blocked: set, per_group: int = 1) -> list[dict]:
    """Least-covered-class-first. First pass: one image per duplicate group. If that can't reach n and per_group > 1,
    later passes may add another (rotated/flipped) copy of a photo already chosen IN THIS SPLIT, never one from a
    blocked group."""
    base = [c for c in cands if c["group"] not in blocked and any(c["counts"])]
    chosen, used = [], collections.Counter()
    cover = np.zeros(len(NAMES))
    for cap in range(1, per_group + 1):
        while len(chosen) < n:
            ids = {c["image"] for c in chosen}
            pool = [c for c in base if used[c["group"]] < cap and c["image"] not in ids]
            if not pool:
                break
            avail = [k for k in range(len(NAMES)) if any(c["counts"][k] for c in pool)]
            k = min(avail, key=lambda k: (cover[k], k))
            elig = sorted((c for c in pool if c["counts"][k]), key=lambda c: c["image"])
            pick = elig[int(rng.integers(len(elig)))]
            chosen.append(pick)
            used[pick["group"]] += 1
            cover += np.array([1 if x else 0 for x in pick["counts"]])
    return chosen


def main():
    items = load(ZIP)
    gid, pairs, _ = groups(items, ZIP, threshold=DUP_BITS)
    for i in items:
        i["group"] = gid[i["image"]]
    sizes = collections.Counter(gid.values())
    print(f"{len(items)} images -> {len(sizes)} duplicate groups (largest {max(sizes.values())}, "
          f"{sum(1 for s in sizes.values() if s > 1)} with copies); near-dup pairs: {len(pairs)}")

    rng = np.random.default_rng(SEED)
    selection, blocked = {}, set()
    for split, n in TARGET.items():
        cands = [i for i in items if i["split"] == ORIG[split]]
        chosen = select(cands, n, rng, blocked, per_group=2 if split == "train" else 1)
        if len(chosen) < n:
            raise SystemExit(f"STOP: only {len(chosen)} eligible distinct images for {split} (need {n})")
        selection[split] = chosen
        blocked |= {c["group"] for c in chosen}

    sel_groups = {c["group"] for v in selection.values() for c in v}
    clean = [i for i in items if not any(i["counts"]) and i["group"] not in
             {c["group"] for s in ("train", "valid") for c in selection[s]}]

    # ---- write the dataset (copies; the ZIP is untouched) ----
    if OUT.exists():
        shutil.rmtree(OUT)                                # only our own generated folder
    z = zipfile.ZipFile(ZIP)
    rows = []
    for split, chosen in selection.items():
        for sub in ("images", "labels"):
            (OUT / split / sub).mkdir(parents=True, exist_ok=True)
        for c in sorted(chosen, key=lambda c: c["image"]):
            name = Path(c["image"]).name
            (OUT / split / "images" / name).write_bytes(z.read(c["image"]))
            (OUT / split / "labels" / (Path(name).stem + ".txt")).write_bytes(z.read(c["label"]))
            rows.append({"selected_split": split, "original_split": c["split"], "image": name, "sha256": c["sha256"],
                         "source": c["source"], "dup_group": c["group"].split("/")[-1][:40],
                         **{n: c["counts"][k] for k, n in enumerate(NAMES)}, "instances": sum(c["counts"])})
    (OUT / "clean_holdout" / "images").mkdir(parents=True, exist_ok=True)
    for c in clean:
        (OUT / "clean_holdout" / "images" / Path(c["image"]).name).write_bytes(z.read(c["image"]))
    (OUT / "data.yaml").write_text(
        "# 250-image subset (150/50/50) of Roboflow 'Ceiling' v1 (CC BY 4.0, universe.roboflow.com/scipublic/ceiling-y9dkm)\n"
        "# Built by sample_dataset.py (seed 42). train_yolo.py rewrites `path` to an absolute path at run time.\n"
        "path: .\ntrain: train/images\nval: valid/images\ntest: test/images\n\nnames:\n"
        + "".join(f"  {k}: {n}\n" for k, n in enumerate(NAMES)), encoding="utf-8")

    with open(HERE / "selection_manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summary = {}
    for split, chosen in selection.items():
        summary[split] = {"images": len(chosen),
                          "images_with_class": {n: sum(1 for c in chosen if c["counts"][k]) for k, n in enumerate(NAMES)},
                          "instances": {n: sum(c["counts"][k] for c in chosen) for k, n in enumerate(NAMES)},
                          "multi_class_images": sum(1 for c in chosen if sum(1 for x in c["counts"] if x) > 1)}
    avail = {s: {n: sum(1 for i in items if i["split"] == s and i["counts"][k]) for k, n in enumerate(NAMES)}
             for s in ORIG.values()}
    json.dump({"zip_sha256": __import__("hashlib").sha256(ZIP.read_bytes()).hexdigest(), "seed": SEED,
               "dup_threshold_bits": DUP_BITS, "duplicate_groups": len(sizes), "summary": summary,
               "available_images_with_class_per_original_split": avail,
               "clean_holdout": [Path(c["image"]).name for c in clean],
               "unused_images": len(items) - sum(len(v) for v in selection.values()),
               "distinct_photos_per_split": {sp: len({c["group"] for c in ch}) for sp, ch in selection.items()},
               "train_images_that_are_a_second_copy_of_a_selected_photo":
                   len(selection["train"]) - len({c["group"] for c in selection["train"]})},
              open(HERE / "selection_summary.json", "w"), indent=1)
    for split in TARGET:
        s = summary[split]
        print(f"{split:5} {s['images']:3d} images | images with class: " +
              " ".join(f"{n[8:]}={s['images_with_class'][n]}" for n in NAMES) +
              " | instances: " + " ".join(f"{n[8:]}={s['instances'][n]}" for n in NAMES))
    print("clean (unannotated) holdout images:", len(clean))
    print("distinct photos per split:", {sp: len({c["group"] for c in ch}) for sp, ch in selection.items()})


if __name__ == "__main__":
    main()
