# BUILD PROMPT: FixIt Madison — a building inspector and tenant lawyer in your pocket, built on Databricks

You are an expert full-stack + data engineer acting as the lead developer on a 24-hour hackathon team (MadHacks 2026, UW–Madison). Your job is to build **FixIt Madison** end to end, on **Databricks**, in priority order, so that a polished, reliable 3-minute live demo exists by the deadline — even if lower-priority features are unfinished.

Read this entire document before writing code. Then follow the **Build Order** section exactly. Keep a running `PROGRESS.md` in the repo root (what's done, what's next, known issues, how to run) and update it after every milestone.

---

## 0. Ground rules for you (the coding agent)

1. **Demo-first.** Every milestone must end in something that runs and can be shown. Never leave the app in a broken state for long. Commit working states often with clear messages.
2. **Priority tiers are law.** Finish all **P0** before any **P1**; all P1 before any P2. If time is short, cut from the bottom.
3. **Verify, don't assume.** Databricks features, model names, API payloads and Free Edition limits change. Before building on any Databricks feature, check it actually works in this workspace with a tiny test (a 5-line notebook cell or a curl call). If something doesn't work, use the documented **fallback** for it in this spec and note it in `PROGRESS.md`.
4. **No secrets in code.** Use environment variables / Databricks secrets. Provide a `.env.example`. Ask the human for any credentials you need (Databricks host/token, Twilio, voice API keys) — never invent them.
5. **Demo Mode everywhere.** Every AI-dependent step must have a cached/precomputed fallback, toggled by `DEMO_MODE=true`. If an LLM call, vision call, or phone call fails during the live demo, the app silently serves the cached result for the demo inputs. This is non-negotiable.
6. **Synthetic data only for people.** Never use real tenants' names, phone numbers, or personal info. Landlord/property data in the demo is synthetic unless it comes from a genuinely public dataset. Label synthetic data clearly in the UI ("Demo data").
7. **Write small tests** for the critical pure functions (code-section matching, deadline math, evidence hashing, collective-action matching, scoring). Don't spend time on UI tests.
8. When unsure between two approaches, pick the one that is **more reliable on stage**, not the more impressive one on paper.

---

## 1. Product overview

### One-liner
**FixIt Madison catches rental problems before you sign, documents them while you live there, and fights your landlord when they ignore you — powered by a Databricks lakehouse that connects every tenant's reports into city-wide accountability.**

### The problem
- Madison has a lot of student and low-income rentals with recurring problems (no heat, mold, broken locks, missing smoke detectors, pests).
- Madison has strong tenant protections that most renters never use:
  - **Minimum Housing & Property Maintenance Code** — Madison General Ordinances (MGO) **Chapter 27**.
  - **Rent abatement** (MGO 32.04): tenants can recoup rent for certain uncorrected code violations. To qualify: there must be a code violation affecting use of the unit; the tenant must notify the housing provider and give them time to fix it; if not fixed, the tenant contacts Building Inspection and files a complaint, then answers the inspector's call and schedules an inspection.
  - **Anti-retaliation** (MGO Ch. 32): landlords may not retaliate against tenants for complaining to Building Inspection, applying for rent abatement, or asking for code repairs; adverse actions within six months of a complaint may be presumed retaliatory.
  - City Building Inspection says complaint cases generally resolve within 30–60 days.
- The process is confusing, evidence is scattered, tenants act alone, and nobody can see which landlords are repeat offenders.

> The agent must treat these legal facts as **content to display with citations and links**, and must show a clear disclaimer: *"FixIt is not a lawyer and this is not legal advice. For help, contact the Tenant Resource Center (608-257-0006) or City of Madison Building Inspection (608-266-4551)."* Link official city pages rather than paraphrasing law as definitive.

### Users
1. **Renter (primary)** — a UW student or Madison tenant.
2. **Tenant group / union organizer** — wants to see patterns across buildings and file together.
3. **City inspector / council staff (secondary, demo persona)** — wants to know where to inspect next.

### The four "wow" moments (these ARE the demo)
1. **Listing X-Ray** — paste a rental listing → FixIt finds possible code issues *in the landlord's own listing photos* + pulls the address's complaint history → "Don't sign yet" report with tour questions and a lease addendum.
2. **Live walkthrough scan** — point the phone camera at the apartment → violations boxed live, each matched to the exact MGO Chapter 27 section, with severity.
3. **The AI calls your landlord** — a voice agent (disclosing it's an AI acting on the tenant's behalf) calls the property manager, lists violations with ordinance citations, and logs the promised repair date; the deadline clock starts; on expiry it pre-fills the city complaint.
4. **"You're not alone"** — the lakehouse matches your report to neighbors in the same building and other buildings owned by the same landlord → one tap creates a joint complaint. Plus a landlord report card and city heatmap, queryable in plain English with Genie.

---

