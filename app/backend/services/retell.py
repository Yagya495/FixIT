"""Retell phone calls. Explicit opt-in only; never part of Demo Mode fallback.

Records use the existing SQLite/Delta abstraction. Polling is deliberate: Databricks
Apps' login gateway cannot accept unauthenticated provider webhooks. Single App worker.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .. import config, db
from . import cases, taxonomy

API = "https://api.retellai.com"
PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "retell_landlord.md"
# One question only: recording consent is asked for, never assumed. Timing is asked next (see prompt).
OPENING = (
    "Hi, this is FixIT, an AI assistant calling with the tenant's authorization. This is a test call about a "
    "demo maintenance case for {{tenant_name}} at {{property_address}}. This call is recorded and transcribed. "
    "Is it okay to continue on a recorded line?"
)
END_CALL_TOOL = {"type": "end_call", "name": "end_call",
                 "description": "Politely end the call when finished, when the recipient declines, or when consent is withdrawn."}
PROVIDER_TERMINAL = {"ended", "error", "not_connected"}
# `rejected`: Retell definitively refused the create request, so no call exists.
TERMINAL = PROVIDER_TERMINAL | {"rejected"}
UNCERTAIN = {"creating", "unknown"}
# Retell documents create-phone-call idempotency for one hour; stay well inside it.
IDEMPOTENT_RESUME_WINDOW = timedelta(minutes=50)
# Create responses that mean the request was refused before any call was placed.
DEFINITIVE_REJECTIONS = {400, 401, 402, 403, 404, 422, 429}
_LOCK = threading.RLock()
E164 = r"^\+[1-9][0-9]{7,14}$"
CALL_ID = r"[\w-]{1,128}"


class StartCall(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    attempt_id: str = Field(pattern=r"^[a-zA-Z0-9_-]{16,80}$")
    to_number: str = Field(pattern=E164)
    tenant_name: str = Field(min_length=1, max_length=120)
    management_company: str = Field(default="", max_length=200)
    previous_requests: str = Field(default="", max_length=2000)
    preferred_timeline: str = Field(default="", max_length=300)
    tenant_authorized: Literal[True]
    recipient_consented: Literal[True]
    recording_consented: Literal[True]
    case_reviewed: Literal[True]
    test_call: Literal[True]


class ProviderError(HTTPException):
    """A sanitized Retell failure. `provider_status` is None when no HTTP response arrived."""

    def __init__(self, detail: str, provider_status: int | None = None, dnc_hint: bool = False):
        super().__init__(502, detail)
        self.provider_status = provider_status
        self.dnc_hint = dnc_hint


def configured() -> bool:
    return bool(config.RETELL_API_KEY and config.RETELL_AGENT_ID and
                re.fullmatch(E164, config.RETELL_FROM_NUMBER) and
                len(config.RETELL_OPERATOR_TOKEN) >= 32)


def authorize(token: str | None) -> None:
    if len(config.RETELL_OPERATOR_TOKEN) < 32:
        raise HTTPException(503, "Retell operator access is not configured.")
    # Bytes: compare_digest raises TypeError on non-ASCII str (header values are latin-1 decoded).
    if not token or not secrets.compare_digest(token.encode("utf-8", "surrogateescape"),
                                               config.RETELL_OPERATOR_TOKEN.encode("utf-8")):
        raise HTTPException(401, "Enter the Retell operator access token.")


def request(method: str, path: str, payload: dict | None = None, params: dict | None = None) -> dict:
    """No automatic retries: a POST timeout may mean the call was already placed."""
    try:
        with httpx.Client(timeout=20, follow_redirects=False) as client:
            r = client.request(method, API + path, params=params,
                               headers={"Authorization": f"Bearer {config.RETELL_API_KEY}"}, json=payload)
    except httpx.HTTPError:
        raise ProviderError("Retell could not be reached.") from None
    if not r.is_success:
        # Provider bodies may contain phone numbers, prompts, or credentials: never surface them.
        hint = r.status_code == 400 and bool(re.search(r"do[\s_-]*not[\s_-]*call|\bdnc\b", r.text, re.I))
        raise ProviderError(f"Retell returned HTTP {r.status_code}. Check the Retell dashboard.", r.status_code, hint)
    if r.status_code == 204 or not r.content:
        return {}
    try:
        result = r.json()
    except ValueError:
        result = None
    if not isinstance(result, dict):
        raise ProviderError("Retell returned an invalid response.", r.status_code)
    return result


def _now() -> str:
    return datetime.now(ZoneInfo("America/Chicago")).replace(tzinfo=None).isoformat(timespec="seconds")


def context_for(case: dict, body: StartCall) -> dict[str, str]:
    """Only case observations and verified per-issue citations; no synthetic neighbors/history."""
    issues, references = [], []
    order = {"emergency": 0, "urgent": 1, "routine": 2}
    # Defense in depth: a section verified for one issue type is never cited for another type.
    approved = taxonomy.verified_review()["mapping"]
    for v in sorted(case["violations"], key=lambda v: order.get(v.get("severity"), 3)):
        issues.append({"issue": v["name"], "severity": v["severity"],
                       "observations": [{"note": o.get("note"), "basis": o.get("basis_text", o.get("basis")),
                                         "photo_available": bool(o.get("evidence_id"))}
                                        for o in v.get("observations", [])],
                       "needs_in_person_verification": bool(v.get("verify_in_person"))})
        allowed = set(approved.get(v.get("violation_type"), []))
        for s in v.get("code_sections", []):
            if s.get("verified") is True and s.get("official_text") is True and s.get("section_id") in allowed:
                references.append({"issue": v["name"], "section": s["section_id"],
                                   "excerpt": s.get("snippet", ""), "url": s.get("url", ""),
                                   "meaning": "Possibly relevant, not a confirmed violation"})
    return {
        "tenant_name": body.tenant_name,
        "property_address": case.get("address") or "Not supplied",
        "unit_number": case.get("unit") or "Not supplied",
        # Do not infer the real manager from the fictional property dataset.
        "management_company": body.management_company or "Not supplied",
        "maintenance_issues": json.dumps(issues),
        "issue_severity": case["severity"],
        "issue_description": "Use only the observations in maintenance_issues; all are demo case information.",
        "previous_requests": body.previous_requests or "No previous communications supplied. Do not infer any.",
        "housing_code_references": json.dumps(references),
        "preferred_timeline": body.preferred_timeline or "Ask for a timeline; no preferred date supplied.",
        "current_date": datetime.now(ZoneInfo("America/Chicago")).strftime("%A %Y-%m-%d %H:%M %Z"),
    }


ACKNOWLEDGEMENT = ["acknowledged", "disputed", "unclear", "not_discussed"]
APPOINTMENT_KINDS = ["inspection", "repair_estimate", "repair_commitment", "none"]
ANALYSIS_FIELDS = {
    "appointment_date": "Explicit date YYYY-MM-DD only if the recipient gave an unambiguous date, resolved using "
                        "current_date; otherwise empty. Never invent or infer a date from vague timing.",
    "date_as_spoken": "The recipient's exact words offering the inspection, estimate or repair, including any timing. "
                      "Copy verbatim from the recipient's speech. Empty if none. Never quote the AI agent.",
    "coordinator": "Who coordinates the work, only if the recipient stated it; otherwise empty.",
    "tenant_information_requested": "Information the recipient requested from the tenant, or empty.",
    "next_steps": "Factual next steps in the recipient's terms, including refusals, disputes or claims that the "
                  "repair is already done. Say plainly if nothing was agreed. Never invent an agreement.",
}


def analysis_schema() -> list[dict]:
    return [
        {"type": "enum", "name": "acknowledgement", "choices": ACKNOWLEDGEMENT,
         "description": "Did the recipient acknowledge the reported issues? disputed = they said the issue does not "
                        "exist or is not their responsibility; not_discussed if the issues were never discussed."},
        {"type": "enum", "name": "appointment_kind", "choices": APPOINTMENT_KINDS,
         "description": "What the recipient offered: inspection (a visit to look, not a repair promise), "
                        "repair_estimate (an approximate or tentative repair time), repair_commitment (the recipient "
                        "clearly committed to completing the repair), or none. Agent suggestions do not count."},
        *({"type": "string", "name": k, "description": v, "required": False} for k, v in ANALYSIS_FIELDS.items()),
        {"type": "boolean", "name": "follow_up_needed", "description": "Whether tenant follow-up is needed. True if unclear."},
        {"type": "boolean", "name": "do_not_call",
         "description": "True if the recipient asked for no more AI calls, refused to speak with an AI, or withdrew consent."},
    ]


def agent_settings() -> dict:
    return {
        "language": "en-US", "max_call_duration_ms": 300000, "ring_duration_ms": 30000,
        "end_call_after_silence_ms": 30000, "enable_dnc_detection": True,
        "data_storage_setting": "everything", "data_storage_retention_days": 30,
        "opt_in_signed_url": True,
        "contact_memory_config": {"enable_read": False, "enable_update": False},
        "voicemail_option": {"action": {"type": "hangup"}},
        "ivr_option": {"action": {"type": "hangup"}},
        "post_call_analysis_data": analysis_schema(),
    }


def llm_config(model: str = "gpt-4.1") -> dict:
    return {"model": model, "model_temperature": 0.2, "start_speaker": "agent",
            "general_prompt": PROMPT_PATH.read_text(encoding="utf-8"), "begin_message": OPENING,
            "general_tools": [END_CALL_TOOL]}


def check_agent() -> None:
    """Fail closed if the configured remote agent no longer uses the reviewed prompt/tools."""
    agent = request("GET", f"/get-agent/{config.RETELL_AGENT_ID}", params={"version": "latest"})
    engine = (agent.get("response_engine") or {})
    if engine.get("type") != "retell-llm" or not re.fullmatch(r"[\w-]+", str(engine.get("llm_id", ""))):
        raise HTTPException(409, "Retell must use the dedicated FixIT single-prompt agent.")
    # The call runs the agent's pinned LLM version when it has one; check that exact version.
    version = engine.get("version")
    llm = request("GET", f"/get-retell-llm/{engine['llm_id']}",
                  params={"version": int(version)} if isinstance(version, int) else None)
    if (llm.get("general_prompt") != PROMPT_PATH.read_text(encoding="utf-8") or llm.get("begin_message") != OPENING
            or llm.get("start_speaker") != "agent"
            or llm.get("states") or llm.get("knowledge_base_ids")
            or [t.get("type") for t in (llm.get("general_tools") or [])] != ["end_call"]
            or agent.get("pre_session_tools") or agent.get("post_session_tools")
            # Transcripts must not be pushed to an unreviewed endpoint.
            or agent.get("webhook_url")):
        raise HTTPException(409, "Retell agent differs from the reviewed FixIT configuration. Run the setup check.")


def _get(attempt_id: str) -> dict:
    row = db.q1("SELECT * FROM {silver.retell_calls} WHERE attempt_id = :a", {"a": attempt_id})
    if not row:
        raise HTTPException(404, "Retell call not found.")
    return row


def public(row: dict) -> dict:
    out = {k: db.jl(row.get(k)) for k in (
        "attempt_id", "request_id", "provider_call_id", "status", "transcript", "outcome_json",
        "disconnection_reason", "created_at", "updated_at")}
    out["resumable"] = _resumable(row)
    return out


def history(rid: str) -> list[dict]:
    return [public(r) for r in db.q("SELECT * FROM {silver.retell_calls} WHERE request_id = :r ORDER BY created_at", {"r": rid})]


def _payload(row: dict) -> dict | None:
    stored = db.jl(row.get("context_json")) or {}
    return stored.get("provider_request") if isinstance(stored, dict) else None


def _resumable(row: dict) -> bool:
    """An uncertain create can be re-sent with the SAME idempotency key while Retell still deduplicates it."""
    if row.get("status") not in UNCERTAIN or row.get("provider_call_id") or not _payload(row):
        return False
    try:
        created = datetime.fromisoformat(str(row["created_at"]).replace("Z", "")).replace(tzinfo=None)
    except ValueError:
        return False
    return datetime.fromisoformat(_now()) - created < IDEMPOTENT_RESUME_WINDOW


def _create(attempt_id: str, payload: dict, first: bool = True) -> dict:
    """Send one create request and record a definite, rejected or uncertain result. Never retried here.

    Only the FIRST request's 4xx proves no call exists. On a resend, the original may already have placed one."""
    try:
        result = request("POST", "/v2/create-phone-call", payload)
    except Exception as e:  # anything unexpected is treated as "the call may exist"
        if first and isinstance(e, ProviderError) and e.provider_status in DEFINITIVE_REJECTIONS:
            outcome = {"analyzed": False, "do_not_call": e.dnc_hint, "review_required": True,
                       "source": "rejected", "rejected_status": e.provider_status}
            db.execute("UPDATE {silver.retell_calls} SET status = 'rejected', outcome_json = :o, "
                       "disconnection_reason = :d, updated_at = :u WHERE attempt_id = :a",
                       {"o": json.dumps(outcome), "d": f"provider_rejected_http_{e.provider_status}",
                        "u": _now(), "a": attempt_id})
            hint = (" The number may be on Retell's do-not-call list." if e.provider_status == 400 else "")
            raise HTTPException(502, f"Retell rejected the call request (HTTP {e.provider_status}); no call was "
                                     f"placed.{hint} Check the Retell dashboard.") from None
        db.execute("UPDATE {silver.retell_calls} SET status = 'unknown', updated_at = :u WHERE attempt_id = :a",
                   {"a": attempt_id, "u": _now()})
        raise HTTPException(502, "Call creation is uncertain. Do not redial. Check Retell, then resume this "
                                 "attempt or reconcile its call ID.") from None
    call_id = str(result.get("call_id", ""))
    status = result.get("call_status", "registered")
    if not re.fullmatch(CALL_ID, call_id) or status not in {"registered", "ongoing", *PROVIDER_TERMINAL}:
        db.execute("UPDATE {silver.retell_calls} SET status = 'unknown', updated_at = :u WHERE attempt_id = :a",
                   {"a": attempt_id, "u": _now()})
        raise HTTPException(502, "Retell did not return a valid call. Do not redial. Check Retell and reconcile.")
    db.execute("UPDATE {silver.retell_calls} SET provider_call_id = :c, status = :s, updated_at = :u WHERE attempt_id = :a",
               {"c": call_id, "s": status, "u": _now(), "a": attempt_id})
    return public(_get(attempt_id))


