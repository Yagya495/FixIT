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

## Databricks features confirmed working
**None yet.** Nothing has been run against a workspace. Do not claim any Databricks feature works in the demo until
`scripts/dbx_check.py` / the notebooks have confirmed it.

## Next
1. 🧑 Install CLI + `databricks auth login --profile fixit` (docs/DATABRICKS_SETUP.md §0). Then: discovery → model tests
   → (approval) catalog/tables/synthetic → Genie → warehouse write test → `DATA_BACKEND=databricks` → App deploy + SP grants.
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
