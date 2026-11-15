"""No live calls: provider is stubbed; all writes use a scratch SQLite database."""
import copy
import json
import threading
from datetime import datetime
from unittest.mock import Mock
from zoneinfo import ZoneInfo

import httpx
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.backend import config, db
from app.backend.services import retell


BODY = dict(attempt_id="attempt_1234567890", to_number="+16085550123", tenant_name="Demo Tenant",
            tenant_authorized=True, recipient_consented=True, recording_consented=True,
            case_reviewed=True, test_call=True)
CASE = dict(request_id="RR-test", address="1234 Demo St", unit="A", landlord="Fictional Manager",
            severity="urgent", violations=[dict(name="Leak", violation_type="LEAK_PLUMBING", severity="urgent", observations=[
                dict(note="A brown ring", basis_text="Seen in photo", evidence_id="E-1")], code_sections=[
                    dict(section_id="27.99(unverified)", snippet="Do not send", verified=False, official_text=True),
                    dict(section_id="27.05(2)(j)", snippet="Checked excerpt", verified=True, official_text=True)])])


@pytest.fixture
def setup(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "DATA_BACKEND", "local")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SQLITE_PATH", tmp_path / "test.db")
    monkeypatch.setattr(db, "_local", threading.local())
    monkeypatch.setattr(config, "CALLS_ENABLED", True)
    monkeypatch.setattr(config, "CALL_ALLOWLIST", {BODY["to_number"]})
    monkeypatch.setattr(config, "RETELL_API_KEY", "fake-provider-key")
    monkeypatch.setattr(config, "RETELL_AGENT_ID", "agent_test")
    monkeypatch.setattr(config, "RETELL_FROM_NUMBER", "+16085550456")
    monkeypatch.setattr(config, "RETELL_OPERATOR_TOKEN", "operator-token-" + "x" * 32)
    db.init_local_schema()
    monkeypatch.setattr(retell.cases, "get_case", lambda rid: copy.deepcopy(CASE) if rid == "RR-test" else None)
    monkeypatch.setattr(retell.cases, "set_deadline", Mock(side_effect=AssertionError("must not set a deadline")))
    def provider(method, path, payload=None, params=None):
        if path.startswith("/get-agent/"):
            return {"response_engine": {"type": "retell-llm", "llm_id": "llm_test"}}
        if path.startswith("/get-retell-llm/"):
            return {"general_prompt": retell.PROMPT_PATH.read_text(), "begin_message": retell.OPENING,
                    "start_speaker": "agent", "general_tools": [{"type": "end_call"}]}
        if path == "/v2/create-phone-call":
            return {"call_id": "call_test", "call_status": "registered"}
        if path.startswith("/v2/stop-call/"):
            return {}
        return finished()
    fake = Mock(side_effect=provider)
    monkeypatch.setattr(retell, "request", fake)
    return fake


def finished(kind="inspection", quote="We can inspect on November 17", date="2026-11-17"):
    return {"call_id": "call_test", "agent_id": "agent_test", "to_number": BODY["to_number"],
            "metadata": {"fixit_attempt_id": BODY["attempt_id"], "fixit_request_id": "RR-test"},
            "call_status": "ended", "transcript_object": [{"role": "user", "content": quote}],
            "call_analysis": {"call_summary": "An inspection was offered.", "custom_analysis_data": {
                "appointment_kind": kind, "appointment_date": date, "date_as_spoken": quote,
                "follow_up_needed": True, "acknowledgement": "acknowledged"}}}


def start():
    return retell.start("RR-test", retell.StartCall(**BODY))


@pytest.mark.parametrize("field", ["tenant_authorized", "recipient_consented", "recording_consented", "case_reviewed", "test_call"])
def test_each_consent_required(field):
    with pytest.raises(ValidationError):
        retell.StartCall(**{**BODY, field: False})
    data = {k: v for k, v in BODY.items() if k != field}
    with pytest.raises(ValidationError):
        retell.StartCall(**data)


@pytest.mark.parametrize("number", ["6085550123", "911", "+1 6085550123", "https://example.com"])
def test_phone_validation(number):
    with pytest.raises(ValidationError):
        retell.StartCall(**{**BODY, "to_number": number})


