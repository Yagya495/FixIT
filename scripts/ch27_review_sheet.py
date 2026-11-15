"""Build the human review sheet for proposed Chapter 27 mappings. Changes nothing in Databricks or the app.

Every excerpt in docs/legal/ch27_proposed_mappings.json must appear word for word (whitespace-normalized) in the
Databricks parse (docs/legal/ch27_parsed_sections.json) under the section it claims; otherwise the script fails.
With --pdf-text (a page-marked text dump of the PDF, "=== PAGE n ===" headers) it also checks each excerpt against
the PDF's own text layer and that the recorded page is right.

  python scripts/ch27_review_sheet.py [--pdf-text ch27.txt]
Writes docs/legal/CH27_REVIEW.md and eval/code_review.csv (approved_section_ids / reviewer left BLANK).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEGAL = ROOT / "docs" / "legal"
sys.path.insert(0, str(ROOT))


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def loose(s: str) -> str:
    """For the PDF text layer only: it splits bold captions from their period ("Smoke Alarms ." )."""
    return re.sub(r" ([.,;:)])", r"\1", norm(s))


def pdf_pages(path: Path) -> list[str]:
    raw = path.read_text(encoding="utf-8")
    pages = re.split(r"=== PAGE \d+ ===", raw)[1:]
    junk = re.compile(r"^(11/14/26, 8:55 PM|Madison, WI Code of Ordinances|about:blank|\d+|/|\(\d+\)|\([a-z]+\))$")
    return [loose(" ".join(l for l in p.splitlines() if not junk.match(l.strip()))) for p in pages]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf-text")
    ap.add_argument("--fix-pages", action="store_true", help="write the page found in the PDF back into the JSON")
    a = ap.parse_args()
    from app.backend.services.taxonomy import VIOLATION_TYPES

    prop = json.loads((LEGAL / "ch27_proposed_mappings.json").read_text(encoding="utf-8"))
    parsed = {s["section_id"]: s for s in json.loads((LEGAL / "ch27_parsed_sections.json").read_text(encoding="utf-8"))}
    pages = pdf_pages(Path(a.pdf_text)) if a.pdf_text else None
    cf = LEGAL / "ch27_parse_corrections.json"
    corrections = json.loads(cf.read_text(encoding="utf-8"))["corrections"] if cf.exists() else []
    names = {v["type_id"]: v for v in VIOLATION_TYPES}
    errors = []

    for p in prop["proposals"]:
        if p["type_id"] not in names:
            errors.append(f"unknown type {p['type_id']}")
        for it in p["items"]:
            sec = parsed.get(it["section"])
            if not sec or not it["section_id"].startswith(it["section"]):
                errors.append(f"{p['type_id']}: section {it['section']} / {it['section_id']} not in the parse")
                continue
            if norm(it["excerpt"]) not in norm(sec["text"]):
                errors.append(f"{p['type_id']} {it['section_id']}: excerpt NOT found verbatim in parsed {it['section']}")
            if pages is not None:
                # Match the excerpt (or, across a page break, its start) in the PDF's own text layer.
                ex = loose(it["excerpt"])
                hit = next((i + 1 for i, t in enumerate(pages) if ex in t), None)
                if hit is None:
                    hit = next((i + 1 for i, t in enumerate(pages) if ex[:60] in t), None)
                    if hit is not None:
                        it["spans_page_break"] = True
                if hit is None:
                    errors.append(f"{p['type_id']} {it['section_id']}: excerpt not found in the PDF text layer")
                elif hit != it["page"] and a.fix_pages:
                    it["page"] = hit
                elif hit != it["page"]:
                    errors.append(f"{p['type_id']} {it['section_id']}: page is {hit}, JSON says {it['page']}")
        for nm in p.get("not_mapped", []):
            sec = parsed[nm["section_id"].split("(")[0]]
            if norm(nm["excerpt"]) not in norm(sec["text"]):
                errors.append(f"{p['type_id']} not_mapped {nm['section_id']}: excerpt not in the parse")
    missing = set(names) - {p["type_id"] for p in prop["proposals"]}
    if missing:
        errors.append(f"types with no proposal row: {sorted(missing)}")
    if errors:
        print("FAILED:\n  " + "\n  ".join(errors))
        return 1
    if a.fix_pages:  # pages come from the PDF text layer, never typed by hand
        clean = {**prop, "proposals": [{**p, "items": [{k: v for k, v in i.items() if k != "spans_page_break"}
                                                         for i in p["items"]]} for p in prop["proposals"]]}
        (LEGAL / "ch27_proposed_mappings.json").write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n",
                                                            encoding="utf-8")

    def status(p: dict) -> str:
        d = p.get("decision", "")
        if d.startswith("VERIFIED"):
            return "**Verified** (reviewer: Naisha Chadha, 2026-11-14; applied and deployed)"
        if d.startswith("PROVISIONAL"):
            extra = " (mold aspect pending a separate legal source)" if "mold" in d.lower() else ""
            return "Provisionally accepted; **not verified** (pending official-source cross-check + reviewer name)" + extra
        if d.startswith("ON HOLD"):
            return "**On hold** (27.06(4) cross-reference + SPS requirements)"
        if "pending additional legal-source" in d:
            return "Pending separate legal source"
        return "Under review"

    title = lambda sid: f"{sid} - {norm(parsed[sid]['title'])}"
    md = [
        "# Chapter 27 mapping review sheet (PROPOSED, NOT VERIFIED)",
        "",
        "> **Nothing on this sheet is verified.** These are FixIt's proposed links between its issue categories and",
        "> Madison General Ordinances Chapter 27. The app keeps showing \"section number pending verification\" until a",
        "> named person approves a row (see *How to approve*). FixIt is not a lawyer and this is not legal advice.",
        "",
        f"- **Source:** {prop['source_pdf']}",
        f"- **Official page:** {prop['source_url']}",
        f"- **Parsed by:** {prop['parsed_by']}",
        f"- **Numbering:** {prop['numbering_note']}",
        "- **Excerpt check:** every excerpt below was machine-checked to appear word for word in the Databricks parse"
        + (" and in the PDF's own text layer, on the page shown." if pages is not None else "."),
        "- **Kinds:** *direct* = Chapter 27 itself states the requirement. *reference* = Chapter 27 only says to follow",
        "  another law or code, whose text FixIt has not reviewed.",
        "- **Evidence levels:** *ordinance text (independently confirmed)* = read on the live official Municode page;",
        "  *City guidance* = City of Madison web pages (helpful, not ordinance text); *interpretation* = FixIt's or the",
        "  reviewer's reading of how a provision applies. Live check details: `docs/legal/ch27_live_check.md`.",
        "",
        "## Summary",
        "",
        "| FixIt issue category | Proposed section(s) | Kind | Separate legal source needed? | Status |",
        "|---|---|---|---|---|",
    ]
    for p in prop["proposals"]:
        v = names[p["type_id"]]
        ids = ", ".join(dict.fromkeys(f"§{i['section_id']}" for i in p["items"])) or "**none found in Ch. 27**"
        kinds = ", ".join(dict.fromkeys(i["kind"] for i in p["items"])) or "—"
        md.append(f"| {v['name']} (`{p['type_id']}`) | {ids} | {kinds} | "
                  f"{'**Yes**' if p['separate_source_required'] else 'No'} | {status(p)} |")
    md += ["", "## Details", ""]
    for p in prop["proposals"]:
        v = names[p["type_id"]]
        md += [f"### {v['name']} (`{p['type_id']}`)", ""]
        if p["separate_source_required"]:
            md += ["> ⚠ **Separate legal-source verification required.** Chapter 27 does not itself establish the full",
                   "> requirement for this category.", ""]
        if not p["items"]:
            md += ["**Proposed section:** none. Chapter 27 contains no provision for this category.", ""]
        for it in p["items"]:
            md += [f"**§{it['section_id']}**: {it['kind']}" + (f" ({it['caption']})" if it["caption"] else ""),
                   "",
                   f"- Section title: *{title(it['section'])}*",
                   f"- PDF page: {it['page']}" + (" (continues onto the next page)" if it.get("spans_page_break") else ""),
                   f"- Numbering evidence: {it['numbering_evidence']}"]
            if it["references"]:
                md.append("- Refers to (not reviewed by FixIt): " + "; ".join(it["references"]))
            md += ["", f"> {norm(it['excerpt'])}", ""]
        for nm in p.get("not_mapped", []):
            md += [f"**Considered, NOT mapped: §{nm['section_id']}** (p. {nm['page']}). {nm['reason']}", "",
                   f"> {norm(nm['excerpt'])}", ""]
        md += [f"**Why it matches:** {p['why']}", "", f"**Uncertainty / missing source:** {p['uncertainty']}", ""]
        if p.get("related"):
            md += ["**Related sources, by evidence level:**", ""]
            md += [f"- *{r['level']}*: {r['source']}. {r['note']}" for r in p["related"]]
            md += [""]
        if p.get("decision"):
            md += [f"**Decision so far:** {p['decision']}", ""]
        md += ["**Verified:** Yes. Reviewer: Naisha Chadha (2026-11-14)." if p.get("decision", "").startswith("VERIFIED")
               else "**Verified:** No. Nothing is verified until a named reviewer approves it after the live-source check.", ""]
    md += [
        "## Problems found in the current placeholder summaries",
        "",
        "These FixIt summaries are shown in the deployed app today, labeled \"plain-language summary, not official text\".",
        "Corrected on git branch `ch27-review` (not deployed yet):",
        "",
        "- **CH27-SMOKE** says carbon monoxide alarms are required. Chapter 27 does not mention carbon monoxide.",
        "- **CH27-MOISTURE** mentions \"conditions that support mold growth\". Chapter 27 does not mention mold.",
        "- **CH27-ELECTRICAL** says outlets must be \"covered\". Chapter 27 does not mention cover plates.",
        "- **CH27-WINDOWS** says windows must be \"glazed without cracks or holes\". Chapter 27 says \"proper repair\" and",
        "  \"weathertight\"; screens are required seasonally.",
        "- **CH27-HEAT** gives no temperature. Chapter 27 sets 67°F in habitable rooms, kitchens and bathrooms.",
        "- **CH27-PESTS** says dwellings must be \"kept free of insects, rodents\". Chapter 27 assigns extermination",
        "  responsibility once an infestation (sustained presence) exists; it has no general pest-free rule.",
        "- **CH27-SECURITY** omitted the rented-unit condition, the story/access rule for windows and approved alternatives.",
        "- **CH27-EGRESS** says handrails must be \"firmly fastened\". Chapter 27 refers handrails to the SPS code.",
        "- Category wording (explanations, remedies, names) for heat, plumbing, surfaces, locks, windows, pests, exits,",
        "  electrical and water damage was corrected on the same branch (see the git log).",
        "",
        "## Unresolved source discrepancies (not silently resolved)",
        "",
        *[f"- **{u['where']}** ({u['status']}): {u['issue']}" for u in prop.get("unresolved_discrepancies", [])],
        "",
        "## Parse defects, corrected from the PDF's own text layer",
        "",
        "ai_parse_document lost words at these page breaks. The raw parse (`ch27_parsed_sections.json`) is kept unmodified;",
        "the correct text is in `docs/legal/ch27_parse_corrections.json`. Neither passage is used in a mapping.",
        "",
        *[f"- **§{c['section_id']}** (PDF pp. {', '.join(map(str, c['pdf_pages']))}; {c['defect']}): "
          f"> {c['pdf_text']}" for c in corrections],
        "",
        "## How to approve",
        "",
        "1. Read each excerpt against the current official text on Municode (link above).",
        "2. In `eval/code_review.csv`, fill `approved_section_ids` (e.g. `27.04(2)(h)`) and `reviewer` **only** for rows the",
        "   reviewer personally checked against the official source and explicitly approved. Reviewer: **Naisha Chadha**.",
        "   Every other reviewer field stays blank. Leave `CO_DETECTOR_MISSING` blank unless a separate source is verified.",
        "",
        "   **What a reviewer approval means:** the ordinance citation and quoted text were checked against the official",
        "   source. It does **not** mean the reviewer is a lawyer or a City inspector, and it does **not** mean that an",
        "   AI-detected condition is a confirmed legal violation.",
        "",
        "3. Run `python scripts/code_parse.py approve --profile fixit --warehouse <id>` (dry run) and check the plan.",
        "   Only then run it with `--apply`. Until then nothing in the app changes.",
        "",
    ]
    (LEGAL / "CH27_REVIEW.md").write_text("\n".join(md), encoding="utf-8")

    out = ROOT / "eval" / "code_review.csv"
    prev = {r["type_id"]: r for r in csv.DictReader(out.open(encoding="utf-8"))} if out.exists() else {}
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["type_id", "name", "proposed_section_ids", "kind", "separate_source_required", "proposed_excerpts",
                    "uncertainty", "auto_candidates (id | title | page | score)", "decision", "approved_section_ids", "reviewer",
                    "notes"])
        for p in prop["proposals"]:
            r = prev.get(p["type_id"], {})
            w.writerow([p["type_id"], names[p["type_id"]]["name"],
                        "; ".join(dict.fromkeys(i["section_id"] for i in p["items"])),
                        "; ".join(dict.fromkeys(i["kind"] for i in p["items"])),
                        "yes" if p["separate_source_required"] else "no",
                        " || ".join(f"[{i['section_id']}] {norm(i['excerpt'])}" for i in p["items"]),
                        p["uncertainty"], norm(r.get("candidates (id | title | page | score)",
                                                     r.get("auto_candidates (id | title | page | score)", ""))),
                        p.get("decision", ""), r.get("approved_section_ids", ""), r.get("reviewer", ""), r.get("notes", "")])
    print(f"OK: {sum(len(p['items']) for p in prop['proposals'])} excerpts verified. Wrote "
          f"{(LEGAL / 'CH27_REVIEW.md').relative_to(ROOT)} and {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
