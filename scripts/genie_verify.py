"""Check that every saved Genie answer (demo/cached_outputs/genie) matches a fresh run of its own SQL. Read-only.

  python scripts/genie_verify.py            (uses profile `fixit` and warehouse 6361516ab33ba2d2)

Run after every Databricks reset. Genie's SQL may use calendar days/years (DATEDIFF, YEAR(CURRENT_DATE)), which can
shift slightly when the data is regenerated at a different time of day; re-capture with genie.warm() if one drifts.
"""
import glob, json, sys, os
sys.path.insert(0, os.getcwd())
from scripts.code_parse import conn
if os.environ.get("PROFILE", "fixit") == "sleepsafe": sys.exit("refused profile")
_, cn = conn(os.environ.get("PROFILE", "fixit"), os.environ.get("WAREHOUSE", "6361516ab33ba2d2")); cur = cn.cursor()
ok = 0
files = sorted(glob.glob("demo/cached_outputs/genie/*.json"))
for f in files:
    c = json.load(open(f, encoding="utf-8"))
    cur.execute(c["sql"])
    cols = [d[0] for d in cur.description]
    rows = [dict(zip(cols, [None if v is None else str(v) for v in r])) for r in cur.fetchall()][:25]
    saved = [{k: (None if v is None else str(v)) for k, v in r.items()} for r in c["rows"]]
    def num(x):
        try: return round(float(x), 6)
        except (TypeError, ValueError): return x
    same = [{k: num(v) for k, v in r.items()} for r in rows] == [{k: num(v) for k, v in r.items()} for r in saved]
    ok += same
    print(("MATCH   " if same else "MISMATCH"), c["question"], "| first row:", saved[:1])
print(f"{ok}/{len(files)} saved Genie answers match a fresh run of their SQL on current data")
sys.exit(0 if ok == len(files) else 1)
