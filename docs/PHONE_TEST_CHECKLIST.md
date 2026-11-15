# Real-phone test: video walkthrough (Android + iPhone)

Use the deployed App over HTTPS (sign in first). In Scan, set **Address `1770 Fair Oaks Ave`** and a test unit
(`PHONE-A1`, `PHONE-I1`, …) so the demo building stays clean. Don't create a repair request from test scans. Note
the phone model, OS version and browser for each row.

## Setup
- [ ] App opens and sign-in works on the phone (Android Chrome; iPhone Safari; optionally iPhone Chrome)
- [ ] Health is fine: the Scan page loads with "Record a walkthrough video" visible, no horizontal scrolling
- [ ] Prepare one real visible issue (e.g. an outlet with the cover plate removed, a water-stained ceiling tile or a
      photo of one on a screen) and one clean wall

## Recording (the "Record a walkthrough video" button)
- [ ] Opens the camera in **video** mode (not photo) · Android: ☐ · iPhone: ☐
- [ ] Record 10–15 s, walk slowly, hold 2–3 s on the issue, then "Use video"
- [ ] "Extracting frames from the video…" appears, then "Sampled N frames (1 per second) from a N-second video."
      N ≈ length in seconds (max 30) · Android: ☐ · iPhone: ☐
- [ ] Progress shows "Analyzing frames 1–5 of N…" and advances; findings appear after the first batch
- [ ] Source line says **"Analyzed live just now by llama-4-maverick…"** (not "Saved result" / "Demo script" /
      "Partly analyzed"). If "Partly analyzed" appears, note how many frames failed.
- [ ] Total time for a 12 s clip (target < 60 s): ____ s

## Upload of an existing video ("Photos / video")
- [ ] A clip recorded earlier in the camera app can be picked from the gallery
- [ ] **iPhone HEVC/MOV:** record with Settings > Camera > Formats = **High Efficiency** (HEVC .mov) and upload →
      frames extracted? ☐ yes ☐ no / error "Couldn't read …"  Then repeat with **Most Compatible** (H.264) ☐
- [ ] **Android:** a 4K/60fps or HDR clip → frames extracted? ☐ (some HDR/HEVC clips fail to decode in browsers)
- [ ] A clip longer than 30 s → message says frames were "spread across the m:ss video" (max 30)
- [ ] Portrait and landscape clips both produce upright frames (check thumbnails) ☐

## Accuracy of findings and evidence frames
- [ ] The real issue is detected (type: ________) · the clean wall produces nothing
- [ ] Expanding the finding: each listed frame thumbnail actually shows the issue (open 2–3 of them) ☐
- [ ] A finding seen in several frames appears **once**, with "Seen or reported N times in this scan"
- [ ] No smoke/CO finding just because no alarm is in view ☐
- [ ] Re-uploading the same clip in the same scan adds no new findings ("repeated frames… skipped")

## Failure handling
- [ ] Airplane mode during analysis → an error says where it stopped ("Stopped after N of M frames…"); earlier frames kept
- [ ] Unsupported file (e.g. a .txt renamed .mp4) → "Couldn't read …" message, no crash
- [ ] Live camera (still capture) still works ☐

## If HEVC/MOV fails
Expected on some desktop browsers; iPhone Safari normally decodes its own HEVC. If a phone can't read its own clip:
record with "Most Compatible", or upload photos instead. Report the exact phone/OS/browser; a server-side transcode
would be a post-demo change.
