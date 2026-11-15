# FixIt Madison

**Catch rental problems before you sign, document them while you live there, and push back when the landlord ignores you.**
Built on Databricks for MadHacks 2026.

- Context and decisions: [`CONTEXT.md`](CONTEXT.md) · Status: [`PROGRESS.md`](PROGRESS.md) · Full spec: [`docs/BUILD_PROMPT.md`](docs/BUILD_PROMPT.md)

## Run locally (no Databricks needed)

```bash
make setup        # venv + pip + npm
make build        # build the React app into app/frontend/dist
make api          # http://localhost:8000 (FastAPI serves the built UI + /api)
# or, for frontend hot reload:  make dev  → http://localhost:5173
make test         # unit + end-to-end tests
```

**Windows (no `make`)**, from the repo root in PowerShell:
```powershell
python -m venv .venv; .venv\Scripts\python -m pip install -r app\requirements.txt pytest
cd app\frontend; npm install; npm run build; cd ..\..
.venv\Scripts\python -m uvicorn app.backend.main:app --port 8000     # http://127.0.0.1:8000
.venv\Scripts\python -m pytest -q app/backend/tests                   # 168 backend tests (2026-11-15)
cd app\frontend; npm test; cd ..\..                                  # 10 frontend tests
```

Demo day: follow [`docs/DEMO_CHECKLIST.md`](docs/DEMO_CHECKLIST.md). Databricks: [`docs/DATABRICKS_SETUP.md`](docs/DATABRICKS_SETUP.md).

With no Databricks config, the app runs on SQLite (`data/fixit.db`, seeded automatically with the synthetic Madison
dataset). In `DEMO_MODE=true`, AI steps fall back to cached or scripted outputs.

Copy `.env.example` to `.env` to configure. Key switches:

| Var | Meaning |
|---|---|
| `DEMO_MODE` | `true` serves cached/scripted results whenever a live AI call fails |
| `DATA_BACKEND` | `local` (SQLite) or `databricks` (SQL warehouse + UC Volumes) |
| `DATABRICKS_HOST` / `DATABRICKS_TOKEN` | enables live model-serving calls (vision, chat) even with the local backend |
| `CHAT_ENDPOINT` / `VISION_ENDPOINT` / `EMBEDDING_ENDPOINT` | serving endpoint names, verified by `notebooks/00_smoke_tests.py` |
| `GENIE_SPACE_ID` | enables the live Genie Conversation API (otherwise the sample questions run as local SQL) |

## Databricks setup (in order)

1. Add this repo as a **Git folder** in the workspace.
2. `notebooks/00_smoke_tests.py`: pick endpoints, record results in PROGRESS.md.
3. `notebooks/01_setup_catalog.sql`: catalog `fixit`, schemas, volumes.
4. `notebooks/30_gold_tables.sql`: table DDL + comments.
5. `notebooks/20_violation_taxonomy.py`: `ref.violation_types` (+ unverified seed sections).
6. `notebooks/05_generate_synthetic.py`: synthetic owners/properties/reports + landlord scores.
7. Upload the Chapter 27 PDF to `/Volumes/fixit/raw/code_docs/`, then run `10_parse_code.sql` → `11_build_vector_index.py`
   → the remap cell in `20_violation_taxonomy.py`.
8. `40_landlord_scores.sql`: the SQL version of the scores, for scheduled refresh.
9. `70_genie_space.py`: create the Genie space and put its ID in the app env.

## Deploy the App

```bash
databricks auth login --host https://<workspace>.cloud.databricks.com   # once
databricks apps create fixit-madison                                     # once
make deploy                                                              # build → bundle → sync → deploy
```
Then, in the App UI, add the SQL warehouse as a resource (key `sql-warehouse`). Grant the app's service principal the
permissions listed in `notebooks/01_setup_catalog.sql`. **Apps auto-stop ~24h after deploy, so redeploy right before judging.**

Before going on stage, put the exact demo photos in `demo/demo_inputs/{listing,walkthrough}/` and run
`curl -X POST localhost:8000/api/demo/warm` (with Databricks configured) to cache live vision results. Commit
`demo/cached_outputs/`. `POST /api/demo/reset` reseeds the local DB.

## Retell AI phone calls

_Deployed 2026-11-15 from `ch27-review`: Case page → "AI calls your landlord" → **Real phone call (Retell)**. Keys come from the App's `fixit-retell` secret scope. Always off in `PUBLIC_DEMO` mode._

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

## Public demo (no Databricks sign-in)

Databricks Apps always require a workspace sign-in. For judges, the same app can run in **`PUBLIC_DEMO=true`** mode:
SQLite with the synthetic dataset, saved/scripted AI results labeled on screen, no Databricks credentials, per-browser
case lists, upload and rate limits. Container: `deploy/public/Dockerfile`; Render Blueprint: `render.yaml`. Findings,
security and costs: [`docs/PUBLIC_HOSTING.md`](docs/PUBLIC_HOSTING.md). **Not deployed yet.**

## 3-minute demo

See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md): listing X-Ray → video walkthrough → verified Chapter 27 citation →
repair letter → simulated call → complaint draft → "You're not alone" → Genie → architecture, with fallbacks.

---
FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant Resource Center (608-257-0006) or City
of Madison Building Inspection (608-266-4551).