def test_gates_never_contact_provider(setup, monkeypatch):
    monkeypatch.setattr(config, "CALLS_ENABLED", False)
    with pytest.raises(HTTPException, match="disabled"):
        start()
    monkeypatch.setattr(config, "CALLS_ENABLED", True)
    monkeypatch.setattr(config, "CALL_ALLOWLIST", set())
    with pytest.raises(HTTPException, match="allowlist"):
        start()
    setup.assert_not_called()


def test_context_uses_verified_citations_only_and_no_fictional_history(setup):
    data = retell.context_for(CASE, retell.StartCall(**BODY))
    assert all(isinstance(v, str) for v in data.values())
    assert "unverified" not in data["housing_code_references"]
    assert "27.05(2)(j)" in data["housing_code_references"]
    assert "Fictional Manager" not in json.dumps(data)
    assert data["management_company"] == "Not supplied"
    assert "No previous communications" in data["previous_requests"]
    assert "A brown ring" in data["maintenance_issues"]


def test_start_payload_and_idempotency(setup):
    first = start()
    assert start() == first
    creates = [c for c in setup.call_args_list if c.args[0] == "POST"]
    assert len(creates) == 1
    payload = creates[0].args[2]
    assert payload["idempotency_key"] == BODY["attempt_id"]
    assert payload["honor_internal_dnc"] is True
    assert payload["agent_override"]["agent"]["enable_dnc_detection"] is True
    assert payload["agent_override"]["agent"]["data_storage_retention_days"] == 30
    with pytest.raises(HTTPException, match="different"):
        retell.start("RR-other", retell.StartCall(**BODY))
    assert "context_json" not in first and "consent_json" not in first and "to_number" not in first


def test_uncertain_creation_persists_and_never_redials(setup):
    previous = setup.side_effect
    def fail(method, path, payload=None, params=None):
        if method == "POST":
            raise HTTPException(502, "timeout")
        return previous(method, path, payload, params)
    setup.side_effect = fail
    with pytest.raises(HTTPException, match="uncertain"):
        start()
    assert start()["status"] == "unknown"
    assert len([c for c in setup.call_args_list if c.args[0] == "POST"]) == 1
    with pytest.raises(HTTPException, match="previous call"):
        retell.start("RR-test", retell.StartCall(**{**BODY, "attempt_id": "another_attempt_12345"}))
    assert retell.refresh(BODY["attempt_id"], "call_test")["status"] == "ended"


@pytest.mark.parametrize("kind", ["inspection", "repair_estimate", "repair_commitment"])
def test_outcome_types_do_not_set_deadlines(setup, kind):
    start()
    setup.return_value = finished(kind=kind)
    setup.side_effect = None
    value = retell.refresh(BODY["attempt_id"])
    assert value["outcome_json"]["appointment_kind"] == kind
    assert value["outcome_json"]["appointment_date"] == "2026-11-17"
    retell.cases.set_deadline.assert_not_called()


def test_agent_speech_cannot_be_used_as_recipient_commitment():
    call = finished(kind="repair_commitment")
    call["transcript_object"][0]["role"] = "agent"
    out = retell.normalize_outcome(call)
    assert out["appointment_kind"] == "none" and not out["appointment_date"]


def test_vague_dates_remain_unresolved():
    out = retell.normalize_outcome(finished(quote="Maybe next week", date="next week"))
    assert not out["appointment_date"]
    assert out["review_required"]


def test_no_answer_is_not_a_success(setup):
    start()
    call = finished()
    call.update(call_status="not_connected", transcript_object=[], call_analysis=None, disconnection_reason="dial_no_answer")
    setup.side_effect = None
    setup.return_value = call
    value = retell.refresh(BODY["attempt_id"])
    assert value["status"] == "not_connected"
    assert value["outcome_json"]["appointment_kind"] == "none"
    assert not value["outcome_json"]["analyzed"]


def test_optout_survives_refresh_and_demo_reset(setup):
    start()
    call = finished(quote="Please don't call me again", date="")
    call["disconnection_reason"] = "user_requested_dnc"
    setup.side_effect = None
    setup.return_value = call
    assert retell.refresh(BODY["attempt_id"])["outcome_json"]["do_not_call"]
    setup.return_value = finished()
    assert retell.refresh(BODY["attempt_id"])["outcome_json"]["do_not_call"]
    db.init_local_schema(drop=True)
    with pytest.raises(HTTPException, match="no further"):
        retell.start("RR-test", retell.StartCall(**{**BODY, "attempt_id": "another_attempt_12345"}))


