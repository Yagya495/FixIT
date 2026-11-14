# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Smoke tests (Milestone 1)
# MAGIC Run cell by cell. Record what works in `PROGRESS.md` and the chosen endpoints in `.env` / `app/app.yaml`.
# MAGIC If a step fails, use the fallback listed in `docs/BUILD_PROMPT.md` §3.

# COMMAND ----------
dbutils.widgets.text("catalog", "fixit")
CATALOG = dbutils.widgets.get("catalog")
display(spark.sql("SELECT current_catalog() AS catalog, current_user() AS user"))

# COMMAND ----------
# MAGIC %md ## 1. List serving endpoints → pick chat / vision / embedding

# COMMAND ----------
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
eps = [(e.name, (e.state.ready if e.state else None), e.task) for e in w.serving_endpoints.list()]
for e in sorted(eps):
    print(e)

# COMMAND ----------
# Set candidates (edit after looking at the list above)
CHAT = "databricks-claude-sonnet-4-5"
VISION = "databricks-claude-sonnet-4-5"
EMBED = "databricks-gte-large-en"

# COMMAND ----------
# MAGIC %md ## 2. ai_query chat

# COMMAND ----------
display(spark.sql(f"SELECT ai_query('{CHAT}', 'Reply with exactly: OK') AS reply"))

# COMMAND ----------
# MAGIC %md ## 3. ai_extract / ai_classify

# COMMAND ----------
display(spark.sql("""
SELECT ai_classify('There are mouse droppings under my kitchen sink', ARRAY('PESTS','HEAT','PLUMBING','ELECTRICAL')) AS cls,
       ai_extract('The landlord said they would fix the heat by Thursday', ARRAY('repair', 'date')) AS ext
"""))

# COMMAND ----------
# MAGIC %md ## 4. Vision: image input via serving endpoint (base64)

# COMMAND ----------
import base64, io, json, struct, zlib, requests
def tiny_png():
    w_, h_ = 64, 48
    raw = b"".join(b"\x00" + bytes([200, 60, 60]) * w_ for _ in range(h_))
    c = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + c(b"IHDR", struct.pack(">IIBBBBB", w_, h_, 8, 2, 0, 0, 0)) + c(b"IDAT", zlib.compress(raw)) + c(b"IEND", b"")
b64 = base64.b64encode(tiny_png()).decode()
resp = w.api_client.do("POST", f"/serving-endpoints/{VISION}/invocations", body={
    "messages": [{"role": "user", "content": [
        {"type": "text", "text": "What color is this image? One word."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}]}],
    "max_tokens": 20})
print(resp["choices"][0]["message"]["content"])
# If this fails: try another endpoint from the list; otherwise use the sidecar local detector fallback.

# COMMAND ----------
# MAGIC %md ## 5. Embeddings + Vector Search endpoint

# COMMAND ----------
r = w.api_client.do("POST", f"/serving-endpoints/{EMBED}/invocations", body={"input": ["smoke detector missing"]})
print(len(r["data"][0]["embedding"]), "dims")

# COMMAND ----------
try:
    print([e.name for e in w.vector_search_endpoints.list_endpoints()])
except Exception as e:
    print("Vector search list failed:", e)

# COMMAND ----------
# MAGIC %md ## 6. ai_parse_document on one PDF (after 01_setup + uploading code_docs)

# COMMAND ----------
try:
    display(spark.sql(f"""
      SELECT path, ai_parse_document(content) AS parsed
      FROM READ_FILES('/Volumes/{CATALOG}/raw/code_docs/', format => 'binaryFile') LIMIT 1"""))
except Exception as e:
    print("ai_parse_document failed:", e)

# COMMAND ----------
# MAGIC %md ## 7. Genie API reachable

# COMMAND ----------
try:
    print(w.api_client.do("GET", "/api/2.0/genie/spaces"))
except Exception as e:
    print("Genie list failed (create the space in the UI and use its ID):", e)

# COMMAND ----------
# MAGIC %md ## 8. SQL warehouses (the App needs one + CAN USE for its service principal)

# COMMAND ----------
for wh in w.warehouses.list():
    print(wh.id, wh.name, wh.state)
