"""Targeted cleanup of disposable test records listed in a manifest (default: DRY RUN, read-only).

  python scripts/cleanup_test_records.py docs/ops/test_records_2026-11-15.json            # dry run (SELECT only)
  python scripts/cleanup_test_records.py <manifest> --apply --confirm <manifest_sha256>   # only with user approval

Safety:
  - Deletes ONLY rows whose key is listed in the manifest, table by table, never by pattern or date.
  - Refuses to run if the manifest was edited (sha mismatch), if any listed row is missing or extra rows match, if a
    listed scan's address is not the disposable building, or if any listed record touches the demo building.
  - Volume files are deleted only if no remaining evidence row references them (content-addressed files are shared).
  - Records each table's Delta version first, so `RESTORE TABLE ... TO VERSION AS OF <v>` can undo the row deletes.
  - Profile 'fixit' only; never prints credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISPOSABLE_ADDRESS_PREFIX = "1770 FAIR OAKS"
PROTECTED_PROPERTY = "P-DEMO-1234"
ORDER = ["silver.complaints", "silver.deadlines", "silver.calls", "gold.reports", "silver.repair_requests",
         "gold.violations", "silver.detections", "silver.evidence", "silver.scans"]


def load_manifest(path: Path) -> dict:
    m = json.loads(path.read_text(encoding="utf-8"))
    claimed = m.pop("manifest_sha256")
    actual = hashlib.sha256(json.dumps(m, indent=1, sort_keys=True).encode()).hexdigest()
    if claimed != actual:
        sys.exit(f"manifest was modified (sha {actual[:16]} != {claimed[:16]}); refusing")
    m["manifest_sha256"] = claimed
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--confirm", default="")
    a = ap.parse_args()
    m = load_manifest(Path(a.manifest))
    if a.apply and a.confirm != m["manifest_sha256"]:
        sys.exit("--apply needs --confirm <full manifest_sha256>")

    os.environ.update({"DATA_BACKEND": "databricks", "DATABRICKS_CONFIG_PROFILE": "fixit",
                       "DATABRICKS_WAREHOUSE_ID": os.environ.get("DATABRICKS_WAREHOUSE_ID", "6361516ab33ba2d2"),
                       "FIXIT_CATALOG": "fixit"})
    sys.path.insert(0, str(ROOT))
    from app.backend import db

    def ids_clause(col, ids, prefix="v"):
        p = {f"{prefix}{i}": v for i, v in enumerate(ids)}
        return f"{col} IN ({', '.join(':' + k for k in p)})", p

    problems = []
    scans = m["tables"]["silver.scans"]["ids"]
    w, p = ids_clause("scan_id", scans)
    rows = db.q(f"SELECT scan_id, address, property_id FROM {{silver.scans}} WHERE {w}", p)
    for r in rows:
        if not (r["address"] or "").upper().startswith(DISPOSABLE_ADDRESS_PREFIX) or r["property_id"] == PROTECTED_PROPERTY:
            problems.append(f"scan {r['scan_id']} is not on the disposable building")
    plan = []
    for table in ORDER:
        spec = m["tables"][table]
        w, p = ids_clause(spec["key"], spec["ids"])
        n = db.q1(f"SELECT COUNT(*) AS n FROM {{{table}}} WHERE {w}", p)["n"]
        expected = spec.get("expected_rows", len(spec["ids"]))
        if int(n) != int(expected):
            problems.append(f"{table}: {n} rows match, manifest expects {expected}")
        if table in ("gold.reports", "silver.repair_requests", "gold.violations"):
            bad = db.q1(f"SELECT COUNT(*) AS n FROM {{{table}}} WHERE {w} AND property_id = :pp", {**p, "pp": PROTECTED_PROPERTY})["n"]
            if int(bad):
                problems.append(f"{table}: listed rows touch the demo building")
        plan.append((table, w, p, int(n)))
        print(f"{'DELETE' if a.apply else 'would delete'} {int(n):3} rows from {db.t(table)} where {spec['key']} in manifest")

    # Volume files: keep any file still referenced by evidence outside the manifest.
    ev_ids = m["tables"]["silver.evidence"]["ids"]
    files = []
    for path in m["volume_files"]:
        w1, p1 = ids_clause("evidence_id", ev_ids, "e")
        other = db.q1(f"SELECT COUNT(*) AS n FROM {{silver.evidence}} WHERE volume_path = :vp AND NOT ({w1})", {**p1, "vp": path})["n"]
        if int(other):
            print(f"keep (shared with non-test evidence): {path}")
        else:
            files.append(path)
    print(f"{'DELETE' if a.apply else 'would delete'} {len(files)} of {len(m['volume_files'])} volume files (rest shared/kept)")

    if problems:
        print("\nREFUSING:", *problems, sep="\n  ")
        return 1
    if not a.apply:
        print("\nDRY RUN only: nothing was changed.")
        return 0

    versions = {}
    for table in ORDER:
        h = db.q(f"DESCRIBE HISTORY {db.t(table)} LIMIT 1")
        versions[table] = h[0]["version"] if h else None
    log = ROOT / "docs" / "ops" / f"cleanup_log_{m['manifest_sha256'][:12]}.json"
    log.write_text(json.dumps({"delta_versions_before": versions, "manifest": a.manifest}, indent=1, default=str), encoding="utf-8")
    print("Delta versions before cleanup recorded in", log.relative_to(ROOT))
    for table, w, p, n in plan:
        db.execute(f"DELETE FROM {{{table}}} WHERE {w}", p)
    from databricks.sdk import WorkspaceClient

    wc = WorkspaceClient(profile="fixit")
    for path in files:
        wc.files.delete(path)
    for table, w, p, _ in plan:
        left = db.q1(f"SELECT COUNT(*) AS n FROM {{{table}}} WHERE {w}", p)["n"]
        print(f"{table}: {left} listed rows remain")
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
