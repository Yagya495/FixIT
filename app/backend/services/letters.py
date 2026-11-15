"""Repair request letters (P0-6), tour questions + lease addendum (P0-4), complaint drafts (P0-8, P0-9).

Template-based on purpose: deterministic, instant, no LLM dependency on stage.
"""
from __future__ import annotations

from datetime import datetime

from .. import config

TONES = ("friendly", "formal", "final")


def _cite(s: dict) -> str:
    if s.get("verified"):
        return f'MGO § {s["section_id"]}'
    if str(s.get("section_id", "")).startswith("PENDING-"):
        return "legal source not yet verified"
    return "MGO Ch. 27 — section pending verification"


def _issue_lines(violations: list[dict], with_evidence: bool = True) -> list[str]:
    lines = []
    for i, v in enumerate(violations, 1):
        secs = ", ".join(f'{s["title"]} ({_cite(s)})' for s in v.get("code_sections", [])) or "MGO Chapter 27"
        ev = ""
        if with_evidence and v.get("evidence_ids"):
            ev = f' Photo evidence: {", ".join(v["evidence_ids"][:3])}.'
        if v.get("verify_in_person"):
            ev += " Seen in a photo; needs an in-person check."
        if v.get("tenant_reported"):
            ev += " Reported by the tenant."
        # "Possibly relevant": a cited section is the rule that may apply, not a finding that it was violated.
        lines.append(f'{i}. {v["name"]} ({v["severity"]}). Possibly relevant code: {secs}. Requested fix: {v["remedy"]}{ev}')
    return lines


def repair_letter(violations: list[dict], address: str, unit: str | None, landlord: str, tone: str,
                  fix_by: datetime, today: datetime | None = None) -> str:
    today = today or datetime.now()
    where = f"{address}{', Unit ' + unit if unit else ''}"
    issues = "\n".join(_issue_lines(violations))
    date_s = today.strftime("%B %d, %Y")
    fix_s = fix_by.strftime("%A, %B %d, %Y")
    if tone == "friendly":
        opening = (f"Hi {landlord},\n\nI hope you're doing well. I'm writing about a few maintenance issues at {where} "
                   f"that need attention:")
        ask = f"Could you let me know when these can be fixed? Ideally by {fix_s}. Thanks so much for your help!"
        close = "Best,"
    elif tone == "final":
        # Not "FINAL NOTICE": the City issues "Official Notices"; a tenant letter must not read like one.
        opening = (f"{landlord}:\n\nFINAL REQUEST BEFORE A CITY COMPLAINT. I have previously notified you of the following conditions at {where}, "
                   f"which may violate the City of Madison Minimum Housing and Property Maintenance Code (MGO Chapter 27):")
        ask = (f"If these conditions are not corrected by {fix_s}, I intend to file a complaint with City of Madison "
               f"Building Inspection, and may seek rent abatement under MGO 32.04 if the conditions remain uncorrected "
               f"after the city's inspection deadline. Under MGO Chapter 32, retaliation "
               f"against a tenant for requesting code repairs or contacting Building Inspection is prohibited.")
        close = "Sincerely,"
    else:
        opening = (f"Dear {landlord},\n\nI am writing to formally request repairs at {where}. The following conditions "
                   f"may violate the City of Madison Minimum Housing and Property Maintenance Code (MGO Chapter 27):")
        ask = (f"Please complete these repairs by {fix_s} and confirm the scheduled date in writing. I have kept dated, "
               f"hashed photo evidence of each condition.")
        close = "Sincerely,"
    return (f"{date_s}\n\n{opening}\n\n{issues}\n\n{ask}\n\n{close}\n[Tenant name]\n{where}\n\n"
            f"---\n{config.DISCLAIMER}")


def tour_questions(violations: list[dict], history: dict | None) -> list[str]:
    qs = []
    types = {v["violation_type"] for v in violations}
    if "WATER_DAMAGE_MOLD" in types:
        qs.append("I noticed what looks like a water stain in one of the photos. What caused it, and was the leak fixed and the area tested for mold?")
    if "SMOKE_DETECTOR_MISSING" in types or "CO_DETECTOR_MISSING" in types:
        qs.append("Where are the smoke alarms and any carbon monoxide alarms, and when were they last tested? Does the building have fuel-burning appliances, a fireplace or an attached garage?")
    if "EXPOSED_WIRING" in types:
        qs.append("Will the missing outlet/switch covers and any exposed wiring be fixed by a licensed electrician before move-in?")
    if "PEST_EVIDENCE" in types:
        qs.append("Has the building had pest treatments in the last year? Who pays for extermination?")
    if "DAMAGED_SURFACES" in types:
        qs.append("Will the damaged/peeling surfaces be repaired and repainted before move-in? (Ask about lead paint if built before 1978.)")
    if history and history.get("heat_reports_recent", 0) > 0:
        qs.append(f'FixIt\'s demo data (simulated) shows {history["heat_reports_recent"]} recent heat complaints at this building. Has the heating system been repaired or replaced, and how do I report no-heat after hours?')
    defaults = [
        "How do I submit repair requests, and what's your typical response time for urgent issues?",
        "Can we add a move-in condition checklist and a written list of repairs to complete before move-in to the lease?",
        "Who is the management contact for emergencies (no heat, leaks, lockouts)?",
        "Are heat and hot water included, and how is the unit heated?",
    ]
    for d in defaults:
        if len(qs) >= 5:
            break
        qs.append(d)
    return qs[:5]


