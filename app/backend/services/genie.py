"""'Ask the data' (P0-11): Genie Conversation API, with local SQL answers for the sample questions."""
from __future__ import annotations

import time
from datetime import datetime, timedelta

import httpx

from .. import config, db, llm
from . import demo_cache

SAMPLE_QUESTIONS = [
    "Which owners have the most open heat issues this month?",
    "What is the median days-to-fix by neighborhood?",
    "Which buildings have 3+ mold reports in the last year?",
    "How many emergency issues are open right now?",
    "Show violation counts by type for the last 6 months.",
    "Which management companies improved their fix times the most?",
    "Which buildings near campus have the most open issues?",
    "What percent of issues are fixed within 30 days, by owner grade?",
]


def _local_sql(i: int, now: datetime) -> tuple[str, dict, str]:
    month = (now - timedelta(days=30)).isoformat()
    year = (now - timedelta(days=365)).isoformat()
    six = (now - timedelta(days=182)).isoformat()
    if i == 0:
        return ("""SELECT o.name AS owner, COUNT(*) AS open_heat_issues FROM {gold.reports} r
                   JOIN {gold.properties} p ON p.property_id = r.property_id JOIN {gold.owners} o ON o.owner_id = p.owner_id
                   WHERE r.violation_category = 'HEAT' AND r.status IN ('open','escalated') AND r.reported_at >= :m
                   GROUP BY o.name ORDER BY open_heat_issues DESC LIMIT 10""", {"m": month},
                "Owners ranked by open HEAT reports filed in the last 30 days.")
    if i == 1:
        # Median isn't portable to SQLite; compute in Python below.
        return ("""SELECT p.neighborhood, r.reported_at, r.fixed_at FROM {gold.reports} r
                   JOIN {gold.properties} p ON p.property_id = r.property_id WHERE r.fixed_at IS NOT NULL""", {},
                "Median days from report to fix, by neighborhood (fixed issues only).")
    if i == 2:
        return ("""SELECT p.address_norm AS building, p.neighborhood, COUNT(*) AS mold_reports FROM {gold.reports} r
                   JOIN {gold.properties} p ON p.property_id = r.property_id
                   WHERE r.violation_category = 'MOLD_MOISTURE' AND r.reported_at >= :y
                   GROUP BY p.address_norm, p.neighborhood HAVING COUNT(*) >= 3 ORDER BY mold_reports DESC LIMIT 25""",
                {"y": year}, "Buildings with 3 or more mold/moisture reports in the last 12 months.")
    if i == 3:
        return ("""SELECT COUNT(*) AS open_emergency_issues FROM {gold.reports}
                   WHERE severity = 'emergency' AND status IN ('open','escalated')""", {},
                "Emergency-severity issues currently open or escalated.")
    if i == 4:
        return ("""SELECT violation_type, COUNT(*) AS reports FROM {gold.reports} WHERE reported_at >= :s
                   GROUP BY violation_type ORDER BY reports DESC""", {"s": six},
                "Report counts by violation type, last 6 months.")
    if i == 5:
        return ("""SELECT o.management_company, r.reported_at, r.fixed_at FROM {gold.reports} r
                   JOIN {gold.properties} p ON p.property_id = r.property_id JOIN {gold.owners} o ON o.owner_id = p.owner_id
                   WHERE r.fixed_at IS NOT NULL""", {},
                "Change in median days-to-fix: last 12 months vs. the 12 months before (negative = faster).")
    if i == 6:
        return ("""SELECT p.address_norm AS building, p.neighborhood,
                          SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_issues
                   FROM {gold.properties} p JOIN {gold.reports} r ON r.property_id = p.property_id
                   WHERE p.neighborhood IN ('Langdon','Mifflin','Regent','Greenbush')
                   GROUP BY p.address_norm, p.neighborhood ORDER BY open_issues DESC LIMIT 15""", {},
                "Near-campus buildings (Langdon, Mifflin, Regent, Greenbush) by open issues. Predicted risk arrives with the P1 model.")
    return ("""SELECT s.grade, r.reported_at, r.fixed_at FROM {gold.reports} r
               JOIN {gold.properties} p ON p.property_id = r.property_id JOIN {gold.landlord_scores} s ON s.owner_id = p.owner_id""",
            {}, "Share of issues fixed within 30 days of being reported, by owner grade.")


