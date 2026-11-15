"""Prepare a dedicated Retell agent. Dry run is offline; --apply creates resources, never calls.

python scripts/retell_setup.py --voice-id <voice-id> [--model gpt-4.1] [--apply]
python scripts/retell_setup.py --check
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.backend import config
from app.backend.services import retell


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--voice-id")
    p.add_argument("--model", default="gpt-4.1")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    if args.check:
        retell.check_agent()
        print("Dedicated FixIT prompt and tools match.")
        return
    if not args.voice_id:
        p.error("--voice-id is required; choose a voice from your Retell dashboard")
    llm = retell.llm_config(args.model)  # includes start_speaker="agent": the AI speaks first on outbound calls
    agent = {"agent_name": "FixIT — authorized landlord test calls", "voice_id": args.voice_id,
             "response_engine": {"type": "retell-llm", "llm_id": "<created-llm-id>"}, **retell.agent_settings()}
    if not args.apply:
        print(json.dumps({"dry_run": True, "llm": llm, "agent": agent}, indent=2))
        return
    if not config.RETELL_API_KEY:
        p.error("Set RETELL_API_KEY in .env or the environment first")
    result = retell.request("POST", "/create-retell-llm", llm)
    print("Created LLM:", result["llm_id"], "(retain this ID if agent creation fails)")
    agent["response_engine"]["llm_id"] = result["llm_id"]
    created = retell.request("POST", "/create-agent", agent)
    print("Set RETELL_AGENT_ID=" + created["agent_id"])
    print("No phone number purchased; no call placed. Calling remains separately gated.")


if __name__ == "__main__":
    main()
