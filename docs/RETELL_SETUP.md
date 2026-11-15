# Retell integration

Implemented locally on `feature/retell-ai`, based on `origin/ch27-review`.
`origin/main` has only a README. No deployment, remote agent creation, call, or push was
performed as part of implementation. The existing simulated call is still available.

## What it does

The Case page has a separate Retell phone-call panel. It collects a demo tenant name,
allowlisted phone number, optional management company, previous requests, preferred
timeline, and four unchecked authorization/consent confirmations. It sends the case's
observations and only verified official citations associated with those issues.
It never sends synthetic neighbor reports or infers the actual manager from demo data.

The agent uses `app/backend/prompts/retell_landlord.md`, based on the owner's supplied
landlord communication instructions. For the current hackathon policy, it explicitly
identifies the call as a test and the case as a demonstration. Only consenting
teammates/judges may be called. There is no switch to silently turn this into a real
landlord outreach campaign.

The backend retrieves call status, transcript and structured analysis from Retell.
Inspection appointments, repair estimates and repair commitments are distinct. An AI
summary is labeled for review and does not automatically change a deadline, mark a
letter sent, or file a complaint. The transcript and outcomes are available in the
operator-protected call panel. They are not appended to the unprotected simulated-call
API or evidence packet. No fake result is substituted if Retell fails.

## Local configuration

1. Install the normal app dependencies (`make setup`). No additional Retell SDK is
   needed; the backend uses the existing httpx dependency and official REST API.
2. In the ignored `.env`, configure:

   ```dotenv
   CALLS_ENABLED=false
   CALL_ALLOWLIST=+1<consenting-test-recipient>
   RETELL_API_KEY=<private-server-key>
   RETELL_AGENT_ID=<dedicated-FixIT-agent-id>
   RETELL_FROM_NUMBER=+1<Retell-owned-or-imported-number>
   RETELL_OPERATOR_TOKEN=<separate-random-secret-at-least-32-characters>
   ```

   Generate the operator secret with a password manager. It is distinct from the Retell
   key. Never place either key in frontend source, a VITE variable, Git, or a URL.
   The UI keeps the operator token in component memory only; locking the panel clears it.
3. Pick a voice ID in Retell's dashboard. Prepare the exact agent configuration offline:

   ```sh
   .venv/bin/python scripts/retell_setup.py --voice-id YOUR_VOICE_ID
   ```

   Review the prompt, opening and settings. After authorization to create Retell
   resources, run the same command with `--apply`. It creates a dedicated single-prompt
   LLM and agent, prints their IDs, and never buys a phone number or places a call.
   Model defaults to `gpt-4.1`; `--model` accepts a model supported by your Retell account.
   If agent creation fails after LLM creation, retain the printed LLM ID and inspect it
   in Retell before repeating setup (there is no automatic resource deletion).
4. Put the created agent ID in `.env`. After configuration, `--check` verifies the
   remote prompt, opening, `start_speaker: agent`, tools (only `end_call`), no
   knowledge bases/states/session tools and no agent `webhook_url`, reading the exact
   LLM version the agent pins. An account-level webhook (set in the Retell dashboard)
   is not visible to this check: keep it unset for this account. The backend repeats this check
   before every call. Use a dedicated agent and do not edit it during a test. Calls
   explicitly select the latest version; use only this controlled test agent.
5. Acquire/import a calling number in Retell separately. Confirm the recipient is on
   the exact E.164 allowlist and has consented to AI calling, recording and transcription.
6. Only after authorization to run a real phone test, set `CALLS_ENABLED=true`, restart,
   open the case, unlock the Retell panel, review case facts and tick the consent boxes.
   Pressing **Place authorized test call** places a real, potentially billable call.

Audio and transcripts are stored by Retell with a 30-day retention setting; signed URLs
are requested. FixIt stores the transcript, supplied context, consent and outcomes in
its database. It does not download audio or expose recording URLs. FixIt records have
no automatic retention deletion yet. All-participant recording consent is required;
there is no claim that storage opt-out disables the provider's audio processing.

## Databricks

The current app uses FastAPI/React on Databricks Apps, SQL Warehouse/Unity Catalog for
structured data, a Volume for evidence, Llama 4 Maverick for vision/chat and Genie for
analytics. Retell handles telephony and its own conversational model. It does not replace
Llama vision or call Databricks to make the speech conversation.

Before an approved deployment:

1. Run `notebooks/02_retell_calls.sql` on the **fixit** workspace/profile. If using a
   different catalog, edit the catalog name deliberately. This adds only
   `fixit.silver.retell_calls`. SQLite creates the equivalent table on startup.
2. Give the App service principal SELECT/MODIFY on this table (existing silver schema
   grants already provide this). Do not add it to demo reset/cleanup lists.
3. Add Retell API key and operator token as Databricks App secret resources; bind them
   with `valueFrom` environment entries. Configure agent ID, from number, allowlist and
   `CALLS_ENABLED` in the deployment environment. No secret values belong in app.yaml.
4. Ensure App outbound access to `https://api.retellai.com`. Bundle with the normal
   build script; it includes the prompt under backend/prompts. Deploy only after
   explicit approval. The shipped app.yaml does not enable calls.

