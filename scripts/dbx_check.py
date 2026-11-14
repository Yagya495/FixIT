"""Probe a Databricks workspace for FixIt Milestone 1 — from your laptop, via a CLI profile.

Read-only unless you pass a --test-* / --write-test flag. Never prints tokens.

  python scripts/dbx_check.py --profile fixit                       # discover: user, endpoints, warehouses, catalogs, ...
  python scripts/dbx_check.py --profile fixit --test-models         # real chat / vision / embedding calls (tiny token cost)
  python scripts/dbx_check.py --profile fixit --test-sql <WH_ID>    # SELECT-only checks on the warehouse
  python scripts/dbx_check.py --profile fixit --test-sql <WH_ID> --write-test   # write+read+delete one row in fixit.silver

Model checks are designed so a name alone can't pass:
  - chat must echo a random nonce,
  - vision must name the color of a randomly colored image (a text-only model can only guess),
  - embeddings must return a numeric vector.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import random
import secrets
import struct
import sys
import time
import zlib

REFUSED_PROFILES = {"sleepsafe"}  # another project's workspace: never touch it from here
COLORS = {"red": (220, 30, 30), "green": (30, 170, 60), "blue": (30, 60, 220), "yellow": (240, 220, 30)}


def png(rgb, w=96, h=64) -> bytes:
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    c = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)  # noqa: E731
    return b"\x89PNG\r\n\x1a\n" + c(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + \
        c(b"IDAT", zlib.compress(raw)) + c(b"IEND", b"")


def section(t: str) -> None:
    print(f"\n== {t} " + "=" * max(0, 60 - len(t)))


def try_(label, fn):
    try:
        return fn()
    except Exception as e:  # report and keep going: discovery should list everything it can
        print(f"  {label}: FAILED -> {type(e).__name__}: {str(e)[:300]}")
        return None


def invoke(w, endpoint: str, body: dict) -> dict:
    return w.api_client.do("POST", f"/serving-endpoints/{endpoint}/invocations", body=body)


def text_of(resp: dict) -> str:
    c = resp["choices"][0]["message"]["content"]
    if isinstance(c, list):
        c = "".join(p.get("text", "") for p in c if isinstance(p, dict))
    return c or ""


def discover(w) -> dict:
    out: dict = {}
    section("Identity")
    me = try_("current user", lambda: w.current_user.me())
    print(f"  host: {w.config.host}")
    if me:
        print(f"  user: {me.user_name}")

    section("Serving endpoints (state / task)")
    eps = try_("list endpoints", lambda: list(w.serving_endpoints.list())) or []
    out["endpoints"] = []
    for e in sorted(eps, key=lambda e: e.name):
        state = getattr(getattr(e, "state", None), "ready", None)
        task = getattr(e, "task", None)
        out["endpoints"].append({"name": e.name, "ready": str(state), "task": task})
        print(f"  {e.name:55s} ready={state} task={task}")

    section("SQL warehouses")
    whs = try_("list warehouses", lambda: list(w.warehouses.list())) or []
    out["warehouses"] = []
    for wh in whs:
        row = {"id": wh.id, "name": wh.name, "state": str(wh.state), "size": wh.cluster_size,
               "serverless": wh.enable_serverless_compute, "type": str(wh.warehouse_type)}
        out["warehouses"].append(row)
        print(f"  {wh.id}  {wh.name!r} state={wh.state} size={wh.cluster_size} serverless={wh.enable_serverless_compute}")

    section("Unity Catalog")
    cats = try_("list catalogs", lambda: [c.name for c in w.catalogs.list()]) or []
    out["catalogs"] = cats
    print(f"  catalogs: {cats}")
    print(f"  'fixit' catalog exists: {'fixit' in cats}")
    if "fixit" in cats:
        print(f"  fixit schemas: {try_('list schemas', lambda: [s.name for s in w.schemas.list('fixit')])}")

    section("Other features")
    vs = try_("vector search endpoints", lambda: [e.name for e in w.vector_search_endpoints.list_endpoints()])
    if vs is not None:
        print(f"  vector search endpoints: {vs}")
    g = try_("genie spaces", lambda: w.api_client.do("GET", "/api/2.0/genie/spaces"))
    if g is not None:
        print(f"  genie spaces visible: {len(g.get('spaces', []))}")
    apps = try_("apps", lambda: [a.name for a in w.apps.list()])
    if apps is not None:
        print(f"  apps: {apps}")
        out["apps"] = apps

    section("Edition signals (cannot be confirmed from the API alone)")
    print("  Free Edition typically: serverless-only warehouses, a 'workspace' default catalog, <=3 apps,")
    print("  one vector search endpoint. Confirm in the workspace UI (account menu shows 'Free Edition').")
    return out


def test_models(w, chat: str, vision: str, embed: str) -> dict:
    res = {}
    section(f"Chat: {chat}")
    nonce = secrets.token_hex(3)
    r = try_("chat", lambda: invoke(w, chat, {"messages": [{"role": "user", "content": f"Reply with exactly this code and nothing else: {nonce}"}],
                                              "max_tokens": 20, "temperature": 0}))
    if r:
        t = text_of(r)
        res["chat"] = nonce in t
        print(f"  reply={t.strip()[:80]!r} -> {'PASS' if res['chat'] else 'FAIL (did not echo nonce)'}")

    section(f"Vision: {vision}")
    color = random.choice(list(COLORS))
    b64 = base64.b64encode(png(COLORS[color])).decode()
    t0 = time.time()
    r = try_("vision", lambda: invoke(w, vision, {"messages": [{"role": "user", "content": [
        {"type": "text", "text": "What single color fills this image? Answer with one word from: red, green, blue, yellow."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}], "max_tokens": 10, "temperature": 0}))
    if r:
        t = text_of(r).strip().lower()
        res["vision"] = color in t
        print(f"  expected={color} reply={t[:40]!r} ({time.time() - t0:.1f}s) -> "
              f"{'PASS' if res['vision'] else 'FAIL (wrong color: endpoint may not read images)'}")

    section(f"Embeddings: {embed}")
    r = try_("embed", lambda: invoke(w, embed, {"input": ["smoke detector missing in bedroom"]}))
    if r:
        vec = r.get("data", [{}])[0].get("embedding", [])
        res["embed"] = bool(vec) and all(isinstance(x, (int, float)) for x in vec[:5])
        print(f"  dims={len(vec)} -> {'PASS' if res['embed'] else 'FAIL'}")
    return res


def test_sql(w, warehouse_id: str, catalog: str, write: bool) -> dict:
    from databricks import sql as dbsql

    res = {}
    section(f"SQL warehouse {warehouse_id}")
    conn = try_("connect", lambda: dbsql.connect(server_hostname=w.config.host.replace("https://", ""),
                                                 http_path=f"/sql/1.0/warehouses/{warehouse_id}",
                                                 credentials_provider=lambda: w.config.authenticate))
    if not conn:
        return res
    with conn.cursor() as cur:
        cur.execute("SELECT current_user() AS u, current_catalog() AS c, :p AS echo", {"p": "ok"})
        print(f"  {cur.fetchall()}")
        res["read"] = True
        for tbl in ("gold.properties", "gold.reports", "gold.landlord_scores"):
            ok = try_(tbl, lambda: (cur.execute(f"SELECT COUNT(*) FROM {catalog}.{tbl}"), cur.fetchone()[0])[1])
            if ok is not None:
                print(f"  {catalog}.{tbl}: {ok} rows")
        demo = try_("demo story", lambda: (cur.execute(
            f"SELECT COUNT(*) FROM {catalog}.gold.reports WHERE property_id='P-DEMO-1234' AND violation_category='HEAT' "
            f"AND status IN ('open','escalated') AND reported_at >= current_timestamp() - INTERVAL 30 DAYS"), cur.fetchone()[0])[1])
        if demo is not None:
            print(f"  open HEAT reports at 1234 Demo St (30d): {demo}  (expected 6)")
        if write:
            rid = f"SMOKE-{secrets.token_hex(4)}"
            ok = try_("write/read/delete", lambda: (
                cur.execute(f"INSERT INTO {catalog}.silver.deadlines (request_id, due_date, status, created_at, updated_at, sim_offset_days) "
                            "VALUES (:r, :d, 'open', :d, :d, 0)", {"r": rid, "d": __import__("datetime").datetime.now()}),
                cur.execute(f"SELECT COUNT(*) FROM {catalog}.silver.deadlines WHERE request_id = :r", {"r": rid}),
                cur.fetchone()[0],
                cur.execute(f"DELETE FROM {catalog}.silver.deadlines WHERE request_id = :r", {"r": rid}))[2])
            res["write"] = ok == 1
            print(f"  write test row {rid}: {'PASS (inserted, read back, deleted)' if res['write'] else 'FAIL'}")
    conn.close()
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True, help="Databricks CLI profile (e.g. fixit)")
    ap.add_argument("--allow-profile", action="store_true", help="override the refused-profile guard")
    ap.add_argument("--test-models", action="store_true")
    ap.add_argument("--chat", default=os.getenv("CHAT_ENDPOINT", "databricks-claude-sonnet-4-5"))
    ap.add_argument("--vision", default=os.getenv("VISION_ENDPOINT", "databricks-claude-sonnet-4-5"))
    ap.add_argument("--embed", default=os.getenv("EMBEDDING_ENDPOINT", "databricks-gte-large-en"))
    ap.add_argument("--test-sql", metavar="WAREHOUSE_ID")
    ap.add_argument("--catalog", default=os.getenv("FIXIT_CATALOG", "fixit"))
    ap.add_argument("--write-test", action="store_true", help="insert+delete one row in <catalog>.silver.deadlines")
    ap.add_argument("--json", metavar="PATH", help="also save results as JSON (no secrets)")
    a = ap.parse_args()

    if a.profile in REFUSED_PROFILES and not a.allow_profile:
        print(f"Refusing profile {a.profile!r}: it belongs to another project. Create a separate 'fixit' profile.")
        return 2
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(profile=a.profile)
    results = {"profile": a.profile, "host": w.config.host, "discovery": discover(w)}
    if a.test_models:
        results["models"] = test_models(w, a.chat, a.vision, a.embed)
    if a.test_sql:
        results["sql"] = test_sql(w, a.test_sql, a.catalog, a.write_test)
    if a.json:
        with open(a.json, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nSaved {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
