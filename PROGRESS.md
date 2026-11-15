# PROGRESS.md

_Last updated: 2026-11-14 (evening)_

## Status: P0 verified in a real browser (local + Demo Mode). Databricks Milestone 1 blocked on login (no CLI/profile on this machine)

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

Needs the user: Chapter 27 PDF export · staged photos for eval + stage · manual checklist on the App/phone.

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

## Next
1. 🧑 Open the App URL, click Continue on the OAuth prompt, and walk the demo in the browser (docs/DEMO_CHECKLIST.md).
   Apps auto-stop ~24 h after deploy: redeploy (`databricks apps deploy …`) the day of judging.
2. 🧑 Chapter 27 PDF (export from Municode) → upload to `/Volumes/fixit/raw/code_docs/` → `10_parse_code.sql` →
   human-review the remap in `20_violation_taxonomy.py`. Until then keep the "pending verification" labels.
3. 🧑 Real demo photos into `demo/demo_inputs/{listing,walkthrough}/` → `/api/demo/warm` with live models → commit cache.
4. MLflow tracing on vision/LLM calls. 5. Full 3-minute dry run ×3, Demo Mode on and off, on the deployed App. Then P1.

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
- Chapter 27 PDF export (Municode print/download), and the checklist if the city provides one.
- Demo listing photos (staged or with permission) and staged walkthrough photos/clips.
- P1 only: Twilio SID/token/number and consenting allowlist numbers.

## How to run
README → "Run locally" (Windows commands included). Demo day: `docs/DEMO_CHECKLIST.md`.
