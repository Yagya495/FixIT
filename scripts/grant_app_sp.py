"""Grant the FixIt App's service principal the minimum Unity Catalog privileges it needs (and show them).

  python scripts/grant_app_sp.py --profile fixit --warehouse <id> --sp <service_principal_client_id> [--apply]

What the app touches (and nothing else):
  silver.* + gold.*  : SELECT + MODIFY (cases, calls, deadlines, complaints, evidence rows; gold.reports, gold.violations)
  ref.*              : SELECT (taxonomy)
  raw.evidence volume: READ + WRITE (hash-named evidence files)
No ALL PRIVILEGES, no CREATE, no MANAGE, no other volumes, no other catalogs.
"""
from __future__ import annotations

import argparse
import re
import sys


def grants(c: str, sp: str) -> list[str]:
    p = f"`{sp}`"
    return [
        f"GRANT USE CATALOG ON CATALOG {c} TO {p}",
        f"GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA {c}.silver TO {p}",
        f"GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA {c}.gold TO {p}",
        f"GRANT USE SCHEMA, SELECT ON SCHEMA {c}.ref TO {p}",
        f"GRANT USE SCHEMA ON SCHEMA {c}.raw TO {p}",
        f"GRANT READ VOLUME, WRITE VOLUME ON VOLUME {c}.raw.evidence TO {p}",
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse", required=True)
    ap.add_argument("--sp", required=True, help="service_principal_client_id from `databricks apps get`")
    ap.add_argument("--catalog", default="fixit")
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.profile == "sleepsafe" or not re.fullmatch(r"[0-9a-f-]{36}", a.sp):
        print("refused (profile or SP id format)")
        return 2
    stmts = grants(a.catalog, a.sp)
    for s in stmts:
        print(("APPLY " if a.apply else "PLAN  ") + s)
    if not a.apply:
        return 0
    from databricks import sql as dbsql
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(profile=a.profile)
    conn = dbsql.connect(server_hostname=w.config.host.replace("https://", ""), http_path=f"/sql/1.0/warehouses/{a.warehouse}",
                         credentials_provider=lambda: w.config.authenticate)
    cur = conn.cursor()
    for s in stmts:
        cur.execute(s)
    print("\nEffective grants for the SP:")
    for obj, kind in [(a.catalog, "CATALOG"), (f"{a.catalog}.silver", "SCHEMA"), (f"{a.catalog}.gold", "SCHEMA"),
                      (f"{a.catalog}.ref", "SCHEMA"), (f"{a.catalog}.raw", "SCHEMA"), (f"{a.catalog}.raw.evidence", "VOLUME")]:
        cur.execute(f"SHOW GRANTS `{a.sp}` ON {kind} {obj}")
        print(f"  {kind} {obj}: {sorted({r[1] for r in cur.fetchall()})}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
