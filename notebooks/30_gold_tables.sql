-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 30 · Silver/gold table DDL (+ comments for Genie) and data-quality checks
-- MAGIC Column sets match `app/backend/db.py::LOCAL_DDL` so the app writes the same rows to both backends.
-- MAGIC Arrays are stored as JSON strings (portable SQL path); booleans as INT 0/1.

-- COMMAND ----------
USE CATALOG fixit;

-- COMMAND ----------
CREATE TABLE IF NOT EXISTS ref.violation_types (
  type_id STRING NOT NULL, name STRING, category STRING, visual_cues STRING, default_severity STRING,
  code_sections STRING COMMENT 'JSON array of silver.code_sections.section_id', plain_explanation STRING, remedy_request STRING
) COMMENT 'Fixed taxonomy of ~11 rental violation types mapped to MGO Chapter 27 sections';

CREATE TABLE IF NOT EXISTS silver.code_sections (
  section_id STRING NOT NULL, title STRING, text STRING, source_doc STRING, page INT, url STRING,
  verified INT COMMENT '1 = parsed from the official PDF; 0 = unverified seed'
) COMMENT 'MGO Chapter 27 sections parsed with ai_parse_document';

-- COMMAND ----------
CREATE TABLE IF NOT EXISTS gold.owners (
  owner_id STRING NOT NULL, name STRING COMMENT 'Owner name (synthetic)', management_company STRING,
  is_synthetic INT COMMENT '1 = synthetic demo data'
) COMMENT 'Property owners / management companies. All demo rows are synthetic.';

CREATE TABLE IF NOT EXISTS gold.properties (
  property_id STRING NOT NULL, address_norm STRING COMMENT 'Normalized street address, uppercase, no unit',
  lat DOUBLE, lon DOUBLE, neighborhood STRING COMMENT 'Madison neighborhood name (e.g. Langdon, Mifflin, Regent)',
  units INT COMMENT 'Number of rental units', year_built INT, owner_id STRING COMMENT 'FK gold.owners.owner_id', is_synthetic INT
) COMMENT 'Rental buildings in Madison';

CREATE TABLE IF NOT EXISTS gold.reports (
  report_id STRING NOT NULL, property_id STRING COMMENT 'FK gold.properties', unit_hash STRING COMMENT 'Hashed unit id (privacy)',
  violation_category STRING COMMENT 'HEAT|SMOKE_CO|ELECTRICAL|MOLD_MOISTURE|PESTS|SECURITY|PLUMBING|STRUCTURAL|EGRESS|SANITATION',
  violation_type STRING COMMENT 'FK ref.violation_types.type_id', severity STRING COMMENT 'routine|urgent|emergency',
  reported_at TIMESTAMP, fixed_at TIMESTAMP COMMENT 'NULL if not fixed',
  status STRING COMMENT 'open|escalated|fixed. An open issue = status IN (open, escalated)',
  source STRING COMMENT 'fixit|public|synthetic'
) COMMENT 'One row per tenant-reported issue';

CREATE TABLE IF NOT EXISTS gold.landlord_scores (
  owner_id STRING NOT NULL, buildings INT, units INT, open_issues INT, issues_last_12mo INT, issues_per_unit DOUBLE,
  median_days_to_fix DOUBLE, pct_fixed_within_30d DOUBLE COMMENT '0-1', repeat_buildings INT COMMENT 'Buildings with >=3 issues in 12 months',
  emergency_issues INT, score DOUBLE COMMENT 'Weighted z-score; higher = worse', grade STRING COMMENT 'A-F'
) COMMENT 'Landlord report cards. Formula in notebooks/40_landlord_scores.sql';

CREATE TABLE IF NOT EXISTS gold.violations (
  violation_id STRING NOT NULL, scan_id STRING, property_id STRING, violation_type STRING, severity STRING, confidence DOUBLE,
  code_section_ids STRING COMMENT 'JSON array', explanation STRING, evidence_ids STRING COMMENT 'JSON array', status STRING
) COMMENT 'Deduplicated violations per scan from the vision pipeline';

