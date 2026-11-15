"""Read-only SQL warehouse + AI Functions check (no tables created).

  python scripts/sql_ai_check.py --profile fixit --warehouse <id> --chat <endpoint>
"""
from __future__ import annotations

import argparse
import secrets
import sys
import time

REFUSED = {"sleepsafe"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse", required=True)
    ap.add_argument("--chat", required=True)
    a = ap.parse_args()
    if a.profile in REFUSED:
        return 2
    from databricks import sql as dbsql
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(profile=a.profile)
    t0 = time.time()
    conn = dbsql.connect(server_hostname=w.config.host.replace("https://", ""),
                         http_path=f"/sql/1.0/warehouses/{a.warehouse}",
                         credentials_provider=lambda: w.config.authenticate)
    print(f"connected in {time.time() - t0:.1f}s (includes warehouse start)")
    checks = {
        "identity + named param": ("SELECT current_user() AS u, current_catalog() AS c, :p AS echo", {"p": "ok"}),
        "timestamp param binding": ("SELECT CAST(:ts AS TIMESTAMP) AS t, typeof(:ts2) AS ty",
                                    {"ts": "2026-11-19T17:00:00", "ts2": __import__("datetime").datetime(2026, 11, 19, 17)}),
        "can create catalog? (privilege check only)": ("SHOW GRANTS ON METASTORE", {}),
        "ai_query": (f"SELECT ai_query('{a.chat}', :q) AS r", {"q": f"Reply with exactly: {secrets.token_hex(3)}"}),
        "ai_classify": ("SELECT ai_classify('There are mouse droppings under my kitchen sink', "
                        "ARRAY('PESTS','HEAT','PLUMBING','ELECTRICAL')) AS r", {}),
        "ai_extract": ("SELECT ai_extract('The landlord said they would fix the heat by Thursday', ARRAY('repair','date')) AS r", {}),
        "ai_parse_document exists": ("DESCRIBE FUNCTION ai_parse_document", {}),
        "samples readable": ("SELECT COUNT(*) FROM samples.nyctaxi.trips", {}),
    }
    with conn.cursor() as cur:
        for name, (q, p) in checks.items():
            t0 = time.time()
            try:
                cur.execute(q, p)
                rows = cur.fetchmany(3)
                print(f"PASS {name} ({time.time() - t0:.1f}s): {[tuple(r) for r in rows]}"[:300])
            except Exception as e:
                print(f"FAIL {name}: {type(e).__name__}: {str(e).splitlines()[0][:220]}")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
