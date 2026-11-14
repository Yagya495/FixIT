# Databricks setup runbook (Milestone 1)

Order matters. Steps marked 🧑 need you; steps marked 💸 create resources (ask first on a shared/paid workspace).
Never use the `sleepsafe` profile for this project (`scripts/dbx_check.py` refuses it).

## 0. 🧑 Install the CLI and log in (Windows)
```powershell
winget install Databricks.DatabricksCLI          # official package; restart the terminal afterwards
databricks -v                                     # winget listed 1.26.0 on 2026-11-14
databricks auth login --host https://<your-workspace-host> --profile fixit   # opens a browser (OAuth)
databricks auth profiles                          # 'fixit' should show Valid: YES
databricks current-user me -p fixit               # confirms which user you are
```
Free Edition hosts look like `https://dbc-xxxxxxxx-xxxx.cloud.databricks.com`. The account menu in the workspace UI
says "Free Edition" if it is one.

## 1. Discover (read-only)
```powershell
.venv\Scripts\python scripts\dbx_check.py --profile fixit --json build\dbx_discovery.json
```
Lists: user, serving endpoints (with task type), SQL warehouses, catalogs, vector search endpoints, Genie spaces, apps.

## 2. Verify models (tiny pay-per-token cost; free on Free Edition)
Pick candidates from step 1's list (chat, image-capable, embedding), then:
```powershell
.venv\Scripts\python scripts\dbx_check.py --profile fixit --test-models --chat <chat-ep> --vision <vision-ep> --embed <embed-ep>
```
A name is not proof: chat must echo a random nonce, vision must name a **random** color, embeddings must return a
vector. Run the vision test twice (a text-only model can guess 1 in 4). Record the winners in `.env` and `app/app.yaml`.

## 3. 💸 Catalog, schemas, volumes, tables
Add this repo as a **Git folder** in the workspace, then run in order:
1. `notebooks/00_smoke_tests.py` (same checks in-workspace + `ai_query`, `ai_classify`, `ai_parse_document`)
2. `notebooks/01_setup_catalog.sql`: catalog `fixit`, 6 schemas, 6 volumes. If `CREATE CATALOG` is denied
   (possible on Free Edition), use the default catalog and set `FIXIT_CATALOG` everywhere.
3. `notebooks/30_gold_tables.sql`: DDL + comments + DQ checks (all failure counts should be 0)
4. `notebooks/20_violation_taxonomy.py`: taxonomy + **unverified** seed sections
5. `notebooks/05_generate_synthetic.py`: owners/properties/reports + scores (same generator as the app)
6. Verify the story from your laptop:
   `scripts/dbx_check.py --profile fixit --test-sql <WAREHOUSE_ID>` → "open HEAT reports at 1234 Demo St (30d): 6"

## 4. 💸 Genie
`notebooks/70_genie_space.py` (API), or create the space in the UI with the same tables, instructions and 8 sample
questions. Put the ID in `GENIE_SPACE_ID`. Then the City page caption should read "Answered live by Databricks Genie".

## 5. Live AI from your laptop (still on SQLite)
`.env`:
```
DEMO_MODE=false            # honest testing: no scripted fallbacks
DATA_BACKEND=local
DATABRICKS_CONFIG_PROFILE=fixit
CHAT_ENDPOINT=<verified>
VISION_ENDPOINT=<verified>
EMBEDDING_ENDPOINT=<verified>
GENIE_SPACE_ID=<id>
```
Upload a photo that is NOT in the cache: API `source` must be `live`. Then set `DEMO_MODE=true` and run
`curl -X POST localhost:8000/api/demo/warm` to cache the real demo photos.

## 6. Warehouse backend from your laptop
`.env`: add `DATA_BACKEND=databricks` and `DATABRICKS_WAREHOUSE_ID=<id>`, then
`scripts/dbx_check.py --profile fixit --test-sql <id> --write-test` (inserts, reads back and deletes one row in
`fixit.silver.deadlines`). Run the demo flow; check that new rows appear in `fixit.silver.*`.
Switch back to `DATA_BACKEND=local` at any time: the SQLite fallback is unchanged.

## 7. 💸 Deploy the App
```powershell
cd app\frontend; npm run build; cd ..\..
.venv\Scripts\python scripts\bundle.py                                  # stages build\app
databricks apps create fixit-madison -p fixit                           # once
databricks sync build\app /Workspace/Users/<you>/fixit-madison-app --full -p fixit
databricks apps deploy fixit-madison --source-code-path /Workspace/Users/<you>/fixit-madison-app -p fixit
```
In the App UI: add the SQL warehouse as a resource with key **`sql-warehouse`** (app.yaml reads it) and the
serving endpoints as resources (Can Query).

## 8. 💸 Grant the App's service principal (the #1 cause of silent failures)
Find the SP in the App's "Authorization" tab, then run the GRANTs at the bottom of `01_setup_catalog.sql`
(USE CATALOG; USE SCHEMA + SELECT/MODIFY on silver/gold; SELECT on ref; READ/WRITE VOLUME on raw.evidence and
raw.uploads) and give it **CAN USE** on the warehouse. Verify: create a case in the deployed App and see the row in
`fixit.silver.repair_requests`; upload a photo and see the file under `/Volumes/fixit/raw/evidence/`.
