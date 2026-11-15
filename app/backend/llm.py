"""Thin client for Databricks model serving (OpenAI-compatible chat/invocations API)."""
from __future__ import annotations

import base64
import json
import re
import time
from typing import Any

import httpx

from . import config


class LLMUnavailable(RuntimeError):
    pass


def _auth_headers() -> dict[str, str]:
    if config.DATABRICKS_TOKEN:
        return {"Authorization": f"Bearer {config.DATABRICKS_TOKEN}"}
    try:  # Databricks Apps service principal / CLI profile
        from databricks.sdk.core import Config

        return Config().authenticate()
    except Exception as e:  # pragma: no cover
        raise LLMUnavailable(f"no Databricks credentials: {e}") from e


def _host() -> str:
    if config.DATABRICKS_HOST:
        return config.DATABRICKS_HOST
    try:  # CLI profile (DATABRICKS_CONFIG_PROFILE) or other SDK unified-auth source
        from databricks.sdk.core import Config

        return config._normalize_host(Config().host or "")
    except Exception as e:
        raise LLMUnavailable(f"no Databricks host: {e}") from e


def available() -> bool:
    return bool(config.DATABRICKS_HOST or config.DATABRICKS_TOKEN or config.DATABRICKS_CONFIG_PROFILE)


def chat(messages: list[dict], endpoint: str | None = None, max_tokens: int = 1200, temperature: float = 0.2,
         timeout: float | None = None) -> str:
    if not available():
        raise LLMUnavailable("Databricks not configured")
    endpoint = endpoint or config.CHAT_ENDPOINT
    url = f"{_host()}/serving-endpoints/{endpoint}/invocations"
    try:
        body = {"messages": messages, "max_tokens": max_tokens, "temperature": temperature}
        for attempt in range(RETRIES + 1):
            r = httpx.post(url, headers=_auth_headers(), timeout=timeout or config.LLM_TIMEOUT_S, json=body)
            # Pay-per-token endpoints rate-limit bursts (e.g. a video's frames): back off briefly and retry.
            if r.status_code in RETRY_STATUS and attempt < RETRIES:
                time.sleep(_retry_delay(r, attempt))
                continue
            break
        r.raise_for_status()
        data = r.json()
        content = data["choices"][0]["message"]["content"]
        if isinstance(content, list):  # some endpoints return content parts
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        return content
    except Exception as e:
        raise LLMUnavailable(str(e)) from e


RETRY_STATUS = {429, 503}
RETRIES = 3


def _retry_delay(r: httpx.Response, attempt: int) -> float:
    """Retry-After (seconds) when the server sends it, else 1, 2, 4 s; capped at 8 s."""
    try:
        return min(8.0, max(0.0, float(r.headers.get("retry-after", ""))))
    except ValueError:
        return min(8.0, 2.0 ** attempt)


def image_part(jpeg_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    b64 = base64.b64encode(jpeg_bytes).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}}


def extract_json(text: str) -> Any:
    """Pull the first JSON object out of a model reply (handles ```json fences)."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    raw = m.group(1) if m else text[text.find("{"): text.rfind("}") + 1]
    return json.loads(raw)
