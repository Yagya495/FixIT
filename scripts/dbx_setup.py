"""Milestone 1 setup from your laptop: catalog/schemas/volumes, tables, taxonomy, synthetic data, story check.

DRY RUN BY DEFAULT: prints every statement and upload it would make. Nothing changes without --apply.

  python scripts/dbx_setup.py --profile fixit --warehouse <id> --catalog fixit             # print the plan
  python scripts/dbx_setup.py --profile fixit --warehouse <id> --catalog fixit --apply     # do it
  ... --catalog workspace   # Free Edition fallback if CREATE CATALOG is denied (uses the existing catalog)
  ... --only data           # re-run just the data load (idempotent: INSERT OVERWRITE)

Uses the SAME SQL as notebooks/01_setup_catalog.sql + 30_gold_tables.sql (catalog substituted) and the SAME
generator as the local demo (app/backend/services/synthetic.py), so the story matches SQLite exactly.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REFUSED = {"sleepsafe"}
SEED_DIR = "raw/uploads/_seed"  # inside the catalog's raw.uploads volume


def sql_statements(path: Path, catalog: str) -> list[str]:
    """Strip notebook comment lines (-- ..., -- MAGIC, -- COMMAND), substitute the catalog, split on ';'."""
    body = "\n".join(l for l in path.read_text(encoding="utf-8").splitlines() if not l.lstrip().startswith("--"))
    body = re.sub(r"\bfixit\b", catalog, body)
    # Terminators are at line ends; COMMENT strings may contain ';' mid-line ("...PDF; 0 = unverified seed").
    stmts = [s.strip() for s in re.split(r";[ \t]*(?:\r?\n|$)", body) if s.strip()]
    if catalog == "workspace":  # existing catalog: never try to create it
        stmts = [s for s in stmts if not s.upper().startswith("CREATE CATALOG")]
    return stmts


def seed_rows(now: datetime) -> dict[str, list[dict]]:
    from app.backend.services import landlords, synthetic
    from app.backend.services.taxonomy import SEED_CODE_SECTIONS, VIOLATION_TYPES

    data = synthetic.generate(now=now)
    scores = landlords.compute_scores(data["owners"], data["properties"], data["reports"], now)
    return {
        "ref.violation_types": [{**v, "code_sections": json.dumps(v["code_sections"])} for v in VIOLATION_TYPES],
        "silver.code_sections": [dict(s) for s in SEED_CODE_SECTIONS],
        "gold.owners": data["owners"], "gold.properties": data["properties"], "gold.reports": data["reports"],
        "gold.landlord_scores": scores,
    }


STORY_CHECKS = {
    "open HEAT at 1234 Demo St, last 7d (expect 6)":
        "SELECT COUNT(*) FROM {c}.gold.reports WHERE property_id='P-DEMO-1234' AND violation_category='HEAT' "
        "AND status IN ('open','escalated') AND reported_at >= current_timestamp() - INTERVAL 7 DAYS",
    "owner O-DEMO grade (expect D)": "SELECT grade FROM {c}.gold.landlord_scores WHERE owner_id='O-DEMO'",
    "owner's other buildings open issues (expect 11)":
        "SELECT SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) FROM {c}.gold.reports r "
        "JOIN {c}.gold.properties p ON p.property_id=r.property_id WHERE p.owner_id='O-DEMO' AND p.property_id<>'P-DEMO-1234'",
    "rows not flagged synthetic (expect 0)":
        "SELECT (SELECT COUNT(*) FROM {c}.gold.owners WHERE is_synthetic<>1) + "
        "(SELECT COUNT(*) FROM {c}.gold.properties WHERE is_synthetic<>1) + "
        "(SELECT COUNT(*) FROM {c}.gold.reports WHERE source<>'synthetic')",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse", required=True)
    ap.add_argument("--catalog", default="fixit")
    ap.add_argument("--only", choices=["ddl", "data", "check"])
    ap.add_argument("--apply", action="store_true", help="actually create/modify resources")
    a = ap.parse_args()
    if a.profile in REFUSED:
        print("refused profile")
        return 2
    c = a.catalog
    plan_ddl = sql_statements(ROOT / "notebooks" / "01_setup_catalog.sql", c) + \
        sql_statements(ROOT / "notebooks" / "30_gold_tables.sql", c)
    now = datetime.now().replace(microsecond=0)
    rows = seed_rows(now)

    print(f"Catalog: {c} | warehouse: {a.warehouse} | mode: {'APPLY' if a.apply else 'DRY RUN (nothing will change)'}")
    if a.only in (None, "ddl"):
        print(f"\n-- {len(plan_ddl)} DDL statements (from notebooks 01 + 30):")
        for s in plan_ddl:
            print("   " + " ".join(s.split())[:150])
    if a.only in (None, "data"):
        print(f"\n-- Data load (generator now={now.isoformat()}): upload JSONL to /Volumes/{c}/{SEED_DIR}/ then INSERT OVERWRITE")
        for t, r in rows.items():
            print(f"   {c}.{t}: {len(r)} rows")
    if not a.apply:
        print("\nDry run only. Re-run with --apply after approval.")
        return 0

    from databricks import sql as dbsql
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(profile=a.profile)
    conn = dbsql.connect(server_hostname=w.config.host.replace("https://", ""),
                         http_path=f"/sql/1.0/warehouses/{a.warehouse}",
                         credentials_provider=lambda: w.config.authenticate)
    cur = conn.cursor()

    if a.only in (None, "ddl"):
        print("\n== DDL")
        for s in plan_ddl:
            try:
                cur.execute(s)
                if s.upper().startswith("SELECT"):  # the DQ check block in notebook 30
                    for r in cur.fetchall():
                        print(f"   DQ {r[0]}: {r[1]}")
                else:
                    print("   ok  " + " ".join(s.split())[:110])
            except Exception as e:
                msg = str(e).splitlines()[0][:240]
                print(f"   FAIL {' '.join(s.split())[:80]} -> {msg}")
                if s.upper().startswith("CREATE CATALOG"):
                    print("\nCREATE CATALOG was denied. Re-run with --catalog workspace (Free Edition fallback).")
                    return 1
                if "PERMISSION" in msg.upper() or "DENIED" in msg.upper():
                    return 1

    if a.only in (None, "data"):
        print("\n== Data")
        for t, r in rows.items():
            path = f"/Volumes/{c}/{SEED_DIR}/{t.replace('.', '__')}.jsonl"
            buf = io.BytesIO("\n".join(json.dumps(x, default=str) for x in r).encode())
            w.files.upload(path, buf, overwrite=True)
            cur.execute(f"DESCRIBE TABLE {c}.{t}")
            cols = [(row[0], row[1]) for row in cur.fetchall() if row[0] and not row[0].startswith("#")]
            select = ", ".join(f"CAST(`{n}` AS {ty}) AS `{n}`" for n, ty in cols)
            cur.execute(f"INSERT OVERWRITE {c}.{t} SELECT {select} FROM read_files('{path}', format => 'json')")
            cur.execute(f"SELECT COUNT(*) FROM {c}.{t}")
            print(f"   {c}.{t}: {cur.fetchone()[0]} rows (expected {len(r)})")

    print("\n== Story check")
    for name, q in STORY_CHECKS.items():
        cur.execute(q.format(c=c))
        print(f"   {name}: {cur.fetchone()[0]}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
