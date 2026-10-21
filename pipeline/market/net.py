"""Outbound HTTP for market signals: timeouts, a 24h cache, a GitHub rate limit, a query log.

Every request URL goes through `Net.get_json` / `Net.get_text`, so the outbound log
(`<state>/market/outbound.jsonl`) is complete. The GitHub token is read from the macOS
Keychain at call time and never stored, logged or printed.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

USER_AGENT = "blog-pipeline-market/0.1 (+https://github.com/yvetteTsai22/blog)"
CACHE_TTL_S = 24 * 3600


class SourceError(Exception):
    """A source failed (network, HTTP status, parse, missing credential)."""


def keychain_token(service: str, run: Callable = subprocess.run) -> str:
    if not service:
        raise SourceError("no keychain service configured for the GitHub token")
    try:
        out = run(["security", "find-generic-password", "-s", service, "-w"],
                  capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        raise SourceError("keychain lookup failed") from None
    token = (out.stdout or "").strip()
    if out.returncode != 0 or not token:
        raise SourceError(f"GitHub token missing from Keychain item '{service}'; GitHub signals skipped")
    return token


def _default_fetch(url: str, headers: dict, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise SourceError(f"{type(exc).__name__}") from None


@dataclass
class Net:
    state_dir: Path
    timeout_s: float = 15.0
    github_per_minute: int = 30
    keychain_service: str = ""
    fetch: Callable[[str, dict, float], bytes] = _default_fetch
    token_reader: Callable[[str], str] = keychain_token
    clock: Callable[[], float] = time.time
    sleep: Callable[[float], None] = time.sleep
    _github_calls: list[float] = field(default_factory=list)
    _token: str | None = field(default=None, repr=False)

    @property
    def dir(self) -> Path:
        return self.state_dir / "market"

    def _log(self, kind: str, url: str, purpose: str, cached: bool) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        row = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "kind": kind, "purpose": purpose, "url": url, "cached": cached}
        with (self.dir / "outbound.jsonl").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")

    def _cache_path(self, url: str) -> Path:
        return self.dir / "cache" / (hashlib.sha256(url.encode()).hexdigest() + ".bin")

    def _github_wait(self) -> None:
        now = self.clock()
        self._github_calls = [t for t in self._github_calls if now - t < 60]
        if len(self._github_calls) >= self.github_per_minute:
            self.sleep(60 - (now - self._github_calls[0]) + 0.1)
        self._github_calls.append(self.clock())

    def _headers(self, github: bool) -> dict:
        headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
        if github:
            if self._token is None:
                self._token = self.token_reader(self.keychain_service)
            headers["Authorization"] = f"Bearer {self._token}"
            headers["Accept"] = "application/vnd.github+json"
        return headers

    def get_bytes(self, url: str, kind: str, purpose: str) -> bytes:
        """kind: `feed` (route B pull) or `query` (route A phrase query)."""
        cache = self._cache_path(url)
        if cache.is_file() and self.clock() - cache.stat().st_mtime < CACHE_TTL_S:
            self._log(kind, url, purpose, cached=True)
            return cache.read_bytes()
        github = url.startswith("https://api.github.com/")
        headers = self._headers(github)
        if github:
            self._github_wait()
        self._log(kind, url, purpose, cached=False)
        body = self.fetch(url, headers, self.timeout_s)
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(body)
        return body

    def get_json(self, url: str, kind: str, purpose: str):
        body = self.get_bytes(url, kind, purpose)
        try:
            return json.loads(body)
        except ValueError:
            raise SourceError("invalid JSON") from None

    def get_text(self, url: str, kind: str, purpose: str) -> str:
        return self.get_bytes(url, kind, purpose).decode("utf-8", errors="replace")