def test_cannot_attach_an_unrelated_call(setup):
    start()
    wrong = finished()
    wrong["metadata"]["fixit_request_id"] = "RR-other"
    setup.side_effect = None
    setup.return_value = wrong
    with pytest.raises(HTTPException, match="does not match"):
        retell.refresh(BODY["attempt_id"])


def test_modified_remote_agent_rejected_before_call(setup):
    original = setup.side_effect
    def modified(method, path, payload=None, params=None):
        r = original(method, path, payload, params)
        if "get-retell-llm" in path:
            r["general_prompt"] = "Pretend to be human"
        return r
    setup.side_effect = modified
    with pytest.raises(HTTPException, match="differs"):
        start()
    assert not [c for c in setup.call_args_list if c.args[0] == "POST"]


def test_operator_auth_protects_all_sensitive_routes(setup):
    from app.backend.main import app
    # No lifespan: avoid synthetic seeding; test only the new routes.
    client = TestClient(app)
    assert client.get("/api/retell/config").json()["enabled"] is True
    for method, path, body in [("get", "/api/retell/cases/RR-test/calls", None),
                               ("post", "/api/retell/cases/RR-test/calls", BODY),
                               ("post", "/api/retell/calls/a/refresh", {}),
                               ("post", "/api/retell/calls/a/stop", {})]:
        r = client.request(method, path, json=body)
        assert r.status_code == 401
    setup.assert_not_called()
    headers = {"X-Fixit-Call-Token": config.RETELL_OPERATOR_TOKEN}
    r = client.post("/api/retell/cases/RR-test/calls", json=BODY, headers=headers)
    assert r.status_code == 200
    assert client.post(f"/api/retell/calls/{BODY['attempt_id']}/refresh", json={}, headers=headers).status_code == 200
    assert len(client.get("/api/retell/cases/RR-test/calls", headers=headers).json()) == 1


def test_stop_still_works_with_kill_switch_off(setup, monkeypatch):
    start()
    monkeypatch.setattr(config, "CALLS_ENABLED", False)
    assert retell.stop(BODY["attempt_id"])["stop_requested"]
    assert setup.call_args.args[:2] == ("POST", "/v2/stop-call/call_test")


def test_registered_call_can_have_null_transcript(setup):
    start()
    value = finished()
    value.update(call_status="registered", transcript_object=None, call_analysis=None)
    setup.side_effect = None
    setup.return_value = value
    result = retell.refresh(BODY["attempt_id"])
    assert result["transcript"] == []
    assert not result["outcome_json"]["analyzed"]


@pytest.mark.parametrize("status", [401, 429, 500])
def test_provider_errors_are_sanitized_and_not_retried(monkeypatch, status):
    transport = Mock(return_value=httpx.Response(status, json={"error": "secret-phone-and-key"}))
    client = httpx.Client(transport=httpx.MockTransport(transport))
    monkeypatch.setattr(httpx, "Client", lambda **kw: client)
    with pytest.raises(HTTPException) as error:
        retell.request("POST", "/v2/create-phone-call", {})
    assert "secret-phone-and-key" not in error.value.detail
    assert transport.call_count == 1


def test_provider_stop_accepts_empty_204(monkeypatch):
    client = httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(204)))
    monkeypatch.setattr(httpx, "Client", lambda **kw: client)
    assert retell.request("POST", "/v2/stop-call/call_test") == {}


# ---------------------------------------------------------------- review fixes (2026-11-15)
def _post_fails(setup, error):
    previous = setup.side_effect
    def fail(method, path, payload=None, params=None):
        if method == "POST" and path == "/v2/create-phone-call":
            raise error
        return previous(method, path, payload, params)
    setup.side_effect = fail
    return previous


def _creates(setup):
    return [c for c in setup.call_args_list if c.args[:2] == ("POST", "/v2/create-phone-call")]


def test_non_ascii_token_is_401_not_500(setup):
    with pytest.raises(HTTPException) as e:
        retell.authorize("tökén-" + "x" * 40)
    assert e.value.status_code == 401


def test_dnc_rejection_is_definitive_and_sticky(setup):
    _post_fails(setup, retell.ProviderError("HTTP 400", 400, dnc_hint=True))
    with pytest.raises(HTTPException, match="no call was placed"):
        start()
    row = retell.history("RR-test")[0]
    assert row["status"] == "rejected" and row["outcome_json"]["do_not_call"] and not row["resumable"]
    assert retell.refresh(BODY["attempt_id"])["status"] == "rejected"  # nothing to fetch, no provider GET
    with pytest.raises(HTTPException, match="no further"):
        retell.start("RR-test", retell.StartCall(**{**BODY, "attempt_id": "another_attempt_12345"}))


