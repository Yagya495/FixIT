-- Databricks notebook source
-- Additive migration only. Run on the fixit profile/workspace after approval.
-- No changes to existing case/call/deadline tables; no reset, no data backfill.
CREATE TABLE IF NOT EXISTS fixit.silver.retell_calls (
  attempt_id STRING NOT NULL,
  request_id STRING NOT NULL,
  provider_call_id STRING,
  to_number STRING,
  status STRING,
  context_json STRING,
  consent_json STRING,
  transcript STRING,
  outcome_json STRING,
  disconnection_reason STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
) USING DELTA
COMMENT 'Authorized Retell test-call attempts, consent, transcripts and unreviewed outcomes. Keep across demo resets.';
-- Existing App SP schema grants SELECT/MODIFY on fixit.silver cover this table.
-- Delta does not enforce unique keys. Use the existing single-worker App for this integration.
