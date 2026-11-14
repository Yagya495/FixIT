-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 40 · Landlord scores (P0-10). SQL twin of `landlords.compute_scores`
-- MAGIC score = 0.35·z(issues_per_unit) + 0.35·z(median_days_to_fix) + 0.20·z(−pct_fixed_within_30d) + 0.10·z(emergency_per_unit)
-- MAGIC A < −0.5 ≤ B < 0 ≤ C < 0.5 ≤ D < 1.0 ≤ F. Schedule as a Job after new reports land.

-- COMMAND ----------
USE CATALOG fixit;

CREATE OR REPLACE TEMP VIEW base AS
WITH u AS (SELECT owner_id, COUNT(*) AS buildings, SUM(units) AS units FROM gold.properties GROUP BY owner_id),
r AS (
  SELECT p.owner_id, r.property_id, r.status, r.severity, r.reported_at, r.fixed_at,
         (unix_timestamp(r.fixed_at) - unix_timestamp(r.reported_at)) / 86400 AS fix_days,
         r.reported_at >= current_timestamp() - INTERVAL 365 DAYS AS last12
  FROM gold.reports r JOIN gold.properties p ON p.property_id = r.property_id),
per_bldg AS (SELECT owner_id, property_id, COUNT(*) AS n FROM r WHERE last12 GROUP BY 1, 2),
agg AS (
  SELECT owner_id,
         SUM(CASE WHEN status IN ('open','escalated') THEN 1 ELSE 0 END) AS open_issues,
         SUM(CASE WHEN last12 THEN 1 ELSE 0 END) AS issues_last_12mo,
         percentile_approx(fix_days, 0.5) AS median_days_to_fix,
         SUM(CASE WHEN fix_days <= 30 THEN 1 ELSE 0 END) /
           NULLIF(SUM(CASE WHEN fix_days IS NOT NULL OR status IN ('open','escalated') THEN 1 ELSE 0 END), 0) AS pct_fixed_within_30d,
         SUM(CASE WHEN last12 AND severity = 'emergency' THEN 1 ELSE 0 END) AS emergency_issues
  FROM r GROUP BY owner_id)
SELECT u.owner_id, u.buildings, u.units, COALESCE(a.open_issues, 0) AS open_issues,
       COALESCE(a.issues_last_12mo, 0) AS issues_last_12mo,
       ROUND(COALESCE(a.issues_last_12mo, 0) / u.units, 3) AS issues_per_unit,
       ROUND(a.median_days_to_fix, 1) AS median_days_to_fix, ROUND(a.pct_fixed_within_30d, 3) AS pct_fixed_within_30d,
       (SELECT COUNT(*) FROM per_bldg b WHERE b.owner_id = u.owner_id AND b.n >= 3) AS repeat_buildings,
       COALESCE(a.emergency_issues, 0) AS emergency_issues,
       COALESCE(a.emergency_issues, 0) / u.units AS emerg_pu
FROM u LEFT JOIN agg a ON a.owner_id = u.owner_id WHERE u.units > 0;

-- COMMAND ----------
CREATE OR REPLACE TEMP VIEW z AS
SELECT *,
  (issues_per_unit - avg(issues_per_unit) OVER ()) / NULLIF(stddev_pop(issues_per_unit) OVER (), 0) AS z1,
  (COALESCE(median_days_to_fix, percentile_approx(median_days_to_fix, 0.5) OVER ()) - avg(median_days_to_fix) OVER ())
     / NULLIF(stddev_pop(median_days_to_fix) OVER (), 0) AS z2,
  (-COALESCE(pct_fixed_within_30d, 1) - avg(-COALESCE(pct_fixed_within_30d, 1)) OVER ())
     / NULLIF(stddev_pop(-COALESCE(pct_fixed_within_30d, 1)) OVER (), 0) AS z3,
  (emerg_pu - avg(emerg_pu) OVER ()) / NULLIF(stddev_pop(emerg_pu) OVER (), 0) AS z4
FROM base;

INSERT OVERWRITE gold.landlord_scores
SELECT owner_id, buildings, units, open_issues, issues_last_12mo, issues_per_unit, median_days_to_fix, pct_fixed_within_30d,
       repeat_buildings, emergency_issues, ROUND(score, 3) AS score,
       CASE WHEN score < -0.5 THEN 'A' WHEN score < 0 THEN 'B' WHEN score < 0.5 THEN 'C' WHEN score < 1.0 THEN 'D' ELSE 'F' END AS grade
FROM (SELECT *, 0.35 * COALESCE(z1, 0) + 0.35 * COALESCE(z2, 0) + 0.20 * COALESCE(z3, 0) + 0.10 * COALESCE(z4, 0) AS score FROM z);

-- COMMAND ----------
SELECT grade, COUNT(*) FROM gold.landlord_scores GROUP BY grade ORDER BY grade;
SELECT * FROM gold.landlord_scores WHERE owner_id = 'O-DEMO';
