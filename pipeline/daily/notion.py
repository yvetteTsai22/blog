"""Minimal Notion REST client for the Slip box (stdlib only).

The token comes from pipeline.local.yml `notion.token` and is never printed or logged.
Every call targets the Slip box data source by id; nothing searches for databases.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Iterator

from common import notion_schema as ns
from common.config import Config

API = "https://api.notion.com/v1"
VERSION = "2025-09-03"
TIMEOUT = 30
RETRIES = 3
SLIP_BOX_ID = ns.SLIP_BOX_DATA_SOURCE.removeprefix("collection://")


class NotionError(Exception):
    """A Notion call failed; the message never contains the token."""


class Notion:
    def __init__(self, token: str, data_source_id: str = SLIP_BOX_ID):
        if not token:
            raise NotionError("notion.token is missing from pipeline.local.yml")
        self._token = token
        self.data_source_id = data_source_id

    @classmethod
    def from_config(cls, config: Config) -> "Notion":
        return cls(config.get("notion.token") or "")

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        for attempt in range(RETRIES):
            req = urllib.request.Request(
                API + path,
                data=data,
                method=method,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Notion-Version": VERSION,
                    "Content-Type": "application/json",
                },
            )
            try:
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    return json.load(resp)
            except urllib.error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                    time.sleep(float(exc.headers.get("Retry-After") or 2 ** attempt))
                    continue
                raise NotionError(f"{method} {path.split('?')[0]} -> HTTP {exc.code}") from None
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise NotionError(f"{method} {path.split('?')[0]} -> {exc.__class__.__name__}") from None
        raise NotionError("unreachable")

    def query(self, filter_: dict) -> Iterator[dict]:
        body: dict = {"filter": filter_, "page_size": 100}
        while True:
            out = self._call("POST", f"/data_sources/{self.data_source_id}/query", body)
            yield from out.get("results") or []
            if not out.get("has_more"):
                return
            body = {**body, "start_cursor": out["next_cursor"]}

    def page_text(self, page_id: str) -> str:
        """Top-level block text as markdown-ish lines (headings as `## `)."""
        lines, cursor = [], None
        while True:
            qs = "?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
            out = self._call("GET", f"/blocks/{page_id}/children{qs}")
            for block in out.get("results") or []:
                kind = block.get("type", "")
                rich = (block.get(kind) or {}).get("rich_text") or []
                text = "".join(r.get("plain_text", "") for r in rich)
                lines.append(f"## {text}" if kind.startswith("heading") else text)
            if not out.get("has_more"):
                return "\n".join(lines)
            cursor = out["next_cursor"]

    def update_page(self, page_id: str, properties: dict) -> dict:
        return self._call("PATCH", f"/pages/{page_id}", {"properties": properties})


def agent_session_filter(since_iso: str) -> dict:
    """Literature notes from agent sessions created on or after `since_iso`."""
    return {
        "and": [
            {"property": ns.SOURCE, "select": {"equals": ns.SOURCE_AGENT_SESSION}},
            {"timestamp": "created_time", "created_time": {"on_or_after": since_iso}},
        ]
    }


def writing_filter() -> dict:
    """Permanent notes still in 寫作中."""
    return {"property": ns.BLOG_STATUS, "select": {"equals": ns.BLOG_WRITING}}