def _gate(to_number: str) -> None:
    if not config.CALLS_ENABLED or not configured():
        raise HTTPException(503, "Phone calls are disabled or Retell is not fully configured.")
    if to_number not in config.CALL_ALLOWLIST:
        raise HTTPException(403, "This number is not on the consenting test-recipient allowlist.")


def start(rid: str, body: StartCall) -> dict:
    _gate(body.to_number)
    with _LOCK:
        prior = db.q1("SELECT * FROM {silver.retell_calls} WHERE attempt_id = :a", {"a": body.attempt_id})
        consent = body.model_dump()
        fingerprint = hashlib.sha256(json.dumps(consent, sort_keys=True).encode()).hexdigest()
        if prior:
            if prior["request_id"] != rid or db.jl(prior["consent_json"])["fingerprint"] != fingerprint:
                raise HTTPException(409, "This attempt ID belongs to a different call request.")
            return public(prior)  # Never redial an ambiguous or completed attempt.
        # Require the previous call to be refreshed and analyzed before another call to this number.
        for old in db.q("SELECT * FROM {silver.retell_calls} WHERE to_number = :n", {"n": body.to_number}):
            outcome = db.jl(old["outcome_json"]) or {}
            if outcome.get("do_not_call"):
                raise HTTPException(403, "Recipient requested no further AI calls.")
            if old["status"] not in TERMINAL or (old["status"] == "ended" and not outcome.get("analyzed")):
                raise HTTPException(409, "Refresh the previous call first. Uncertain calls must be resumed or "
                                         "reconciled before another attempt.")
        case = cases.get_case(rid)
        if not case:
            raise HTTPException(404, "Case not found.")
        variables = context_for(case, body)
        check_agent()  # read-only provider checks before reserving/dialing
        now = _now()
        payload = {
            "from_number": config.RETELL_FROM_NUMBER, "to_number": body.to_number,
            "override_agent_id": config.RETELL_AGENT_ID, "override_agent_version": "latest",
            "idempotency_key": body.attempt_id, "honor_internal_dnc": True,
            "retell_llm_dynamic_variables": variables,
            "metadata": {"fixit_attempt_id": body.attempt_id, "fixit_request_id": rid},
            "agent_override": {"agent": agent_settings()},
        }
        # The exact request is kept so an uncertain create can be re-sent byte-for-byte with the same key.
        db.insert("silver.retell_calls", {
            "attempt_id": body.attempt_id, "request_id": rid, "provider_call_id": None,
            "to_number": body.to_number, "status": "creating",
            "context_json": {"variables": variables, "provider_request": payload},
            "consent_json": {**consent, "fingerprint": fingerprint, "authorized_at": now},
            "transcript": [], "outcome_json": {}, "disconnection_reason": None,
            "created_at": now, "updated_at": now,
        })
        return _create(body.attempt_id, payload)


