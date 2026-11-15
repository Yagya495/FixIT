# Video processing performance and demo recommendations (2026-11-15)

## Measured (same synthetic clips, same Llama 4 Maverick endpoint)
| Run | Frames | Local backend (SQLite) | Deployed App (Databricks SQL + UC Volume) |
|---|---|---|---|
| 12 s clip | 12 | 24 s (batches 9.4 / 8.3 / 2.3 s) | 44–53 s (batches 14–20 / 17–20 / 5–8 s) |
| 40 s clip | 30 | 56 s (~8–10 s per batch of 5) | 98 s (11–20 s per batch of 5) |

The first finding appears after the first batch (~15–20 s deployed). Every frame was analyzed live; 9 endpoint 429s were
absorbed by retries (each retry waits 1–4 s, which explains the variable batch times).

## Where the time goes (deployed)
- **Model calls:** ~3.5–4 s each, 2 in parallel → ~9 s per batch of 5 (the same locally). More parallelism mostly buys
  429s on the pay-per-token endpoint.
- **Storage before analysis (~5–8 s per batch, deployed only):** for each frame, in sequence: a SELECT (duplicate
  check), a UC Volume upload, then an INSERT. Model calls don't start until all 5 frames are stored.
- **Writes after analysis:** one INSERT per detection, then rebuilding the scan's findings (SELECT, DELETE, one INSERT per
  finding). Each SQL statement on the warehouse costs ~0.3–1 s.

## Recommendations for the 3-minute demo (no code change)
1. **Use a short clip on stage:** 8–10 s, slow pan, hold on 2 issues → 8–10 frames, 2 batches, ~30–40 s deployed, first
   finding in ~15–20 s. Narrate while it runs (the progress line helps).
2. **Warm everything 5–10 min before:** open the App (Apps cold-start), run one scan at the disposable address (warms
   the SQL warehouse, the model endpoint and the Volume path). Redeploy on judging day only if the App stopped.
3. **Pre-record the stage clip and test it on the same phone/laptop** the day before; keep a backup clip that is known to
   produce a clear finding, and the photo-upload path as plan B (Demo Mode's cached photos are instant).
4. **Avoid HEVC surprises:** record with "Most Compatible" on iPhone (see `PHONE_TEST_CHECKLIST.md`).
5. Keep Demo Mode on: if the endpoint fails, the UI labels scripted results "Demo script", never as live.

## Safe code improvements (need approval; local first, then one reviewed redeploy)
| # | Change | Expected gain | Risk |
|---|---|---|---|
| A | Start model calls immediately; store evidence (Volume upload + row) in parallel instead of before analysis | −5–8 s per batch deployed (~35–40% of a 12-frame run) | Low: frame order and association already tested; keep writes in order |
| B | One multi-row INSERT for a batch's evidence rows and one for its detections (`db.insert_many` exists) | −2–4 s per batch | Low |
| C | Skip the duplicate-check SELECT per frame: one SELECT for the whole batch | −1–2 s per batch | Low |
| D | Client-side near-duplicate frame skip (tiny perceptual hash; only when the camera barely moved) | Fewer model calls on slow pans | Medium: could drop a frame that differs slightly; keep conservative threshold |
| E | Downscale frames to 1024 px (from 1280) | Smaller uploads; possibly faster model | Medium: may hurt small details; measure on staged photos first |
| F | Demo Mode: cache a live result by frame hash so a rehearsed clip replays instantly on stage (labeled "Saved result") | Stage run in seconds | Medium: must stay clearly labeled; only for the rehearsed clip |

Recommended for the demo: **A + B + C** (pure speed, no behavior change), measured locally against the live endpoint and
then on the App. Not recommended before the demo: raising parallelism (429s), D/E without measurements.
