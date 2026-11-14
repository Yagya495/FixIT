# PROGRESS.md

_Last updated: 2026-11-14_

## Status: Milestones 2–6 built **locally**; Databricks wiring not yet verified (Milestone 1 blocked on credentials)

The whole P0 demo flow runs end to end on the local backend (SQLite + Demo Mode fallbacks) and is covered by an
automated end-to-end test. The Databricks side (notebooks, SQL-warehouse backend, Volumes, Vector Search, Genie
client, App bundle) is written but **has not been run against a workspace yet**.

## Done
- [x] `CONTEXT.md`, repo scaffold, `.env.example`, Makefile, README
- [x] Dual data layer (`db.py`): SQLite ↔ Databricks SQL warehouse, one SQL code path with `:named` params
- [x] P0-2 taxonomy (11 types) + **unverified** seed code sections (placeholder ids `CH27-*`, labeled in the UI)
- [x] P0-12 synthetic Madison dataset (≈250 owners, 2,004 properties, ≈12k reports, seasonality, demo story:
      `1234 DEMO ST`, 6 open heat reports in 7 days, owner grade **D**, 3 other buildings with **11** open issues)
- [x] P0-10 landlord scores (Python + SQL twin), report cards, building pages with timeline + map
- [x] P0-1 code matching: BM25 fallback (all taxonomy types hit top-3), Vector Search client path
- [x] P0-3 vision pipeline: strict-JSON prompt, Pydantic validation, one retry, threshold labels, dedup, MLflow-free for now
- [x] P0-4 Listing X-Ray: verdict rules, building history, tour questions, lease addendum (+PDF)
- [x] P0-5 evidence locker: SHA-256, hash-named storage (local dir / UC Volume), verify endpoint, evidence packet PDF
- [x] P0-6 repair letter with tone slider (friendly / formal / final notice), copy/PDF/mark sent
- [x] P0-7 simulated AI call: AI disclosure first, code citations, handles date/vague/refusal/hostile/"talk to tenant",
      browser TTS + speech-to-text, scripted demo lines, LLM extraction with a regex fallback
- [x] P0-8 deadlines: FixIt default windows, countdown, "Simulate +8 days", escalation → pre-filled complaint (never submitted)
- [x] P0-9 collective match + joint complaint (anonymized Unit A, B, …)
- [x] P0-11 "Ask the data": Genie Conversation API client + local SQL answers for all 8 sample questions
- [x] P0-13 Demo Mode: vision cache by SHA-256, scripted scenario fallback, call script, `/api/demo/reset`, `/api/demo/warm`
- [x] React UI: Home, Listing X-Ray, Scan (live camera + photo/video upload with client-side 1 fps sampling), Case,
      My cases, Landlords, Owner, Building, City (map + inspect-next + Genie), About
- [x] Notebooks: 00 smoke, 01 catalog, 05 synthetic, 10 parse, 11 vector index, 20 taxonomy, 30 DDL + DQ checks, 40 scores, 70 Genie
- [x] Tests: 36 passing (`make test`): code matching, deadline math, commitment parsing, hashing, dedup, scoring,
      address matching, collective, verdict + full API end-to-end
- [x] Sidecar skeleton with hard allowlist + kill switch for P1 calls

## Next
1. **Milestone 1 on Databricks** (needs inputs below): run `00_smoke_tests`, pick endpoints, create catalog, deploy the bundle,
   grant the SP, and flip `DATA_BACKEND=databricks`.
2. Parse the real Chapter 27 PDF → replace placeholder section ids (`20_violation_taxonomy` remap cell, human-reviewed).
3. Put the real demo photos in `demo/demo_inputs/`, run `/api/demo/warm`, and commit the cache.
4. Add MLflow tracing to vision/LLM calls.
5. Full 3-minute dry run ×3 (Demo Mode on and off), then P1 in spec order.

## Known issues / deviations
- Code section numbers are **placeholders** until Ch. 27 is parsed. The UI says "section number pending verification".
- Arrays are stored as JSON strings and booleans as INT 0/1 in Delta (keeps one SQL path for both backends).
- `20_violation_taxonomy` is `.py`, not `.sql`, so it can reuse `taxonomy.py`.
- Demo Mode walkthrough fallback returns the scripted staged-corner detections for **any** uncached frame. That's intentional for
  the stage, but turn `DEMO_MODE=false` for honest testing.
- `DATA_BACKEND=databricks` paths (warehouse inserts, Volume uploads, Vector Search query, Genie polling) are untested.
- Official city URLs in `config.OFFICIAL_LINKS` (report a problem, rent abatement) need a human to verify them.
- Bounding boxes are off by default (`SHOW_BBOXES=false`); thumbnails are shown instead.
- Frontend bundle is >500 kB (Leaflet + Recharts). Fine for the demo.

## Blockers / inputs needed from the human
- Databricks: confirm which workspace/CLI profile to use (an existing `sleepsafe` profile was found but not used),
  the SQL warehouse ID, and whether `CREATE CATALOG` is allowed (Free Edition).
- MGO Chapter 27 PDF + Minimum Housing Standards Checklist PDF + saved city pages (rent abatement, retaliation, reporting).
- Demo listing photos (staged or with permission) and staged walkthrough photos/clips.
- P1 only: Twilio SID/token/number and the consenting allowlist numbers.

## How to run
See README → "Run locally". Quick start: `make setup && make build && make api` → http://localhost:8000
