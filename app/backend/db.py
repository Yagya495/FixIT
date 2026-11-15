"""Data access for both backends.

- local:      SQLite at data/fixit.db. Table `silver.scans` is stored as `silver__scans`.
- databricks: SQL warehouse via databricks-sql-connector; `silver.scans` -> `fixit.silver.scans`.

All SQL uses `:named` params and table names wrapped as {silver.scans}, which `q()` resolves.
"""
from __future__ import annotations

import json
import re
import sqlite3
import threading
import time
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from . import config

_TABLE_RE = re.compile(r"\{([a-z]+)\.([a-z_]+)\}")
_local = threading.local()


def t(name: str) -> str:
    schema, table = name.split(".")
    if config.DATA_BACKEND == "databricks":
        return f"{config.CATALOG}.{schema}.{table}"
    return f"{schema}__{table}"


def _resolve(sql: str) -> str:
    return _TABLE_RE.sub(lambda m: t(f"{m.group(1)}.{m.group(2)}"), sql)


# ---------------------------------------------------------------- connections
def _sqlite() -> sqlite3.Connection:
    conn = getattr(_local, "sqlite", None)
    if conn is None:
        config.DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(config.SQLITE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        _local.sqlite = conn
    return conn


def _databricks():
    conn = getattr(_local, "dbx", None)
    if conn is None:
        from databricks import sql as dbsql  # type: ignore

        from . import llm

        host = llm._host().replace("https://", "")  # env host, or the CLI profile's host
        kwargs: dict[str, Any] = {
            "server_hostname": host,
            "http_path": f"/sql/1.0/warehouses/{config.DATABRICKS_WAREHOUSE_ID}",
        }
        if config.DATABRICKS_TOKEN:
            kwargs["access_token"] = config.DATABRICKS_TOKEN
        else:  # Databricks Apps / CLI profile: use SDK unified auth
            from databricks.sdk.core import Config

            cfg = Config()
            kwargs["credentials_provider"] = lambda: cfg.authenticate
        conn = dbsql.connect(**kwargs)
        _local.dbx = conn
    return conn


@contextmanager
def _cursor():
    if config.DATA_BACKEND == "databricks":
        cur = _databricks().cursor()
        try:
            yield cur
        finally:
            cur.close()
    else:
        conn = _sqlite()
        cur = conn.cursor()
        try:
            yield cur
            conn.commit()
        finally:
            cur.close()


# ---------------------------------------------------------------- query API
def q(sql: str, params: dict | None = None) -> list[dict]:
    with _cursor() as cur:
        cur.execute(_resolve(sql), _bind(params))
        if cur.description is None:
            return []
        cols = [d[0] for d in cur.description]
        return [{c: _norm(v) for c, v in zip(cols, row)} for row in cur.fetchall()]


def _norm(v: Any) -> Any:
    """Delta returns datetime/Decimal objects; SQLite returns str/float. App code expects the latter."""
    if isinstance(v, datetime):
        return v.replace(tzinfo=None).isoformat(timespec="seconds")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return v


def q1(sql: str, params: dict | None = None) -> dict | None:
    rows = q(sql, params)
    return rows[0] if rows else None


_ISO_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?([+-]\d{2}:\d{2}|Z)?$")


def _bind(params: dict | None) -> dict:
    """On Databricks, bind ISO timestamp strings as datetimes so Delta TIMESTAMP columns get a TIMESTAMP, not a
    STRING (avoids relying on implicit string→timestamp store assignment). SQLite keeps the strings as-is."""
    params = params or {}
    if config.DATA_BACKEND != "databricks":
        return params
    return {k: (datetime.fromisoformat(v.replace("Z", "+00:00")) if isinstance(v, str) and _ISO_TS.match(v) else v)
            for k, v in params.items()}


def execute(sql: str, params: dict | None = None) -> None:
    # Delta uses optimistic concurrency: two requests updating the same row can conflict. Our UPDATE/DELETEs are
    # idempotent, so retry those briefly instead of surfacing a 500 on stage.
    retryable = config.DATA_BACKEND == "databricks" and sql.lstrip().upper().startswith(("UPDATE", "DELETE"))
    for attempt in range(4 if retryable else 1):
        try:
            with _cursor() as cur:
                cur.execute(_resolve(sql), _bind(params))
            return
        except Exception as e:
            if not retryable or "CONCURRENT" not in str(e).upper() or attempt == 3:
                raise
            time.sleep(0.3 * (attempt + 1))


def insert(table: str, row: dict) -> None:
    row = {k: (json.dumps(v) if isinstance(v, (list, dict)) else v) for k, v in row.items()}
    cols = ", ".join(row)
    vals = ", ".join(f":{k}" for k in row)
    execute(f"INSERT INTO {{{table}}} ({cols}) VALUES ({vals})", row)


def insert_many(table: str, rows: Iterable[dict], chunk: int = 500) -> None:
    rows = list(rows)
    if not rows:
        return
    cols = list(rows[0])
    norm = [[json.dumps(r[c]) if isinstance(r[c], (list, dict)) else r[c] for c in cols] for r in rows]
    if config.DATA_BACKEND == "databricks":
        # Multi-row VALUES with positional literals is slow but fine for demo-sized writes.
        for i in range(0, len(norm), chunk):
            part = norm[i : i + chunk]
            params, ph = {}, []
            for j, r in enumerate(part):
                names = []
                for c, v in zip(cols, r):
                    key = f"{c}_{j}"
                    params[key] = v
                    names.append(f":{key}")
                ph.append("(" + ", ".join(names) + ")")
            execute(f"INSERT INTO {{{table}}} ({', '.join(cols)}) VALUES {', '.join(ph)}", params)
    else:
        conn = _sqlite()
        conn.executemany(
            f"INSERT INTO {t(table)} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})", norm
        )
        conn.commit()


def jl(value: Any) -> Any:
    """Decode a JSON-encoded array/object column."""
    if isinstance(value, str) and value[:1] in "[{":
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    return value


# ---------------------------------------------------------------- local schema
LOCAL_DDL = {
    "ref.violation_types": "type_id TEXT PRIMARY KEY, name TEXT, category TEXT, visual_cues TEXT, default_severity TEXT, code_sections TEXT, plain_explanation TEXT, remedy_request TEXT",
    "silver.code_sections": "section_id TEXT PRIMARY KEY, title TEXT, text TEXT, source_doc TEXT, page INTEGER, url TEXT, verified INTEGER",
    "gold.owners": "owner_id TEXT PRIMARY KEY, name TEXT, management_company TEXT, is_synthetic INTEGER",
    "gold.properties": "property_id TEXT PRIMARY KEY, address_norm TEXT, lat REAL, lon REAL, neighborhood TEXT, units INTEGER, year_built INTEGER, owner_id TEXT, is_synthetic INTEGER",
    "gold.reports": "report_id TEXT PRIMARY KEY, property_id TEXT, unit_hash TEXT, violation_category TEXT, violation_type TEXT, severity TEXT, reported_at TEXT, fixed_at TEXT, status TEXT, source TEXT",
    "gold.landlord_scores": "owner_id TEXT PRIMARY KEY, buildings INTEGER, units INTEGER, open_issues INTEGER, issues_last_12mo INTEGER, issues_per_unit REAL, median_days_to_fix REAL, pct_fixed_within_30d REAL, repeat_buildings INTEGER, emergency_issues INTEGER, score REAL, grade TEXT",
    "gold.violations": "violation_id TEXT PRIMARY KEY, scan_id TEXT, property_id TEXT, violation_type TEXT, severity TEXT, confidence REAL, code_section_ids TEXT, explanation TEXT, evidence_ids TEXT, status TEXT",
    "silver.scans": "scan_id TEXT PRIMARY KEY, user_id TEXT, property_id TEXT, unit TEXT, mode TEXT, address TEXT, created_at TEXT",
    "silver.evidence": "evidence_id TEXT PRIMARY KEY, scan_id TEXT, volume_path TEXT, sha256 TEXT, captured_at TEXT, uploaded_at TEXT, media_type TEXT",
    "silver.detections": "detection_id TEXT PRIMARY KEY, scan_id TEXT, evidence_id TEXT, violation_type TEXT, confidence REAL, bbox TEXT, note TEXT, model_endpoint TEXT, created_at TEXT",
    "silver.repair_requests": "request_id TEXT PRIMARY KEY, user_id TEXT, scan_id TEXT, property_id TEXT, unit TEXT, violation_ids TEXT, tone TEXT, letter_text TEXT, sent_at TEXT, created_at TEXT",
    "silver.calls": "call_id TEXT PRIMARY KEY, request_id TEXT, mode TEXT, transcript TEXT, commitment_date TEXT, commitment_text TEXT, landlord_tone TEXT, created_at TEXT",
    "silver.deadlines": "request_id TEXT PRIMARY KEY, due_date TEXT, status TEXT, created_at TEXT, updated_at TEXT, sim_offset_days INTEGER",
    "silver.complaints": "complaint_id TEXT PRIMARY KEY, request_id TEXT, payload_json TEXT, generated_at TEXT, joint INTEGER, units TEXT",
}


def init_local_schema(drop: bool = False) -> None:
    conn = _sqlite()
    for name, cols in LOCAL_DDL.items():
        if drop:
            conn.execute(f"DROP TABLE IF EXISTS {t(name)}")
        conn.execute(f"CREATE TABLE IF NOT EXISTS {t(name)} ({cols})")
    conn.execute(f"CREATE INDEX IF NOT EXISTS ix_reports_prop ON {t('gold.reports')}(property_id)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS ix_props_owner ON {t('gold.properties')}(owner_id)")
    conn.commit()


def table_count(name: str) -> int:
    try:
        row = q1(f"SELECT COUNT(*) AS n FROM {{{name}}}")
        return int(row["n"]) if row else 0
    except Exception:
        return 0