def resume(attempt_id: str) -> dict:
    """Operator-requested re-send of an uncertain create with the same idempotency key (Retell dedupes for 1 h)."""
    with _LOCK:
        row = _get(attempt_id)
        _gate(row["to_number"])
        payload = _payload(row)
        if not _resumable(row) or not payload:
            raise HTTPException(409, "This attempt cannot be resumed safely. Find it in Retell and reconcile its call ID.")
        if (payload.get("idempotency_key") != attempt_id or payload.get("to_number") != row["to_number"]
                or payload.get("override_agent_id") != config.RETELL_AGENT_ID
                or payload.get("from_number") != config.RETELL_FROM_NUMBER):
            raise HTTPException(409, "Retell configuration changed since this attempt. Reconcile it in Retell instead.")
        return _create(attempt_id, payload, first=False)


_PUNCT = re.compile(r"[^\w]+")


def _norm(text: str) -> str:
    return " " + _PUNCT.sub(" ", text.casefold()).strip() + " "


OPT_OUT = re.compile(
    r"\b(?:do not|don't|dont|stop|never|quit)\s+(?:ever\s+)?(?:call|calling|contact|contacting|ring)\b"
    r"|\b(?:no|not any)\s+more\s+(?:ai\s+)?calls\b"
    r"|\b(?:remove|take)\s+(?:me|my number|this number)\s+(?:off|from)\b"
    r"|\bdo not call list\b|\bdon't want (?:any )?(?:more )?(?:ai |robot )?calls\b",
    re.I)


