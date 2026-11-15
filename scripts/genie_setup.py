"""Create (or find) the FixIt Genie space over the gold tables, then ask one question through the Conversation API.

  python scripts/genie_setup.py --profile fixit --warehouse <id> [--catalog fixit] [--create]

Without --create it only looks for an existing space titled TITLE and tests it. Same tables, instructions and the
8 sample questions as notebooks/70_genie_space.py / app/backend/services/genie.py.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
TITLE = "FixIt Madison — Ask the data"
REFUSED = {"sleepsafe"}


def instructions(c: str) -> str:
    return f"""FixIt Madison rental-issue data. ALL owner/property/report data is SYNTHETIC demo data.
Relationships: {c}.gold.reports.property_id -> {c}.gold.properties.property_id; properties.owner_id -> {c}.gold.owners.owner_id;
{c}.gold.landlord_scores.owner_id -> owners.owner_id; reports.violation_type -> {c}.ref.violation_types.type_id.
An open issue means reports.status IN ('open','escalated'). Days to fix = fixed_at - reported_at (fixed rows only).
'Neighborhood' is properties.neighborhood (Madison neighborhoods). Near campus = Langdon, Mifflin, Regent, Greenbush.
'This month' = last 30 days by reported_at. Grades A (best) to F (worst). Show owner names from gold.owners.name."""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", required=True)
    ap.add_argument("--warehouse", required=True)
    ap.add_argument("--catalog", default="fixit")
    ap.add_argument("--create", action="store_true")
    a = ap.parse_args()
    if a.profile in REFUSED:
        return 2
    from databricks.sdk import WorkspaceClient
    from app.backend.services.genie import SAMPLE_QUESTIONS

    w = WorkspaceClient(profile=a.profile)
    c = a.catalog
    spaces = w.api_client.do("GET", "/api/2.0/genie/spaces").get("spaces", [])
    space = next((s for s in spaces if s.get("title") == TITLE), None)
    if space:
        print("found existing FixIt space:", space["space_id"])
    elif a.create:
        tables = sorted(f"{c}.{t}" for t in ["gold.reports", "gold.violations", "gold.properties", "gold.owners",
                                             "gold.landlord_scores", "ref.violation_types"])
        hexid = lambda: uuid.uuid4().hex  # noqa: E731
        serialized = {
            "version": 1,
            "config": {"sample_questions": sorted([{"id": hexid(), "question": [q]} for q in SAMPLE_QUESTIONS], key=lambda x: x["id"])},
            "data_sources": {"tables": [{"identifier": t} for t in tables]},
            "instructions": {"text_instructions": [{"id": hexid(), "content": [instructions(c)]}]},
        }
        try:
            space = w.api_client.do("POST", "/api/2.0/genie/spaces", body={
                "title": TITLE, "description": "Synthetic Madison rental issues (FixIt Madison, MadHacks 2026)",
                "warehouse_id": a.warehouse, "serialized_space": json.dumps(serialized)})
            print("created space:", space.get("space_id"))
        except Exception as e:
            print("CREATE FAILED:", str(e)[:800])
            return 1
    else:
        print("no FixIt space yet; re-run with --create")
        return 0

    sid = space["space_id"]
    q = SAMPLE_QUESTIONS[0]
    t0 = time.time()
    r = w.api_client.do("POST", f"/api/2.0/genie/spaces/{sid}/start-conversation", body={"content": q})
    conv, msg = r["conversation_id"], r["message_id"]
    m = {}
    for _ in range(40):
        m = w.api_client.do("GET", f"/api/2.0/genie/spaces/{sid}/conversations/{conv}/messages/{msg}")
        if m.get("status") in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(2)
    print(f"conversation status={m.get('status')} in {time.time() - t0:.0f}s for: {q}")
    for att in m.get("attachments", []):
        if att.get("text"):
            print("  text:", att["text"].get("content", "")[:300])
        if att.get("query"):
            print("  sql:", " ".join((att["query"].get("query") or "").split())[:400])
            res = w.api_client.do("GET", f"/api/2.0/genie/spaces/{sid}/conversations/{conv}/messages/{msg}"
                                          f"/attachments/{att['attachment_id']}/query-result")
            data = res.get("statement_response", {}).get("result", {}).get("data_array", [])
            print("  rows:", data[:3])
    print(f"\nGENIE_SPACE_ID={sid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
