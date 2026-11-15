"""Experiment 2: group-aware split of the FULL Roboflow ceiling dataset (seed 42). The ZIP is only read; experiment 1
(experiments/yolo_ceiling/) is not modified.

- Duplicate groups (same photo incl. rotated/flipped copies) from experiments/yolo_ceiling/dedup.py (same rule as exp 1).
- TEST = exactly experiment 1's 50 test images (one per photo), so both models are scored on identical images and the
  Llama 4 Maverick baseline on those images stays valid. All other copies of those 50 photos are EXCLUDED.
- VALID = ~15% of all distinct photos, one image per photo, least-covered-class-first over photos.
- TRAIN = every remaining annotated photo with ALL its copies (augmented copies only of training photos).
- Unannotated images: excluded from train/valid (the only two look like unlabeled cracks); kept as the clean holdout.

    python experiments/yolo_ceiling_full/sample_full.py
"""
import collections
import csv
import hashlib
import json
import shutil
import sys
import zipfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
EXP1 = HERE.parent / "yolo_ceiling"
sys.path.insert(0, str(EXP1))
from analyze_dataset import NAMES, ZIP, load  # noqa: E402
from dedup import DUP_BITS, groups  # noqa: E402

SEED = 42
VALID_FRAC = 0.15
OUT = HERE / "dataset_full"


def main():
    items = load(ZIP)
    gid, _, _ = groups(items, ZIP, threshold=DUP_BITS)
    for i in items:
        i["group"] = gid[i["image"]]
        i["name"] = Path(i["image"]).name
    by_group = collections.defaultdict(list)
    for i in items:
        by_group[i["group"]].append(i)
    n_groups = len(by_group)

    exp1 = list(csv.DictReader(open(EXP1 / "selection_manifest.csv", encoding="utf-8")))
    exp1_test = {r["image"]: r["sha256"] for r in exp1 if r["selected_split"] == "test"}
    test = [i for i in items if i["name"] in exp1_test and i["split"] == "test"]
    assert len(test) == 50 and all(i["sha256"] == exp1_test[i["name"]] for i in test), "exp1 test set not reproduced"
    test_groups = {i["group"] for i in test}
    excluded = {"copy_of_a_test_photo": [i for g in test_groups for i in by_group[g] if i not in test]}

    unannotated = [i for i in items if not any(i["counts"]) and i["group"] not in test_groups]
    excluded["unannotated"] = unannotated
    rest = [g for g in sorted(by_group) if g not in test_groups]

    def gcounts(g):                    # copies share the photo, so a group's classes = union over its images
        return [max(i["counts"][k] for i in by_group[g]) for k in range(len(NAMES))]

    eligible = [g for g in rest if any(gcounts(g))]
    n_valid = round(VALID_FRAC * n_groups)
    rng = np.random.default_rng(SEED)
    valid_groups, cover = [], np.zeros(len(NAMES))
    pool = list(eligible)
    while len(valid_groups) < n_valid:
        avail = [k for k in range(len(NAMES)) if any(gcounts(g)[k] for g in pool)]
        k = min(avail, key=lambda k: (cover[k], k))
        elig = sorted(g for g in pool if gcounts(g)[k])
        g = elig[int(rng.integers(len(elig)))]
        valid_groups.append(g); pool.remove(g)
        cover += np.array([1 if x else 0 for x in gcounts(g)])
    # one representative image per validation photo: the annotated copy with the most instances (ties: name)
    valid = [sorted((i for i in by_group[g] if any(i["counts"])), key=lambda i: (-sum(i["counts"]), i["name"]))[0]
             for g in valid_groups]
    excluded["extra_copy_of_a_valid_photo"] = [i for g in valid_groups for i in by_group[g] if i not in valid]
    train_groups = [g for g in eligible if g not in valid_groups]
    train = [i for g in train_groups for i in by_group[g] if any(i["counts"])]

    # ---- write ----
    if OUT.exists():
        shutil.rmtree(OUT)                             # only this experiment's generated folder
    z = zipfile.ZipFile(ZIP)
    rows = []
    for split, chosen in (("train", train), ("valid", valid), ("test", test)):
        for sub in ("images", "labels"):
            (OUT / split / sub).mkdir(parents=True, exist_ok=True)
        for c in sorted(chosen, key=lambda c: c["name"]):
            (OUT / split / "images" / c["name"]).write_bytes(z.read(c["image"]))
            (OUT / split / "labels" / (Path(c["name"]).stem + ".txt")).write_bytes(z.read(c["label"]))
            rows.append({"selected_split": split, "original_split": c["split"], "image": c["name"], "sha256": c["sha256"],
                         "source": c["source"], "dup_group": c["group"].split("/")[-1][:40],
                         **{n: c["counts"][k] for k, n in enumerate(NAMES)}, "instances": sum(c["counts"])})
    (OUT / "clean_holdout" / "images").mkdir(parents=True, exist_ok=True)
    for c in [i for i in items if not any(i["counts"])]:
        (OUT / "clean_holdout" / "images" / c["name"]).write_bytes(z.read(c["image"]))
    (OUT / "data.yaml").write_text(
        "# Experiment 2: full group-aware split of Roboflow 'Ceiling' v1 (CC BY 4.0, universe.roboflow.com/scipublic/ceiling-y9dkm)\n"
        "# Built by sample_full.py (seed 42); test = experiment 1's test images. `path` is rewritten at run time.\n"
        "path: .\ntrain: train/images\nval: valid/images\ntest: test/images\n\nnames:\n"
        + "".join(f"  {k}: {n}\n" for k, n in enumerate(NAMES)), encoding="utf-8")
    with open(HERE / "selection_manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    def stats(chosen):
        return {"image_files": len(chosen), "distinct_photos": len({c["group"] for c in chosen}),
                "images_with_class": {n: sum(1 for c in chosen if c["counts"][k]) for k, n in enumerate(NAMES)},
                "photos_with_class": {n: len({c["group"] for c in chosen if c["counts"][k]}) for k, n in enumerate(NAMES)},
                "instances": {n: sum(c["counts"][k] for c in chosen) for k, n in enumerate(NAMES)}}
    summary = {"zip_sha256": hashlib.sha256(ZIP.read_bytes()).hexdigest(), "seed": SEED, "images_examined": len(items),
               "distinct_photos": n_groups, "splits": {s: stats(c) for s, c in (("train", train), ("valid", valid), ("test", test))},
               "excluded": {k: {"image_files": len(v), "distinct_photos": len({i['group'] for i in v}),
                                "images": sorted(i["name"] for i in v)} for k, v in excluded.items()},
               "clean_holdout": sorted(i["name"] for i in items if not any(i["counts"]))}
    used = len(train) + len(valid) + len(test) + sum(len(v) for v in excluded.values())
    summary["accounted_for"] = used
    json.dump(summary, open(HERE / "selection_summary.json", "w"), indent=1)
    print(f"{len(items)} images, {n_groups} distinct photos; accounted for {used}")
    for s in ("train", "valid", "test"):
        st = summary["splits"][s]
        print(f"{s:5}: {st['image_files']:3d} files / {st['distinct_photos']:3d} photos | photos with class: "
              + " ".join(f"{n[8:]}={st['photos_with_class'][n]}" for n in NAMES))
    for k, v in summary["excluded"].items():
        print(f"excluded {k}: {v['image_files']} files / {v['distinct_photos']} photos")


if __name__ == "__main__":
    main()
