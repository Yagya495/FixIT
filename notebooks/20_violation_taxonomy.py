# Databricks notebook source
# MAGIC %md
# MAGIC # 20 · Violation taxonomy → `ref.violation_types` (P0-2)
# MAGIC Source of truth: `app/backend/services/taxonomy.py`. After `10_parse_code.sql` has produced real
# MAGIC `silver.code_sections`, use the remap cell to replace placeholder `CH27-*` ids with real section ids
# MAGIC (found by match_code over the parsed text, then **reviewed by a human**, never guessed).

# COMMAND ----------
import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.getcwd(), "..")))
from app.backend.services.taxonomy import VIOLATION_TYPES, SEED_CODE_SECTIONS
import pandas as pd
dbutils.widgets.text("catalog", "fixit")
CATALOG = dbutils.widgets.get("catalog")

# COMMAND ----------
rows = [{**v, "code_sections": json.dumps(v["code_sections"])} for v in VIOLATION_TYPES]
spark.createDataFrame(pd.DataFrame(rows)).write.mode("overwrite").saveAsTable(f"{CATALOG}.ref.violation_types")

# Seed unverified sections only if parsing hasn't populated the table yet.
if spark.table(f"{CATALOG}.silver.code_sections").count() == 0:
    seed = pd.DataFrame(SEED_CODE_SECTIONS).astype({"page": "Int64"})
    spark.createDataFrame(seed).selectExpr("section_id", "title", "text", "source_doc", "CAST(page AS INT) page", "url", "CAST(verified AS INT) verified") \
        .write.mode("append").saveAsTable(f"{CATALOG}.silver.code_sections")

# COMMAND ----------
# MAGIC %md ## Remap to parsed sections (run after 10/11). Review the proposals before applying.

# COMMAND ----------
from app.backend.services.code_match import rank_sections
parsed = [r.asDict() for r in spark.table(f"{CATALOG}.silver.code_sections").where("verified = 1").collect()]
proposals = []
for v in VIOLATION_TYPES:
    hits = rank_sections(f'{v["name"]}. {v["plain_explanation"]}', parsed, k=3)
    proposals.append({"type_id": v["type_id"], "candidates": [(h["section_id"], h["title"], h["score"]) for h in hits]})
display(pd.DataFrame(proposals))

# COMMAND ----------
# Fill in after review, e.g. {"SMOKE_DETECTOR_MISSING": ["27.xx(x)"], ...}. Leave empty to keep placeholders.
APPROVED = {}
for t, secs in APPROVED.items():
    spark.sql(f"UPDATE {CATALOG}.ref.violation_types SET code_sections = '{json.dumps(secs)}' WHERE type_id = '{t}'")
