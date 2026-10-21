"""Minimal HTTP client for TypeSafe System One. Stdlib only; the key is never logged."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Callable

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
ENV_KEY = "JEV_API"
TIMEOUT_S = 60
RETRY_STATUSES = (429, 529)
MAX_ATTEMPTS = 4


class JevError(Exception):
    """A Jev call failed. The message never contains the API key or the request body."""


class JevClient:
    def __init__(self, api_key: str, endpoint: str = ENDPOINT, timeout: float = TIMEOUT_S,
                 sleep: Callable[[float], None] = time.sleep, opener=urllib.request.urlopen):
        if not api_key:
            raise JevError(f"{ENV_KEY} is not set")
        self._key = api_key
        self.endpoint = endpoint
        self.timeout = timeout
        self._sleep = sleep
        self._open = opener

    def __repr__(self) -> str:  # keep the key out of tracebacks and logs
        return f"JevClient(endpoint={self.endpoint!r})"

    @classmethod
    def from_config(cls, config) -> "JevClient":
        return cls(config.env_value(ENV_KEY) or "")

    def system_one(self, body: dict) -> dict:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        for attempt in range(MAX_ATTEMPTS):
            req = urllib.request.Request(self.endpoint, data=data, method="POST", headers={
                "Authorization": f"Bearer {self._key}",
                "Content-Type": "application/json",
            })
            try:
                with self._open(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code in RETRY_STATUSES and attempt < MAX_ATTEMPTS - 1:
                    self._sleep(2 ** attempt)
                    continue
                detail = _error_detail(exc)
                raise JevError(f"HTTP {exc.code}{': ' + detail if detail else ''}") from None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                raise JevError(f"request failed: {exc.__class__.__name__}") from None
        raise JevError("retries exhausted")


def _error_detail(exc: urllib.error.HTTPError) -> str:
    try:
        body = json.loads(exc.read().decode("utf-8"))
    except Exception:
        return ""
    detail = body.get("detail") if isinstance(body, dict) else None
    return str(detail)[:200] if detail else ""
