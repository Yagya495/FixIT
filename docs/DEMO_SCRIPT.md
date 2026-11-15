# FixIt Madison: 3-minute demo script (Databricks track)

_Updated 2026-11-15 (afternoon). Matches the deployed App (`ch27-review` @ `2c74f5d`): video walkthrough live, three
verified Chapter 27 citations, synthetic data. The speed change `003565b` is **not** deployed; timings below are for
the deployed build._

Every claim below is verified (PROGRESS.md). **Don't say anything that isn't in this script about AI accuracy, legal
effect, or features we haven't built.**

Presenter (P) drives; Teammate (T) plays the landlord on the call.
- **Live App (Databricks sign-in):** https://fixit-madison-7474647207905142.aws.databricksapps.com
- **Public demo (no sign-in):** _not deployed yet; pending approval_ (PUBLIC_DEMO mode, see "Fallbacks")

## What's real, what's synthetic, what's simulated (say it once, early)
| Real | Synthetic (labeled "Demo data" in the UI) | Simulated |
|---|---|---|
| Llama 4 Maverick vision + chat on Databricks Model Serving; Delta tables in Unity Catalog; UC Volume evidence with SHA-256; Genie space; the three verified Chapter 27 citations | All 2,004 buildings, 251 owners, 11,941 reports, complaint histories and landlord grades (only street geography is real) | The landlord call (teammate plays the landlord); "+8 days"; complaint and joint-complaint drafts are never submitted |

## The three verified citations (the only ones)
Reviewed against the official Chapter 27 and approved by the project's Legal Reviewer (2026-11-14). The App shows "Possibly relevant:
MGO § …", the exact excerpt, and "Whether this condition violates it is for a City of Madison inspector to decide."
"Legal Reviewer" is the public label for the project's reviewer role. It is **not** a lawyer's review or any
professional or independent legal certification, so never present it as one; say "a team member checked the citation
and quoted text against the official ordinance."
| Issue | Citation |
|---|---|
| No heat (`NO_HEAT`) | **MGO §27.04(2)(h)** (67°F + occupant exception) |
| Plumbing leak (`LEAK_PLUMBING`) | **MGO §27.05(2)(j)** |
| Damaged surfaces (`DAMAGED_SURFACES`) | **MGO §27.05(2)(g)1.** ("good repair", "serious cracking … peeling paint") |

Every other category shows a FixIt plain-language summary marked **"section number pending verification"**. Never call
those citations. **"Report no heat"** always produces the verified §27.04(2)(h) card, whatever the model sees, so it is
the dependable way to show a verified citation on stage.

## Before you start
**Day before:** keep Databricks usage light (no notebooks, no GPU, no bulk tests). Free Edition stops compute for the
rest of the day when the fair-usage quota is exceeded, and that is what stopped the App on 2026-11-15.

