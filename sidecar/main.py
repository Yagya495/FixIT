"""FixIt sidecar (runs on a laptop, outside the workspace).

P1 responsibilities (skeleton; P0 does not depend on this):
  - Listing fetcher: only for sites whose terms allow it. Default answer: "upload the photos instead".
  - Twilio voice webhooks for the real allowlisted AI call (reuses app.backend.services.calls.SimulatedCall).
  - Optional local vision fallback (YOLO-World / OWL-ViT).
Exposed via cloudflared/ngrok ONLY for Twilio webhooks.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import Response

from app.backend import config
from app.backend.services import calls as calls_svc

app = FastAPI(title="FixIt sidecar")
ALLOWED_LISTING_DOMAINS: set[str] = set()  # add only domains whose ToS permit automated fetching


@app.get("/health")
def health():
    return {"ok": True, "calls_enabled": config.CALLS_ENABLED, "allowlist_size": len(config.CALL_ALLOWLIST)}


@app.post("/listing/fetch")
def listing_fetch(url: str = Form(...)):
    from urllib.parse import urlparse

    if urlparse(url).hostname not in ALLOWED_LISTING_DOMAINS:
        raise HTTPException(422, "This site's terms don't allow automated fetching. Upload the listing photos instead.")
    raise HTTPException(501, "Not implemented")


@app.post("/calls/outbound")
def outbound(to: str = Form(...), request_id: str = Form(...)):
    """Place a real call. HARD guard: kill switch + allowlist, checked in code."""
    if not calls_svc.phone_allowed(to):
        raise HTTPException(403, "Calls disabled or number not on the consent allowlist.")
    # P1-1: twilio.rest.Client(...).calls.create(to=to, from_=TWILIO_FROM_NUMBER, url=f"{PUBLIC_URL}/twilio/voice?rid=...")
    raise HTTPException(501, "Twilio integration not implemented yet (P1-1)")


@app.post("/twilio/voice")
def twilio_voice():
    # P1-1: return TwiML <Say> opening line (AI disclosure first) + <Gather input="speech">.
    return Response("<Response><Say>FixIt call handling is not enabled.</Say><Hangup/></Response>", media_type="text/xml")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=int(os.getenv("SIDECAR_PORT", "8010")))
