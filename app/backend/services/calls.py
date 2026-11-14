"""AI landlord call (P0-7 simulated). Deterministic agent state machine; LLM used only for extraction
(with a regex fallback). The same agent logic is reused by the P1 phone sidecar.

Rules: discloses AI in the first sentence, cites code, stays polite, never threatens, never claims to be a
lawyer or the city.
"""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime

from .. import config, db, llm
from . import deadlines

HOSTILE = re.compile(r"\b(shut up|f\*+|fuck|stop calling|go away|scam|sue|lawyer|harass)\b", re.I)
REFUSE = re.compile(r"\b(not (going|gonna) to|won't|will not|refuse|not my problem|can't help|no way)\b", re.I)
TENANT = re.compile(r"\b(talk|speak) (to|with) (the )?(tenant|them|him|her|resident)\b", re.I)
WHO = re.compile(r"\b(who is this|who's calling|is this a robot|are you (a )?(robot|ai|real))\b", re.I)
WHAT = re.compile(r"\b(what('s| is| exactly)?\b.*\b(problem|issue|wrong|going on)|which (issues?|problems?|repairs?))\b", re.I)
BUSY = re.compile(r"\b(busy|swamped|slammed|backed up)\b", re.I)


def _issue_names(violations: list[dict]) -> str:
    names = [v["name"].lower() for v in violations] or ["maintenance issues"]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def opening_line(address: str, unit: str | None) -> str:
    return (f"Hi, this is an automated AI assistant calling on behalf of your tenant at {address}"
            f"{', unit ' + unit if unit else ''}. This call may be recorded for their records.")


def _violations_sentence(violations: list[dict]) -> str:
    parts = []
    for v in violations:
        secs = [s for s in v.get("code_sections", [])]
        cite = ""
        if secs:
            s = secs[0]
            cite = f", which relates to the Madison housing code on {s['title'].lower()}" + (
                f", section {s['section_id']}" if s.get("verified") else "")
        parts.append(f"{v['name'].lower()}{cite}")
    if len(parts) > 1:
        listing = "; ".join(parts[:-1]) + "; and " + parts[-1]
    else:
        listing = parts[0] if parts else "maintenance issues"
    return (f"I'm calling about {len(violations)} issue{'s' if len(violations) != 1 else ''} in the unit: {listing}. "
            f"The tenant has dated photo documentation. When can these repairs be completed?")


class SimulatedCall:
    def __init__(self, request_id: str, address: str, unit: str | None, violations: list[dict]):
        self.call_id = f"C-{uuid.uuid4().hex[:10]}"
        self.request_id, self.address, self.unit, self.violations = request_id, address, unit, violations
        self.transcript: list[dict] = []
        self.state = "opened"
        self.asked_date = 0
        self.commitment: datetime | None = None
        self.commitment_text = ""
        self._say(opening_line(address, unit))

    def _say(self, text: str) -> str:
        self.transcript.append({"speaker": "ai", "text": text, "at": datetime.now().isoformat(timespec="seconds")})
        return text

    @property
    def done(self) -> bool:
        return self.state == "closed"

    def landlord_says(self, text: str, now: datetime | None = None) -> str | None:
        now = now or datetime.now()
        self.transcript.append({"speaker": "landlord", "text": text, "at": now.isoformat(timespec="seconds")})
        if self.done:
            return None
        if HOSTILE.search(text):
            self.state = "closed"
            return self._say("I understand. I'll end the call here. The tenant will follow up in writing, and may "
                             "contact City of Madison Building Inspection if the issues aren't addressed. Thank you for your time.")
        if self.state == "opened":
            self.state = "asked"
            prefix = ("I'm an AI assistant acting for the tenant. I'm not a person, a lawyer, or the city. "
                      if WHO.search(text) else "")
            return self._say(prefix + _violations_sentence(self.violations))

        if TENANT.search(text):
            return self._say("The tenant has asked that scheduling be confirmed through me and in writing. "
                             "Could you give me a specific date when the repairs will be done?")
        when = deadlines.parse_commitment(text, now)
        if when:
            self.commitment, self.commitment_text = when, text
            self.state = "closed"
            return self._say(f"Thank you. To confirm: the repairs will be completed by {when.strftime('%A, %B %d')}. "
                             f"I'll let the tenant know, and they'll follow up in writing. Have a good day.")
        if WHAT.search(text) and not REFUSE.search(text):
            # Clarifying question, not a dodge: restate the issues and ask again (doesn't count as a re-ask).
            return self._say(f"Of course. The tenant documented {_issue_names(self.violations)}, with dated photos. "
                             "When can someone come out to repair these?")
        if REFUSE.search(text) or self.asked_date >= 1:
            self.state = "closed"
            return self._say("Understood. Since we don't have a repair date, the tenant will follow up in writing and "
                             "may contact City of Madison Building Inspection. Thank you for your time.")
        self.asked_date += 1
        prefix = "I understand you're busy. " if BUSY.search(text) else "Thanks. "
        return self._say(prefix + "Could you give me a specific day the repairs can be completed, "
                         "for example a day this week?")

    def transcript_text(self) -> str:
        return "\n".join(f"{'AI' if t['speaker'] == 'ai' else 'Landlord'}: {t['text']}" for t in self.transcript)


