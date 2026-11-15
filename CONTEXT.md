# CONTEXT.md — FixIt Madison

The short reference for anyone (human or coding agent) picking up this repo. The full spec is
`docs/BUILD_PROMPT.md`. Status lives in `PROGRESS.md`. This file covers **what we're building, the decisions
already made, and the conventions to follow.**

---

## 1. What it is

**FixIt Madison** catches rental problems before you sign, documents them while you live there, and pushes back
on the landlord when they ignore you. A Databricks lakehouse links every tenant's reports into city-wide
accountability.

Built for **MadHacks 2026 (UW–Madison)**: a 24-hour hackathon with a 3-minute live demo. **The demo comes first.**

### The four demo "wow" moments
1. **Listing X-Ray**: upload listing photos and an address. You get possible code issues in the photos, the building's complaint
   history, the owner's grade, a verdict (Sign / Ask first / Don't sign yet), tour questions and a lease addendum.
2. **Walkthrough scan**: camera or uploads. Each violation is matched to an MGO Chapter 27 section, with severity, explanation
   and remedy.
3. **AI calls the landlord**: a simulated call (P0) or a real allowlisted Twilio call (P1). The AI says it's an AI, cites
   the code and pulls out a repair date. A deadline clock starts, and when it runs out a city complaint is pre-filled (never auto-submitted).
4. **You're not alone**: matches neighbours in the same building and other buildings with the same owner. "File together"
   creates a joint complaint. Also: landlord report cards, a city map, and Genie "Ask the data".

### Users
Renter (primary) · tenant organizer · city inspector/council staff (demo persona).

---

## 2. Priority tiers (law)
- **Current priorities (user, 2026-11-14):** 1) complete the Chapter 27 citation review, 2) improve real-photo analysis
  reliability, 3) finish frontend and mobile testing, 4) prepare the three-minute demo. No P1 work.
- **P0** (demo): code KB, taxonomy, scan, listing X-Ray, evidence locker + packet PDF, repair letter, simulated call,
  deadlines + escalation, collective match, landlord report card, Genie, synthetic dataset, Demo Mode.
- **P1**: real phone call, Lease X-Ray, risk model (MLflow), AI/BI dashboard, Ask FixIt RAG, eval panel, Chicago
  public-data pipeline, emergency routing, tour checklist.
- **P2**: move-in/out diff, heat logger, multilingual, building group, resource router, second city, insurance export.

Finish every P0 before starting any P1.

---

## 3. Key decisions (made, don't re-litigate)

