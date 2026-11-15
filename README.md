# # FixIt Madison

**Catch rental problems before you sign, document them while you live there, and push back when the landlord ignores you.**

FixIt Madison is a tenant-assistance app built on Databricks for **MadHacks 2026** (UW–Madison). It uses a vision
model to spot possible housing-code issues in photos and walkthrough videos. It matches them to Madison's Minimum Housing
Code (MGO Chapter 27), drafts repair letters and complaint packets, and can have an AI agent call the landlord. A
Databricks lakehouse links every tenant's reports into building- and owner-level accountability.

> FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant Resource Center (608-257-0006) or
> City of Madison Building Inspection (608-266-4551).

---

## Contents
- [Features](#features)
- [Architecture](#architecture)
- [Repository layout](#repository-layout)
- [Run locally](#run-locally)
- [Configuration](#configuration)
- [Retell AI phone calls](#retell-ai-phone-calls)
- [Databricks setup and deployment](#databricks-setup-and-deployment)
- [Testing](#testing)
- [Legal content and honesty rules](#legal-content-and-honesty-rules)
- [Current status](#current-status)
- [Documentation index](#documentation-index)

---

## Features

| Feature | What it does |
|---|---|
| **Listing X-Ray** (`/listing`) | Upload listing photos + an address. You get possible issues in the photos, the building's (simulated) complaint history, the owner's grade, a verdict (*Sign / Ask first / Don't sign yet*), tour questions and a lease addendum. |
| **Walkthrough scan** (`/scan`) | Photos, a phone camera, or a walkthrough video. Video frames are sampled in the browser (1 fps, max 30 spread across the clip) and analyzed in batches of 5. Each finding links to the exact frames that show it, with severity, explanation and remedy. |
| **Evidence locker** | Every image is stored with its SHA-256 hash and capture/upload timestamps, then bundled into a PDF evidence packet. |
| **Repair letter** | Friendly / formal / final-request tones, generated from the case. Marked as a draft, never sent automatically. |
| **AI calls the landlord** | A **simulated call** (scripted agent + browser speech) for the stage. Separately, a **real Retell AI phone call** for consenting test recipients (see below). |
| **Follow-up deadline + escalation** | A FixIt reminder clock (not a legal deadline). When it runs out, a City complaint is pre-filled, never auto-submitted. |
| **You're not alone** | Matches neighbours in the same building and the owner's other buildings. "File together" builds a joint complaint draft. |
| **Landlord report cards, city map, Ask the data** | Owner grades, a Leaflet map of open issues, and Databricks Genie answering analytics questions. |
| **Demo Mode** | Every AI step tries live first, then falls back to a cached or scripted result. The UI always says which (`live / cache / fallback / none`). |

All owners, buildings, neighbour reports and landlord grades are **synthetic** (2,004 buildings, 251 owners, 11,941
reports; only street geography is real), and the UI labels them that way.

---

## Architecture

```
React UI (Vite/TS/Tailwind) ──> FastAPI ──> db.py ──> SQLite (local)  |  Databricks SQL Warehouse (Unity Catalog `fixit`)
                                   │           └──> evidence: data/evidence  |  UC Volume fixit.raw.evidence
                                   ├──> llm.py ──> Databricks Model Serving (Llama 4 Maverick: chat + vision, GTE embeddings)
                                   │                  └─ fallback ─> demo cache
                                   ├──> Genie Conversation API (analytics)
                                   └──> Retell AI REST API (opt-in phone calls; polled, no public webhook)
```

- **One app, two data backends.** `DATA_BACKEND=local` uses SQLite (`data/fixit.db`, seeded automatically).
  `DATA_BACKEND=databricks` uses a SQL warehouse. Both use one ANSI SQL code path with `:named` parameters.
  `db.t("silver.scans")` maps to `silver__scans` locally.
- **Unity Catalog `fixit`:** schemas `raw` (volumes), `bronze` (parse staging), `silver` (app rows), `gold`
  (analytics), `ref` (taxonomy), `ml`.
- **Deployment:** the React build is served by FastAPI as a single **Databricks App** behind Databricks sign-in.
- **Models:** `databricks-llama-4-maverick` for vision and chat (verified with random-color and nonce smoke tests),
  `databricks-gte-large-en` for embeddings. Code matching uses taxonomy mappings plus a BM25 fallback; a Vector Search
  client exists, but no index is active.

---

## Repository layout

```
app/
  backend/            FastAPI app: main.py, config.py, db.py, llm.py, seed.py
    services/         domain logic (scans, vision, code_match, cases, letters, calls, deadlines,
                      collective, landlords, genie, synthetic, retell, ...)
    routes/retell.py  operator-protected Retell endpoints
    prompts/          Retell landlord-call prompt
    tests/            pytest suite
    code_sections_verified.json   the only human-approved Chapter 27 citations
  frontend/           React + Vite + TypeScript + Tailwind (pages/, components/)
  app.yaml            Databricks App config
notebooks/            Databricks notebooks: smoke tests, catalog, synthetic data, Ch. 27 parse, vector index,
                      taxonomy, gold tables, landlord scores, Genie space, Retell table migration
scripts/              dbx_setup, dbx_check, bundle, app_smoke, genie_setup/verify, code_parse,
                      ch27_review_sheet, eval_vision, retell_setup, cleanup_test_records, ...
docs/                 setup runbooks, demo script/checklists, legal review (docs/legal), ops plans (docs/ops)
eval/                 vision evaluation instructions and the code-review sheet
experiments/          isolated YOLO-OBB detector experiments (not used by the app)
sidecar/              local helper skeleton (listing fetch / telephony placeholder)
demo/                 demo inputs and cached model outputs for Demo Mode
```

A deeper walkthrough of request flow and modules is in [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md).

---

## Run locally

No Databricks account is needed. With no Databricks config, the app runs on SQLite with the synthetic dataset, and in
`DEMO_MODE=true` AI steps fall back to cached or scripted outputs.

**macOS / Linux**
```bash
make setup        # venv + pip + npm
make build        # build the React app into app/frontend/dist
make api          # http://localhost:8000 (FastAPI serves the built UI + /api)
# or, for frontend hot reload:  make dev  → http://localhost:5173
make test         # backend tests
```

**Windows (no `make`)**, from the repo root in PowerShell:
```powershell
python -m venv .venv; .venv\Scripts\python -m pip install -r app\requirements.txt pytest
cd app\frontend; npm install; npm run build; cd ..\..
.venv\Scripts\python -m uvicorn app.backend.main:app --port 8000     # http://127.0.0.1:8000
.venv\Scripts\python -m pytest -q app/backend/tests
```

`POST /api/demo/reset` reseeds the local database (Retell call records, consents and opt-outs are kept).

---

## Configuration

Copy `.env.example` to `.env` (gitignored). Never commit secrets.

| Variable | Meaning |
|---|---|
| `DEMO_MODE` | `true` serves cached/scripted results whenever a live AI call fails |
| `DATA_BACKEND` | `local` (SQLite) or `databricks` (SQL warehouse + UC Volumes) |
| `FIXIT_DATA_DIR` | Local data directory (default `data/`) |
| `DATABRICKS_HOST` / `DATABRICKS_TOKEN` / `DATABRICKS_CONFIG_PROFILE` | Enables live model-serving calls (any one of these). Use only the CLI profile `fixit` for this project |
| `DATABRICKS_WAREHOUSE_ID`, `FIXIT_CATALOG` | Warehouse backend settings |
| `CHAT_ENDPOINT` / `VISION_ENDPOINT` / `EMBEDDING_ENDPOINT` | Serving endpoint names, verified by `notebooks/00_smoke_tests.py` / `scripts/dbx_check.py` |
| `GENIE_SPACE_ID` | Enables live Genie (otherwise the sample questions run as prepared local SQL) |
| `SHOW_BBOXES` | Show model bounding boxes (default off: labeled thumbnails) |
| `CALLS_ENABLED` | Master kill switch for real phone calls (default `false`) |
| `CALL_ALLOWLIST` | Comma-separated exact E.164 numbers of consenting test recipients |
| `RETELL_API_KEY`, `RETELL_AGENT_ID`, `RETELL_FROM_NUMBER` | Retell account key, dedicated FixIT agent, Retell-owned calling number |
| `RETELL_OPERATOR_TOKEN` | Separate random secret (≥32 chars) that unlocks the Retell panel |

---

## Retell AI phone calls

The Case page has a separate **Retell phone call** panel that places a real call to a consenting teammate or judge
role-playing the landlord. The simulated call is unchanged and remains the stage default.

**How the agent behaves** (prompt: `app/backend/prompts/retell_landlord.md`):
- Opens by saying it is an AI acting with the tenant's authorization and that this is a test call. It discloses the
  recording and transcription and **asks** for recording consent before anything else.
- Uses only the supplied case facts. Raises the most urgent issue first. Asks for inspection or repair plans, dates,
  the coordinator and anything needed from the tenant.
- Keeps inspection appointments, repair estimates and firm repair commitments distinct.
- Cites only backend-verified code sections, and only as "possibly relevant".
- Never threatens enforcement, never claims to be a lawyer or inspector, and never agrees to anything for the tenant.
- Ends the call when the recipient refuses to talk to an AI, withdraws consent, or asks not to be called again.

**Safety controls:**
- Kill switch and exact-number allowlist.
- Operator token: the demo app has no tenant login.
- Four explicit confirmations before every call.
- A durable attempt is saved before dialing, and the attempt ID is sent as Retell's idempotency key.
- No automatic redial. An uncertain create can only be **resumed** with the same key within 50 minutes, or
  **reconciled** using verified call metadata.
- Sticky opt-outs, and a pre-call check that the remote agent still matches the reviewed prompt.

**Handling results:**
- Results (status, transcript, analysis) are **polled**, because the Databricks App's sign-in blocks webhooks.
- Machine-extracted outcomes are labeled for review and **never** change deadlines, letters or complaints
  automatically.

Setup, API, failure handling and the Databricks migration: [`docs/RETELL_SETUP.md`](docs/RETELL_SETUP.md).

```bash
.venv/bin/python scripts/retell_setup.py --voice-id <voice>          # offline dry run of the agent config
.venv/bin/python scripts/retell_setup.py --voice-id <voice> --apply  # creates one LLM + one agent (no number, no call)
.venv/bin/python scripts/retell_setup.py --check                     # verify the live agent matches the bundled prompt
```

---

## Databricks setup and deployment

Full runbook: [`docs/DATABRICKS_SETUP.md`](docs/DATABRICKS_SETUP.md). In short:

1. `databricks auth login --host https://<workspace>.cloud.databricks.com --profile fixit`
2. Discover and verify models: `scripts/dbx_check.py --profile fixit [--test-models ...]`
3. Catalog, tables and synthetic data: `scripts/dbx_setup.py --profile fixit --warehouse <id> --catalog fixit [--apply]`
   (or run notebooks 01 → 30 → 20 → 05). The story check must print 6 / D / 11 / 0.
4. Genie space: `scripts/genie_setup.py` or `notebooks/70_genie_space.py`. Put the ID in `GENIE_SPACE_ID`.
5. Deploy:
   ```bash
   cd app/frontend && npm run build && cd ../..
   .venv/bin/python scripts/bundle.py
   databricks workspace import-dir build/app /Workspace/Users/<you>/fixit-madison-app --overwrite -p fixit
   databricks apps deploy fixit-madison --source-code-path /Workspace/Users/<you>/fixit-madison-app -p fixit
   .venv/bin/python scripts/app_smoke.py --profile fixit --url <app-url>
   ```
   (`databricks sync` skips the ignored `build/` folder, so use `import-dir`.) Grant the App's service principal the
   permissions at the bottom of `notebooks/01_setup_catalog.sql`.
   **Apps auto-stop about 24 h after deploy: redeploy right before judging.**

---

## Testing

```bash
.venv/bin/python -m pytest -q app/backend/tests     # backend: 203 tests (code matching, deadlines, hashing,
                                                    # collective matching, grading, detection, video, legal prep, Retell)
cd app/frontend && npx tsc -b && npm run build && npm test   # type check, production build, 10 frontend tests
```

- `scripts/app_smoke.py`: end-to-end check against a deployed App (it creates test rows).
- `scripts/eval_vision.py`: live-only vision evaluation on staged photos (see `eval/README.md`).
- `scripts/genie_verify.py`: saved Genie answers must match a fresh run of their SQL.
- Retell tests stub the provider; they never place calls.

---

## Legal content and honesty rules

- Legal output is shown as **content with citations and links**, never as definitive law. Every legal output carries
  the disclaimer above.
- **Only three Chapter 27 mappings are verified** (reviewed against the official source and explicitly approved):

  | Issue | Citation |
  |---|---|
  | Leaks / plumbing | MGO §27.05(2)(j) |
  | No heat | MGO §27.04(2)(h) |
  | Damaged surfaces | MGO §27.05(2)(g)1. |

  They are shown as "Possibly relevant: MGO § …" with the exact excerpt and "Whether this condition violates it is
  for a City of Madison inspector to decide." Every other category stays a provisional FixIt summary. Section numbers
  are never guessed.
- **Wording:** "possible issue" (never "violation found"), "not an inspection", "FixIt reminder, not a legal deadline",
  "draft, not submitted", "Final request" (the City issues Official Notices).
- A photo without a visible alarm never produces a smoke/CO finding. The smoke/CO legal-deadline display and the
  state-law display are hard-disabled.
- Synthetic people only. Real calls go only to allowlisted, consenting test recipients, with AI disclosure first.
  Never call real landlords.

Details: [`CONTEXT.md`](CONTEXT.md) §4–6 and [`docs/legal/`](docs/legal/).

---

## Current status

_As of 2026-11-15. The chronological log is in [`PROGRESS.md`](PROGRESS.md)._

- **Deployed:** the Databricks App runs branch `ch27-review` (commit `2c74f5d`: video walkthrough, wording and
  photo-detection fixes, the three verified citations). `main` on GitHub holds only the initial README.
- **Retell integration:** implemented on `feature/retell-ai` (local, not deployed or merged).
  - Backend and frontend tests pass, and a mocked browser run passed.
  - A dedicated Retell agent exists, and **one consented live test call** placed from a local run completed
    end to end (disclosure, consent, transcript and outcome captured).
  - Deploying it needs approval for the `silver.retell_calls` Delta table, App secrets, outbound access and a redeploy.
- **Experiments:** two YOLO-OBB detector experiments live in `experiments/`. They are not integrated: the reports
  recommend better labels and data first. The app's detector remains Llama 4 Maverick.
- **Paused until after the demo:** further legal review (`docs/legal/HUMAN_REVIEW_CHECKLIST.md`), real property-data
  ingestion and listing scraping.

---

## Documentation index

| Doc | Purpose |
|---|---|
| [`CONTEXT.md`](CONTEXT.md) | Decisions, conventions, legal and safety rules (read first) |
| [`PROGRESS.md`](PROGRESS.md) | Chronological status log, blockers, official sources |
| [`docs/CODEBASE_MAP.md`](docs/CODEBASE_MAP.md) | Request flow and module map |
| [`docs/BUILD_PROMPT.md`](docs/BUILD_PROMPT.md) | Original full specification |
| [`docs/DATABRICKS_SETUP.md`](docs/DATABRICKS_SETUP.md) | Workspace setup and deployment runbook |
| [`docs/RETELL_SETUP.md`](docs/RETELL_SETUP.md) | Retell configuration, safety, API, failure handling |
| [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md), [`docs/DEMO_CHECKLIST.md`](docs/DEMO_CHECKLIST.md) | Three-minute demo and run sheet |
| [`docs/DEMO_PERFORMANCE.md`](docs/DEMO_PERFORMANCE.md), [`docs/PHONE_TEST_CHECKLIST.md`](docs/PHONE_TEST_CHECKLIST.md) | Video speed and real-phone testing |
| [`docs/legal/`](docs/legal/) | Chapter 27 source, parse, reviews, state-law design, City inquiry draft |
| [`eval/README.md`](eval/README.md) | Vision evaluation method |

---

## Three-minute demo

1. **Hook:** "Most Madison renters never use the rights they already have."
2. **Listing X-Ray:** demo listing photos, address `1234 Demo St`. Verdict *Don't sign yet*, 6 heat reports, owner
   grade D, tour questions and addendum.
3. **Scan:** a short walkthrough clip of the staged corner. Findings with frames, Chapter 27 card, *Create repair request*.
4. **Call:** the AI discloses it's an AI, cites code as possibly relevant and captures the date. The countdown starts.
   *Simulate +8 days* → *Escalate* → pre-filled City complaint.
5. **You're not alone:** 6 neighbours reported heat, and the owner's 3 other buildings have 11 open issues →
   *File together*. Then `/city`: map, "Where to inspect next", and a Genie question.
6. **Close:** "FixIt: catch it before you sign, document it while you live there, fight it when they ignore you."

---

FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant Resource Center (608-257-0006) or City
of Madison Building Inspection (608-266-4551).
