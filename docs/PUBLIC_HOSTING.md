# Public access for judges: findings and plan (2026-11-15)

Goal: a URL judges and Devpost visitors can open **without a Databricks sign-in**, while the Databricks App stays as is.
Nothing here is deployed or provisioned. Every account, deploy and DNS step needs the owner's approval.

## 1. The Databricks App was stopped (investigation, read-only, profile `fixit`)
**Confirmed (CLI/API, 2026-11-15):**
- `apps get fixit-madison`: compute **STOPPED**, *"App compute was stopped due to workspace or account status."*; app
  status UNAVAILABLE; no active deployment listed. `update_time` 13:52 UTC, about 6.5 h after the last deploy (07:19 UTC,
  `01f1e0c4e722…`, SUCCEEDED). So this is **not** the normal 24 h auto-stop.
- The rest of the workspace still answers: API calls work, the SQL warehouse is STOPPED (normal 10 min auto-stop; last
  query 09:50 UTC), `databricks-llama-4-maverick` is READY and answered one 3-token test call. No clusters, no job runs.
- Free Edition docs: when an account exceeds the fair-usage quota, *"compute is shut down for the rest of the day"* (in
  extreme cases the month); data and settings are kept. Apps also stop 24 h after start/deploy. Up to 3 apps per account.

**Likely cause (inference, not confirmed):** the account hit Free Edition's daily fair-usage limit, and Databricks stopped
the App's compute. The message wording matches; no API exposes the quota, so the cause can't be proven from the CLI.
Usage that day included the App on MEDIUM compute since ~03:37 UTC with several redeploys, Model Serving calls during
video tests, warehouse queries, and Serverless GPU notebook sessions (YOLO runs). **Which of these used the most is
unknown.** The `system.billing.usage` table could show it, but querying it would start the warehouse, so it was not run.