| Decision | Choice | Why |
|---|---|---|
| Repo location | `~/fixit-madison` (its own git repo) | Home dir is a stray git repo; keep the project isolated |
| App stack | FastAPI backend + React/Vite/TS/Tailwind frontend, built to static files served by FastAPI | One Databricks App; demos better than Streamlit |
| **Dual data backend** | `DATA_BACKEND=local` → SQLite (`data/fixit.db`), `DATA_BACKEND=databricks` → SQL warehouse | App runs and demos before Databricks is ready, and is a stage fallback if the warehouse fails |
| SQL dialect | Plain ANSI SQL with `:named` params (works in sqlite3 *and* databricks-sql-connector ≥3). Dates computed in Python and passed as params. Arrays stored as JSON strings | One code path for both backends |
| Synthetic data | One pure-Python generator (`app/backend/services/synthetic.py`) used by the local seeder, `scripts/dbx_setup.py` and `notebooks/05_generate_synthetic.py`. Generated at a fixed `REFERENCE_NOW` (2026-11-14 12:00) then shifted to the real `now`; the demo story has its own RNG stream | Same demo story everywhere, at any time of day (before this, the demo owner's grade flipped D/F with the clock) |
| Demo dataset (user, 2026-11-14) | Keep the synthetic dataset (2,004 buildings, 251 owners, 11,941 reports) for MadHacks. UI says explicitly what is synthetic: records, simulated complaint histories, fictional landlord grades. No real property-data ingestion, listing scraping or real complaint-history integration now; real Madison property data is **future work, not P0** (PROGRESS.md) | No real tenants or landlords; honest demo |
| Databricks profile | Only the CLI profile `fixit` (Free Edition workspace). Never `sleepsafe` | User instruction |
| Models | `databricks-llama-4-maverick` (chat + vision), `gte-large-en` (embeddings); verified live. No Claude endpoints in this workspace | Free Edition availability |
| Ch. 27 parse staging | `ai_parse_document` output goes to `fixit.bronze.code_sections_parsed` (staging). The App reads only silver/ref (its SP has no bronze grants) | Parsing never changes what the App shows |
| Approved citations | `scripts/code_parse.py approve` stores only excerpt-checked text from the approved categories, never a whole parsed section | The parser drops words at some page breaks |
| Video | Frames sampled **in the browser** (canvas, 1 fps, max 30) and uploaded as JPEGs | No OpenCV in the app |
| LLM / vision / embeddings | Databricks model serving, OpenAI-compatible `/serving-endpoints/{name}/invocations`. Endpoint names in `config.py` / env, **verified by smoke tests** | Free Edition availability varies |
| Code matching | Vector Search Delta Sync index (Databricks) → fallback BM25 over `code_sections` + taxonomy mapping (local, no deps) | Must always return an answer |
| Bounding boxes | Shown only if `SHOW_BBOXES=true`; default is labeled thumbnails | Don't show wrong boxes on stage |
| Simulated call | Deterministic scripted agent state machine + optional LLM turns; browser `speechSynthesis` TTS + Web Speech STT / typing for the "landlord" | Reliability on stage |
| Commitment extraction | LLM, then a regex/date-parser fallback (`deadlines.parse_commitment`) | Pure, tested |
| Genie | Conversation API client; in local/demo mode the 8 sample questions map to real SQL run on the local DB | Real answers even offline |
| PDFs | `reportlab` | Pure Python, works in Apps |

---

## 4. Demo Mode (non-negotiable)
`DEMO_MODE=true` means every AI step tries live first, and on failure or timeout serves a cached result:
- Vision: cached by image SHA-256 (`demo/cached_outputs/vision/<sha>.json`). In walkthrough mode, any frame that misses the
  cache falls back to the scripted "staged corner" scenario (covered smoke detector, water stain, missing outlet cover).
- Listing X-Ray: the demo listing photos are cached by hash.
- Call: scripted transcript. Genie: in Demo Mode a saved live Genie answer is served instantly (labeled "saved"); live
  Genie takes ~17-24 s. Letters: template-based, no LLM needed.
- `POST /api/demo/reset` (hidden) reseeds the DB and clears cases. Databricks twin: `scripts/dbx_setup.py --only reset
  --apply` (story check must print 6 / D / 11 / 0). After any Databricks reset run `scripts/genie_verify.py` (8/8 saved
  Genie answers must match a fresh run of their SQL; re-capture with `genie.warm()` if one drifts).
- Responses carry `"source": "live" | "cache" | "fallback" | "none"`. **The UI shows it** (decision changed 2026-11-14 at the
  user's request): a gray line on Listing/Scan ("Analyzed live just now by …", "Saved result…", "Demo script…"), the
  Genie caption, and the call's extraction note. Never imply a live model when it wasn't one.
- Wording rules: "possible issue" (never "violation found"), "not an inspection", "FixIt reminder, not a legal deadline",
  "draft, not submitted", "Final request" (never "Final notice": the City issues Official Notices).
- Citations are "Possibly relevant code", never a finding. A verified citation card says whether the condition violates
  it is for a City inspector to decide. Safety guidance (lead paint, shock risk) is labeled "General safety information,
  not a Chapter 27 requirement".

---

## 5. Legal content rules
- Show as **content with citations and links**, never as definitive law.
- Disclaimer on every legal output: *"FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant
  Resource Center (608-257-0006) or City of Madison Building Inspection (608-266-4551)."*
- MGO **Ch. 27** = Minimum Housing & Property Maintenance Code. **MGO 32.04** = rent abatement. The city's page lists six
  conditions: violation affects use → tenant contacted the landlord and allowed time → complaint filed with Building
  Inspection → tenant answered the inspector's call and scheduled an inspection → a specific violation with an **Official
  Notice** setting a repair deadline → the deadline passed unresolved. **MGO Ch. 32** anti-retaliation: the city says actions
  within six months of a complaint "may be seen as retaliation" (its page links MGO 32.15). Building Inspection: "Generally,
  cases are resolved within 30 to 60 days." Only current tenants can file interior complaints. Sources + check date:
  PROGRESS.md → "Official sources".
- **Never guess section numbers.** Seed rows are FixIt summaries (`verified=0`, "section number pending verification").
  Only a human-approved review sets `verified=1`, remaps the taxonomy, and is saved to
  `app/backend/code_sections_verified.json` (merged, never overwritten) so both backends and resets keep it.
- **Ch. 27 source:** `docs/legal/Madison_Chapter_27.pdf` (user's Municode export, 41 pp, §27.01–§27.13, printed
  11/14/26; sha256 `7feae63e…`). Raw parse: `docs/legal/ch27_parsed_sections.json` (kept unmodified). Parse defects at page
  breaks (§27.05(2)(h)7., §27.05(2)(x)) are corrected from the PDF text in `docs/legal/ch27_parse_corrections.json`.
- **Review workflow:** proposals in `docs/legal/ch27_proposed_mappings.json` → `scripts/ch27_review_sheet.py` checks every
  excerpt verbatim against the parse and the PDF text layer and writes `docs/legal/CH27_REVIEW.md` + `eval/code_review.csv`
  → user decides → cross-check against the current official source → user supplies the reviewer name →
  `code_parse.py approve` (dry run, then `--apply`).
- **Reviewer rule (user, 2026-11-14):** reviewer = **Naisha Chadha**, entered **only** for citations she personally
  reviewed and explicitly approved after the official-source comparison; every other reviewer field stays blank. Nothing
  provisional becomes verified without her explicit approval. Approval means the citation and quoted text were checked
  against the official source; it does **not** mean she is a lawyer or City inspector, or that an AI-detected condition
  is a confirmed violation (recorded as `review_meaning` in `code_sections_verified.json`).
- **Live official check (2026-11-14):** all 26 provisional excerpts match live Municode Chapter 27 (version Sep 1, 2026;
  no amendments newer than the PDF). Plumbing, heat and surfaces were re-checked structurally (right subsection label,
  exceptions present) and are **ready for the reviewer's personal approval**. MGO 32.04(4)(d) (rent-abatement
  schedule) independently confirms several subsection numbers. Record: `docs/legal/ch27_live_check.md`.
- **Review status (2026-11-14):** all decisions **provisional, nothing verified**. Provisionally accepted: plumbing
  §27.05(2)(j); heat §27.04(2)(h) (67°F in habitable rooms, kitchens, bathrooms + occupant exception; no "heating
  season"); surfaces §27.05(2)(g)1.; locks §27.05(2)(h), (h)3., (h)4., with (h)6. as a supporting reference only
  (alternative devices are allowed only with Building Inspection approval, never automatically); windows
  §27.05(2)(h) + §27.04(2)(f) / §27.07(2)(c) for screens (by June 1) and storm windows (Oct 15–Nov 15); pests §27.07(2)(d)
  + §27.03 "infestation" (sustained presence; owner exterminates except in single-family dwellings); electrical §27.04(2)(g)
  only; water damage §27.05(2)(g)1./(g)2. as potentially relevant. **On hold:** exits (see the §27.06(4) item below;
  SPS stair/handrail specs unreviewed). **Pending other sources:** smoke alarms, CO, mold. Considered and not mapped:
  §27.05(2)(m) for heat, §27.04(2)(g)3. for electrical.
- **§27.06(4) cross-reference (UNRESOLVED, do not guess):** §27.04(2)(d) says "except as provided in Sec. 27.06(4), MGO",
  but §27.06(4) is about habitable rooms below grade. Identical in the live text and the oldest Municode version (Feb
  2018); the rent-abatement exit row doesn't mention it. **City Building Inspection clarification is needed** (or the
  amending ordinances, e.g. Ord. 9326 (1987), Ord. 12,349 (1999)).
- **Chapter 27 does not mention** carbon monoxide, mold, cover plates or cracked glass, and has no general "pest-free" rule.
  Smoke alarms: §27.05(2)(w) only incorporates MGO 34.907 + SPS codes.
- **Keep these distinct (user decision):** official City guidance (e.g. the Common Code Violations page lists missing
  cover plates and "at least 67°F at all times") vs general maintenance obligations (e.g. §27.05(2)(g)1.) vs specific
  legal requirements. The rent-abatement schedule MGO 32.04(4)(d) lists mold under §27.05(2)(g)1. for abatement: that's
  the City's abatement classification, not a Chapter 27 mold rule. No citation is forced.
- **Smoke alarms, read on official sources** (`docs/legal/OTHER_SOURCES_REVIEW.md` §5):
  - **MGO 34.907** ("Fire Alarm and Detection Systems") applies to buildings built before 2009 (after 2009: IFC 907);
    owner-occupied single-family homes excluded from (1)(b). Alarms in each bedroom, every sleeping area, within 6 ft of
    each bedroom door and on each floor; hardwired+battery or sealed 10-year battery; the tenant maintains and tests
    in-unit alarms; the owner repairs within **5 days of written notice** ((1)(c)4.). Its internal references
    ("sub. (2)(a)/(2)(b)/(3)(h)") don't match the current numbering (unresolved).
  - **Wis. Stat. §101.145** (residential buildings): basement, head of each stairway on every floor, each sleeping area or
    within 6 ft. **§101.645** (dwellings; SPS 328 for 1-2 family built before 6/1/1980): basement and each floor. Both:
    the occupant maintains in-unit; the owner fixes within 5 days of written notice.
- **CO alarms:** not in Chapter 27. **Wis. Stat. §101.149** (residential buildings): triggered by a fuel-burning appliance,
  forced-air furnace, outside appliance or attached garage (with exemptions); outside each sleeping area. **§101.647**
  (1-2 unit dwellings): basement + each floor unless no attached garage, no fireplace and no fuel-burning appliance.
  Both: 5 days after written notice. Madison: **MGO 29.19 is "Accrediting Standards and Tests"** (not CO); CO enters
  only via **MGO 29.22** (adopts SPS 328). The rent-abatement row "29.19 … Carbon Monoxide Detectors" doesn't match the
  current code (unresolved).
- **Applicability (user decision):** keep MGO 34.907, the state smoke statutes, the state CO statutes and SPS references
  separate; document overlaps; **do not choose a governing rule without sufficient evidence**. A 5-day written-notice
  deadline may be shown only when the applicable source and its conditions are established, always separate from
  FixIt's reminders. Building facts (units, construction year, garage/fireplace/fuel-burning appliances/heating) come
  only from the user or explicit data, never inferred from photos or synthetic records.
  **Prototype on `ch27-review` (not deployed, nonpersistent):** `services/alarm_rules.py` + `POST /api/alarm-rules` +
  an optional card on the Case page (smoke/CO cases only). Statuses: "stated conditions appear met (not legally
  verified)", "may apply", "outside stated scope", "not evaluated"; never "applies"; never a governing rule. The 5-day
  deadline display is hard-disabled (`LEGAL_DEADLINE_DISPLAY_ENABLED = False`). No DB schema change. Construction
  periods: before June 1, 1980 / June 1, 1980–2008 / 2009 or later / unknown. Tests: `test_alarm_rules.py`.