**T-30 min**
1. App status: `databricks apps get fixit-madison --profile fixit`. If compute is STOPPED, start it (owner's call):
   `databricks apps start fixit-madison --profile fixit`, wait for RUNNING. If it says *"stopped due to workspace or
   account status"* and won't start, quota is exhausted: use the fallback (below).
2. Open the App and click **Continue** on the Databricks authorization screen (warms the SQL warehouse; cold adds ~10 s).
3. Reset the data: `python scripts/dbx_setup.py --profile fixit --warehouse 6361516ab33ba2d2 --catalog fixit --only reset --apply`
   (story check must print 6 / D / 11 / 0), then `python scripts/genie_verify.py` (8/8).
4. **Stage clip** on the demo device: 8–10 s, slow pan, holding ~2 s each on 2 obvious issues. A visible leak under a
   sink or peeling/cracked paint maps to a verified citation; an uncovered outlet is reliably detected but maps to an
   unverified summary. Keep a backup clip and 2–3 photos.
5. Run the stage clip once through `/scan` (warms the endpoint; ~30–40 s for 8–10 frames), then reset again (step 3).
6. Tabs: `/listing`, `/scan`, `/city`, `/about`. Volume up. Zoom 110%.

## Script
| Time | Do | Say (verbatim is fine) |
|---|---|---|
| **0:00** | Home | "Madison renters have real rights (a housing code, rent abatement, anti-retaliation), but most never use them. FixIt makes them usable, and it runs entirely on Databricks." |
| **0:10** | `/listing`: address `1234 Demo St`, choose listing photos, **X-Ray this listing** | "Before you sign: the landlord's listing photos go to **Llama 4 Maverick on Databricks Model Serving**, and the address is looked up in our **Delta lakehouse in Unity Catalog**." |
| **0:25** | Point at verdict + building history + gray source line | "Don't sign yet: six heat complaints in thirty days, owner graded D. **This building data is synthetic** (see the Demo data badge); we don't use real tenants' information. The gray line says exactly where each AI result came from." |
| **0:35** | `/scan` → **Photos / video** → pick the stage clip (or **Record a walkthrough video** on the phone) | "After move-in, walk through with your phone. The browser pulls one frame per second (up to 30 over the whole clip) and sends them in batches of five." |
| **0:45** | Progress bar running ("Analyzing frames 1–5 of 9…") | "Each frame is SHA-256-hashed and stored in a **Unity Catalog Volume** as tamper-evident evidence, while the model looks for possible issues. Findings appear batch by batch." *(Talk over the ~30–40 s wait.)* |
| **1:10** | Results: tap a finding | "The same problem across several frames becomes **one** finding that cites exactly the frames that show it. The source line says **analyzed live by Llama 4 Maverick**. It's a possible issue, not an inspection; only a City inspector can find a violation." |
| **1:20** | **Report no heat** (or tap a leak/surface finding if the model found one) → open the code card | "Heat can't be photographed, so the tenant reports it. This is one of three citations a person verified against the official ordinance: **MGO 27.04(2)(h)**, quoted exactly, and the app says whether it's violated is for a City inspector to decide. Anything unverified says 'pending verification'." |
| **1:35** | **Create repair request →**, slide tone to **Final request** | "One tap writes the repair letter, from friendly up to a final request before a city complaint." |
| **1:45** | **Call landlord** (voice on). T: "Hello, who's calling?" … "What's the problem?" … "We're busy this week, maybe Thursday." (or **Demo line** ×3) | "This call is **simulated**; my teammate is the landlord. The AI says it's an AI in its first sentence, lists the issues and asks for a date." |
| **2:05** | Point at green box | "The **Databricks chat model** extracted Thursday. FixIt starts a reminder; it's not a legal deadline." |
| **2:10** | **Simulate +8 days** → **Prepare city complaint draft →** | "Thursday passes. FixIt pre-fills a **draft** for the City's complaint form and links the official rent-abatement and retaliation pages. **FixIt never submits anything.**" |
| **2:20** | Dark banner → **File together** | "You're not alone: six households reported heat, and this owner's other buildings have eleven open issues, all synthetic demo data. FixIt drafts a joint complaint; every household has to agree before it's filed." |
| **2:32** | `/city`, first sample question | "For organizers: **Databricks Genie** over our gold tables. This answer came from Genie and was saved for the demo; the caption says so." |
| **2:45** | `/about` | "Under the hood: Unity Catalog with bronze, silver and gold Delta tables, a Volume for evidence, Model Serving, ai_parse_document on the official Chapter 27 PDF, Genie, and a **Databricks App** running as its own service principal with least-privilege grants. Green chips are what's running right now." |
| **2:55** | — | "FixIt: catch it before you sign, document it while you live there, push back when they ignore you." |

**Timing risk:** the video step is the slow one on the deployed build (12 frames ≈ 44–53 s). Use an 8–10 s clip. If
analysis passes ~45 s, move on to the case and come back to the scan tab later; findings keep arriving.

### Optional live-Genie beat (adds ~20 s)
Type a new question (e.g. "How many buildings does Isthmus Edge Properties (demo) own?"). Live Genie takes ≈17–24 s;
the caption reads "Answered live by Databricks Genie."

## Architecture (what to say if asked)
```
Phone/laptop browser (React)  ── frames sampled in-browser (canvas, 1 fps, ≤30, batches of 5)
        │ HTTPS, workspace sign-in
Databricks App "fixit-madison" (FastAPI, own service principal, least-privilege grants)
   ├─ SQL warehouse (2X-Small serverless) → Unity Catalog `fixit`: bronze / silver / gold / ref Delta tables
   ├─ UC Volume `fixit.raw.evidence` ← every photo/frame, SHA-256 hashed
   ├─ Model Serving `databricks-llama-4-maverick` ← vision (frames, listing photos) + chat (call extraction)
   └─ Genie space "FixIt Madison — Ask the data" ← gold tables (saved answers in Demo Mode, labeled)
Offline: ai_parse_document parsed the official Ch. 27 PDF → staging table → human review → 3 verified citations
```
Not built / not enabled, so don't claim: Vector Search (BM25 fallback), MLflow, risk model, real phone calls, YOLO
(evaluated offline, not in the app).

## Words to avoid
- ❌ "violation found", "code violation detected", "inspection" → ✅ "possible issue", "spotted", "only an inspector can confirm"
- ❌ "legal deadline", "the landlord must by law" → ✅ "FixIt reminder", "the date they promised"
- ❌ "files a complaint", "submits to the city" → ✅ "drafts", "pre-fills; you submit"
- ❌ "real landlord data", "these tenants" → ✅ "synthetic demo data"
- ❌ "cites the law for every issue" → ✅ "three citations are verified; the rest are marked pending verification"
- ❌ "the AI is X% accurate", "YOLO", "computer vision model we trained" (not in the product)
- ❌ "Vector Search", "MLflow", "risk model", "real phone calls"

## Fallbacks
| Problem | Do |
|---|---|
| Video analysis slow (>45 s) | Move on to the case; return later. Or upload 2–3 backup photos instead |
| Live model finds nothing / misses an issue | "The model didn't flag that one, and the app says so honestly." Use **Report no heat** to continue |
| Model endpoint fails | Demo Mode takes over automatically; results are labeled **"Demo script"** / **"Saved result"**, so say "this is the saved demo path" |
| App STOPPED / quota exhausted / sign-in fails | **Public demo URL** (once approved and deployed): same UI, synthetic data, scripted AI results labeled on screen and a banner saying so. Otherwise the local server: `.venv\Scripts\python -m uvicorn app.backend.main:app --port 8000` (SQLite, same story; rebuild its frontend first, since the local fallback still runs an older build) |
| Voice silent | Transcript is on screen; continue |
| Genie slow | Use a sample question (saved answer, instant) |
| Phone camera won't open | Camera needs HTTPS (the App URL); use **Photos / video** with a pre-recorded clip |

## Manual verification checklist for the deployed App (~10 min, after it is running)
- [ ] App loads after "Continue"; every page works; refresh on `/city` and `/cases/<id>` isn't blank
- [ ] `/about`: chips running for Store, Act, Connect, Serve; "live model, Demo Mode backup" for See; Genie running
- [ ] Listing X-Ray: verdict, gray source line, Demo data badge, tour questions, addendum PDF
- [ ] Video: stage clip → progress per batch → findings citing their frames → "Analyzed live …" source line
- [ ] **Report no heat** → card shows "Possibly relevant: MGO § 27.04(2)(h)", exact excerpt, City-inspector sentence
- [ ] An unverified category (e.g. exposed wiring) shows "section number pending verification"
- [ ] Case: tone slider Friendly / Formal / **Final request**; letter says "FINAL REQUEST BEFORE A CITY COMPLAINT"
- [ ] Call: double-click "Demo line" fast → one line per click, no error; commitment = next Thursday
- [ ] Deadline box "Follow-up deadline" / "Promised date passed" + not-a-legal-deadline footnote
- [ ] Complaint draft starts "DRAFT for the City's…"; joint complaint starts "DRAFT, NOT SUBMITTED…"
- [ ] Evidence packet PDF: "Tenant Evidence Packet" + "NOT an official inspection record"
- [ ] City: map tiles load; sample question shows "Saved answer from Databricks Genie"
- [ ] Phone width: nav scrolls without a visible scrollbar; no sideways scroll (real-phone checklist: `docs/PHONE_TEST_CHECKLIST.md`)
- [ ] After testing: run the reset command (step 3)
