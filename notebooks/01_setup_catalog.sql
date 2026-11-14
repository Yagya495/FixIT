-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 01 · Catalog, schemas, volumes
-- MAGIC On Free Edition, if `CREATE CATALOG` is not permitted, use the workspace's default catalog and set
-- MAGIC `FIXIT_CATALOG` accordingly everywhere (app env + notebooks widget).

-- COMMAND ----------
CREATE CATALOG IF NOT EXISTS fixit;
USE CATALOG fixit;

-- COMMAND ----------
CREATE SCHEMA IF NOT EXISTS raw    COMMENT 'Volumes: uploads, listings, code docs, leases, evidence, public data';
CREATE SCHEMA IF NOT EXISTS bronze COMMENT 'Raw parsed/ingested data';
CREATE SCHEMA IF NOT EXISTS silver COMMENT 'Cleaned, conformed app + pipeline data';
CREATE SCHEMA IF NOT EXISTS gold   COMMENT 'Analytics-ready tables used by the app, Genie and dashboards';
CREATE SCHEMA IF NOT EXISTS ref    COMMENT 'Reference data (violation taxonomy)';
CREATE SCHEMA IF NOT EXISTS ml     COMMENT 'Models and features';

-- COMMAND ----------
CREATE VOLUME IF NOT EXISTS raw.uploads     COMMENT 'Walkthrough photos/videos';
CREATE VOLUME IF NOT EXISTS raw.listings    COMMENT 'Listing photos';
CREATE VOLUME IF NOT EXISTS raw.code_docs   COMMENT 'MGO Chapter 27 PDF, checklist, saved city pages';
CREATE VOLUME IF NOT EXISTS raw.leases      COMMENT 'Lease PDFs (P1)';
CREATE VOLUME IF NOT EXISTS raw.evidence    COMMENT 'Canonical evidence copies, SHA-256 named';
CREATE VOLUME IF NOT EXISTS raw.public_data COMMENT 'Chicago/Madison public datasets (P1)';

-- COMMAND ----------
-- MAGIC %md
-- MAGIC ## Grant the App's service principal (replace `<app-sp>` with the app's SP application ID)
-- MAGIC This is the #1 cause of silent failures.

-- COMMAND ----------
-- GRANT USE CATALOG ON CATALOG fixit TO `<app-sp>`;
-- GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA fixit.silver TO `<app-sp>`;
-- GRANT USE SCHEMA, SELECT, MODIFY ON SCHEMA fixit.gold TO `<app-sp>`;
-- GRANT USE SCHEMA, SELECT ON SCHEMA fixit.ref TO `<app-sp>`;
-- GRANT USE SCHEMA ON SCHEMA fixit.raw TO `<app-sp>`;
-- GRANT READ VOLUME, WRITE VOLUME ON VOLUME fixit.raw.evidence TO `<app-sp>`;
-- GRANT READ VOLUME, WRITE VOLUME ON VOLUME fixit.raw.uploads TO `<app-sp>`;
-- Also: SQL warehouse → Permissions → add the SP with CAN USE.