- Mold: no mold-specific requirement found; general repair duty in Wis. Stat. §704.07(2)(a).
- Default deadline windows (7 days routine / 48h urgent / 24h emergency) are **FixIt defaults, not legal deadlines**.

## 6. Safety / privacy
- Synthetic people only, `is_synthetic=true`, and a "Demo data" badge in the UI. Unit numbers are hashed in `reports`; joint complaints
  call units "Unit A, B…".
- Real calls: hard allowlist (`CALL_ALLOWLIST`), kill switch (`CALLS_ENABLED`), AI disclosure in the first sentence. Never call real landlords.
- Listing URLs are fetched only by the sidecar and only where the site's terms allow it. Uploaded photos are the default.
- Below the confidence threshold (0.6): show "possible issue — verify in person".
- Evidence: SHA-256 plus capture/upload timestamps, all listed in the packet.

---

## 7. Architecture
```
React UI ──> FastAPI (Databricks App) ──> db.py ──> SQLite (local) | SQL Warehouse (fixit.*)
                    │                └──> evidence: data/evidence | UC Volume fixit.raw.evidence
                    └──> llm.py ──> Databricks serving endpoints (chat / vision / embeddings) ─fallback─> demo_cache
Sidecar (local, FastAPI): listing fetcher, Twilio voice (P1), local vision fallback → writes to Databricks
Notebooks: 00 smoke → 01 catalog → 05 synthetic → 10 parse code → 11 vector index → 20 taxonomy → 30 gold → 40 scores → 70 genie
```
Unity Catalog `fixit`: schemas `raw`(volumes) `bronze` `silver` `gold` `ref` `ml`. The full table list is in spec §6. The local
SQLite uses the same table names with the schema prefix flattened (`silver.scans` → `silver__scans`) through `db.t("silver.scans")`.

