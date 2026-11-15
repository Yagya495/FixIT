# Targeted cleanup of 2026-11-15 deployment test records (PLAN, NOT EXECUTED)

> Needs the user's explicit authorization of this exact manifest. No full reset. Nothing has been deleted.

**Manifest:** `docs/ops/test_records_2026-11-15.json` · sha256 `7d71403caf8a93da…` (full value inside the file; the
script refuses to run if the file is edited).
**Script:** `scripts/cleanup_test_records.py` (dry run by default; dry run executed 2026-11-15: counts below match).

## What the deployment tests created (all on the disposable synthetic building 1770 Fair Oaks Ave, `P-00542`)
Found with read-only SELECTs. Nothing else was written to these tables since the deployment (07:00 UTC): no other scans
and no other repair requests.

| Table | Rows | Exact records |
|---|---|---|
| `silver.scans` | 9 | `S-5627707e19` (QA-1), `S-e086f1cb0b` (QA-2), `S-4abfa46677` (QA-3), `S-50b1a5a60b` (QA-4), `S-a017de26a3` (QA-5), `S-516dd3cfb9` (QA-6), `S-d0eab98c5d` (QA-7), `S-ef953c6211` (smoke listing), `S-6ef4f904bb` (QA-SMOKE) |
| `silver.evidence` | 81 | the frames/photos of those scans (ids in the manifest) |
| `silver.detections` | 26 | all detections of those 9 scans |
| `gold.violations` | 11 | findings of those scans (ids in the manifest) |
| `silver.repair_requests` | 1 | `RR-a1f14979d7` (the only item in "My cases") |
| `gold.reports` | 1 | `R-FX-a1f14979d7-0` (NO_HEAT at P-00542; makes that building show 1 open issue) |
| `silver.calls` | 1 | `C-39be884a24` (simulated call) |
| `silver.deadlines` | 1 | `RR-a1f14979d7` (status escalated, +8 simulated days) |
| `silver.complaints` | 2 | `CP-6c160d88f6` (escalation), `CP-01e4559cf2` (joint) |
| UC Volume `fixit/raw/evidence` | 56 files | content-addressed files used only by those 81 evidence rows (none shared with non-test evidence) |

## What is NOT touched
The demo building `P-DEMO-1234` and every synthetic report/owner/property; `gold.landlord_scores`; `silver.code_sections`
and `ref.violation_types` (the three approved citations); `code_sections_verified.json`; the Genie space and its saved
answers; any file referenced by a non-test evidence row. The script refuses if any listed record touches the demo
building, if counts differ from the manifest, or if a listed scan is not on the disposable building.

## Steps (after authorization)
1. Dry run again (read-only) and confirm the same counts.
2. `--apply --confirm <manifest sha256>`: records each table's current Delta version in `docs/ops/cleanup_log_<sha>.json`,
   deletes the listed rows (dependents first: complaints, deadlines, calls, reports, repair requests, violations,
   detections, evidence, scans), then the 56 unreferenced volume files, then re-counts (expect 0 remaining).
3. Verify on the App: "My cases" empty, 1770 Fair Oaks Ave back to 0 open issues, demo story unchanged (6 open at
   1234 Demo St; owner D, 0.916, 17 open), health shows 3 verified sections, 8 saved Genie answers unaffected.

## Undo
Rows: `RESTORE TABLE fixit.<schema>.<table> TO VERSION AS OF <recorded version>` per table. **Volume file deletes are not
reversible** (only test frames of synthetic drawings; the originals are in the local scratch folder). Alternative if
you prefer zero risk: delete only the rows and keep the 56 files (they are invisible without evidence rows).

## Smaller alternative
Only the case is visible in the demo. Deleting just `RR-a1f14979d7` and its dependents (`R-FX-a1f14979d7-0`,
`C-39be884a24`, its deadline, `CP-6c160d88f6`, `CP-01e4559cf2`) removes everything a viewer could see; the 9 scans and
their files are invisible without a case.
