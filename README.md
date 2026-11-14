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
.venv\Scripts\python -m pytest -q app/backend/tests                   # 44 tests
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

## 3-minute demo script

1. **Hook**: "Most Madison renters never use the rights they already have."
2. **Listing X-Ray** (`/listing`): upload the demo listing photos, address `1234 Demo St`. Verdict: *Don't sign yet*, 6 heat reports, owner grade D, tour questions + addendum.
3. **Scan** (`/scan`): live camera on the staged corner. Detections → tap one → Chapter 27 section → *Create repair request*.
4. **Call** (case page): *Call landlord*. The AI discloses, cites code, the teammate says "Thursday", the commitment is captured, and the countdown starts. *Simulate +8 days* → *Escalate* → pre-filled city complaint.
5. **You're not alone**: banner says 6 neighbours reported heat and the owner's 3 other buildings have 11 open issues → *File together*. Then `/city`: map, "Where to inspect next", and the Genie question.
6. **Under the hood**: `/about`.
7. **Close**: "FixIt: catch it before you sign, document it while you live there, fight it when they ignore you."

---
FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant Resource Center (608-257-0006) or City
of Madison Building Inspection (608-266-4551).
