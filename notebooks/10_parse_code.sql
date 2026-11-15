-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 10 · Parse MGO Chapter 27 → sections → chunks (P0-1)
-- MAGIC 1. Upload the Chapter 27 PDF (+ Minimum Housing Standards Checklist, saved city pages) to `/Volumes/fixit/raw/code_docs/`.
-- MAGIC 2. Run this notebook. Output shape verified on this workspace 2026-11-14 (ai_parse_document v2.0):
-- MAGIC    `parsed:document:elements[*]` with `content`, `type`, `bbox[0].page_id`.
-- MAGIC 3. Sections are inserted with **verified = 0**. Only a human review (`scripts/code_parse.py propose` → fill the CSV →
-- MAGIC    `approve`) sets verified = 1. Laptop equivalent of this notebook: `scripts/code_parse.py parse`.

-- COMMAND ----------
USE CATALOG fixit;

CREATE OR REPLACE TABLE bronze.code_docs_parsed AS
SELECT path, ai_parse_document(content) AS parsed
FROM READ_FILES('/Volumes/fixit/raw/code_docs/', format => 'binaryFile')
WHERE lower(path) LIKE '%.pdf';

-- COMMAND ----------
-- Inspect the structure before trusting cell 3.
SELECT path, schema_of_variant(parsed) FROM bronze.code_docs_parsed LIMIT 1;

-- COMMAND ----------
-- Flatten to elements (one row per text element) with page numbers.
CREATE OR REPLACE TABLE bronze.code_elements AS
SELECT path AS source_doc,
       e.pos AS element_idx,
       CAST(e.value:type AS STRING) AS element_type,
       CAST(e.value:content AS STRING) AS content,
       COALESCE(CAST(e.value:bbox[0]:page_id AS INT), CAST(e.value:page_id AS INT)) + 1 AS page
FROM bronze.code_docs_parsed,
     LATERAL variant_explode(COALESCE(parsed:document:elements, parsed:elements)) AS e
WHERE CAST(e.value:content AS STRING) IS NOT NULL
  AND coalesce(CAST(e.value:type AS STRING), '') NOT IN ('page_header', 'page_footer', 'page_number');

-- COMMAND ----------
-- MAGIC %md Split into sections at explicit headings like `27.051 - ENERGY CODE ...` (2-3 digits after the dot, so 27.051
-- MAGIC and 27.085 are not folded into 27.05 / 27.08). Results go to a bronze STAGING table: the app reads only silver/ref,
-- MAGIC so parsing changes nothing it shows. Same SQL as `scripts/code_parse.py parse`. Subsection ids are not derived here;
-- MAGIC a human approves them via docs/legal/CH27_REVIEW.md -> `scripts/code_parse.py approve`.

-- COMMAND ----------
CREATE OR REPLACE TABLE bronze.code_sections_parsed AS
WITH tagged AS (
  SELECT *, regexp_extract(content, '^\s*(27\.[0-9]{2,3})\s*-\s', 1) AS sec_start
  FROM bronze.code_elements),
grouped AS (
  SELECT *, last_value(NULLIF(sec_start, ''), true) OVER (PARTITION BY source_doc ORDER BY element_idx
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS section_id
  FROM tagged)
SELECT section_id,
       trim(regexp_replace(min_by(content, element_idx), '^\s*27\.[0-9]+\s*-\s*', '')) AS title,
       array_join(transform(array_sort(collect_list(struct(element_idx, content))), x -> x.content), '\n') AS text,
       min_by(source_doc, element_idx) AS source_doc,
       min(page) AS page,
       'https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO' AS url,
       0 AS verified   -- NEVER 1 here; only a named human reviewer approves sections
FROM grouped WHERE section_id IS NOT NULL
GROUP BY section_id;

SELECT section_id, title, page, length(text) AS chars FROM bronze.code_sections_parsed ORDER BY section_id;

-- COMMAND ----------
-- Chunk (~800 tokens ≈ 3200 chars, ~100 token overlap ≈ 400 chars).
CREATE OR REPLACE TABLE silver.code_chunks (chunk_id STRING, section_id STRING, text STRING, source_doc STRING, page INT)
TBLPROPERTIES (delta.enableChangeDataFeed = true);

INSERT INTO silver.code_chunks
SELECT concat(section_id, '#', pos) AS chunk_id, section_id,
       concat(section_id, ' ', title, '\n', substring(text, pos * 2800 + 1, 3200)) AS text, source_doc, page
FROM silver.code_sections
LATERAL VIEW posexplode(sequence(0, CAST(floor(greatest(length(text) - 1, 0) / 2800) AS INT))) s AS pos, _x;

SELECT COUNT(*) AS chunks FROM silver.code_chunks;

-- COMMAND ----------
-- Sanity: the smoke alarm paragraph (27.05(2)(w)) should be in the parsed 27.05 text.
SELECT section_id, title FROM bronze.code_sections_parsed WHERE lower(text) LIKE '%smoke alarms shall be installed%';