def _days(a: str, b: str) -> float:
    return (datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds() / 86400


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    return None if n == 0 else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


def _post_process(i: int, rows: list[dict], now: datetime) -> list[dict]:
    if i == 1:
        g = {}
        for r in rows:
            g.setdefault(r["neighborhood"], []).append(_days(r["reported_at"], r["fixed_at"]))
        return sorted(({"neighborhood": k, "median_days_to_fix": round(_median(v), 1), "fixed_issues": len(v)}
                       for k, v in g.items()), key=lambda r: -r["median_days_to_fix"])
    if i == 5:
        y1, y2 = (now - timedelta(days=365)).isoformat(), (now - timedelta(days=730)).isoformat()
        g = {}
        for r in rows:
            bucket = "recent" if r["reported_at"] >= y1 else ("prior" if r["reported_at"] >= y2 else None)
            if bucket:
                g.setdefault(r["management_company"], {"recent": [], "prior": []})[bucket].append(_days(r["reported_at"], r["fixed_at"]))
        out = []
        for k, v in g.items():
            if len(v["recent"]) >= 5 and len(v["prior"]) >= 5:
                a, b = _median(v["prior"]), _median(v["recent"])
                out.append({"management_company": k, "prior_median_days": round(a, 1), "recent_median_days": round(b, 1),
                            "change_days": round(b - a, 1)})
        return sorted(out, key=lambda r: r["change_days"])[:10]
    if i == 7:
        g = {}
        for r in rows:
            e = g.setdefault(r["grade"], [0, 0])
            e[1] += 1
            if r["fixed_at"] and _days(r["reported_at"], r["fixed_at"]) <= 30:
                e[0] += 1
        return [{"owner_grade": k, "pct_fixed_within_30d": round(100 * a / b, 1), "issues": b} for k, (a, b) in sorted(g.items())]
    return rows


def local_answer(question: str, now: datetime | None = None) -> dict | None:
    now = now or datetime.now()
    try:
        i = SAMPLE_QUESTIONS.index(question)
    except ValueError:
        ql = question.lower()
        keys = ["heat", "median", "mold", "emergency", "by type", "improved", "campus", "percent"]
        i = next((k for k, w in enumerate(keys) if w in ql), None)
        if i is None:
            return None
    sql, params, desc = _local_sql(i, now)
    rows = _post_process(i, db.q(sql, params), now)
    return {"question": question, "text": desc, "rows": rows[:25], "columns": list(rows[0].keys()) if rows else [],
            "sql": " ".join(db._resolve(sql).split()), "source": "local"}


# ---------------------------------------------------------------- Genie Conversation API
def _genie(question: str, timeout_s: float = 45) -> dict:
    host = llm._host()  # scheme-normalized; also resolves a CLI profile's host
    headers = llm._auth_headers()
    base = f"{host}/api/2.0/genie/spaces/{config.GENIE_SPACE_ID}"
    r = httpx.post(f"{base}/start-conversation", headers=headers, json={"content": question}, timeout=20)
    r.raise_for_status()
    j = r.json()
    conv, msg = j["conversation_id"], j["message_id"]
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        m = httpx.get(f"{base}/conversations/{conv}/messages/{msg}", headers=headers, timeout=20).json()
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(1.5)
    if m.get("status") != "COMPLETED":
        raise RuntimeError(f"Genie status {m.get('status')}")
    text, sql, rows, cols = "", None, [], []
    texts = [a["text"].get("content", "").strip() for a in m.get("attachments", []) if a.get("text")]
    # Genie may add a follow-up suggestion ("Would you prefer…?") next to the answer: show the answer.
    answers = [t for t in texts if t and not t.endswith("?")]
    text = (answers or texts or [""])[-1].replace("**", "")  # UI renders plain text
    for a in m.get("attachments", []):
        if a.get("query"):
            sql = a["query"].get("query")
            text = text or a["query"].get("description", "")
            res = httpx.get(f"{base}/conversations/{conv}/messages/{msg}/attachments/{a['attachment_id']}/query-result",
                            headers=headers, timeout=20).json()
            sr = res.get("statement_response", {})
            cols = [c["name"] for c in sr.get("manifest", {}).get("schema", {}).get("columns", [])]
            rows = [dict(zip(cols, r)) for r in sr.get("result", {}).get("data_array", [])]
    return {"question": question, "text": text, "sql": sql, "rows": rows[:25], "columns": cols, "source": "genie"}


def warm() -> list[dict]:
    """Ask Genie every sample question live and save the answers (run before going on stage)."""
    out = []
    for q in SAMPLE_QUESTIONS:
        try:
            demo_cache.put("genie", q, _genie(q))
            out.append({"question": q, "ok": True})
        except Exception as e:
            out.append({"question": q, "ok": False, "error": str(e)[:200]})
    return out


def ask(question: str) -> dict:
    if config.GENIE_SPACE_ID and llm.available():
        cached = demo_cache.get("genie", question) if config.DEMO_MODE else None
        if cached:
            # Live Genie takes ~20 s; on stage serve the saved Genie answer instantly (labeled "cache" in the UI).
            return cached | {"source": "cache"}
        try:
            ans = _genie(question)
            if config.DEMO_MODE:
                demo_cache.put("genie", question, ans)
            return ans
        except Exception:
            if cached:
                return cached | {"source": "cache"}
    ans = local_answer(question)
    if ans:
        return ans
    return {"question": question, "text": "In offline mode I can answer the sample questions. Connect a Genie space for free-form questions.",
            "rows": [], "columns": [], "sql": None, "source": "none"}