Polling is intentional: the deployed App is behind Databricks OAuth, so direct Retell
webhooks cannot reach it without a separately authenticated relay. No public webhook
route is added. The panel polls every 10 seconds up to 60 times while open, stops after
errors, and allows manual refresh. Closing the browser does not hang up a phone call.
Results persist when refreshed; reopen the panel and refresh after reconnecting. End
calls with the UI's **End call** button or in Retell; the agent has a five-minute cap.

## Agent behavior and outcome accuracy

- Opening (`services/retell.py` `OPENING`): AI identity, tenant authorization, test call,
  recording/transcription disclosure, then one question: is it okay to continue on a
  recorded line? Declining ends the call before any case discussion.
- Post-call analysis uses enum fields for `acknowledgement` and `appointment_kind`
  (inspection / repair_estimate / repair_commitment / none) and optional strings
  (`required: false`, so an empty value doesn't mark the call unsuccessful).
- The backend keeps an offer only if the analysis quotes the recipient verbatim
  (punctuation-insensitive, whole words, recipient turns only). Dates must be explicit
  YYYY-MM-DD and not before the call day. Everything is labeled for review; no deadline,
  letter or complaint changes automatically.
- Opt-out is sticky: Retell's `do_not_call` analysis, `user_requested_dnc`, a DNC
  rejection, or recipient phrases such as "stop calling", "take me off your list",
  "no more calls".
- Citations: only sections that are verified, official text and in the human-approved
  mapping for that same issue type (`code_sections_verified.json`).

## Failure handling and operational limits

- A durable attempt (with the exact provider request) is saved before dialing, and its
  ID is sent as Retell's body `idempotency_key`. The backend never retries a create
  automatically. Repeated requests with that attempt return its stored state.
- A **definitive rejection of the first request** (HTTP 400/401/402/403/404/422/429)
  means no call was placed: the attempt becomes `rejected` (terminal) and a new attempt
  may be prepared. A 400 whose body mentions do-not-call (`honor_internal_dnc`) also
  sets a sticky opt-out. Provider bodies are never shown or stored.
- A timeout, 5xx, invalid response or crash becomes `unknown` (or stays `creating`) and
  blocks every new call to that number.
- **Resume** (operator button, `POST /calls/{id}/resume`): within 50 minutes of creation,
  re-sends the byte-identical stored request with the same idempotency key. Retell
  documents that such a retry within one hour does not create another call. Refused
  if calling is disabled, the agent ID or from-number changed, or the attempt is linked.
  A failed resume always stays `unknown` (the first request may have placed a call).
  The one-hour deduplication is Retell's documented behavior; it is not live-verified.
- **Reconcile**: find `fixit_attempt_id` in Retell call metadata and enter the call ID.
  The backend verifies case ID, attempt ID, agent and recipient before linking. If the
  window passed and Retell never created a call, an operator must verify that in the
  dashboard and repair the attempt record deliberately.
- An `ended` call with no Retell analysis blocks further calls to that number until
  analysis arrives; if Retell never produces analysis, repair the record deliberately.
- Refresh the previous call before calling the same number again. An ended call needs
  completed analysis. Retell's native do-not-call detection and `honor_internal_dnc`
  are enabled. Explicit opt-outs captured by FixIt are sticky across refreshes and demo
  resets and block further calls to that number.
- `CALLS_ENABLED=false` prevents new calls. Refresh and stop still work for existing
  calls. Disabling the switch alone does not terminate an ongoing call.
- Keep the existing single-process, single-worker App deployment. The in-process lock
  serializes call creation; Delta has no enforced unique key. Multi-instance operation
  requires a transactional reservation service before enabling dialing.
- The operator token is a demo access gate, not multi-tenant identity/authorization.
  Public production rollout requires tenant authentication, case ownership, recipient
  consent management, retention controls, and operational review.
- Voice behavior and extraction accuracy still require a consented live test. Local
  tests stub Retell; they do not prove the provider account, phone number or voice works.

## API

Every endpoint except `/api/retell/config` requires `X-Fixit-Call-Token`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/retell/config` | Enabled flag, test-call and recording disclosure |
| GET | `/api/retell/cases/{rid}/calls` | Persisted call history |
| POST | `/api/retell/cases/{rid}/calls` | Explicit authorized call creation |
| POST | `/api/retell/calls/{attempt_id}/refresh` | Fetch result; optional `provider_call_id` for reconciliation |
| POST | `/api/retell/calls/{attempt_id}/resume` | Re-send an uncertain create with the same idempotency key (50-min window) |
| POST | `/api/retell/calls/{attempt_id}/stop` | Request hangup |

Official references checked during implementation:
[Create phone call](https://docs.retellai.com/api-references/create-phone-call),
[Get call](https://docs.retellai.com/api-references/get-call),
[Stop call](https://docs.retellai.com/api-references/stop-call),
[Create LLM](https://docs.retellai.com/api-references/create-retell-llm),
[Create agent](https://docs.retellai.com/api-references/create-agent).