-- COMMAND ----------
CREATE TABLE IF NOT EXISTS silver.scans (scan_id STRING NOT NULL, user_id STRING, property_id STRING, unit STRING,
  mode STRING COMMENT 'walkthrough|listing|movein|moveout', address STRING, created_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS silver.evidence (evidence_id STRING NOT NULL, scan_id STRING, volume_path STRING, sha256 STRING,
  captured_at TIMESTAMP, uploaded_at TIMESTAMP, media_type STRING);
CREATE TABLE IF NOT EXISTS silver.detections (detection_id STRING NOT NULL, scan_id STRING, evidence_id STRING, violation_type STRING,
  confidence DOUBLE, bbox STRING, note STRING, model_endpoint STRING, created_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS silver.repair_requests (request_id STRING NOT NULL, user_id STRING, scan_id STRING, property_id STRING,
  unit STRING, violation_ids STRING, tone STRING, letter_text STRING, sent_at TIMESTAMP, created_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS silver.calls (call_id STRING NOT NULL, request_id STRING, mode STRING, transcript STRING,
  commitment_date TIMESTAMP, commitment_text STRING, landlord_tone STRING, created_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS silver.deadlines (request_id STRING NOT NULL, due_date TIMESTAMP, status STRING COMMENT 'open|met|missed|escalated',
  created_at TIMESTAMP, updated_at TIMESTAMP, sim_offset_days INT COMMENT 'Demo: simulated days elapsed');
CREATE TABLE IF NOT EXISTS silver.complaints (complaint_id STRING NOT NULL, request_id STRING, payload_json STRING,
  generated_at TIMESTAMP, joint INT, units STRING);

-- COMMAND ----------
CREATE OR REPLACE VIEW gold.building_history COMMENT 'Per-building issue summary' AS
SELECT p.property_id, p.address_norm, p.neighborhood, p.owner_id,
       COUNT(r.report_id) AS total_reports,
       SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_issues,
       SUM(CASE WHEN r.violation_category = 'HEAT' AND r.reported_at >= current_timestamp() - INTERVAL 30 DAYS THEN 1 ELSE 0 END) AS heat_reports_30d,
       MAX(r.reported_at) AS last_reported_at
FROM gold.properties p LEFT JOIN gold.reports r ON r.property_id = p.property_id
GROUP BY p.property_id, p.address_norm, p.neighborhood, p.owner_id;

CREATE OR REPLACE VIEW gold.neighborhood_stats COMMENT 'Per-neighborhood issue stats' AS
SELECT p.neighborhood, COUNT(r.report_id) AS reports,
       SUM(CASE WHEN r.status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_issues,
       percentile_approx(CASE WHEN r.fixed_at IS NOT NULL THEN (unix_timestamp(r.fixed_at) - unix_timestamp(r.reported_at)) / 86400 END, 0.5) AS median_days_to_fix
FROM gold.properties p LEFT JOIN gold.reports r ON r.property_id = p.property_id GROUP BY p.neighborhood;

-- COMMAND ----------
-- MAGIC %md ## Data-quality checks (all counts should be 0)

-- COMMAND ----------
SELECT 'null property keys' AS check, COUNT(*) AS failures FROM gold.properties WHERE property_id IS NULL
UNION ALL SELECT 'lat/lon outside Madison bbox', COUNT(*) FROM gold.properties WHERE lat NOT BETWEEN 42.95 AND 43.20 OR lon NOT BETWEEN -89.60 AND -89.20
UNION ALL SELECT 'invalid severity', COUNT(*) FROM gold.reports WHERE severity NOT IN ('routine','urgent','emergency')
UNION ALL SELECT 'invalid status', COUNT(*) FROM gold.reports WHERE status NOT IN ('open','escalated','fixed')
UNION ALL SELECT 'orphan reports', COUNT(*) FROM gold.reports r LEFT ANTI JOIN gold.properties p ON r.property_id = p.property_id
UNION ALL SELECT 'fixed before reported', COUNT(*) FROM gold.reports WHERE fixed_at < reported_at;