## 2. Feature list by priority

### P0 — must ship (the demo)
| ID | Feature | Acceptance criteria |
|---|---|---|
| P0-1 | **Housing code knowledge base** | MGO Chapter 27 PDF (and the city's Minimum Housing Standards Checklist PDF) parsed with `ai_parse_document` into `silver.code_sections` (section number, title, text, page). Chunked + embedded + indexed in Vector Search (fallback: in-memory embeddings in the app). Query "missing smoke detector in bedroom" returns the right section in top 3. |
| P0-2 | **Violation taxonomy** | A fixed taxonomy of ~10 violation types, each mapped to code section(s), severity, plain-English explanation, and a "what to ask for" remedy. Stored in `ref.violation_types`. (See §6.) |
| P0-3 | **Walkthrough scan** | Upload photos/video OR live camera in the browser. Frames sampled (1–2 fps for video). Each frame → vision model → detections of taxonomy violations with confidence + bounding box when possible. Results land in `silver.detections` and are deduplicated into `gold.violations`. UI shows boxes/labels, severity chips, matched code section, explanation. |
| P0-4 | **Listing X-Ray** | User pastes a listing URL **or** uploads listing photos (see §8 for scraping rules). Photos → same vision pipeline. Address → property lookup → complaint history from the lakehouse. Output: risk summary, flagged photos with annotations, 5 tour questions, and a generated lease addendum requiring fixes before move-in. |
| P0-5 | **Evidence locker** | Every photo/frame stored in a UC Volume with SHA-256 hash, capture timestamp, and scan ID recorded in `silver.evidence`. One-click **Evidence Packet PDF** (violations, photos, timestamps, hashes, code citations). |
| P0-6 | **Repair request letter** | Generates a formal repair request (tone slider: friendly → formal → final notice) with violations, code citations, evidence references, requested fix-by date. Copy / download PDF / "send" (demo: mark as sent + timestamp). |
| P0-7 | **AI landlord call (demo-safe)** | **Primary for demo reliability: in-browser simulated call** — the "landlord" is a teammate speaking into a second device/browser tab, OR a scripted fallback. The agent (LLM + TTS) opens with AI disclosure, states violations + citations, asks for a repair date, extracts the commitment, writes transcript + extracted commitment to `silver.calls`. **P1-1 upgrades this to a real phone call.** |
| P0-8 | **Deadline tracker + escalation** | Commitment date (or default reasonable window) → countdown. "Simulate time passing" button for demo. On expiry: status → escalate, and a **pre-filled City Building Inspection complaint** (all fields, evidence attached) is generated. Do NOT actually submit to the city. |
| P0-9 | **"You're not alone" collective match** | On a new report, query `gold` for same-building reports (same address/unit group) in last 30 days and same-owner reports across buildings. Show counts + types. One tap → joint complaint draft listing all (anonymized) units and issues. |
| P0-10 | **Landlord report card** | Per owner/management company: open issues, issues by type, median days-to-fix, repeat-offender flag, letter grade (A–F) with transparent formula. Per building page with timeline. |
| P0-11 | **Genie space** | Created programmatically (or via UI if API fails) over the gold tables, with instructions + 8 sample questions. Embedded in the app via the Genie Conversation API ("Ask the data" box). |
| P0-12 | **Synthetic Madison dataset** | Generator notebook creating realistic synthetic owners, properties (real Madison street names/neighborhoods OK, fake owners), reports, repair outcomes. Clearly flagged `is_synthetic=true`. |
| P0-13 | **Demo Mode + caching** | `DEMO_MODE=true` serves cached outputs for the scripted demo inputs if any live call fails. Includes a hidden "demo reset" endpoint. |

### P1 — big upgrades (do after all P0 works end to end)
| ID | Feature | Acceptance criteria |
|---|---|---|
| P1-1 | **Real phone call** | Twilio (or similar) outbound call to an **allowlisted** number only (teammates/judges who consent). Realtime voice agent (speech-to-text → LLM → TTS, or a realtime voice API). AI disclosure in first sentence. Transcript + extracted commitment written back to Databricks. Runs as a separate small service (see §5.4). |
| P1-2 | **Lease X-Ray** | Upload lease PDF → `ai_parse_document` → `ai_extract` clauses → `ai_classify` into categories (repairs responsibility, entry/notice, fees, deposit, renewal, etc.) → flag clauses that *may* conflict with Wisconsin/Madison rules, each with a cited source link and a "possibly problematic — check with the Tenant Resource Center" label. Never state definitively that a clause is illegal. |
| P1-3 | **Building risk prediction** | Model predicting probability a building gets a heat/mold/pest complaint this winter from features (building age, owner history, past reports, unit count, neighborhood). Trained in a notebook, tracked in **MLflow**, registered in Unity Catalog, batch-scored into `gold.building_risk`. Shown as "Where the city should inspect next" map + risk badge on listing X-Ray. |
| P1-4 | **AI/BI dashboard** | City-wide dashboard (violations by type over time, by neighborhood, worst owners, median fix times) created via the Lakeview dashboards API from a hand-built template, or manually if API fails. Linked from the app. |
| P1-5 | **"Ask FixIt" tenant-rights assistant** | RAG chat grounded ONLY in parsed code sections + a small set of saved official city pages (rent abatement, retaliation, reporting complaints). Every answer cites sources. Refuses / redirects when outside scope. Traced in MLflow. |
| P1-6 | **Evaluation + metrics slide** | A labeled eval set (~40–80 images: positive/negative per violation type, from your own staged photos + public images you have rights to) and ~30 "issue → correct code section" pairs. Compute detection precision/recall per type and code-matching top-3 accuracy. Log to MLflow. Show the numbers on an "Our accuracy" panel. |
| P1-7 | **Real public data pipeline** | Run the same bronze→silver→gold pipeline on **Chicago's public Building Violations dataset** (data.gov / Chicago data portal) to prove it works on real city-scale data. If Madison code-enforcement data is available on the City of Madison open data portal, prefer it. Download files locally and upload to a Volume (outbound internet from the workspace may be restricted). |
| P1-8 | **Severity triage + emergency routing** | Emergency types (no heat in winter, gas smell, exposed live wiring, no water) skip the letter flow and show "Call Building Inspection now" + 911 guidance for immediate danger. |
| P1-9 | **Tour checklist generator** | From listing X-Ray + building history, generate a printable checklist for the in-person tour. |

### P2 — only if ahead of schedule
- **Move-in / move-out diff**: compare two walkthrough scans of the same unit to show pre-existing damage (deposit protection).
- **Winter heat logger**: phone/sensor posts indoor temps hourly → chart as evidence when heat fails.
- **Multilingual letters + UI** (Spanish, Hmong, Chinese).
- **Building group**: anonymous opt-in channel for tenants in the same building.
- **Resource router**: map each situation to Tenant Resource Center, mediation, legal aid.
- **Second city**: load another city's housing code PDF and show the pipeline generalizes.
- **Renter's insurance helper**: export evidence as a claim-ready packet.

---

## 3. Databricks environment & constraints (verify all of these first)

Assume **Databricks Free Edition** unless the human says otherwise. Known constraints to verify in the first hour:
- Serverless compute only; limited size. No custom GPU model serving.
- **Up to 3 Databricks Apps**; apps auto-stop ~24 hours after start/deploy → **redeploy right before judging.**
- **One Vector Search (a.k.a. AI Search) endpoint**, one unit; Direct Vector Access not supported → use a **Delta Sync index** on a Delta table.
- One active Lakeflow declarative pipeline per type. → Use SQL/notebooks + Jobs for the main pipeline; optionally export a declarative pipeline definition as a deliverable.
- **Agent Bricks UI is not available** on Free Edition → build agents in code.
- **Outbound internet from the workspace may be limited to trusted domains** → anything that fetches external URLs (listing pages, Twilio webhooks, external model APIs) should run in a small **local/sidecar service** that writes into Databricks via the SQL connector / Files API / REST.
- Some foundation models may be unavailable. **List serving endpoints** and pick: (a) a strong chat model, (b) an embedding model, (c) a model that accepts **image input**. Record choices in `config.py`.

### First-hour verification checklist (write `notebooks/00_smoke_tests.py`)
1. `SELECT current_catalog(), current_user()`; create catalog/schema/volume.
2. `ai_query('<chat-endpoint>', 'Say OK')` works.
3. `ai_parse_document` works on one uploaded PDF page.
4. `ai_extract` / `ai_classify` work on a string.
5. An image-capable endpoint accepts a base64 image and returns text. **If none:** fallback = run an open-vocabulary detector (e.g., YOLO-World or OWL-ViT) locally in the sidecar + a text LLM for reasoning; or call an external vision API from the sidecar.
6. Embedding endpoint works; Vector Search endpoint + Delta Sync index can be created.
7. Genie space create API works (fallback: create in UI, use Conversation API by space ID).
8. A "hello world" Databricks App deploys and can query a table through the SQL warehouse using its service principal. **Grant the app's service principal** `USE CATALOG`, `USE SCHEMA`, `SELECT`/`MODIFY` on the schemas, `READ/WRITE VOLUME`, and `CAN USE` on the SQL warehouse — the #1 cause of silent failures.

---

## 4. Architecture

```
                    ┌──────────────────────────────────────────────┐
                    │          Databricks App (FixIt UI + API)      │
                    │  FastAPI backend  +  React/Vite/Tailwind UI   │
                    │  - Listing X-Ray   - Walkthrough scan         │
                    │  - Evidence/letters - Deadlines/escalation    │
                    │  - Collective match - Landlord cards - Genie  │
                    └───────┬───────────────────────┬──────────────┘
                            │ SQL warehouse         │ Model serving
                            │ (databricks-sql)      │ (chat, vision, embeddings)
                            ▼                       ▼
   ┌──────────────────────────────────────────────────────────────────┐
   │                    Unity Catalog: catalog `fixit`                │
   │  Volumes: raw_uploads, evidence, code_docs, leases, listings      │
   │  bronze → silver → gold Delta tables (see §6)                     │
   │  Vector Search index on silver.code_chunks                        │
   │  MLflow: experiments, traces, registered risk model               │
   │  Genie space + AI/BI dashboard over gold                          │
   └──────────────────────────────────────────────────────────────────┘
                            ▲
                            │ SQL connector / Files API / REST
   ┌────────────────────────┴─────────────────────────────────────────┐
   │  Sidecar service (local laptop or small cloud box)                │
   │  - Listing fetcher (respecting ToS; or manual upload fallback)    │
   │  - Twilio voice webhook + realtime voice agent (P1-1)             │
   │  - Optional local vision detector fallback                        │
   │  - Exposed via a tunnel (cloudflared/ngrok) only for Twilio       │
   └──────────────────────────────────────────────────────────────────┘
```

**Why a sidecar:** Databricks Apps sit behind workspace authentication, so third-party webhooks (Twilio) can't call them directly, and workspace outbound internet may be restricted. Keep the sidecar tiny and stateless; all state lives in Delta.

### Tech choices
- **Backend:** Python 3.11, FastAPI, `databricks-sdk`, `databricks-sql-connector`, `mlflow`, `pydantic`, `reportlab` or `weasyprint` for PDFs, `hashlib`.
- **Frontend:** React + Vite + TypeScript + Tailwind; build to static files served by FastAPI (single app). Map: Leaflet + OpenStreetMap tiles (or MapLibre). Charts: Recharts. Camera: `getUserMedia`, capture frames to canvas → upload JPEGs.
- **If time is very tight:** Streamlit is acceptable for the app, but the React version demos much better. Decide in the first hour and don't switch.
- **Deployment:** Databricks CLI (`databricks apps deploy` or bundles). Document exact commands in `README.md`.

---

## 5. Component specs

### 5.1 Code knowledge base (P0-1)
1. Human downloads MGO Chapter 27 (Municode) as PDF + City of Madison "Minimum Housing Standards Checklist" PDF + saved copies of the city pages on rent abatement, retaliation, and reporting complaints. Upload to `/Volumes/fixit/raw/code_docs/`.
2. `notebooks/10_parse_code.sql`:
   - `ai_parse_document` → `bronze.code_docs_parsed`.
   - Split into sections by heading pattern (e.g., `27.05(2)(a)`) → `silver.code_sections(section_id, title, text, source_doc, page, url)`.
   - Chunk (~800 tokens, overlap 100) → `silver.code_chunks(chunk_id, section_id, text, source_doc, page)`; enable Change Data Feed.
3. Create Vector Search **Delta Sync** index on `silver.code_chunks.text` using the embedding endpoint.
4. Function `match_code(issue_description) -> list[{section_id, title, snippet, url, score}]` (top 3). Unit-test with taxonomy examples.
5. Fallback: if Vector Search fails, compute embeddings once into a Delta table and do cosine similarity in the app.

### 5.2 Vision pipeline (P0-3, P0-4)
- **Input:** images (JPEG/PNG) or video (sample 1–2 fps server-side with OpenCV/ffmpeg, max 30 frames).
- **Prompting the vision model:** give it the taxonomy (IDs, names, visual cues), ask for strict JSON:
  ```json
  {"detections":[{"violation_type":"SMOKE_DETECTOR_MISSING","confidence":0.0-1.0,
    "bbox":[x,y,w,h] or null,"evidence_note":"short description","severity_hint":"routine|urgent|emergency"}],
   "scene":"bedroom|kitchen|bathroom|hallway|exterior|other"}
  ```
  Validate with Pydantic; on invalid JSON, retry once with a "fix your JSON" message; then fall back to empty detections.
- **Confidence threshold** per type (start 0.6); below threshold → "possible issue — check in person".
- **Dedup** across frames: same type + overlapping scene within a scan → one violation with multiple evidence frames.
- Write `silver.detections` (one row per detection per frame) and `gold.violations` (deduped, with matched code section, severity, explanation, remedy).
- **Bounding boxes:** if the model's boxes are unreliable, show labeled frame thumbnails instead of boxes — don't show wrong boxes on stage.
- **Local fallback:** open-vocabulary detector (YOLO-World/OWL-ViT) with text prompts per violation type, run in the sidecar, results posted to the same tables.
- Trace every call with MLflow tracing (`mlflow.trace` / autolog) so you can open a trace in the demo.

### 5.3 Listing X-Ray (P0-4)
- **Input A (preferred for reliability):** user uploads listing photos + types the address.
- **Input B:** user pastes a listing URL → the **sidecar** fetches the page and extracts image URLs + address **only if the site's terms allow it**; otherwise show "Upload the listing photos instead." For the demo, pre-save one listing's photos (staged or with permission) in `/Volumes/fixit/raw/listings/demo/`.
- Pipeline: photos → vision pipeline (listing mode: prompt tuned for "signs of problems in marketing photos": stains, missing detectors, damaged surfaces, exposed wiring, mold, pests evidence, broken windows/locks) → address normalization → property match in `gold.properties` (fuzzy match on normalized address) → history from `gold.building_history` + `gold.landlord_scores` + `gold.building_risk` (P1-3).
- Output card: **"Sign / Ask first / Don't sign yet"** verdict with transparent reasons, annotated photos, building history summary, owner report-card grade, 5 generated tour questions, and a generated **lease addendum** ("Landlord agrees to repair the following before move-in: …").
- Clearly mark findings as "possible issues spotted in photos — verify in person."

### 5.4 AI landlord call (P0-7 simulated, P1-1 real)
**Agent script requirements (both modes):**
1. First sentence: *"Hi, this is an automated AI assistant calling on behalf of your tenant at [address], unit [X]. This call may be recorded for their records."*
2. States violations in plain language with code section references.
3. Asks: "When can these repairs be completed?" Handles: gives a date / vague answer / refuses / asks to talk to tenant / hostile. Stays polite and factual; never threatens; never claims to be a lawyer or the city.
4. If no date: states the tenant will follow up in writing and may contact City Building Inspection.
5. Closes by confirming the commitment back.
6. Post-call: LLM extracts `{commitment_date, commitment_text, landlord_tone, follow_up_needed}` → `silver.calls` + creates `silver.deadlines` row.

**P0 simulated call:** browser page with two roles — "Tenant's AI" (LLM + TTS via browser speechSynthesis or a TTS endpoint) and "Landlord" (a teammate speaking, captured with Web Speech API / browser STT, or typed). Live transcript on screen. Scripted fallback transcript in Demo Mode.

**P1 real call:** sidecar with Twilio Programmable Voice + a realtime voice pipeline. **Hard allowlist** of phone numbers in config (only consenting teammates/judges); reject all others in code. Store transcript in Delta. Kill switch env var.

### 5.5 Deadlines & escalation (P0-8)
- `silver.deadlines(request_id, violation_ids, due_date, status[open|met|missed|escalated], created_at)`.
- Default window if landlord gives no date: configurable (e.g., 7 days routine, 48h urgent, immediate for emergency) — label as FixIt defaults, not legal deadlines.
- "Simulate +8 days" demo button.
- On missed: generate **pre-filled Building Inspection complaint** (tenant info placeholders, address, unit, issue list with code sections, dates landlord was notified, evidence packet attached, link to the official city "Report a problem — interior housing" page). Show "Next: rent abatement eligibility checklist" with the city's official steps and link. Never auto-submit.

### 5.6 Collective action match (P0-9)
SQL (parameterized) on new report:
- Same building: `gold.reports` where `property_id = :pid` and `reported_at >= now() - 30 days` grouped by `violation_category`.
- Same owner: join `gold.properties` on `owner_id`, open issues by building.
- UI: "6 other households in your building reported HEAT issues this week. This owner's 3 other buildings have 11 open issues." → button **"File together"** → joint complaint draft (units anonymized as "Unit A, Unit B…", issue list, date ranges). In the demo, other households are synthetic.

### 5.7 Landlord report card (P0-10)
`gold.landlord_scores` computed in a notebook/job:
- `open_issues`, `issues_last_12mo`, `issues_per_unit`, `median_days_to_fix`, `pct_fixed_within_30d`, `repeat_buildings` (buildings with ≥3 issues), `emergency_issues`.
- Grade: weighted z-score → A–F. **Show the formula** in the UI ("How grades work").
- Building page: timeline of reports/fixes, violation mix chart, map pin.

### 5.8 Genie (P0-11)
- Space over: `gold.reports`, `gold.violations`, `gold.properties`, `gold.owners`, `gold.landlord_scores`, `gold.building_risk` (P1), `ref.violation_types`.
- Instructions: table relationships, definitions ("open issue = status in (open, escalated)"), "neighborhood" column meaning, synthetic-data note.
- Sample questions:
  1. Which owners have the most open heat issues this month?
  2. What is the median days-to-fix by neighborhood?
  3. Which buildings have 3+ mold reports in the last year?
  4. How many emergency issues are open right now?
  5. Show violation counts by type for the last 6 months.
  6. Which management companies improved their fix times the most?
  7. Which buildings near campus have the highest predicted winter risk?
  8. What percent of issues are fixed within 30 days, by owner grade?
- App embeds an "Ask the data" box calling the Genie Conversation API (start conversation → poll message → render answer text + table + generated SQL). Cache demo questions.

### 5.9 Risk model (P1-3)
- Features per property: building_age, units, owner_grade, past_12mo_issue_counts by category, past_heat_issues, neighborhood, distance_to_campus, median_days_to_fix_owner.
- Label: had heat/mold/pest report in the following winter window (synthetic history must be generated with a learnable but noisy signal).
- Model: gradient boosting (LightGBM/XGBoost/sklearn) — log params, metrics (AUC, precision@top-50), feature importances to MLflow; register to UC as `fixit.ml.building_risk`; batch score → `gold.building_risk`.
- UI: "Where to inspect next" map (top 50 buildings), risk badge on building pages and listing X-Ray.

### 5.10 Evaluation (P1-6)
- `eval/images/<violation_type>/{pos,neg}/*.jpg` + `eval/labels.csv`; `eval/code_matching.csv` (issue text → correct section_id).
- `notebooks/60_eval.py` computes per-type precision/recall, overall F1, code-matching top-1/top-3 accuracy; logs to MLflow; writes `gold.eval_metrics`.
- App "Accuracy" panel shows these numbers. Be honest about sample size.

---

## 6. Data model (Unity Catalog: catalog `fixit`)

Schemas: `raw` (volumes), `bronze`, `silver`, `gold`, `ref`, `ml`.

**Volumes**
- `fixit.raw.uploads` — walkthrough photos/videos
- `fixit.raw.listings` — listing photos
- `fixit.raw.code_docs` — ordinance PDFs, saved city pages
- `fixit.raw.leases` — lease PDFs
- `fixit.raw.evidence` — canonical evidence copies (hash-named)
- `fixit.raw.public_data` — Chicago/Madison public datasets

**ref**
- `violation_types(type_id, name, category[HEAT|SMOKE_CO|ELECTRICAL|MOLD_MOISTURE|PESTS|SECURITY|PLUMBING|STRUCTURAL|EGRESS|SANITATION], visual_cues, default_severity, code_sections ARRAY<STRING>, plain_explanation, remedy_request)`

Seed taxonomy (adjust code sections after parsing Chapter 27 — do not guess section numbers; map them from the parsed text):
| type_id | name | category | default_severity |
|---|---|---|---|
| SMOKE_DETECTOR_MISSING | Missing/disabled smoke detector | SMOKE_CO | urgent |
| CO_DETECTOR_MISSING | Missing CO detector near sleeping area | SMOKE_CO | urgent |
| EXPOSED_WIRING | Exposed wiring / missing outlet or switch cover | ELECTRICAL | urgent (emergency if live/sparking) |
| WATER_DAMAGE_MOLD | Water stains / visible mold | MOLD_MOISTURE | urgent |
| PEST_EVIDENCE | Droppings / insects / pest damage | PESTS | urgent |
| BROKEN_LOCK | Broken/missing entry or window lock | SECURITY | urgent |
| BROKEN_WINDOW | Broken/cracked window or screen | STRUCTURAL | routine (urgent in winter) |
| LEAK_PLUMBING | Active leak / damaged fixtures | PLUMBING | urgent |
| DAMAGED_SURFACES | Holes, peeling paint, damaged flooring | STRUCTURAL | routine |
| BLOCKED_EGRESS | Blocked exit / missing handrail | EGRESS | urgent |
| NO_HEAT | No heat (user-reported / temp evidence) | HEAT | emergency (Oct–May) |

**bronze**
- `code_docs_parsed`, `listing_pages_raw`, `public_violations_raw`, `call_audio_meta`

**silver**
- `code_sections`, `code_chunks` (CDF on)
- `scans(scan_id, user_id, property_id, unit, mode[walkthrough|listing|movein|moveout], created_at)`
- `evidence(evidence_id, scan_id, volume_path, sha256, captured_at, uploaded_at, media_type)`
- `detections(detection_id, scan_id, evidence_id, violation_type, confidence, bbox, note, model_endpoint, created_at)`
- `repair_requests(request_id, user_id, property_id, violation_ids, tone, letter_text, sent_at)`
- `calls(call_id, request_id, mode[simulated|phone], transcript, commitment_date, commitment_text, landlord_tone, created_at)`
- `deadlines(request_id, due_date, status, created_at, updated_at)`
- `complaints(complaint_id, request_id, payload_json, generated_at, joint BOOLEAN, units ARRAY<STRING>)`
- `lease_clauses(lease_id, clause_id, text, category, flag_level, rationale, source_url)` (P1)

**gold**
- `owners(owner_id, name, management_company, is_synthetic)`
- `properties(property_id, address_norm, lat, lon, neighborhood, units, year_built, owner_id, is_synthetic)`
- `reports(report_id, property_id, unit_hash, violation_category, violation_type, severity, reported_at, fixed_at, status, source[fixit|public|synthetic])`
- `violations(violation_id, scan_id, property_id, violation_type, severity, confidence, code_section_ids, explanation, evidence_ids, status)`
- `building_history` (view), `landlord_scores`, `building_risk`, `eval_metrics`, `neighborhood_stats`

Add Delta table comments + column comments on all gold tables (Genie uses them). Add simple data-quality checks (non-null keys, valid enums, lat/lon in Madison bbox) in the pipeline notebooks; log failures.

### Synthetic data generator (`notebooks/05_generate_synthetic.py`)
- ~250 owners (≈15% "bad actors" with high issue rates and slow fixes), ~2,000 properties placed on real Madison neighborhoods (Langdon, Mifflin, Regent, Vilas, Bay Creek, Tenney-Lapham, Eken Park, Allied Drive area, etc.) using approximate neighborhood centroids + jitter, ~12,000 reports over 3 years with seasonality (heat spikes Dec–Feb, mold spikes spring), fix-time distributions tied to owner quality.
- Hand-craft the **demo building** (e.g., "1234 Demo St") and its owner with a story: 6 recent heat reports, owner has 3 other buildings with 11 open issues.
- Every row `is_synthetic=true`; UI shows a "Demo data" badge.

---

## 7. App UX (pages)

1. **Home** — three big actions: "Check a listing", "Scan my apartment", "My cases". Tagline + disclaimer footer.
2. **Listing X-Ray** — upload/URL → progress steps (streamed) → verdict card, annotated photos carousel, building history, owner grade, tour questions, addendum (copy/PDF).
3. **Scan** — live camera or upload → live detections list with severity chips → each item expands to show matched code section (quote snippet + link), explanation, remedy → "Create repair request".
4. **Case page** — violations, evidence packet, letter (tone slider), "Call landlord" (simulated/real), transcript, deadline countdown, "Simulate time passing", escalation → complaint draft, rent abatement steps (official links).
5. **You're not alone** — banner on case page + dedicated view with neighbor counts, owner's other buildings, "File together".
6. **Landlords & Buildings** — search, report cards, grade explainer, building timeline, map.
7. **City view** — heatmap, "Where to inspect next" (P1-3), dashboard link (P1-4), "Ask the data" (Genie).
8. **Ask FixIt** (P1-5) — tenant-rights chat with citations.
9. **About / Trust** — how it works (Databricks architecture diagram), accuracy panel (P1-6), privacy & AI-call policy, not-legal-advice disclaimer.

Design: clean, high-contrast, mobile-first (the scan page will be used on a phone), Badger red accent is fine, big readable type for projector. Show **streamed progress** ("Parsing photos… Matching to Chapter 27… Checking building history…") so the AI feels alive on stage.

---

## 8. Safety, privacy, ethics (build these in, mention them on stage)

- **Not legal advice** disclaimer on every legal output; link official sources; never say a clause is definitively illegal.
- **AI call disclosure** in the first sentence; **allowlist** for real calls; kill switch; no calls to real landlords during the hackathon.
- **No real personal data**; synthetic data labeled; unit numbers hashed in `gold.reports`; joint complaints anonymize units.
- **Listing fetching** only where terms permit; default to user-uploaded photos.
- **Uncertainty shown honestly**: "possible issue — verify in person" under the confidence threshold.
- **Retaliation info**: show the city's anti-retaliation guidance and Tenant Resource Center contact on escalation pages.
- **Evidence integrity**: SHA-256 hash + timestamps; packet lists hashes.

---

## 9. Repo structure

```
fixit-madison/
  README.md                # setup, deploy, demo script
  PROGRESS.md              # living status log
  .env.example
  app/
    app.yaml               # Databricks App config (command, env)
    requirements.txt
    backend/
      main.py              # FastAPI app, serves frontend build
      config.py            # endpoints, catalog names, thresholds, DEMO_MODE
      db.py                # SQL warehouse connection helpers
      models.py            # pydantic schemas
      services/
        vision.py          # frame sampling, VLM calls, dedup
        code_match.py      # vector search / fallback
        listing.py
        evidence.py        # hashing, volume IO, packet PDF
        letters.py
        calls.py           # simulated call orchestration, extraction
        deadlines.py
        collective.py
        landlords.py
        genie.py           # conversation API client
        lease.py           # P1
        rag.py             # P1 Ask FixIt
        demo_cache.py
      routes/              # one router per page/feature
      tests/
    frontend/              # React + Vite + Tailwind
  sidecar/
    main.py                # listing fetcher, Twilio webhooks (P1), local vision fallback
    requirements.txt
  notebooks/
    00_smoke_tests.py
    01_setup_catalog.sql
    05_generate_synthetic.py
    10_parse_code.sql
    11_build_vector_index.py
    20_violation_taxonomy.sql
    30_gold_tables.sql
    40_landlord_scores.sql
    50_risk_model.py        # P1
    55_public_data_pipeline.py  # P1 Chicago/Madison
    60_eval.py              # P1
    70_genie_space.py
    80_dashboard.py         # P1
  eval/
  demo/
    demo_inputs/            # the exact listing photos, walkthrough clips, lease PDF used on stage
    cached_outputs/         # Demo Mode responses
    backup_video.mp4        # recorded full demo (human records)
```

---

## 10. Build order (≈18 hours remaining — timebox strictly)

**Milestone 1 (hours 0–1.5): Foundations**
- Smoke tests (§3). Choose model endpoints. Create catalog/schemas/volumes. Hello-world App deployed with SP permissions working. Repo scaffold. `PROGRESS.md` started.

**Milestone 2 (1.5–4): Data backbone**
- Taxonomy table. Synthetic generator + demo building story. Gold tables + landlord scores. Code PDFs parsed → sections → chunks → vector index (or fallback). `match_code` tested.

**Milestone 3 (4–7): Scan → violations → evidence**
- Vision service with JSON validation + dedup. Scan page (upload first, live camera second). Evidence locker + hashing. Violations show matched code sections. Evidence packet PDF.

**Milestone 4 (7–9.5): Case flow**
- Repair letter with tone slider. Simulated AI landlord call with live transcript + commitment extraction. Deadlines + "simulate time" + escalation complaint draft + rent-abatement steps page.

**Milestone 5 (9.5–11.5): Listing X-Ray + collective**
- Listing upload flow → verdict card, tour questions, addendum. Collective match banner + joint complaint. Landlord report card + building pages + map.

**Milestone 6 (11.5–13): Genie + Demo Mode**
- Genie space + embedded "Ask the data". Demo Mode caching for every scripted demo input. End-to-end dry run of the full 3-minute demo. **At this point P0 is done — freeze P0, fix only bugs.**

**Milestone 7 (13–16): P1 in this order**
1. P1-1 real phone call (allowlisted) — only if P0 call is rock-solid.
2. P1-3 risk model + "where to inspect next".
3. P1-6 eval metrics panel.
4. P1-2 Lease X-Ray.
5. P1-4 dashboard, P1-5 Ask FixIt, P1-7 public data pipeline, P1-8, P1-9 as time allows.

**Milestone 8 (16–18): Polish & submission**
- UI polish for projector, loading states, error states. Redeploy the App (24h auto-stop!). Re-run the full demo 3× with Demo Mode on and off. Human records backup video. Write Devpost: problem, what it does, how it's built (Databricks architecture diagram), challenges, accomplishments, what's next. README with run/deploy steps.

---

## 11. The 3-minute demo script (build to make this flawless)

1. **0:00 — Hook.** "Most Madison renters never use the rights they already have. FixIt makes them automatic."
2. **0:10 — Listing X-Ray.** Upload the demo listing photos → stream → verdict "Don't sign yet": a water stain in photo 7, no smoke detector visible in the bedroom; this building has 6 heat reports; owner grade D. Show tour questions + addendum. *"Found in their own listing photos."*
3. **0:50 — Walkthrough scan.** Phone camera on a staged corner (covered smoke detector, fake water stain, outlet without cover) → live detections → tap one → exact Chapter 27 section quoted.
4. **1:25 — The call.** "Call landlord" → AI discloses, cites the ordinance, teammate-as-landlord says "Thursday" → commitment extracted → countdown starts. Simulate +8 days → missed → complaint pre-filled.
5. **2:10 — You're not alone.** Banner: 6 neighbors reported heat issues; owner's other buildings have 11 open issues → "File together". Jump to City view: heatmap, "Where to inspect next", Genie question: "Which owners have the most open heat issues this month?"
6. **2:40 — Under the hood.** One slide/panel: Databricks architecture (ai_parse_document → Vector Search → vision → Delta bronze/silver/gold → MLflow → Genie → Apps) + accuracy numbers.
7. **2:55 — Close.** "FixIt: catch it before you sign, document it while you live there, fight it when they ignore you."

---

## 12. Definition of done

- All P0 acceptance criteria pass on the deployed Databricks App.
- Full demo script runs end to end in under 3 minutes, three times in a row, with Demo Mode both on and off.
- `README.md` lets a new teammate deploy from scratch; `PROGRESS.md` is current.
- No secrets in the repo; allowlist enforced for real calls; disclaimers visible.
- Devpost draft written.

**Start now with Milestone 1. First, print the smoke-test plan and list the credentials/inputs you need from me (Databricks host + token or CLI profile, SQL warehouse ID, chosen model endpoints if known, Chapter 27 PDF, demo listing photos, Twilio/voice keys for P1). Then begin.**
