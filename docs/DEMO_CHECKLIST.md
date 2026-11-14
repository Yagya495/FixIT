# FixIt Madison: 3-minute demo checklist

Verified end to end in a real browser (Chrome) on the local backend in Demo Mode on 2026-11-14. Re-verify on the
deployed Databricks App before judging (see "Day-of" below).

## T-30 min: setup
- [ ] **Reset the data**: `curl -X POST http://127.0.0.1:8000/api/demo/reset` (or the App URL). Rehearsals add reports
      to 1234 Demo St; without a reset the listing says "9 open issues" instead of 6 and the owner card numbers drift.
- [ ] `GET /api/health` shows `"demo_mode": true` and the backend you expect (`local` or `databricks`).
- [ ] Demo listing photos and walkthrough photos are on the presenting laptop (and phone). If they're in
      `demo/demo_inputs/` and were warmed with `/api/demo/warm`, their vision results come from the cache (instant).
- [ ] Laptop: Chrome, zoom 110–125% for the projector, volume up (the AI call speaks with browser TTS).
- [ ] **Phone camera needs HTTPS.** `getUserMedia` won't open over `http://<laptop-ip>:8000`. Use the deployed App URL
      (HTTPS) on the phone, or skip the live camera and use "Photos / video" upload.
- [ ] Map tiles (OpenStreetMap) and fonts load from the internet. If venue Wi-Fi is bad, tether to a phone.
- [ ] Open tabs in order: `/listing`, `/scan`, `/city`, `/about`.
- [ ] Backup video recorded (human task) in case the laptop or network dies.

## The run (≈3:00)
| Time | Screen | Do | Say / point at |
|---|---|---|---|
| 0:00 | Home | — | "Most Madison renters never use the rights they already have." |
| 0:10 | `/listing` | Address is prefilled `1234 Demo St`. Choose the listing photos → **X-Ray this listing** | Progress steps stream. Verdict **Don't sign yet**, **6 heat complaints in 30 days**, owner grade **D**, flagged photos, tour questions, lease addendum. "Found in their own listing photos." |
| 0:50 | `/scan` | Unit 9. **Photos / video** (or Live camera on phone) with the staged corner | 3 detections: covered smoke detector, water stain, outlet without cover. Tap one: Chapter 27 topic, **"section number pending verification"** label (say it out loud: honest about what's verified). |
| 1:20 | Case page | **Create repair request →**. Drag the tone slider Friendly → Final notice | Letter rewrites with code topics and evidence hashes. |
| 1:30 | Case page | **Call landlord**. Click the **Demo line** button 3× (or a teammate speaks/types: "…Thursday") | AI discloses it's an AI in sentence 1, lists issues, answers "what's the problem?", confirms **Thursday, November 19**. Countdown starts. |
| 1:55 | Case page | **Simulate +8 days** → **Escalate → city complaint** | "Deadline missed." Pre-filled complaint. **"FixIt does not submit this for you."** Links to the city's interior-property complaint form, rent abatement and retaliation pages. |
| 2:10 | Case page (top) | Point at the dark banner → **File together** | "**6 other households** reported heat in 30 days. This owner's **3 other buildings have 11 open issues**." Joint draft with anonymized Units A–G. |
| 2:25 | `/city` | Map → "Where to inspect next" → click the first sample question | "Which owners have the most open heat issues this month?" → Isthmus Edge Properties (demo) first. Say what answered it (the caption under the table says so; see below). |
| 2:40 | `/about` | — | Pipeline with honest status chips (running / fallback / planned). |
| 2:55 | — | — | "FixIt: catch it before you sign, document it while you live there, fight it when they ignore you." |

### If something breaks on stage
- Any AI step fails → Demo Mode serves the cached/scripted result automatically (no error shown).
- Call voice doesn't play → keep going; the transcript is on screen. Mute icon is top-right of the call card.
- Camera won't open → "Photos / video" upload.
- App down → local fallback: `python -m uvicorn app.backend.main:app --port 8000` on the laptop (SQLite, same story).

## What's real, what's synthetic, what's simulated
| Thing | Status | Notes |
|---|---|---|
| Owners, buildings, reports, neighbors, grades | **Synthetic** | Every row `is_synthetic=1` / `source='synthetic'`; owner names end in "(synthetic)" or "(demo)"; "Demo data" badges in the UI. The demo story (1234 Demo St, owner Isthmus Edge Properties (demo), management "Isthmus Edge Management") is hand-crafted. No real people. |
| Madison street names / neighborhoods / map | Real geography | Fake owners placed on approximate neighborhood centroids. |
| Vision results in Demo Mode | **Cached or scripted** unless a live model answered | API `source`: `live` = model answered now; `cache` = saved earlier for that exact image hash; `fallback` = scripted staged-corner/listing scenario (any uncached image gets it!); `none` = model failed with Demo Mode off (UI says so). |
| Housing-code matching | Real logic over **placeholder** sections | Sections are FixIt plain-language summaries labeled "pending verification" until the official Ch. 27 PDF is parsed and the mappings are human-reviewed. |
| Letters, tour questions, addendum | Templates (deterministic) | No LLM needed. |
| AI landlord call | **Simulated** | Deterministic agent; a teammate (or the Demo line button) plays the landlord. Commitment date is parsed from what the landlord said and read back on the call. No phone call is made (Twilio is P1, not built). |
| Commitment extraction | LLM if configured, else regex | `commitment_source` records it; the date the AI confirmed aloud always wins. |
| Deadlines / escalation | Real logic, **simulated clock** | "+8 days" shifts that case's clock only. Windows (7d/48h/24h) are FixIt defaults, not legal deadlines. |
| City complaint | Pre-filled draft | **Never submitted.** Links to the official form. |
| "Ask the data" | Genie **only if connected** | Caption under each answer: "Answered live by Databricks Genie" / "Saved Genie answer" / "FixIt's prepared SQL (Genie not connected)". |
| Legal facts (rent abatement, retaliation, 30–60 days) | Paraphrased from official City pages | Sources and check date in PROGRESS.md → "Official sources". Disclaimer on every legal output. |

## Day-of (Databricks)
- [ ] Redeploy the App within 24 h of judging (Apps auto-stop ~24 h after deploy).
- [ ] Run the checklist above against the App URL, once with `DEMO_MODE=true`, once with `false` (expect real model
      output on uncached photos and the Genie caption to say "live").