def normalize_outcome(call: dict) -> dict:
    analysis = call.get("call_analysis") or {}
    raw = analysis.get("custom_analysis_data") or {}
    out = {k: str(raw.get(k) or "")[:3000] for k in ("acknowledgement", "appointment_kind", *ANALYSIS_FIELDS)}
    out["analyzed"] = bool(analysis)
    out["summary"] = str(analysis.get("call_summary") or "")[:5000]
    if out["acknowledgement"] not in ACKNOWLEDGEMENT:
        out["acknowledgement"] = "unclear"
    if out["appointment_kind"] not in APPOINTMENT_KINDS:
        out["appointment_kind"] = "none"
    try:
        when = datetime.strptime(out["appointment_date"], "%Y-%m-%d").date()
        started = call.get("start_timestamp")
        if isinstance(started, (int, float)):
            call_day = datetime.fromtimestamp(started / 1000, ZoneInfo("America/Chicago")).date()
            if when < call_day:  # a past date cannot be a plan made on this call
                out["appointment_date"] = ""
    except ValueError:
        out["appointment_date"] = ""
    # Offers must be grounded in the recipient's own words; never derive promises from agent speech.
    recipient = " ".join(t.get("content", "") for t in (call.get("transcript_object") or []) if t.get("role") == "user")
    quote = out["date_as_spoken"]
    grounded = bool(quote.strip()) and _norm(quote).strip() != "" and _norm(quote) in _norm(recipient)
    if not grounded or out["appointment_kind"] == "none":
        out["appointment_date"] = ""
        out["appointment_kind"] = "none"
        out["date_as_spoken"] = ""
    out["follow_up_needed"] = raw.get("follow_up_needed") is not False
    out["do_not_call"] = (raw.get("do_not_call") is True or call.get("disconnection_reason") == "user_requested_dnc"
                          or bool(OPT_OUT.search(recipient)))
    out["source"] = "retell" if analysis else "pending"
    out["review_required"] = True
    return out