**Restore (owner's approval; no data change, no new resources):**
1. Check: `databricks apps get fixit-madison --profile fixit`; also look for a usage/quota banner in the workspace UI.
2. Start: `databricks apps start fixit-madison --profile fixit` (restarts the last deployment, `2c74f5d`). If it fails
   with the same message, quota is still exhausted: wait for the daily reset and try again (Databricks doesn't publish
   the reset time).
3. Verify: open the URL → Continue; `python scripts/app_smoke.py --address "1770 Fair Oaks Ave" --unit QA-SMOKE` only if
   you accept new test rows (otherwise the manual checklist in `docs/DEMO_SCRIPT.md`).
4. Keep usage light until judging: no GPU notebooks, no bulk tests. A redeploy (speed change) restarts the 24 h clock.

## 2. Can the Databricks App itself be public? No.
Databricks Apps authenticate every user through the workspace (SSO or one-time password); `CAN_USE` is granted to
users/groups. No anonymous option is documented. A public URL needs a second host.

## 3. Options evaluated
| Option | Verdict | Why |
|---|---|---|
| **A. Public demo on Render (free), PUBLIC_DEMO mode** | **Recommended** | Same FastAPI + React app in one container (UI and `/api` same-origin, as on Databricks). SQLite with the synthetic dataset, reseeded at every start; saved/scripted AI results labeled on screen. **No credentials anywhere.** $0 |
| B. A + live Llama/SQL/Genie through a Databricks token | Not recommended now | See §4: the only verified credential is the owner's admin PAT, and anonymous traffic would draw on the same Free Edition quota that just stopped the App |
| Vercel (frontend) + Render (API) | Not needed | Splits one same-origin app into two hosts (rewrites/CORS). The API still cold-starts on Render. Vercel Hobby is free (non-commercial) and would work if a CDN front is wanted later |
| Hugging Face Spaces | Excluded | Docker/Gradio Spaces now need a paid plan (PRO) |
| Static site (screenshots/video only) | Backup | Zero risk, but not interactive |

## 4. Live Databricks from an external backend: feasibility
- **Authentication:** the workspace allows personal access tokens (`enableTokensConfig=true`, max lifetime 730 days;
  admins manage them; 0 tokens exist today). Free Edition has no account console, so account-level service-principal
  OAuth secrets probably aren't available (not verified). The only verified option is a PAT, and the owner is a
  workspace **admin**: a leaked token means full control of the workspace. A dedicated low-privilege identity with a
  token wasn't verified as possible on Free Edition.
- **Quota:** every public visitor's frames would hit Model Serving, and SQL/Genie would wake the warehouse. All of it
  counts against the account's daily fair-usage limit, so heavy public traffic could **stop the Databricks App on
  judging day**, the same failure as today.
- **Terms:** Free Edition is for non-commercial use (a hackathon demo is fine).
- **If wanted later:** a separate identity with only `CAN_QUERY` on the endpoint, no SQL/Genie, strict per-IP and global
  daily caps, short-lived token stored as a host secret. Owner decision.

## 5. Public demo security (implemented on `ch27-review`, local only)
- `PUBLIC_DEMO=true` (`app/backend/config.py`): forces the local backend and Demo Mode, and **clears every Databricks
  setting even if one is set**. `llm.available()` returns False, and `_auth_headers()` refuses to authenticate. Vision
  never attempts a live call (scripted results, labeled "Demo script").
- `/api/demo/reset` and `/api/demo/warm` return 403. Genie answers the sample questions from prepared SQL (labeled).
- **Case isolation:** an HttpOnly session cookie, and "My cases" lists only the cases created in that browser. Case and
  scan links use random IDs. Uploads live on the host's ephemeral disk and disappear on restart. A banner tells visitors
  the data is synthetic, the AI results are scripted/saved, and not to upload personal photos.
- **Limits (all modes):** 8 MB per image on the public demo (25 MB otherwise), ≤30 files per request; per-IP POST rate
  limit (120 per 10 min on the public demo, off by default elsewhere). It keys on `X-Forwarded-For`, so it's a soft
  guard; it's acceptable only because the public demo makes no paid or credentialed calls.
- **Path traversal fixed (all modes):** the SPA route served any file on the server (`/%2e%2e/%2e%2e/backend/config.py`
  returned source; on Databricks Apps `/proc/self/environ` holds the app service principal's credentials). It is now
  confined to the built frontend. **The deployed App still has the bug** (only signed-in workspace users can reach it);
  it ships with the next approved redeploy.
- Tests: `app/backend/tests/test_public_hosting.py` (16).

## 6. Files (not deployed)
- `deploy/public/Dockerfile`: Node build → Python 3.12 slim, same layout as `make bundle`, non-root user, `$PORT`.
  Not built here (no Docker on this laptop); the same layout was booted locally with `PUBLIC_DEMO=true` and answered
  `/`, `/api/health` and a Genie sample question.
- `render.yaml`: Render Blueprint, `plan: free`, `autoDeploy: false`, no secrets.
- `.dockerignore`: excludes `.env`, `.git`, data, experiments, docs, notebooks.

## 7. Costs and limits (from provider docs, 2026-11-15)
- **Render free web service:** $0; 0.1 CPU / 512 MB; spins down after 15 min without traffic, **~1 min cold start**
  (visitors see a loading page); 750 free instance-hours per workspace per month; ephemeral filesystem; Render may
  restart it at any time. Reseeding takes ~1.2 s locally (2.2 MB DB), so it should take seconds on 0.1 CPU (not measured
  on Render). A paid always-on instance removes spin-down; check the current price on render.com/pricing (the page
  didn't show figures to the fetcher).
- **Vercel Hobby (if used):** free, non-commercial; 100 GB transfer, 1M function invocations/month; functions 300 s max.
- **Databricks Free Edition:** $0; fair-usage quota with daily shutdown; 3 apps; one 2X-Small warehouse.

## 8. Steps once approved
1. Owner creates a Render account (sign-up and any verification code are the owner's).
2. Push `ch27-review` with these commits (it's the public repo) → Render "New Blueprint" from `render.yaml` on
   `ch27-review` → manual deploy.
3. Check: banner visible; `/api/health` shows `public_demo: true, models_configured: false`; the
   `/%2e%2e/%2e%2e/backend/config.py` path returns the HTML page; listing, video and case flows show "Demo script"
   labels; a second browser's "My cases" is empty.
4. Put the URL in Devpost ("public demo: synthetic data and scripted AI results; live Databricks version shown in the
   video") and in `docs/DEMO_SCRIPT.md`.