def lease_addendum(violations: list[dict], address: str, unit: str | None, move_in: str = "[move-in date]") -> str:
    where = f"{address}{', Unit ' + unit if unit else ''}"
    items = "\n".join(f"  {i}. {v['remedy']} (re: {v['name'].lower()})" for i, v in enumerate(violations, 1)) or \
        "  1. [List repairs agreed during the tour]"
    return (f"LEASE ADDENDUM — REPAIRS BEFORE MOVE-IN\n\nPremises: {where}\n\n"
            f"Landlord agrees to complete the following repairs, in a workmanlike manner and in compliance with the "
            f"City of Madison Minimum Housing and Property Maintenance Code (MGO Chapter 27), no later than {move_in}:\n\n"
            f"{items}\n\nIf any listed repair is not complete by that date, Tenant may notify Landlord in writing and "
            f"the parties will agree on a completion date. This addendum does not waive any rights of Tenant under "
            f"state or local law.\n\nLandlord: ____________________  Date: ________\n"
            f"Tenant:   ____________________  Date: ________\n\n---\nDraft generated by FixIt Madison. {config.DISCLAIMER}")


def city_complaint(case: dict, violations: list[dict], notified_dates: list[str], evidence_count: int) -> dict:
    """Pre-filled City of Madison Building Inspection complaint. NEVER auto-submitted."""
    return {
        "form": "DRAFT for the City's interior-property complaint form (not submitted, not an official document)",
        "official_url": config.OFFICIAL_LINKS["report_problem"],
        "submit_note": "FixIt does not submit this for you. Review it, then submit through the official city page or call 608-266-4551.",
        "fields": {
            "Complainant name": "[Your name]", "Phone": "[Your phone]", "Email": "[Your email]",
            "Property address": case.get("address"), "Unit": case.get("unit") or "[unit]",
            "Owner / manager": case.get("landlord"),
            "Problem description": "\n".join(_issue_lines(violations, with_evidence=False)),
            "Date(s) owner was notified": ", ".join(notified_dates) or "[dates]",
            "Owner's promised repair date": case.get("commitment_date") or "None given",
            "Evidence": f"Evidence packet attached ({evidence_count} photos with SHA-256 hashes and timestamps)",
        },
        # Each line paraphrases an official city page (linked below); see PROGRESS.md "Official sources".
        "next_steps": [
            "Submit the complaint (the city says only current tenants can report interior problems), then answer the "
            "inspector's call and schedule an inspection. Check on it at 608-266-4551 ext. 4.",
            "Rent abatement (MGO 32.04) may apply only after the inspector issues an Official Notice with a repair "
            "deadline and that deadline passes with the violation still unfixed. See the city's rent abatement page "
            "for all eligibility steps.",
            "The city says actions against a tenant within six months of their complaint may be seen as retaliation "
            "(MGO Ch. 32). See the city's retaliation page.",
            "Building Inspection says cases are generally resolved within 30 to 60 days, and stay open until fixed.",
        ],
        "links": {k: config.OFFICIAL_LINKS[k] for k in
                  ("report_problem", "rent_abatement", "retaliation", "complaint_process", "tenant_resource_center")},
        "disclaimer": config.DISCLAIMER,
    }


def joint_complaint(address: str, owner: str, unit_issues: list[dict], other_buildings: list[dict]) -> dict:
    letters = [chr(ord("A") + i) for i in range(len(unit_issues))]
    units = [f"Unit {letters[i]}" for i in range(len(unit_issues))]
    lines = [f'{units[i]}: {u["types"]} (first reported {u["first"][:10]}, latest {u["last"][:10]})' for i, u in enumerate(unit_issues)]
    other = [f'{b["address_norm"]}: {b["open_issues"]} open issues' for b in other_buildings]
    return {
        "form": "DRAFT joint complaint (not submitted). Every household must review and agree before anyone files it",
        "official_url": config.OFFICIAL_LINKS["report_problem"],
        "units": units,
        "text": ("DRAFT, NOT SUBMITTED. The other households below reported issues through FixIt but have not yet agreed "
                 "to this complaint. Share it with them to review, edit and sign before anyone files it.\n\n"
                 f"We are tenants of {len(units)} households at {address}, owned or managed by {owner}. "
                 f"We are jointly reporting the following conditions, which may violate MGO Chapter 27:\n\n"
                 + "\n".join(lines)
                 + ("\n\nThe same owner's other buildings currently have open reports:\n" + "\n".join(other) if other else "")
                 + "\n\nUnit numbers are withheld in this draft. Each household will confirm its unit to the inspector."),
        "privacy": "Units are anonymized (Unit A, B, …). Neighbor households in this demo are synthetic.",
        "disclaimer": config.DISCLAIMER,
    }
