# PROGRESS.md

_Last updated: 2026-11-15 (afternoon)_

> **Current status (2026-11-15):** deployed App = `ch27-review` @ `2c74f5d` (video walkthrough), but its compute is
> **STOPPED** ("workspace or account status"; see "App stopped + public demo prep" below). Speed change `003565b` and the
> public-demo / security commits are local-only on `ch27-review`, not deployed. Tests: **168 backend + 10 frontend
> passing**. The sections below are in chronological order; older headings describe their own date.

## Status (2026-11-14): P0 verified in a real browser (local + Demo Mode). Databricks Milestone 1 blocked on login (no CLI/profile on this machine)

The whole P0 demo flow runs end to end on the local backend and was driven through the real React UI in Chrome.
Bugs found in that pass are fixed and covered by tests. The Databricks side is written, statically reviewed and
hardened, but **has still not run against any workspace**: no Databricks CLI, `~/.databrickscfg` or `DATABRICKS_*`
env vars exist on this laptop.

## Done
- [x] `CONTEXT.md`, repo scaffold, `.env.example`, Makefile, README (+ Windows commands)
- [x] Dual data layer (`db.py`): SQLite ↔ Databricks SQL warehouse, one SQL code path with `:named` params
- [x] P0-1…P0-13 built (see CONTEXT §2). Seed code sections remain **unverified placeholders** (`CH27-*`)
- [x] Notebooks 00/01/05/10/11/20/30/40/70, sidecar skeleton (allowlist + kill switch for P1)
- [x] **2026-11-14 browser QA** (Chrome, real UI): listing X-Ray → scan → case → letter tones → simulated call →
      countdown → +8 days → escalation → joint complaint → landlords/owner/building → city map → Ask the data → about;
      console clean; no horizontal overflow at 390 px on any page
- [x] Seeded story validated on a fresh reset: 1234 Demo St has **6** open HEAT reports in the last 7 days (6 households,
      30 days), owner Isthmus Edge Properties (demo) grade **D**, 3 other buildings with **4 + 4 + 3 = 11** open issues.
      All 251 owners / 2,004 properties / 11,941 reports flagged synthetic