## 8. Repo map
```
CONTEXT.md  PROGRESS.md  README.md  .env.example  docs/BUILD_PROMPT.md
app/app.yaml  app/requirements.txt
app/backend/{main,config,db,models,llm}.py
app/backend/services/{synthetic,taxonomy,code_match,vision,listing,evidence,letters,calls,deadlines,collective,landlords,genie,demo_cache,pdfs}.py
app/backend/routes/*.py   app/backend/tests/
app/frontend/ (Vite React TS Tailwind)
sidecar/  notebooks/  eval/  demo/{demo_inputs,cached_outputs}
docs/legal/  (Ch. 27 PDF, parse, corrections, proposals, CH27_REVIEW.md, OTHER_SOURCES_REVIEW.md)
scripts/  dbx_setup · app_smoke · genie_verify · code_parse · ch27_review_sheet · eval_vision · bundle · grant_app_sp
```

## 9. Conventions
- Python 3.11+ (local venv `.venv`, 3.13 OK). Run backend: `make dev` (see README).
- Pure logic lives in `services/` with no I/O where possible. Tests go in `app/backend/tests` (pytest) and cover code matching,
  deadline math, hashing, collective matching and grading.
- No secrets in code: read `.env` (gitignored) and `.env.example` is the template.
- Commit working states often. Update `PROGRESS.md` after every milestone.