def refresh(attempt_id: str, provider_call_id: str | None = None) -> dict:
    with _LOCK:
        row = _get(attempt_id)
        if row["status"] == "rejected":
            return public(row)  # Retell refused the create: there is no call to fetch.
        call_id = provider_call_id or row["provider_call_id"]
        if not call_id or not re.fullmatch(CALL_ID, call_id):
            raise HTTPException(409, "Check Retell for this attempt ID, then resume it or enter its call ID. Do not redial.")
        if row["provider_call_id"] and call_id != row["provider_call_id"]:
            raise HTTPException(409, "Cannot replace a linked call ID.")
        call = request("GET", f"/v2/get-call/{call_id}")
        metadata = call.get("metadata") or {}
        if (call.get("call_id") != call_id or metadata.get("fixit_attempt_id") != attempt_id
                or metadata.get("fixit_request_id") != row["request_id"]
                or call.get("agent_id") != config.RETELL_AGENT_ID or call.get("to_number") != row["to_number"]):
            raise HTTPException(409, "Retell call does not match this saved attempt.")
        status = call.get("call_status")
        if status not in {"registered", "ongoing", *PROVIDER_TERMINAL}:
            raise HTTPException(502, "Retell returned an unrecognized call status.")
        transcript = [{"speaker": "ai" if t.get("role") == "agent" else "landlord", "text": t.get("content", "")}
                      for t in (call.get("transcript_object") or []) if t.get("role") in {"agent", "user"}]
        outcome = normalize_outcome(call)
        old = db.jl(row["outcome_json"]) or {}
        # Sticky opt-out and completed analysis; an older provider snapshot must not erase them.
        if old.get("analyzed") and not outcome["analyzed"]:
            outcome = old
        outcome["do_not_call"] = bool(outcome.get("do_not_call") or old.get("do_not_call"))
        if row["status"] in TERMINAL and status not in PROVIDER_TERMINAL:
            return public(row)
        db.execute("UPDATE {silver.retell_calls} SET provider_call_id = :c, status = :s, transcript = :t, "
                   "outcome_json = :o, disconnection_reason = :d, updated_at = :u WHERE attempt_id = :a",
                   {"c": call_id, "s": status, "t": json.dumps(transcript or db.jl(row["transcript"])),
                    "o": json.dumps(outcome), "d": call.get("disconnection_reason"), "u": _now(), "a": attempt_id})
        # Intentionally no deadline/escalation mutation: machine-extracted dates need human review.
        return public(_get(attempt_id))


