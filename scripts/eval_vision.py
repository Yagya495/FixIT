"""Evaluate the vision model on real or staged apartment photos, live, with no Demo Mode and no cache.

Layout (see eval/README.md):
  eval/photos/<TYPE_ID>/*.jpg   photos that clearly show that violation (e.g. eval/photos/SMOKE_DETECTOR_MISSING/)
  eval/photos/NONE/*.jpg        photos of rooms with none of the 10 visible types (false-positive check)
  eval/labels.csv (optional)    file,labels   for multi-label photos, labels separated by ';' (empty = NONE).
                                 Overrides the folder label for the files it lists.

  python scripts/eval_vision.py --profile fixit                                   # llama-4-maverick, walkthrough prompt
  python scripts/eval_vision.py --profile fixit --vision databricks-gemma-3-12b   # compare a second model
  python scripts/eval_vision.py --profile fixit --mode listing                    # listing (marketing-photo) prompt

Writes eval/results/<timestamp>_<model>_<mode>.json and .md. Photos are sent to the workspace's serving endpoint only;
JPEG EXIF (GPS, device) is stripped before sending. Nothing is written to Databricks tables.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
EXTS = {".jpg", ".jpeg", ".png"}


def strip_jpeg_metadata(data: bytes) -> bytes:
    """Drop APP1..APP15 segments (EXIF/GPS/XMP) from a JPEG without re-encoding. Non-JPEGs pass through."""
    if data[:2] != b"\xff\xd8":
        return data
    out, i = bytearray(b"\xff\xd8"), 2
    while i + 4 <= len(data) and data[i] == 0xFF:
        marker = data[i + 1]
        if marker == 0xDA:  # start of scan: the rest is image data
            out += data[i:]
            return bytes(out)
        seg_len = int.from_bytes(data[i + 2:i + 4], "big")
        if not (0xE1 <= marker <= 0xEF):  # keep APP0 (JFIF), quant/huffman tables, frame headers...
            out += data[i:i + 2 + seg_len]
        i += 2 + seg_len
    return data  # unexpected structure: send unchanged rather than corrupt it


def load_items(photo_dir: Path, labels_csv: Path) -> list[tuple[Path, set[str]]]:
    from app.backend.services.taxonomy import BY_ID

    override = {}
    if labels_csv.exists():
        for r in csv.DictReader(labels_csv.open(encoding="utf-8")):
            override[r["file"].strip()] = {l.strip() for l in (r.get("labels") or "").split(";") if l.strip()}
    items = []
    for p in sorted(photo_dir.rglob("*")):
        if p.suffix.lower() not in EXTS:
            continue
        folder = p.parent.name
        labels = override.get(p.name, set() if folder == "NONE" else {folder})
        unknown = labels - set(BY_ID)
        if unknown:
            print(f"skip {p.name}: unknown label(s) {unknown}")
            continue
        items.append((p, labels))
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--vision", default="databricks-llama-4-maverick")
    ap.add_argument("--mode", choices=["walkthrough", "listing"], default="walkthrough")
    ap.add_argument("--photos", default=str(ROOT / "eval" / "photos"))
    ap.add_argument("--threshold", type=float, default=0.6, help="same as the app's 'certain' threshold")
    a = ap.parse_args()
    if a.profile == "sleepsafe":
        return 2
    os.environ.update({"DATABRICKS_CONFIG_PROFILE": a.profile, "VISION_ENDPOINT": a.vision, "DEMO_MODE": "false"})
    from app.backend import config
    from app.backend.services import vision
    from app.backend.services.taxonomy import VIOLATION_TYPES

    config.VISION_ENDPOINT, config.DEMO_MODE = a.vision, False
    photo_dir = Path(a.photos)
    items = load_items(photo_dir, ROOT / "eval" / "labels.csv")
    if not items:
        print(f"No photos found under {photo_dir}. See eval/README.md.")
        return 1
    types = [v["type_id"] for v in VIOLATION_TYPES if v["type_id"] != "NO_HEAT"]  # NO_HEAT can't be photographed
    per_photo, latencies, failures = [], [], 0
    for p, truth in items:
        data = strip_jpeg_metadata(p.read_bytes())
        mt = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
        t0 = time.time()
        try:
            res = vision.analyze_frame_live(data, a.mode, mt)  # live call only: never cache, never scripted fallback
            # Score what the app would show: the same alarm screening as scans.process_frames (a photo can't show an
            # alarm is missing). Raw model output that was screened out is kept for analysis.
            dets, screened = {}, []
            for d in res.detections:
                kept = vision.screen_detection(d.model_dump())
                if kept is None:
                    screened.append(d.violation_type)
                else:
                    dets[d.violation_type] = max(d.confidence, dets.get(d.violation_type, 0.0))
            err = None
        except Exception as e:
            dets, screened, err = {}, [], f"{type(e).__name__}: {str(e)[:160]}"
            failures += 1
        latencies.append(time.time() - t0)
        pred = {t for t, c in dets.items() if c >= a.threshold}
        per_photo.append({"file": str(p.relative_to(photo_dir)), "truth": sorted(truth), "pred": sorted(pred),
                          "all_detections": dets, "screened_out": screened, "error": err, "secs": round(latencies[-1], 2)})
        mark = "OK " if pred == truth and not err else "XX "
        print(f"{mark}{p.relative_to(photo_dir)}  truth={sorted(truth) or ['NONE']}  pred={sorted(pred) or ['NONE']}"
              + (f"  ERROR {err}" if err else ""))

    metrics = {}
    for t in types:
        tp = sum(1 for r in per_photo if t in r["truth"] and t in r["pred"])
        fp = sum(1 for r in per_photo if t not in r["truth"] and t in r["pred"])
        fn = sum(1 for r in per_photo if t in r["truth"] and t not in r["pred"])
        support = tp + fn
        metrics[t] = {"support": support, "tp": tp, "fp": fp, "fn": fn,
                      "precision": round(tp / (tp + fp), 3) if tp + fp else None,
                      "recall": round(tp / support, 3) if support else None}
    clean = [r for r in per_photo if not r["truth"]]
    summary = {
        "model": a.vision, "mode": a.mode, "threshold": a.threshold, "n_photos": len(per_photo), "call_failures": failures,
        "exact_match_rate": round(sum(1 for r in per_photo if set(r["pred"]) == set(r["truth"])) / len(per_photo), 3),
        "clean_photos": len(clean),
        "clean_photo_false_alarm_rate": round(sum(1 for r in clean if r["pred"]) / len(clean), 3) if clean else None,
        "latency_p50_s": round(statistics.median(latencies), 2),
        "latency_max_s": round(max(latencies), 2),
        "run_at": datetime.now().isoformat(timespec="seconds"),
    }
    out_dir = ROOT / "eval" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{datetime.now():%Y%m%d-%H%M%S}_{a.vision}_{a.mode}"
    (out_dir / f"{stem}.json").write_text(json.dumps({"summary": summary, "per_type": metrics, "photos": per_photo}, indent=2))
    lines = [f"# Vision eval: {a.vision} ({a.mode} prompt)", "",
             f"{summary['n_photos']} photos · threshold {a.threshold} · live calls only (no cache, no Demo Mode) · "
             f"call failures {failures} · p50 {summary['latency_p50_s']} s", "",
             f"- Exact-match rate (all labels right): **{summary['exact_match_rate']}**",
             f"- False alarms on clean photos: **{summary['clean_photo_false_alarm_rate']}** ({len(clean)} clean photos)", "",
             "| Type | Photos with it | Precision | Recall | FP |", "|---|---|---|---|---|"]
    lines += [f"| {t} | {m['support']} | {m['precision']} | {m['recall']} | {m['fp']} |" for t, m in metrics.items()]
    lines += ["", "Small staged sample: treat these numbers as a sanity check, not a benchmark."]
    (out_dir / f"{stem}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n" + "\n".join(lines[2:6]) + f"\n\nSaved eval/results/{stem}.md and .json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