def test_rate_limit_rejection_allows_a_new_attempt(setup):
    previous = _post_fails(setup, retell.ProviderError("HTTP 429", 429))
    with pytest.raises(HTTPException, match="rejected"):
        start()
    setup.side_effect = previous
    assert retell.start("RR-test", retell.StartCall(**{**BODY, "attempt_id": "another_attempt_12345"}))["status"] == "registered"


def test_uncertain_create_can_be_resumed_with_identical_idempotent_request(setup):
    previous = _post_fails(setup, retell.ProviderError("unreachable"))
    with pytest.raises(HTTPException, match="uncertain"):
        start()
    assert retell.history("RR-test")[0]["resumable"]
    setup.side_effect = previous
    assert retell.resume(BODY["attempt_id"])["provider_call_id"] == "call_test"
    first, second = _creates(setup)
    assert first.args[2] == second.args[2] and second.args[2]["idempotency_key"] == BODY["attempt_id"]
    with pytest.raises(HTTPException, match="cannot be resumed"):
        retell.resume(BODY["attempt_id"])  # linked now: never re-sent


def test_failed_resume_stays_uncertain_even_on_4xx(setup):
    _post_fails(setup, retell.ProviderError("unreachable"))
    with pytest.raises(HTTPException):
        start()
    _post_fails(setup, retell.ProviderError("HTTP 429", 429))
    with pytest.raises(HTTPException, match="uncertain"):
        retell.resume(BODY["attempt_id"])
    assert retell.history("RR-test")[0]["status"] == "unknown"  # the first request may have placed a call


def test_resume_refused_after_window_or_config_change(setup, monkeypatch):
    _post_fails(setup, retell.ProviderError("unreachable"))
    with pytest.raises(HTTPException):
        start()
    monkeypatch.setattr(config, "RETELL_FROM_NUMBER", "+16085550999")
    with pytest.raises(HTTPException, match="configuration changed"):
        retell.resume(BODY["attempt_id"])
    monkeypatch.setattr(config, "RETELL_FROM_NUMBER", "+16085550456")
    db.execute("UPDATE {silver.retell_calls} SET created_at = '2026-01-01T00:00:00'")
    with pytest.raises(HTTPException, match="cannot be resumed"):
        retell.resume(BODY["attempt_id"])
    monkeypatch.setattr(config, "CALLS_ENABLED", False)
    with pytest.raises(HTTPException, match="disabled"):
        retell.resume(BODY["attempt_id"])
    assert len(_creates(setup)) == 1


def test_verified_section_is_not_cited_for_another_issue_type(setup):
    case = copy.deepcopy(CASE)
    case["violations"][0]["violation_type"] = "WATER_DAMAGE"  # provisional category
    case["violations"][0]["code_sections"] = [dict(section_id="27.05(2)(g)1.", snippet="x", verified=True, official_text=True)]
    assert json.loads(retell.context_for(case, retell.StartCall(**BODY))["housing_code_references"]) == []


@pytest.mark.parametrize("change", [{"start_speaker": "user"}, {"start_speaker": None}, {"agent_webhook": "https://x.example"}])
def test_agent_check_requires_agent_first_and_no_webhook(setup, change):
    original = setup.side_effect
    def modified(method, path, payload=None, params=None):
        r = original(method, path, payload, params)
        if "get-retell-llm" in path and "start_speaker" in change:
            r["start_speaker"] = change["start_speaker"]
        if "get-agent" in path and "agent_webhook" in change:
            r["webhook_url"] = change["agent_webhook"]
        return r
    setup.side_effect = modified
    with pytest.raises(HTTPException, match="differs"):
        retell.check_agent()


def test_agent_check_reads_pinned_llm_version(setup):
    original = setup.side_effect
    def pinned(method, path, payload=None, params=None):
        if path.startswith("/get-agent/"):
            assert params == {"version": "latest"}
            return {"response_engine": {"type": "retell-llm", "llm_id": "llm_test", "version": 3}}
        if path.startswith("/get-retell-llm/"):
            assert params == {"version": 3}
        return original(method, path, payload, params)
    setup.side_effect = pinned
    retell.check_agent()


