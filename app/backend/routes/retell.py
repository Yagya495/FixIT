"""Operator-protected endpoints for real Retell test calls."""
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from .. import config
from ..services import retell

router = APIRouter(prefix="/api/retell", tags=["Retell"])


def operator(x_fixit_call_token: str | None = Header(default=None)):
    retell.authorize(x_fixit_call_token)


@router.get("/config")
def status():
    return {"enabled": config.CALLS_ENABLED and retell.configured(), "test_calls_only": True,
            "recording_enabled": True}


@router.get("/cases/{rid}/calls", dependencies=[Depends(operator)])
def history(rid: str):
    return retell.history(rid)


@router.post("/cases/{rid}/calls", dependencies=[Depends(operator)])
def start(rid: str, body: retell.StartCall):
    return retell.start(rid, body)


class Refresh(BaseModel):
    provider_call_id: str | None = Field(default=None, pattern=r"^[\w-]{1,128}$")


@router.post("/calls/{attempt_id}/refresh", dependencies=[Depends(operator)])
def refresh(attempt_id: str, body: Refresh):
    return retell.refresh(attempt_id, body.provider_call_id)


@router.post("/calls/{attempt_id}/resume", dependencies=[Depends(operator)])
def resume(attempt_id: str):
    """Re-send an uncertain create with the same idempotency key, within Retell's dedupe window."""
    return retell.resume(attempt_id)


@router.post("/calls/{attempt_id}/stop", dependencies=[Depends(operator)])
def stop(attempt_id: str):
    return retell.stop(attempt_id)


@router.post("/calls/{attempt_id}/apply-date", dependencies=[Depends(operator)])
def apply_date(attempt_id: str):
    """Operator confirms the date captured on the call; it becomes the case's follow-up deadline."""
    return retell.apply_date(attempt_id)
