# Databricks notebook source
# MAGIC %md
# MAGIC # 70 · Genie space over gold tables (P0-11)
# MAGIC Tries the API; if it isn't available, create the space in the UI with the same tables, instructions and
# MAGIC sample questions, then put its ID in `GENIE_SPACE_ID` (app env).

# COMMAND ----------
import json
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
WAREHOUSE_ID = [wh.id for wh in w.warehouses.list()][0]  # or set explicitly
TABLES = ["fixit.gold.reports", "fixit.gold.violations", "fixit.gold.properties", "fixit.gold.owners",
          "fixit.gold.landlord_scores", "fixit.ref.violation_types"]
INSTRUCTIONS = """FixIt Madison rental-issue data. ALL owner/property/report data is SYNTHETIC demo data.
Relationships: reports.property_id -> properties.property_id; properties.owner_id -> owners.owner_id;
landlord_scores.owner_id -> owners.owner_id; reports.violation_type -> violation_types.type_id.
An open issue means reports.status IN ('open','escalated'). Days to fix = fixed_at - reported_at (fixed rows only).
'Neighborhood' is properties.neighborhood (Madison neighborhoods). Near campus = Langdon, Mifflin, Regent, Greenbush.
'This month' = last 30 days by reported_at. Grades A (best) to F (worst)."""
QUESTIONS = [
    "Which owners have the most open heat issues this month?",
    "What is the median days-to-fix by neighborhood?",
    "Which buildings have 3+ mold reports in the last year?",
    "How many emergency issues are open right now?",
    "Show violation counts by type for the last 6 months.",
    "Which management companies improved their fix times the most?",
    "Which buildings near campus have the most open issues?",
    "What percent of issues are fixed within 30 days, by owner grade?",
]

# COMMAND ----------
# VERIFY: the Genie create-space API payload has changed across releases. If this fails, use the UI.
serialized = {"version": 1, "data_sources": {"tables": [{"identifier": t} for t in TABLES]},
              "instructions": {"text_instructions": [{"content": [INSTRUCTIONS]}]},
              "config": {"sample_questions": [{"question": [q]} for q in QUESTIONS]}}
try:
    r = w.api_client.do("POST", "/api/2.0/genie/spaces", body={
        "title": "FixIt Madison — Ask the data", "description": "Synthetic Madison rental issues",
        "warehouse_id": WAREHOUSE_ID, "serialized_space": json.dumps(serialized)})
    print("GENIE_SPACE_ID =", r.get("space_id") or r)
except Exception as e:
    print("Create via API failed — create in UI. Error:", e)

# COMMAND ----------
# Test the Conversation API (set SPACE_ID first)
SPACE_ID = ""
if SPACE_ID:
    import time
    r = w.api_client.do("POST", f"/api/2.0/genie/spaces/{SPACE_ID}/start-conversation", body={"content": QUESTIONS[0]})
    conv, msg = r["conversation_id"], r["message_id"]
    for _ in range(30):
        m = w.api_client.do("GET", f"/api/2.0/genie/spaces/{SPACE_ID}/conversations/{conv}/messages/{msg}")
        if m["status"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(2)
    print(json.dumps(m.get("attachments"), indent=2)[:2000])