## 10. Current status (2026-11-14, late evening)
- All P0 features run end to end locally (SQLite) and on Databricks. **Deployed App:**
  https://fixit-madison-7474647207905142.aws.databricksapps.com (catalog `fixit`, warehouse `6361516ab33ba2d2`, Genie space
  `01f1e089ff07126aac09984f839aaef1`, minimal SP grants). Smoke test `scripts/app_smoke.py` 11/11; data reset to the clean
  story (6 open heat at 1234 Demo St, owner grade D (score 0.916), 11 open issues across 3 other buildings); 8/8 saved Genie
  answers match. Apps auto-stop ~24 h after deploy: redeploy on judging day.
- **Branches:** `main` = what is deployed (70 tests pass there). `ch27-review` = Chapter 27 review work, **not deployed**:
  provisional decisions, corrected wording (heat, plumbing, surfaces, locks, windows, pests, exits renamed "Blocked exit /
  unsafe stairs / missing handrail", electrical, water damage renamed "Water damage / suspected mold", placeholders that no
  longer claim CO/mold/cover plates), "Possibly relevant code" wording, CO "legal source not yet verified" placeholder.
  76 tests pass on the branch.
- Vector Search skipped (not created). No P1 work started (no Twilio).
- Quick start: `make setup && make build && make api` → http://localhost:8000 (Windows commands in README).

## 11. Inputs still needed from the human
- Ch. 27: the reviewer's personal approval of plumbing, heat and surfaces (ready), then the rest; City Building
  Inspection clarification of the §27.06(4) cross-reference; SPS 321.04 / SPS 362 for stairs and handrails.
- Smoke/CO: review the design for building questions and the 5-day written-notice deadline (not implemented).
- Manual checklist on the App + phone (`docs/DEMO_SCRIPT.md`); staged photos for `scripts/eval_vision.py` and the stage cache.
- 19 photos from the user's manual test remain in `/Volumes/fixit/raw/evidence/` (resets never delete files).
- P1 only: Twilio keys + consenting allowlist numbers. Details in `PROGRESS.md`.