def stop(attempt_id: str) -> dict:
    row = _get(attempt_id)
    if not row["provider_call_id"]:
        raise HTTPException(409, "Reconcile the call ID first, or stop it in the Retell dashboard.")
    if row["status"] not in TERMINAL:
        request("POST", f"/v2/stop-call/{row['provider_call_id']}")
    return {"stop_requested": True}


def apply_date(attempt_id: str) -> dict:
    """Operator-confirmed: use the date the recipient gave on this call as the case's follow-up deadline.

    Never automatic: the outcome is machine-extracted, so a person must review it and press the button.
    Only dates that passed normalize_outcome's grounding checks (recipient's own words, not in the past) exist here.
    """
    row = _get(attempt_id)
    outcome = db.jl(row["outcome_json"]) or {}
    when = outcome.get("appointment_date") or ""
    try:
        due = datetime.strptime(when, "%Y-%m-%d").replace(hour=17)
    except ValueError:
        raise HTTPException(409, "This call has no confirmed date to use.")
    cases.set_deadline(row["request_id"], due)
    outcome["applied_to_deadline_at"] = _now()
    db.execute("UPDATE {silver.retell_calls} SET outcome_json = :o, updated_at = :u WHERE attempt_id = :a",
               {"o": json.dumps(outcome), "u": _now(), "a": attempt_id})
    return public(_get(attempt_id))
