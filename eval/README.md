# Vision evaluation (Llama 4 Maverick, live, Demo Mode off)

Goal: an honest answer to "does the model actually spot these problems in real photos?", before we show it on stage.
This is a script-only sanity check (not the P1 MLflow eval panel).

## 1. Collect photos (≈ 30–60 is enough)
Put them in `eval/photos/<TYPE_ID>/` (one folder per violation type) and `eval/photos/NONE/` (clean rooms).

| Folder | What to photograph | Aim for |
|---|---|---|
| `SMOKE_DETECTOR_MISSING` | detector bagged/taped, detector hanging by wires, empty ceiling mount plate (the app shows a mount as "verify in person") | 4–6 |
| `CO_DETECTOR_MISSING` | a labeled CO alarm that is covered, hanging, or removed from its mount. **Not** a room without a CO alarm: the app never reports absence | 0–3 |
| `EXPOSED_WIRING` | outlet or switch with no cover plate; loose wires | 4–6 |
| `WATER_DAMAGE_MOLD` | brown ring stain on ceiling, mold spots in a shower corner | 4–6 |
| `PEST_EVIDENCE` | droppings, dead insects, traps in use | 3–5 |
| `BROKEN_LOCK` | broken/missing deadbolt or window latch | 3–5 |
| `BROKEN_WINDOW` | cracked pane, torn screen | 3–5 |
| `LEAK_PLUMBING` | dripping faucet, puddle under sink, damaged fixture | 3–5 |
| `DAMAGED_SURFACES` | holes in drywall, peeling paint, damaged flooring | 4–6 |
| `BLOCKED_EGRESS` | furniture blocking an exit, stairs missing a handrail | 2–4 |
| `NONE` | normal, tidy rooms (some with a detector, **some with no detector in frame**: these must produce no smoke/CO finding), covered outlets | **10+** (false-alarm check) |

Photos with more than one issue: add a row to `eval/labels.csv` (`file,labels` with labels separated by `;`).

**Staging is fine and expected**: a bag over a smoke detector, an outlet with the cover removed (power off, no
touching wires), a printed water-stain photo taped to a ceiling. Label honestly: if a staged prop is unconvincing, put
the photo in the folder anyway; that's the point of the test.

## 2. Privacy and consent (required)
- Only photograph spaces you have permission to photograph. No people, faces, mail, documents, screens, license plates,
  street numbers or anything that identifies a real tenant or landlord.
- Phones embed GPS in photos. The eval script strips JPEG EXIF before sending, and the app's browser upload re-encodes
  images (which also drops EXIF), but turn off location tagging anyway.
- `eval/photos/` is git-ignored: photos stay on your laptop. Only the numeric results are committed.

## 3. Run (Demo Mode off, live calls only)
```powershell
.venv\Scripts\python scripts\eval_vision.py --profile fixit                                   # Llama 4 Maverick
.venv\Scripts\python scripts\eval_vision.py --profile fixit --vision databricks-gemma-3-12b   # comparison model
.venv\Scripts\python scripts\eval_vision.py --profile fixit --mode listing                    # marketing-photo prompt
```
Output: `eval/results/<timestamp>_<model>_<mode>.md|json`: per-type precision/recall, false-alarm rate on clean photos,
exact-match rate, failures, latency. Every photo is sent live to the serving endpoint; nothing comes from the cache.

## 4. Decide
- A type with recall < 0.5 or more than 1 false alarm on clean photos: don't feature it on stage; use another staged issue.
- If Gemma beats Maverick, set `VISION_ENDPOINT` in `app/app.yaml` and redeploy.
- Then put the exact stage photos in `demo/demo_inputs/{listing,walkthrough}/` and run `POST /api/demo/warm` to save
  their live results for Demo Mode. The app matches them even after the browser re-encodes the upload.

Scoring applies the app's alarm screening (`vision.screen_detection`): a smoke/CO detection counts only when the
photo shows a visible alarm problem; screened-out raw detections are listed per photo as `screened_out`.