- [x] Demo Mode on **and** off tested locally (off: uncached photos give 0 detections with `source: none`, and the UI now says
      the model didn't respond instead of implying a clean room)
- [x] `docs/DEMO_CHECKLIST.md` (run sheet + real/synthetic/simulated table), `docs/DATABRICKS_SETUP.md` (runbook)
- [x] `scripts/dbx_check.py` (workspace probe: read-only by default, refuses `sleepsafe`, nonce/random-color model tests,
      SQL read + optional write/delete test), `scripts/bundle.py` (cross-platform `make bundle`; bundle boots with the
      Apps entry point `uvicorn backend.main:app` and serves UI + API)
- [x] Tests: **44 passing** (`pytest -q app/backend/tests`)

### Fixed this session (all with tests where testable)
| Problem | Fix |
|---|---|
| Call confirmed **Friday** when the landlord said "busy this week… Thursday" | Explicit weekday/date beats vague week phrases |
| Call answered "what's the problem?" with "I understand you're busy" | Restates the issues; "busy" only when said; no "Yes," to "who's calling?" |
| LLM extraction could override the date the AI confirmed aloud | Confirmed-on-call date always sets the deadline; `commitment_source` recorded |
| **Same photo in two scans → HTTP 500** (rehearsals reuse photos) | Detection ids include scan + frame; duplicate file in one scan reuses evidence |
| Joint complaint dated Unit A with the simulated "+8 days" clock | Uses the real report date |
| City map tiles said "API KEY REQUIRED" (CARTO) | OpenStreetMap tiles |
| Leaflet attribution drew over the sticky nav | Map is its own stacking context |
| Nav showed a scrollbar on phones (`no-scrollbar` class never defined) | Defined it |
| Unverified seed text shown **in quotes** like ordinance text | "Plain-language summary, not official text" until verified |
| Vector Search hits auto-marked `verified` | Use the table's flag; automatic matches never shown as verified |
| "Ask the data" labeled "Databricks Genie" while answering from local SQL | Caption says what answered (live Genie / saved Genie / prepared SQL) |
| About page claimed Vector Search, MLflow, risk model, dashboard as running | Status chips computed from `/api/health` (running / fallback / planned P1) |
| "Report a problem" link silently redirected to the generic BI home page | Official interior-property complaint form (see below) |
| Final-notice letter said tenant "may apply for rent abatement" | "may seek… if uncorrected after the city's inspection deadline" |
| `DATABRICKS_HOST` without `https://` (as Apps may inject) broke every live call → silent cache fallback | Host normalized |
| CLI profile (`DATABRICKS_CONFIG_PROFILE`) ignored → live calls never attempted locally | Recognized for models, Genie and the warehouse connection |
| ISO strings written to Delta TIMESTAMP columns | Bound as datetimes on the Databricks backend (untested against a warehouse) |
| Smoke test vision check (solid red, "what color?") passable by a text model | Random color + nonce checks (notebook and script) |
| Silent failures / blocking `alert()` on call, deadline, joint, scan actions | Inline error messages |
| Windows: evidence paths with backslashes (1 test failed) | POSIX paths |

## Milestone 2: accuracy, honesty, demo readiness (2026-11-14, in progress)
Done (no P1 features started):
- **Chapter 27 workflow ready, not run** (no PDF yet). Official source = MGO Ch. 27 on Municode (the City's own "minimum
  housing ordinance" link). `ai_parse_document` output shape verified on this warehouse with a fake fixture (deleted);
  section-split SQL verified on fixture rows. `scripts/code_parse.py upload → parse → propose → (human fills
  eval/code_review.csv with a reviewer) → approve`. **Fixed:** notebook 10 marked every parsed section `verified=1` and
  wiped the seed rows: now `verified=0`, seeds kept, page headers/footers dropped; resets keep approved mappings
  (`app/backend/code_sections_verified.json`). UI distinguishes FixIt summary / official text pending review / verified.
- The "Minimum Housing Standards Checklist" PDF URL now redirects to the BI home page (gone). The current official list
  is the Common Code Violations page ("some of the common issues").
- **Vision eval ready:** `scripts/eval_vision.py` (live only, never cache/Demo Mode, strips JPEG EXIF) +
  `eval/README.md` (what to stage, privacy, decision rules). Mechanics verified on 3 synthetic images (results discarded:
  not an evaluation). **Needs real/staged photos.**
- **Fixed: Demo Mode cache never matched browser uploads** (warm hashes the file on disk; the browser re-encodes).
  The browser now sends the original file's SHA-256 too (test added).
- **Fixed: Delta write conflict → HTTP 500** on the Databricks backend (reading a case UPDATEd the deadline while the call's
  own UPDATE ran). Reads no longer write; UPDATE/DELETE retry on Delta concurrency conflicts (test added).
- **Fixed: double-clicking "Demo line"** sent duplicate lines / hit a closed call ("call not found"). Synchronous guard;
  20 rapid clicks → exactly 3 lines, no error (browser-verified).
- **Source labels**: Listing/Scan show "Analyzed live just now by llama-4-maverick…", "Saved result…", or "Demo script…";
  call shows whether extraction was live; Genie caption; Scan says "No possible issues spotted in N photos" after a live
  empty result (was "Nothing yet").
- **Not-official wording**: "Final request" (not "Final notice": the City issues Official Notices); "Follow-up deadline /
  Promised date passed" + "not a legal deadline"; "DRAFT … not submitted, not an official document"; joint draft says
  neighbors haven't agreed; evidence packet "NOT an official inspection record"; "only a City inspector can determine a
  code violation" on Listing/Scan.
- `docs/DEMO_SCRIPT.md`: 3-minute Databricks-focused script, words to avoid, recovery table, manual checklist for the App.
- Browser-verified on a deployment-equivalent local build (Databricks backend + live models + Genie + Demo Mode).
  The deployed App itself needs the user's OAuth "Continue" (not clicked by the agent).

Needs the user: staged photos for eval + stage · manual checklist on the App/phone.

### Chapter 27 ingested and PROPOSED mappings ready for review (2026-11-14 evening; nothing verified)
- PDF: `docs/legal/Madison_Chapter_27.pdf` (user's Municode export, 41 pp, §27.01–§27.13, newest amendment ORD-24-00056;
  sha256 `7feae63e…e1ff4516`, identical to the user's original). Checked for prompt injection / hidden text: none (no
  invisible or white text, no JS; 78 links, all Municode).
- `code_parse.py upload` → `/Volumes/fixit/raw/code_docs/` · `parse` → `ai_parse_document` found the same 17 sections as a
  local decode of the PDF · `propose` → `eval/code_review.csv`. **Parsed sections go to a staging table
  `fixit.bronze.code_sections_parsed`** (new): the App reads only silver/ref (its SP has no bronze grants), so the deployed
  App and local fallback are unchanged; `silver.code_sections` still has only the 10 seed rows, 0 verified.
- Fixed before running: section regex folded 27.051/27.085/27.101 into 27.05/27.08/27.10 (now 2–3 digits after the dot,
  heading form `27.xx - TITLE`). `approve` now copies only approved rows from the excerpt-checked proposals, merges with
  earlier approvals instead of overwriting them, and supports subsection ids. Notebook 10 aligned.
- Review sheet: **`docs/legal/CH27_REVIEW.md`** (+ CSV), generated by `scripts/ch27_review_sheet.py` from
  `docs/legal/ch27_proposed_mappings.json`; every excerpt is machine-checked verbatim against the Databricks parse
  (`docs/legal/ch27_parsed_sections.json`) and the PDF text layer, with the page computed from the PDF.
- Not established by Ch. 27: **carbon monoxide** (not mentioned at all), **mold** (not mentioned), **smoke alarms**
  (27.05(2)(w) only incorporates MGO 34.907 + SPS codes). Placeholder summaries CH27-SMOKE / -MOISTURE / -ELECTRICAL /
  -WINDOWS overstate the ordinance (listed in the sheet; not changed).
- Parse defects (not quoted): 27.05(2)(h)7. lines out of order; 27.05(2)(x) dropped words.
- **Next (user):** review the sheet, fill `approved_section_ids` + `reviewer`, then `approve` (dry run first), then redeploy.

### Fixed (in code, NOT yet deployed): demo owner grade depended on the time of day the data was generated
- Was: D at 09:00 / 17:00 on 11-14, **F at 21:15 on 11-14 and noon on 11-20**; `test_e2e::test_full_demo_flow` failed.
- Root cause: one shared RNG. Background report dates are rejection-sampled by calendar month, and the dates are
  counted back from `now`, so the number of draws depended on the clock. The hand-crafted demo history is drawn
  *after* that loop, so it got entirely different repair durations each time (median days-to-fix 22 → 41), and its
  score crossed the F cut (1.0). The background barely changed (7 of 11,941 reports differed an hour apart).
- Fix (`synthetic.py`): generate at a fixed `REFERENCE_NOW` (2026-11-14 12:00) and shift every timestamp by
  `now − REFERENCE_NOW` (identical data relative to `now`), and give the demo story its own RNG stream. Scoring
  (`landlords.py`, notebook 40) unchanged. Demo owner now always **D (score 0.916)**, 6 open heat, 11 open elsewhere.
- Tests: `app/backend/tests/test_synthetic.py` (19: 14 times incl. midnight, DST, year end, leap day, summer; whole
  dataset identical relative to now; demo story independent of background size; local seed end to end at 21:15).
  16 of them fail on the old generator. Suite: **70 passed**.
- **Applied 2026-11-14 ~21:30–22:00 (approved):** pre-reset inventory showed only the user's test rows would be removed
  (2 scans, 19 evidence rows, 21 detections, 2 repair requests, 15 app-written reports, all at 1234 Demo St; 0
  non-synthetic owners/properties). Databricks reset with the fixed generator → 6 / D / 11 / 0. 8 Genie answers
  re-captured live (one needed a longer timeout). Redeployed `fixit-madison` (profile `fixit`), smoke test 11/11 PASS,
  reset again to clean, then `scripts/genie_verify.py` → 8/8 saved Genie answers match a fresh run of their SQL
  (one re-captured after the second reset, then the App redeployed with it). Local server restarted + reset: D (0.916),
  6, 11, 0. Workspace resource snapshot before/after identical. The user's 19 uploaded photo files remain in
  `/Volumes/fixit/raw/evidence/` (reset never deletes files).
- Known: Genie's own SQL can use calendar days/years, so a reset at a different time of day can move a saved answer
  slightly (seen once: one value in row 23 of 43). After any reset run `scripts/genie_verify.py`; re-capture if needed.

## Milestone 1 on Databricks: DONE (2026-11-14, approved by the user, profile `fixit` only)
**Deployed App:** https://fixit-madison-7474647207905142.aws.databricksapps.com (workspace sign-in required)

| Step | Result | Evidence |
|---|---|---|
| Catalog | ✅ dedicated `fixit` catalog created (no fallback needed) | `scripts/dbx_setup.py --apply` |
| Schemas / volumes / tables / views | ✅ 6 schemas, 6 volumes, 14 tables, 2 views; DQ checks all 0 on loaded data | same |
| Synthetic data | ✅ 251 owners, 2,004 properties, 11,941 reports, 139 scores, 11 types, 10 seed sections | row counts = generator output |
| Demo story on Databricks | ✅ 6 open HEAT (7 d) · grade D · 11 open in 3 other buildings · 0 non-synthetic rows | story check |
| Warehouse write test | ✅ insert → read back → delete in `fixit.silver.deadlines` | `dbx_check.py --write-test` |
| App flow with `DATA_BACKEND=databricks` (laptop) | ✅ listing (vision live) → scan → evidence in `/Volumes/fixit/raw/evidence/` (hash verified) → case → live call extraction (Thu Nov 19) → escalate → joint (7) | rows in all silver tables, TIMESTAMP-typed |
| Genie space | ✅ "FixIt Madison — Ask the data" `01f1e089ff07126aac09984f839aaef1`, 6 tables, instructions, 8 sample questions | live answers for all 8 cached in `demo/cached_outputs/genie/`; 66 open emergencies = local SQL |
| App `fixit-madison` | ✅ deployed, "App started successfully"; compute MEDIUM (default, Free Edition quota) | `apps deploy` |
| App resources | sql-warehouse CAN_USE · databricks-llama-4-maverick CAN_QUERY · Genie space CAN_RUN | `app/app_create.json` |
| SP grants (minimum) | USE CATALOG fixit · USE SCHEMA+SELECT+MODIFY on silver, gold · USE SCHEMA+SELECT on ref · USE SCHEMA on raw · READ/WRITE VOLUME on raw.evidence only | `scripts/grant_app_sp.py`, verified with SHOW GRANTS |
| Deployed end-to-end (as the SP) | ✅ all 11 steps pass: health, UI, listing (vision **live**), scan, evidence in UC Volume, case + collective, call (extraction **live**), escalate, joint, PDF, Genie | `scripts/app_smoke.py` |
| Live Genie via the App SP | ✅ free-form question answered by Genie (`source=genie`, 17 s) | |
| Reset | ✅ `dbx_setup.py --only reset --apply` clears app rows and reloads the story | run after the smoke test |

Latency (warm warehouse): case page 1.7–2 s, owner 1.5 s, map 0.6 s. Cold warehouse adds ~10 s to the first calls:
open the App a few minutes before presenting. Live Genie takes 17–24 s, so Demo Mode serves the saved Genie answer
instantly (caption says "Saved answer from Databricks Genie").

**Not available / skipped on Free Edition:** Claude endpoints (not offered here; using Llama 4 Maverick); Vector Search
endpoint not created (skipped by decision until the Ch. 27 PDF is verified; BM25 fallback in use). No paid features
were enabled; no upgrade prompts were encountered.

**Deploy gotcha:** `databricks sync` respects `.gitignore`; `build/` is ignored, so it silently uploaded nothing and the first
deploy failed ("no files found"). Fixed by `databricks workspace import-dir` (docs + Makefile updated).

**Browser:** opening the App shows a Databricks "Authorize as…" OAuth prompt the first time; the agent stopped its
auto-continue and did not authorize it. The user should open the URL and click Continue.

## Model/endpoint checks (read-only, 2026-11-14)
Workspace `https://dbc-bae64bde-0c7f.cloud.databricks.com`, **Free Edition** (per the user). Databricks CLI v1.26.0.

| Feature | Result | How verified |
|---|---|---|
| Auth (OAuth via CLI profile `fixit`) | ✅ | SDK + SQL connector authenticated; only profile on this machine |
| SQL warehouse `6361516ab33ba2d2` "Serverless Starter Warehouse" (2X-Small) | ✅ | Started on demand (~3 s); `:named` params; Python datetime binds as `timestamp` |
| Chat: `databricks-llama-4-maverick`, `gpt-oss-120b`, `llama-3-3-70b`, `qwen3-next-80b`, `gemma-3-12b` | ✅ | Each echoed a random nonce. `qwen35-122b` returned an empty reply ❌ |
| Vision: `databricks-llama-4-maverick`, `databricks-gemma-3-12b` | ✅ 3/3 random-color trials each | + FixIt's real strict-JSON prompt: valid output, 0 false positives on a blank image. `llama-3-3-70b`, `qwen35-122b`: "Image input is not supported" ❌ |
| Embeddings: `gte-large-en`, `bge-large-en`, `qwen3-embedding-0-6b` | ✅ 1024 dims | |
| Commitment extraction (app code, live) | ✅ `source=live` | maverick returned 2026-11-19T17:00 (Thursday), matching the state machine |
| AI Functions on the warehouse: `ai_query`, `ai_classify`, `ai_extract` | ✅ | Correct answers (PESTS; {"repair":"fix the heat","date":"Thursday"}) |
| `ai_parse_document` | ✅ exists | Not yet run on a PDF (needs the Ch. 27 PDF) |
| Genie API | ✅ reachable | 1 existing space ("Bakehouse Sales Starter Space"), not ours, untouched |
| Vector Search | ⚠️ no endpoint exists | Creating one is optional; code matching falls back to BM25 |
| Databricks Apps | ✅ API reachable, 0 apps | |
| Catalogs | `system`, `samples`, `workspace` | `CREATE CATALOG` is granted to the account group `_workspace_admins_…`; the user is in workspace `admins` but `is_account_group_member` returned **False** → may be denied. Fallback: `--catalog workspace` |
| Claude endpoints | ❌ none in this workspace | Defaults switched to `databricks-llama-4-maverick` (chat + vision) |

**Not yet verified:** detection quality on real problem photos (needs staged photos), table writes, Volumes, Genie
over FixIt tables, App deployment, service-principal permissions.

## Chapter 27: first three citations verified and deployed (2026-11-14, night; approved by the user)
- **Reviewer:** the project's Legal Reviewer personally reviewed against the official Chapter 27 (Municode, Sep 1, 2026) and explicitly
  approved:
  - `LEAK_PLUMBING` → §27.05(2)(j)
  - `NO_HEAT` → §27.04(2)(h) (67°F + occupant exception)
  - `DAMAGED_SURFACES` → §27.05(2)(g)1.
- **Sequence (each step verified before the next):**
  1. Dry run: exactly 3 mappings, checked excerpts, reviewer present.
  2. 88 tests and the type-check pass.
  3. Branch diff reviewed: no changes to the database layer, seeding, scan/vision, calls or Genie.
  4. Rollback point recorded (below).
  5. **Deployed the reviewed code first** (`01f1e0b3…`), with "Possibly relevant code" wording and the City-inspector line
     confirmed live, 0 verified sections.
  6. Then `code_parse.py approve --apply`: database holds exactly the 3 verified rows with the exact checked text; the
     other 8 categories unchanged.
  7. Data reset: the approvals survived; CO moved to the "legal source not yet verified" placeholder.
  8. Redeployed (`01f1e0b369…`) to restart the app (it had cached the citation table) and bundle the approvals file.
  9. Live check on a test case: the 3 approved categories return `verified=true`, the right section, page and exact
     excerpt; smoke, CO, water damage and exits stay unverified; the letter cites "MGO § …" under "Possibly relevant
     code" with "may violate" framing and the disclaimer.
  10. Smoke test 11/11, then reset to clean: 6 / D (0.916) / 11 / 0, app tables empty.
  11. Genie 5/8 matched after the reset (date windows shifted past midnight UTC); 3 refreshed live → 8/8.
  12. Redeployed (`01f1e0b4…`) with the refreshed answers.
  13. 89 tests pass, none skipped. One test now always runs (it used to skip when approvals exist); one new test locks
      the approved state.
- **Rollback:** git tag `deploy-pre-ch27-2026-11-14` (cef6822 = deployment `01f1e0a5dc26…`). Delta: `silver.code_sections`
  v11, `ref.violation_types` v7 → `RESTORE TABLE fixit.<t> TO VERSION AS OF <v>`, delete
  `app/backend/code_sections_verified.json`, redeploy the tag.
- **Not done:** no merge into `main`; the local fallback (:8000) still runs the older code and data; the smoke/CO legal
  deadline stays disabled; no P1 work.

## Consolidated legal review of the remaining 9 categories (2026-11-14, late; preparation only)
- Report: **`docs/legal/FINAL_LEGAL_REVIEW.md`**. Nothing approved, activated or deployed; reviewer fields blank; no
  `approve --apply`; no Databricks changes; five-day alarm deadline still hard-disabled.
- Recommendations: **READY FOR HUMAN REVIEW** locks, windows, pests, electrical (§27.04(2)(g) only), water damage ·
  **NEEDS CLARIFICATION** exits, smoke alarms, CO alarms · **NO VERIFIED SOURCE** mold, electrical cover plates.
- Sources: Wis. Stats. 101.01/.145/.149/.61/.645/.647, 704.07 and SPS 320/321/328/361/362/366/316, ATCP 134.04 read in
  full on docs.legis.wisconsin.gov (statutes current through 2025 Act 247, published 11-4-26). City BI Common Code
  Violations + Mold/Pests/Smoke-CO pages, Fire Dept. and Public Health pages fetched. Live Municode blocked scripts
  (Cloudflare; not bypassed), so MGO 34.907/29.22 were not re-read. All 26 Ch. 27 excerpts re-verified against an
  independent pypdf extraction of the official PDF (hash unchanged).
- Four new source discrepancies recorded (not interpreted): §27.04(2)(d) → "SPS 321.04(2)" (handrails now in (3));
  §27.05(2)(w) → "SPS 328.02" (now *Scope*); "single-family dwelling" undefined; statute note → "SPS 321.095" (CO is
  321.097). New fact: 101.01(12) "public building" includes use "by 3 or more tenants".
- Code (commit `87df616`, local): cautious wording for smoke (no building-independent requirement, no unsupported
  locations), CO, cover plates, mold (City BI guidance), pests (City BI: photos not accepted as proof), locks, exits; tour
  question; alarm prototype surfaces 101.01(12) without evaluating it; Scan "Looking for possible issues…".
- Tests: 89 before → **94 passed** after (5 new: wording, exactly three approvals, blank reviewer fields, tour question,
  public-building note). Frontend type-check clean.
- Not changed (needs a decision): vision cues that treat an alarm's absence from a photo as a possible issue.
  **Done in round 2 below.**

## Round 2: user decisions applied locally (2026-11-14, later; nothing deployed, nothing approved)
- **Photo detection (priority; `0e5eead`, `d6d2fcc`):**
  - No smoke/CO finding from absence: the prompt, the cues and `vision.screen_detection` all enforce it.
  - Basis on each observation: visible condition / verify in person / tenant report.
  - New tenant buttons "Report smoke/CO alarm missing / not working".
  - Per-photo evidence (`observations`); repeat uploads add nothing and make no model call; building reports
    de-duplicated per unit and type; legacy absence rows excluded on read.
  - Demo cache's "no smoke detector in frame" replaced by a visible empty base plate.
  - 22 tests (`test_detection.py`, synthetic clean-room and alarm images).
- **Legal prep (inactive; `1351d0c` + docs):**
  - §27.05(2)(i) moved out of exits into a separate conditional proposal (unsafe stairs only).
  - (g)1. "waterproof" sentence and (k) bathroom floors added as conditional proposals.
  - `conditional_citations.py`; `state_law.py` (disabled; 4 statute excerpts verified verbatim).
  - `HUMAN_REVIEW_CHECKLIST.md`, `STATE_LAW_DESIGN.md`, `CITY_INQUIRY_DRAFT.md` (not sent).
- Tests: 94 → 116 (detection) → **133 passed** (legal prep). Frontend `tsc -b` clean.
- Not verified: the UI changes in a real browser; live model accuracy on real photos.

## Video walkthrough verified end to end (2026-11-15; local, not deployed)
- Live test: headless Chrome against the Scan page (Vite dev) and a scratch local backend with DEMO_MODE=false,
  calling the live Llama 4 Maverick endpoint (profile `fixit`, inference only; no Databricks data touched).
  Synthetic drawn videos: 12 s MP4, 12 s WebM (duration reported as Infinity), 40 s WebM; desktop 1280px and phone
  emulation (iPhone 13 viewport, Chrome engine); live-camera still capture with Chrome's fake camera. All frames
  "live"; the uncovered outlet was found in 3 (or 8) consecutive frames and consolidated into one finding citing exactly
  those frames; the case evidence packet flags the same frames. The drawn ceiling stain was never detected.
- Fixed: WebM recordings with unknown duration were sampled 30 times past the end ("30 frames analyzed" for 13 real
  frames); videos over 30 s only covered the first 30 s (now 30 frames spread over the whole video); seeks could hang;
  all frames went in one long request (now batches of 5 with progress, 2 parallel model calls per batch, frames stored in
  order); a 429 from the endpoint lost the frame (now bounded retry); partly failed analysis was labeled "live" (now
  "partial" with counts); no in-app way to record (new "Record a walkthrough video" input, `capture="environment"`).
- Tests: backend 133 -> 148 (`test_video_walkthrough.py`); new frontend unit tests (`npm test`, Node test runner, 10).
- Not verified: a real iPhone/Android device (Safari/WebKit not tested; HEVC .mov may not decode in desktop Chrome);
  real apartment footage accuracy. Local live mode needs the Databricks CLI on PATH (winget install isn't on PATH here).

## Video walkthrough deployed (2026-11-15; user-approved code-only deploy, profile `fixit`)
- Pre-checks: backend 148 passed, frontend 10 passed, `tsc -b` clean. Diff vs deployed `aeb7598`: no change to
  `code_sections_verified.json`, `app.yaml`, requirements, demo cache, `code_match.py`, `db.py`, `seed.py`; the three
  approved categories untouched in `taxonomy.py`; `conditional_citations` / `state_law` not imported by the app;
  `LEGAL_DEADLINE_DISPLAY_ENABLED` and `STATE_LAW_DISPLAY_ENABLED` False; no citation/disclaimer line changed in the UI.
- Deployed `2c74f5d` → deployment `01f1e0c4e722…` ("App started successfully"). Rollback tag `deploy-pre-video-2026-11-15`
  (`aeb7598`, deployment `01f1e0b44278…`). Gotcha: in Git Bash set `MSYS_NO_PATHCONV=1`, or `/Workspace/...` is rewritten
  to a Windows path and `import-dir`/`apps deploy` fail. The Databricks SDK's CLI auth needs the winget CLI dir on PATH.
- Deployed-App tests (headless Chrome; auth header added only to same-origin requests; disposable synthetic building
  1770 Fair Oaks Ave, P-00542, units QA-1..QA-7):
  - 12 s MP4 desktop / 12 s WebM phone-size / 40 s WebM / "Record a walkthrough video" input: 12 / 11 / 30 / 12 frames,
    every frame `live` (Llama 4 Maverick), batches of 5 with progress ("Extracting frames…", "Analyzing frames 1–5 of
    12…"), outlet consolidated into 1 finding citing exactly its 3 / 3 / 8 / 3 frames, no page errors, no horizontal
    overflow. The drawn ceiling stain was not detected (model limitation on synthetic drawings).
  - App logs: 7 × HTTP 429 from the endpoint during the runs, all retried; zero "vision live call failed".
  - Citations: NO_HEAT → 27.04(2)(h), LEAK_PLUMBING → 27.05(2)(j), DAMAGED_SURFACES → 27.05(2)(g)1. (verified, official
    text); EXPOSED_WIRING → unverified summary. Synthetic-data labels present on Building, Landlords, Listing, City.
  - `scripts/app_smoke.py` (new optional `--address/--unit`): **11/11 PASS** on 1770 Fair Oaks Ave unit QA-SMOKE.
    Demo story unchanged before/after (6 open at 1234 Demo St; owner D, 0.916, 17 open).
- **Records the tests left in the deployed data (not cleaned up; cleanup needs the user's approval):**
  - My cases: 1 repair request `RR-a1f14979d7` (1770 Fair Oaks Ave, QA-SMOKE) with its building report (P-00542 open
    issues 0 → 1), simulated call, deadline (escalated) and 2 complaints (escalation + joint).
  - Scans (not shown anywhere without a case): 2 smoke scans + 7 test scans (QA-1..QA-7) with ~80 frame images in the
    UC Volume `raw/evidence` and their detections/violations.

## Demo stabilization (user, 2026-11-15): current plan
- **Test-record cleanup, prepared, NOT executed:** read-only inventory found exactly 9 scans, 81 evidence rows, 26
  detections, 11 findings, 1 repair request (+1 building report, 1 call, 1 deadline, 2 complaints) and 56 Volume files,
  all on the disposable building; nothing else written since the deploy. Plan `docs/ops/TEST_RECORD_CLEANUP_PLAN.md`,
  manifest `docs/ops/test_records_2026-11-15.json`, script `scripts/cleanup_test_records.py` (dry run matched; deletes
  only listed keys, records Delta versions, refuses on any mismatch or demo-building record). Awaiting authorization.
- **Real-phone checklist:** `docs/PHONE_TEST_CHECKLIST.md` (Android + iPhone, recording/upload, live source line, frame
  accuracy, HEVC/MOV, failures).
- **Performance:** `docs/DEMO_PERFORMANCE.md`. Deployed 12 frames ≈ 44–53 s, 30 frames ≈ 98 s (local 24 s / 56 s); the gap
  is sequential warehouse/Volume writes before the model calls. Proposed A+B+C (parallel storage, batched inserts, one
  duplicate check per batch): needs approval. Stage advice: 8–10 s clip, warm-up 5–10 min before, backup clip + photos.

## App stopped + public demo prep (2026-11-15, afternoon; new Claude account took over; nothing deployed)
- **Handoff check:** speed commit `003565b` (A+B+C) is committed and pushed but **not deployed** (deployed = `2c74f5d`).
  The test-record cleanup was already executed (`4ffa67b`). The ~40% speedup isn't recorded in the repo (only the 35–40%
  estimate in `docs/DEMO_PERFORMANCE.md`): re-measure before deploying.
- **App STOPPED** (read-only CLI): *"App compute was stopped due to workspace or account status"*, 13:52 UTC, ~6.5 h after
  the last deploy, so not the 24 h auto-stop. The workspace API, Model Serving (READY, answered a 3-token call) and the
  warehouse (normal auto-stop) are fine. Likely cause, not confirmed: the Free Edition daily fair-usage quota (docs:
  compute shut down for the rest of the day). Which usage hit it is unknown. Restore steps: `docs/PUBLIC_HOSTING.md` §1.
- **Public access:** Databricks Apps can't be anonymous. Recommended: the same app in `PUBLIC_DEMO=true` mode on Render's
  free plan (synthetic data, scripted/saved AI results labeled, no credentials). Live Databricks from outside isn't
  recommended (only the admin PAT is verified, and public traffic would burn the quota that stopped the App).
  `docs/PUBLIC_HOSTING.md`, `deploy/public/Dockerfile`, `render.yaml`. Not deployed; needs approval and a Render account.
- **Security:** path traversal in the SPA route (arbitrary file read, e.g. `/%2e%2e/%2e%2e/backend/config.py`; on
  Databricks Apps `/proc/self/environ` holds the app service principal's credentials) fixed and tested. **Still present
  in the deployed App** (only signed-in workspace users can reach it) until the next approved redeploy. Added upload limits
  (all modes) and a per-IP POST limit (public demo). Git history secret scan: clean.
- **Docs:** `docs/DEMO_SCRIPT.md` rewritten (3 verified citations, video beat, architecture, synthetic disclosure,
  fallbacks, quota warning); README test counts and public-demo section.
- Tests: 152 → **168 backend** (`test_public_hosting.py`, 16), 10 frontend, `tsc -b` clean.

## Reviewer name replaced by "Legal Reviewer" in public files (2026-11-15, user privacy decision; local, not pushed)
- Public files (approvals file `reviewers` values, review CSV, proposals' decision text, CH27_REVIEW, live check, docs,
  review-sheet generator, test) now say **"Legal Reviewer"**. Approvals unchanged: same three mappings, sections, exact
  text, `verified`, `review_meaning`. The approvals file gains a `reviewer_identity` note.
- The original identity is preserved in `.private/legal_review_audit.json` (git-ignored, docker-ignored, local only)
  and in git history (`e49ebfc`, `aeb7598`; history not rewritten).
- `scripts/code_parse.py approve`: a reviewer is still required. A **new** approval needs the reviewer's actual name
  (refuses the bare label); the name goes only to the private record and public files get the label.
- The app never displayed reviewer names (UI, API, letters, packet, addendum, complaints); the Databricks tables have no
  reviewer column. The deployed App's bundle still contains the old approvals file until the next approved redeploy.
- Regression test `test_reviewer_privacy.py` (5): all public-demo API responses and generated PDFs, every tracked file,
  approvals-file label, `.private/` never committed, approval-tool behavior. Mutation-checked: an injected name in the
  approvals file or a letter fails it. Tests: **173 backend**, 10 frontend.

## Next (user priority, 2026-11-15 afternoon: judges' access + running App)
1. **Restore the Databricks App** (owner approval): `apps get` → `apps start` once the quota resets → manual checklist.
2. **Public demo** (owner approval + Render account): push `ch27-review` → Render Blueprint → verify (`docs/PUBLIC_HOSTING.md` §8).
3. **One reviewed redeploy** of `ch27-review` HEAD: path-traversal fix + speed change (re-measure first). Restarts the 24 h clock.
4. **Real-phone test** (`docs/PHONE_TEST_CHECKLIST.md`) and **demo dry runs** ×3 with the new script.
- Paused: legal approvals/research, YOLO, real-data ingestion, Twilio, P1.

## Retell phone calls (2026-11-15; merged into `ch27-review`)
Committed on `feature/retell-ai` and merged into `ch27-review` with only the agent's files and lines. Always disabled when `PUBLIC_DEMO=true` (config clears all Retell settings; test added). Not deployed, no Databricks change (`notebooks/02_retell_calls.sql`
prepared, **not applied**).
- **Retell resources (created 2026-11-15 with the user's authorization):** one LLM and one agent ("FixIT — authorized landlord test calls", voice `retell-Nico`, gpt-4.1, temp 0.2,
  start_speaker agent). `scripts/retell_setup.py --check` passes against the live agent. Local `.env` (gitignored, mode
  600) holds the API key, agent ID and a generated operator token; `CALLS_ENABLED=false`; from-number and allowlist empty.
  The API key was pasted in chat: rotate it after testing.
- **What exists:** separate Retell panel on the Case page (`RetellCall.tsx`), operator-token-gated API
  (`routes/retell.py`), `services/retell.py` (kill switch + exact E.164 allowlist, four explicit consents, durable
  attempt saved before dialing, body idempotency key, provider preflight of the remote agent, polling for
  status/transcript/analysis, reconcile by verified metadata, stop, sticky opt-outs), dedicated prompt
  (`prompts/retell_landlord.md`), offline-first agent setup (`scripts/retell_setup.py`), new table
  `silver.retell_calls` (SQLite on startup; kept across demo resets). The simulated call is unchanged.
- **Review fixes against the official Retell API docs (this session):**
  - `start_speaker: "agent"` was missing from the LLM config (Retell describes it as required; outbound AI must speak
    first). Added in `llm_config()`, and the preflight now rejects a mismatched value.
  - Preflight reads the exact LLM version the agent pins and rejects an agent `webhook_url` (transcripts must not go to
    an unreviewed endpoint).
  - Opening no longer asserts "recorded with your prior consent"; it discloses the recording and asks for consent as its
    single question. The prompt now ends the call if the recipient declines, asks what the tenant must provide (e.g.
    access times) without agreeing to it, and ends the call on consent withdrawal.
  - Definitive first-request rejections (HTTP 400/401/402/403/404/422/429) are now `rejected` (no call, new attempt
    allowed) instead of a permanent `unknown`; a 400 mentioning do-not-call sets a sticky opt-out.
  - New operator **Resume**: re-sends the byte-identical stored request with the same idempotency key within 50 min
    (Retell documents 1-hour dedupe). A failed resume always stays `unknown`.
  - Any unexpected exception during create is treated as uncertain (never left half-recorded).
  - Analysis: enum fields for acknowledgement/appointment kind, optional string fields (`required: false`);
    grounding is punctuation-insensitive and whole-word; a grounded offer without a date keeps its kind; dates before
    the call day are dropped; opt-out phrases broadened ("take me off your list", "no more calls") and "never called"
    no longer counts as an opt-out.
  - Citations sent to the agent must also be in the human-approved mapping for that same issue type.
  - Non-ASCII operator token returned HTTP 500 (`compare_digest` on str); now 401.
  - UI: shows `rejected` and the Resume action; HTML/non-JSON responses (e.g. a sign-in redirect) give a clear error.
- **Tests (at merge):** backend **228 passed** incl. upstream suites; earlier in the Retell session: backend 203 passed (181 before this session's additions; Retell suite 29 → 51). Frontend `tsc -b` clean,
  production build OK, **10/10** frontend tests. Provider fully stubbed in all tests.
- **Mocked browser validation (headless Chrome, Playwright):** the real app on a scratch SQLite DB (port 8765,
  Demo Mode, no Databricks credentials, only Retell's HTTP layer stubbed), a scratch case with NO_HEAT
  (verified §27.04(2)(h) sent; no other citation). Passed: wrong token rejected; unlock; button disabled until all four
  consents; call → registered → refresh → ended with inspection/2026-11-17, grounded recipient quote, "no repair
  deadline was set automatically"; consents cleared and attempt not reusable; uncertain create → `unknown`, new call
  blocked → Resume re-sent the same idempotency key → linked; DNC 400 → `rejected` + blocked banner; next call to that
  number refused before reaching the provider; lock clears token; case deadline unchanged; history persists on
  reload; 390 px phone width: no horizontal overflow; no page/console errors.
- **Unverified (needs a live, consented test):** real Retell account/agent creation, the voice and prompt behavior,
  begin-message variable substitution, actual analysis quality, Retell's idempotency dedupe, stop-call on a live call,
  the exact error codes/bodies for DNC rejections, Databricks table creation, App secrets and outbound access to
  `api.retellai.com`, and any deployed behavior.
- **Live test call (2026-11-15, user-authorized, local app on 127.0.0.1:8001):** one call from the Retell number to
  the user's own allowlisted phone, case `RR-325122f1ff` (local SQLite; NO_HEAT + LEAK_PLUMBING). Worked end to end:
  AI identity, tenant authorization, test-call and recording disclosure, recording consent asked and given, case
  variables substituted, most urgent issue first; the user hung up after the first question. Outcome stored honestly
  (`not_discussed`, no appointment, follow-up needed, no opt-out); no deadline change. Prompt nits observed (user
  accepted as fine): one turn asked two questions; "This is considered an emergency" restates FixIt's own severity
  label. `CALLS_ENABLED` set back to `false` afterwards. The Retell from-number is a 218 area code.
- **Remaining for deployment:** approval for the Delta migration (`notebooks/02_retell_calls.sql`), App secret
  resources for the Retell key and operator token, outbound access to `api.retellai.com`, and a redeploy.

## Data decision (user, 2026-11-14): synthetic dataset for the demo
- The demo keeps the existing **synthetic Madison dataset**: 2,004 buildings, 251 owners, 11,941 reports. Every owner,
  building, neighbor report, complaint history and landlord grade is fictional (only street geography is real).
- UI labels (branch `ch27-review`, not deployed): a "Synthetic demo data" badge plus a one-line note on Listing (building
  history), Building, Owner, Landlords and City saying exactly what is synthetic: "simulated complaint history",
  "fictional landlord grade", "fictional owner"; grade badges have a "fictional grade" tooltip; the Case banner says
  "Simulated neighbor reports"; the listing verdict reason and tour question say "(simulated demo history)" /
  "FixIt's demo data (simulated)".
- **Not now:** real property-data ingestion, live rental-listing scraping, real landlord complaint-history integration.

## Future work (not required for P0)
- **Real Madison property data**: assessor/parcel ownership, City Building Inspection complaint and Official Notice
  history, and rental registration data, joined on normalized addresses in the lakehouse. It would need data-use terms,
  privacy review (no tenant PII), a refresh pipeline and honest "as of" dates. A grade built from real records would need
  its own methodology review before being shown about real landlords.
- Listing URL fetching only where a site's terms allow it (sidecar, P1/P2).

## Known issues / deviations
- Code section numbers are **placeholders** until Ch. 27 is parsed and mappings are human-reviewed.
- Demo Mode walkthrough fallback returns the scripted staged-corner detections for **any** uncached frame (by design for
  the stage; `source: "fallback"` in the API). Use `DEMO_MODE=false` for honest testing.
- `DATA_BACKEND=databricks` paths (warehouse inserts, Volume uploads, Vector Search, Genie polling) are **untested**.
- Genie create-space payload in `70_genie_space.py` may not match the current API; the UI fallback is documented.
- Rehearsals mutate the DB (new reports at 1234 Demo St). **Reset before going on stage.**
- Phone camera requires HTTPS (deployed App), not `http://<laptop-ip>`.
- The demo management company "Isthmus Edge Management" has no "(demo)" suffix (the owner does, and every screen has a
  Demo data badge). A web search found no real business with that name.
- Frontend bundle > 500 kB (Leaflet + Recharts). Fine for the demo. Recharts 2.x is deprecated upstream (no action).
- Browser window couldn't be resized by automation; mobile layout was checked in a 390 px same-origin iframe.

## Official sources (checked 2026-11-14 against the live sites)
| Use | URL | Verified content |
|---|---|---|
| Complaint form (interior) | https://www.cityofmadison.com/dpced/building-inspection/file-a-complaint/interior-property | "Only current tenants can report interior property issues." |
| Complaint process | https://www.cityofmadison.com/dpced/building-inspection/file-a-complaint/process | "Generally, cases are resolved within 30 to 60 days." Status: 608-266-4551 ext 4 |
| Rent abatement | https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/rent-abatement | Six eligibility conditions incl. Official Notice + missed deadline; cites MGO 32.04 |
| Retaliation | https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/retaliation | "within six months of their complaint, may be seen as retaliation"; links MGO 32.15 |
| Common code violations (closest official checklist) | https://www.cityofmadison.com/dpced/building-inspection/home-property/rental-housing/common-code-violations | — |
| Chapter 27 (Municode) | https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH27MIHOPRMACO | Loads in a browser (title "CHAPTER 27 - MINIMUM HOUSING AND PROPERTY MAINTENANCE CODE"); scripts get 403 |
| Building Inspection | https://www.cityofmadison.com/dpced/building-inspection | Phone 608-266-4551 |
- A standalone "Minimum Housing Standards Checklist" PDF was **not found** on cityofmadison.com. Ask Building Inspection or
  use the Common Code Violations page.

## Blockers / inputs needed from the human
- Databricks: approve CLI install, log in as profile `fixit`, name the workspace (Free Edition?), approve resource creation.
- Human review of the proposed Chapter 27 mappings (`docs/legal/CH27_REVIEW.md`); a separate legal source for CO alarms,
  mold, and smoke-alarm details (MGO 34.907 / SPS) if those categories should cite anything.
- Demo listing photos (staged or with permission) and staged walkthrough photos/clips.
- P1 only: Twilio SID/token/number and consenting allowlist numbers.

## How to run
README → "Run locally" (Windows commands included). Demo day: `docs/DEMO_CHECKLIST.md`.
