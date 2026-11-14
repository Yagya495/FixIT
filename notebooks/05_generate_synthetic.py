# Databricks notebook source
# MAGIC %md
# MAGIC # 05 · Synthetic Madison dataset (P0-12)
# MAGIC Uses the SAME generator as the app (`app/backend/services/synthetic.py`) so the demo story is identical.
# MAGIC Run from a Databricks Git folder containing this repo. Run `30_gold_tables.sql` first.
# MAGIC Every row is synthetic (`is_synthetic=1`, `source='synthetic'`).

# COMMAND ----------
import os, sys
repo_root = os.path.abspath(os.path.join(os.getcwd(), ".."))
sys.path.insert(0, repo_root)
from app.backend.services import synthetic, landlords
from datetime import datetime
import pandas as pd

dbutils.widgets.text("catalog", "fixit")
CATALOG = dbutils.widgets.get("catalog")

# COMMAND ----------
now = datetime.now().replace(microsecond=0)
data = synthetic.generate(now=now)
scores = landlords.compute_scores(data["owners"], data["properties"], data["reports"], now)
{k: len(v) for k, v in data.items()}, len(scores)

# COMMAND ----------
def write(rows, table, ts_cols=()):
    pdf = pd.DataFrame(rows)
    for c in ts_cols:
        pdf[c] = pd.to_datetime(pdf[c])
    target = spark.table(f"{CATALOG}.{table}").schema
    sdf = spark.createDataFrame(pdf)
    sdf = sdf.select([sdf[f.name].cast(f.dataType).alias(f.name) for f in target])
    sdf.write.mode("overwrite").option("overwriteSchema", "false").saveAsTable(f"{CATALOG}.{table}")
    print(table, sdf.count())

write(data["owners"], "gold.owners")
write(data["properties"], "gold.properties")
write(data["reports"], "gold.reports", ts_cols=("reported_at", "fixed_at"))
write(scores, "gold.landlord_scores")

# COMMAND ----------
display(spark.sql(f"SELECT * FROM {CATALOG}.gold.landlord_scores WHERE owner_id = 'O-DEMO'"))
display(spark.sql(f"""SELECT violation_category, COUNT(*) n FROM {CATALOG}.gold.reports
                      WHERE property_id = 'P-DEMO-1234' AND reported_at >= current_timestamp() - INTERVAL 7 DAYS GROUP BY 1"""))