# ---------------------------------------------------------------- extraction
def heuristic_extract(transcript_text: str, now: datetime) -> dict:
    landlord = "\n".join(l.split(":", 1)[1] for l in transcript_text.splitlines() if l.startswith("Landlord:"))
    when = None
    commit_line = ""
    for line in landlord.splitlines()[::-1]:
        when = deadlines.parse_commitment(line, now)
        if when:
            commit_line = line.strip()
            break
    tone = "hostile" if HOSTILE.search(landlord) else ("reluctant" if re.search(r"busy|probably|maybe|fine|look", landlord, re.I) else "cooperative")
    return {"commitment_date": when.isoformat(timespec="minutes") if when else None, "commitment_text": commit_line,
            "landlord_tone": tone, "follow_up_needed": when is None}


def extract(transcript_text: str, now: datetime) -> tuple[dict, str]:
    try:
        reply = llm.chat([
            {"role": "system", "content": "Extract the landlord's repair commitment from this call transcript. "
             f"Today is {now.strftime('%A %Y-%m-%d')}. Reply with JSON only: "
             '{"commitment_date": "YYYY-MM-DDTHH:MM" or null, "commitment_text": "...", '
             '"landlord_tone": "cooperative|reluctant|hostile|unclear", "follow_up_needed": true|false}. '
             "Use 17:00 if no time is given. null if no specific date was promised."},
            {"role": "user", "content": transcript_text}], max_tokens=300, temperature=0.0, timeout=12)
        data = llm.extract_json(reply)
        if data.get("commitment_date"):
            datetime.fromisoformat(data["commitment_date"])
        return data, "live"
    except Exception:
        return heuristic_extract(transcript_text, now), "fallback"


def save_call(call: SimulatedCall, mode: str = "simulated", now: datetime | None = None) -> dict:
    now = now or datetime.now()
    text = call.transcript_text()
    data, source = extract(text, now)
    # The AI already read this date back to the landlord on the call, so it is what the deadline must use.
    # The extractor (LLM or heuristic) still supplies tone; `commitment_source` records where the date came from.
    data["commitment_source"] = source
    if call.commitment:
        if data.get("commitment_date") and data["commitment_date"][:10] != call.commitment.date().isoformat():
            data["extractor_commitment_date"] = data["commitment_date"]  # keep the disagreement visible for debugging
        data["commitment_date"] = call.commitment.isoformat(timespec="minutes")
        data["commitment_text"] = call.commitment_text
        data["follow_up_needed"] = False
        data["commitment_source"] = "confirmed_on_call"
    row = {"call_id": call.call_id, "request_id": call.request_id, "mode": mode,
           "transcript": json.dumps(call.transcript), "commitment_date": data.get("commitment_date"),
           "commitment_text": data.get("commitment_text"), "landlord_tone": data.get("landlord_tone"),
           "created_at": now.isoformat(timespec="seconds")}
    db.insert("silver.calls", row)
    return {**row, "transcript": call.transcript, "follow_up_needed": data.get("follow_up_needed"), "source": source,
            "commitment_source": data["commitment_source"],
            **({"extractor_commitment_date": data["extractor_commitment_date"]}
               if "extractor_commitment_date" in data else {})}


ACTIVE: dict[str, SimulatedCall] = {}


def calls_for_request(request_id: str) -> list[dict]:
    rows = db.q("SELECT * FROM {silver.calls} WHERE request_id = :r ORDER BY created_at", {"r": request_id})
    for r in rows:
        r["transcript"] = db.jl(r["transcript"])
    return rows


def phone_allowed(number: str) -> bool:
    """P1 guard: real calls only when enabled AND number is allowlisted."""
    return config.CALLS_ENABLED and number in config.CALL_ALLOWLIST
