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
| Synthetic data | One pure-Python generator (`app/backend/services/synthetic.py`) used by both the local seeder and `notebooks/05_generate_synthetic.py` | Same demo story everywhere |
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
- Call: scripted transcript. Genie: cached answers per sample question. Letters: template-based, no LLM needed.
- `POST /api/demo/reset` (hidden) reseeds the DB and clears cases.
- Responses carry `"source": "live" | "cache" | "fallback" | "none"`. **The UI shows it** (decision changed 2026-11-14 at the
  user's request): a gray line on Listing/Scan ("Analyzed live just now by …", "Saved result…", "Demo script…"), the
  Genie caption, and the call's extraction note. Never imply a live model when it wasn't one.
- Wording rules: "possible issue" (never "violation found"), "not an inspection", "FixIt reminder, not a legal deadline",
  "draft, not submitted", "Final request" (never "Final notice": the City issues Official Notices).

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
  Parsing (`scripts/code_parse.py parse` / notebook 10) adds official text with `verified=0`. Only a human-approved
  review (`propose` → fill `eval/code_review.csv` with a reviewer name → `approve`) sets `verified=1` and remaps the taxonomy;
  the approval is saved to `app/backend/code_sections_verified.json` so both backends and resets keep it.
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
```

## 9. Conventions
- Python 3.11+ (local venv `.venv`, 3.13 OK). Run backend: `make dev` (see README).
- Pure logic lives in `services/` with no I/O where possible. Tests go in `app/backend/tests` (pytest) and cover code matching,
  deadline math, hashing, collective matching and grading.
- No secrets in code: read `.env` (gitignored) and `.env.example` is the template.
- Commit working states often. Update `PROGRESS.md` after every milestone.

## 10. Current status (2026-11-14)
- All P0 features are built and run end to end **locally** (SQLite + Demo Mode), verified in a real browser. 44 tests pass.
- Databricks notebooks, the warehouse backend, Volumes, Vector Search, the Genie client and the App bundle are written but **not yet run
  against a workspace**.
- Code section ids are placeholders (`CH27-*`) until the Ch. 27 PDF is parsed and the matches are human-reviewed.
- Quick start: `make setup && make build && make api` → http://localhost:8000

## 11. Inputs still needed from the human
Databricks workspace/profile + SQL warehouse ID, the Ch. 27 PDF + checklist + saved city pages, demo listing/walkthrough
photos, and (P1) Twilio keys + consenting allowlist numbers. Details in `PROGRESS.md`.
