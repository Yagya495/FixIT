"""MGO Chapter 27: upload → parse (ai_parse_document) → propose matches → HUMAN review → approve. Dry run by default.

Nothing here invents section numbers: ids come from headings in the official PDF text, and a section only becomes
`verified=1` (shown as "MGO § …" in the app) when a person approves it in the review CSV.

  # 1. Upload the PDF you exported from Municode (official MGO Ch. 27):
  python scripts/code_parse.py upload  --profile fixit --pdf "C:\\path\\MGO_Ch27.pdf" --apply
  # 2. Parse into bronze.code_docs_parsed / code_elements / code_sections_parsed (STAGING, verified=0; the app never reads bronze):
  python scripts/code_parse.py parse   --profile fixit --warehouse <id> --apply
  # 3. Write eval/code_review.csv: for each violation type, top-3 candidate sections + text snippets:
  python scripts/code_parse.py propose --profile fixit --warehouse <id>
  #    -> a human fills `approved_section_ids` (e.g. "27.05(2)") per row, or leaves it blank to keep the placeholder
  # 4. Apply the review (Databricks ref/silver + app/backend/code_sections_verified.json for the local backend):
  python scripts/code_parse.py approve --profile fixit --warehouse <id> --csv eval/code_review.csv --apply
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OFFICIAL_URL = ("https://library.municode.com/wi/madison/codes/code_of_ordinances"
                "?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO")
VERIFIED_JSON = ROOT / "app" / "backend" / "code_sections_verified.json"
REVIEW_MEANING = ("Reviewer approval means the ordinance citation and quoted text were checked against the official "
                  "source. It does not mean the reviewer is a lawyer or a City inspector, or that an AI-detected "
                  "condition is a confirmed legal violation.")
# Public files show this role label; the reviewer's actual name is kept only in the private, git-ignored audit record.
PUBLIC_REVIEWER_LABEL = "Legal Reviewer"
PRIVATE_AUDIT = ROOT / ".private" / "legal_review_audit.json"


def split_reviewers(approved: dict[str, list[str]], rows: list[dict], prev: dict) -> tuple[dict, list[dict], list[str]]:
    """(public reviewers map, private audit entries for new approvals, errors).

    Every approved row needs a reviewer. A NEW approval (type not already in the approvals file) needs the reviewer's
    actual name, never just the public label, so the private audit record always names who approved it. Types already
    approved keep their existing record (the CSV may show the public label for them)."""
    already = set(prev.get("mapping", {}))
    errors, entries = [], []
    for t in approved:
        name = next(r for r in rows if r["type_id"] == t).get("reviewer", "").strip()
        if not name:
            errors.append(f"{t}: every approved row needs a reviewer name")
        elif t not in already and name.lower() == PUBLIC_REVIEWER_LABEL.lower():
            errors.append(f"{t}: a new approval needs the reviewer's actual name (stored privately; shown publicly as "
                          f"'{PUBLIC_REVIEWER_LABEL}')")
        elif t not in already:
            entries.append({"type_id": t, "section_ids": approved[t], "reviewer": name})
    public = {**prev.get("reviewers", {}), **{t: PUBLIC_REVIEWER_LABEL for t in approved}}
    return public, entries, errors


def record_private_approvals(entries: list[dict], when: str) -> None:
    """Append new approvals (with the reviewer's name) to the private audit record. Never committed or bundled."""
    if not entries:
        return
    rec = json.loads(PRIVATE_AUDIT.read_text(encoding="utf-8")) if PRIVATE_AUDIT.exists() else {
        "purpose": "Private audit record of Chapter 27 reviewer identities. Do not commit or bundle this file.",
        "public_display_label": PUBLIC_REVIEWER_LABEL, "approvals": []}
    rec.setdefault("approvals", []).extend({**e, "approved_on": when} for e in entries)
    PRIVATE_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    PRIVATE_AUDIT.write_text(json.dumps(rec, indent=2), encoding="utf-8")


def parse_sql(c: str) -> list[str]:
    """Same logic as notebooks/10_parse_code.sql, with the fixes: verified=0, seeds kept, headers/footers dropped."""
    vol = f"/Volumes/{c}/raw/code_docs/"
    return [
        f"""CREATE OR REPLACE TABLE {c}.bronze.code_docs_parsed AS
            SELECT path, ai_parse_document(content) AS parsed
            FROM READ_FILES('{vol}', format => 'binaryFile')
            WHERE lower(path) LIKE '%.pdf' AND path NOT LIKE '%/_parser_test/%'""",
        f"""CREATE OR REPLACE TABLE {c}.bronze.code_elements AS
            SELECT path AS source_doc, e.pos AS element_idx, CAST(e.value:type AS STRING) AS element_type,
                   CAST(e.value:content AS STRING) AS content,
                   CAST(e.value:bbox[0]:page_id AS INT) + 1 AS page
            FROM {c}.bronze.code_docs_parsed, LATERAL variant_explode(parsed:document:elements) AS e
            WHERE CAST(e.value:content AS STRING) IS NOT NULL
              AND coalesce(CAST(e.value:type AS STRING), '') NOT IN ('page_header', 'page_footer', 'page_number')""",
        # Staging only: the app reads silver/ref, never bronze, so parsing changes nothing the app shows.
        # Ids come only from explicit headings ("27.051 - ENERGY CODE ..."). Subsection markers ("(2)(h)") are
        # detached list numbering in the Municode export, so they are NOT derived from element order.
        f"""CREATE OR REPLACE TABLE {c}.bronze.code_sections_parsed AS
            WITH tagged AS (
              SELECT *, regexp_extract(content, '^\\\\s*(27\\\\.[0-9]{{2,3}})\\\\s*-\\\\s', 1) AS sec_start
              FROM {c}.bronze.code_elements),
            grouped AS (
              SELECT *, last_value(NULLIF(sec_start, ''), true) OVER (PARTITION BY source_doc ORDER BY element_idx
                        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS section_id
              FROM tagged)
            SELECT section_id,
                   trim(regexp_replace(min_by(content, element_idx), '^\\\\s*27\\\\.[0-9]+\\\\s*-\\\\s*', '')) AS title,
                   array_join(transform(array_sort(collect_list(struct(element_idx, content))), x -> x.content), '\\n') AS text,
                   min_by(source_doc, element_idx) AS source_doc, min(page) AS page,
                   '{OFFICIAL_URL}' AS url,
                   0 AS verified
            FROM grouped WHERE section_id IS NOT NULL GROUP BY section_id""",
    ]


def approved_rows(ids: list[str], types: set[str] | None = None) -> list[dict]:
    """Rows for approved ids, built only from the parsed official text and the excerpt-checked proposals.

    Each id uses only the excerpts the review sheet proposed for it *in the approved categories* (`types`), each of
    which scripts/ch27_review_sheet.py checked word for word against the parse and the PDF text layer.
    Whole parsed sections are never stored: ai_parse_document drops words at some page breaks (seen in 27.05(2)(h)7.
    and 27.05(2)(x)), so only excerpts are trusted. Raises KeyError for an id with no proposed excerpt (no guessing).
    """
    legal = ROOT / "docs" / "legal"
    parsed = {s["section_id"]: s for s in json.loads((legal / "ch27_parsed_sections.json").read_text(encoding="utf-8"))}
    items = [i for p in json.loads((legal / "ch27_proposed_mappings.json").read_text(encoding="utf-8"))["proposals"]
             if types is None or p["type_id"] in types for i in p["items"]]
    out = []
    for sid in ids:
        mine = [i for i in items if i["section_id"] == sid]
        if not mine:
            raise KeyError(sid)
        base = parsed[mine[0]["section"]]
        for i in mine:
            if " ".join(i["excerpt"].split()) not in " ".join(base["text"].split()):
                raise KeyError(f"{sid}: excerpt no longer matches the parse")
        caption = next((i["caption"] for i in mine if i["caption"]), "")
        out.append({"section_id": sid, "title": " ".join(f"{base['title']} {caption}".split()),
                    "text": "\n".join(dict.fromkeys(i["excerpt"] for i in mine)), "source_doc": base["source_doc"],
                    "page": min(i["page"] for i in mine), "url": OFFICIAL_URL})
    return out


def conn(profile: str, warehouse: str):
    from databricks import sql as dbsql
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient(profile=profile)
    return w, dbsql.connect(server_hostname=w.config.host.replace("https://", ""),
                            http_path=f"/sql/1.0/warehouses/{warehouse}", credentials_provider=lambda: w.config.authenticate)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["upload", "parse", "propose", "approve"])
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse")
    ap.add_argument("--catalog", default="fixit")
    ap.add_argument("--pdf")
    ap.add_argument("--csv", default=str(ROOT / "eval" / "code_review.csv"))
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    if a.profile == "sleepsafe":
        return 2
    c = a.catalog

    if a.step == "upload":
        src = Path(a.pdf or "")
        if src.suffix.lower() != ".pdf" or not src.exists():
            print("--pdf must point to the exported Chapter 27 PDF")
            return 1
        dest = f"/Volumes/{c}/raw/code_docs/{src.name}"
        print(f"{'UPLOAD' if a.apply else 'PLAN  '} {src} ({src.stat().st_size:,} bytes) -> {dest}")
        if a.apply:
            from databricks.sdk import WorkspaceClient
            WorkspaceClient(profile=a.profile).files.upload(dest, src.open("rb"), overwrite=True)
        return 0

    if a.step == "parse":
        stmts = parse_sql(c)
        for s in stmts:
            print(("RUN  " if a.apply else "PLAN ") + " ".join(s.split())[:160])
        if not a.apply:
            return 0
        _, cn = conn(a.profile, a.warehouse)
        cur = cn.cursor()
        for s in stmts:
            cur.execute(s)
        cur.execute(f"SELECT COUNT(*), COUNT(DISTINCT source_doc) FROM {c}.bronze.code_elements")
        print("elements, docs:", cur.fetchone())
        cur.execute(f"SELECT section_id, title, page, length(text) FROM {c}.bronze.code_sections_parsed "
                    f"ORDER BY section_id LIMIT 200")
        rows = cur.fetchall()
        print(f"{len(rows)} parsed sections (all verified=0). First 15:")
        for r in rows[:15]:
            print("  ", tuple(r))
        return 0

    from app.backend.services.code_match import rank_sections
    from app.backend.services.taxonomy import VIOLATION_TYPES

    if a.step == "propose":
        _, cn = conn(a.profile, a.warehouse)
        cur = cn.cursor()
        cur.execute(f"SELECT section_id, title, text, source_doc, page, url, verified FROM {c}.bronze.code_sections_parsed")
        cols = [d[0] for d in cur.description]
        parsed = [dict(zip(cols, r)) for r in cur.fetchall()]
        if not parsed:
            print("No parsed sections yet: run `parse --apply` after uploading the PDF.")
            return 1
        out = Path(a.csv)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["type_id", "name", "candidates (id | title | page | score)", "candidate_snippets",
                         "approved_section_ids", "reviewer", "notes"])
            for v in VIOLATION_TYPES:
                hits = rank_sections(f'{v["name"]}. {v["plain_explanation"]} {v["visual_cues"]}', parsed, k=3)
                by = {p["section_id"]: p for p in parsed}
                wr.writerow([v["type_id"], v["name"],
                             " || ".join(f'{h["section_id"]} | {h["title"]} | p.{by[h["section_id"]]["page"]} | {h["score"]}' for h in hits),
                             " || ".join(h["snippet"][:240].replace("\n", " ") for h in hits), "", "", ""])
        print(f"Wrote {out}. A person must read the official text and fill approved_section_ids (blank = keep placeholder).")
        return 0

    # approve
    rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))
    approved = {r["type_id"]: [s.strip() for s in r["approved_section_ids"].replace(";", ",").split(",") if s.strip()]
                for r in rows if r.get("approved_section_ids", "").strip()}
    prev = json.loads(VERIFIED_JSON.read_text(encoding="utf-8")) if VERIFIED_JSON.exists() else {}
    public_reviewers, private_entries, reviewer_errors = split_reviewers(approved, rows, prev)
    if reviewer_errors:
        print("Reviewer check failed:", *reviewer_errors, sep="\n  ")
        return 1
    ids = sorted({s for v in approved.values() for s in v})
    try:
        secs = approved_rows(ids, set(approved))
    except KeyError as e:
        print("Approved id not in docs/legal/ch27_proposed_mappings.json or the parse (typo?):", e)
        return 1
    print(f"{len(approved)} types approved, {len(ids)} distinct sections: {ids}")
    for t, s in approved.items():
        print(f"  {'SET ' if a.apply else 'PLAN'} {t} -> {s}")
    for s in secs:
        print(f"  {'ROW ' if a.apply else 'PLAN'} {s['section_id']} p.{s['page']} | {s['title'][:60]} | {s['text'][:80]}...")
    if not a.apply:
        return 0
    _, cn = conn(a.profile, a.warehouse)
    cur = cn.cursor()
    for s in secs:  # write only the approved rows into the table the app reads
        cur.execute(f"DELETE FROM {c}.silver.code_sections WHERE section_id = :s AND source_doc NOT LIKE 'seed%'",
                    {"s": s["section_id"]})
        cur.execute(f"INSERT INTO {c}.silver.code_sections (section_id, title, text, source_doc, page, url, verified) "
                    f"VALUES (:section_id, :title, :text, :source_doc, :page, :url, 1)", s)
    for t, s in approved.items():
        cur.execute(f"UPDATE {c}.ref.violation_types SET code_sections = :v WHERE type_id = :t", {"v": json.dumps(s), "t": t})
    # Merge with earlier approvals: never drop a previously approved mapping or section.
    sections = {s["section_id"]: s for s in prev.get("sections", [])}
    sections.update({s["section_id"]: {**s, "verified": 1} for s in secs})
    from datetime import date
    record_private_approvals(private_entries, date.today().isoformat())  # reviewer names: private record only
    out = {"source": OFFICIAL_URL, "review_meaning": REVIEW_MEANING,
           "mapping": {**prev.get("mapping", {}), **approved}, "reviewers": public_reviewers}
    if "reviewer_identity" in prev:
        out["reviewer_identity"] = prev["reviewer_identity"]
    out["sections"] = list(sections.values())
    VERIFIED_JSON.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Databricks updated; wrote {VERIFIED_JSON.relative_to(ROOT)} (local backend picks it up on reset).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