def test_grounding_ignores_punctuation_and_keeps_kind_without_date():
    call = finished(kind="inspection", quote="we can send someone to look", date="")
    call["transcript_object"][0]["content"] = "Yeah... we can send someone to look, sometime."
    out = retell.normalize_outcome(call)
    assert out["appointment_kind"] == "inspection" and out["appointment_date"] == ""


def test_partial_word_is_not_grounding():
    call = finished(kind="repair_commitment", quote="fix it", date="")
    call["transcript_object"][0]["content"] = "We can't fixit person"
    assert retell.normalize_outcome(call)["appointment_kind"] == "none"


def test_past_date_is_dropped():
    call = finished(date="2026-11-01")
    call["start_timestamp"] = int(datetime(2026, 11, 15, 12, tzinfo=ZoneInfo("America/Chicago")).timestamp() * 1000)
    out = retell.normalize_outcome(call)
    assert out["appointment_date"] == "" and out["appointment_kind"] == "inspection"


@pytest.mark.parametrize("text,expected", [
    ("Please take me off your list.", True), ("No more calls, okay?", True), ("Stop calling this number", True),
    ("Remove my number from this", True), ("I never called the plumber yet", False), ("Call me Thursday", False),
])
def test_opt_out_phrases(text, expected):
    call = finished(quote="x", date="")
    call["call_analysis"]["custom_analysis_data"]["do_not_call"] = False
    call["transcript_object"] = [{"role": "user", "content": text}]
    assert retell.normalize_outcome(call)["do_not_call"] is expected


def test_analysis_schema_uses_enums_and_optional_fields():
    by_name = {f["name"]: f for f in retell.analysis_schema()}
    assert by_name["appointment_kind"]["type"] == "enum" and "repair_commitment" in by_name["appointment_kind"]["choices"]
    assert by_name["acknowledgement"]["type"] == "enum"
    assert all(by_name[k]["required"] is False for k in retell.ANALYSIS_FIELDS)
    assert retell.llm_config()["start_speaker"] == "agent"


def test_opening_asks_for_recording_consent_instead_of_assuming_it():
    assert "with your prior consent" not in retell.OPENING
    assert retell.OPENING.rstrip().endswith("Is it okay to continue on a recorded line?")
    assert "AI assistant" in retell.OPENING and "test call" in retell.OPENING


def test_public_demo_disables_real_calls_even_with_keys_set():
    """PUBLIC_DEMO must clear every Retell setting so anonymous visitors can never place a real call."""
    import os
    import subprocess
    import sys

    env = {**os.environ, "PUBLIC_DEMO": "true", "CALLS_ENABLED": "true", "CALL_ALLOWLIST": "+16085550123",
           "RETELL_API_KEY": "fake-key", "RETELL_AGENT_ID": "fake-agent", "RETELL_FROM_NUMBER": "+16085550456",
           "RETELL_OPERATOR_TOKEN": "x" * 40}
    code = ("from app.backend import config; from app.backend.services import retell; "
            "print(config.CALLS_ENABLED, len(config.CALL_ALLOWLIST), bool(config.RETELL_API_KEY), retell.configured())")
    out = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, check=True).stdout.split()
    assert out == ["False", "0", "False", "False"]


def test_apply_date_sets_deadline_only_when_operator_confirms(setup, monkeypatch):
    start()
    retell.refresh(BODY["attempt_id"])  # the fixture's set_deadline mock fails if refresh ever sets a deadline
    applied = Mock()
    monkeypatch.setattr(retell.cases, "set_deadline", applied)
    out = retell.apply_date(BODY["attempt_id"])
    applied.assert_called_once_with("RR-test", datetime(2026, 11, 17, 17, 0))
    assert out["outcome_json"]["applied_to_deadline_at"]


def test_apply_date_refuses_calls_without_a_grounded_date(setup, monkeypatch):
    start()
    setup.side_effect = None
    setup.return_value = finished(quote="Maybe next week", date="next week")
    retell.refresh(BODY["attempt_id"])
    with pytest.raises(HTTPException) as e:
        retell.apply_date(BODY["attempt_id"])
    assert e.value.status_code == 409


def test_apply_date_route_requires_operator_token(setup):
    from app.backend.main import app
    client = TestClient(app)
    assert client.post("/api/retell/calls/a/apply-date").status_code == 401
