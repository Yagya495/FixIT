# Databricks notebook source
# MAGIC %md
# MAGIC # 11 · Vector Search Delta Sync index on `silver.code_chunks` (P0-1)
# MAGIC Free Edition: one endpoint, Delta Sync only. Fallback (if this fails): the app's local BM25 matcher already
# MAGIC works over `silver.code_sections`. Note the failure in PROGRESS.md and move on.

# COMMAND ----------
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.vectorsearch import (DeltaSyncVectorIndexSpecRequest, EmbeddingSourceColumn,
                                                 EndpointType, PipelineType, VectorIndexType)
w = WorkspaceClient()
ENDPOINT, INDEX, SOURCE, EMBED = "fixit-vs", "fixit.silver.code_chunks_index", "fixit.silver.code_chunks", "databricks-gte-large-en"

# COMMAND ----------
if ENDPOINT not in [e.name for e in w.vector_search_endpoints.list_endpoints()]:
    w.vector_search_endpoints.create_endpoint_and_wait(name=ENDPOINT, endpoint_type=EndpointType.STANDARD)

# COMMAND ----------
try:
    w.vector_search_indexes.create_index(
        name=INDEX, endpoint_name=ENDPOINT, primary_key="chunk_id", index_type=VectorIndexType.DELTA_SYNC,
        delta_sync_index_spec=DeltaSyncVectorIndexSpecRequest(
            source_table=SOURCE, pipeline_type=PipelineType.TRIGGERED,
            embedding_source_columns=[EmbeddingSourceColumn(name="text", embedding_model_endpoint_name=EMBED)],
            columns_to_sync=["chunk_id", "section_id", "text", "source_doc", "page"]))
except Exception as e:
    print("create_index:", e)  # already exists → sync instead
    w.vector_search_indexes.sync_index(index_name=INDEX)

# COMMAND ----------
# Acceptance test: top-3 contains the smoke detector section.
res = w.vector_search_indexes.query_index(index_name=INDEX, columns=["section_id", "text"],
                                          query_text="missing smoke detector in bedroom", num_results=3)
for r in res.result.data_array:
    print(r[0], r[1][:120].replace("\n", " "))
