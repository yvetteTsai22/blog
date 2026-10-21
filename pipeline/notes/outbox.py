"""Local staging for literature notes: <state>/outbox/<sessionId>.json, ledger <state>/written.jsonl.

Python never talks to Notion. The batch agent reads pending entries, writes them via MCP,
then calls `commit` so the entry moves to the ledger (idempotency on rerun).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Mapping

from .mapping import render_body, to_properties

OUTBOX_DIR = "outbox"
LEDGER_FILE = "written.jsonl"


class Outbox:
    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.dir = self.state_dir / OUTBOX_DIR
        self.ledger = self.state_dir / LEDGER_FILE

    def path(self, session_id: str) -> Path:
        return self.dir / f"{session_id}.json"

    def stage(self, record: Mapping) -> Path:
        """Write the record plus its rendered Notion payload; atomic replace."""
        payload = {
            **record,
            "notion": {"properties": to_properties(record), "content": render_body(record)},
        }
        self.dir.mkdir(parents=True, exist_ok=True)
        target = self.path(record["session_id"])
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, target)
        return target

    def is_staged(self, session_id: str) -> bool:
        return self.path(session_id).is_file()

    def pending(self) -> Iterator[dict]:
        for p in sorted(self.dir.glob("*.json")) if self.dir.is_dir() else []:
            yield json.loads(p.read_text(encoding="utf-8"))

    def written(self) -> dict[str, dict]:
        if not self.ledger.is_file():
            return {}
        out = {}
        for line in self.ledger.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            out[row["session_id"]] = row
        return out

    def is_written(self, session_id: str) -> bool:
        return session_id in self.written()

    def mark_written(self, session_id: str, page_id: str, now: datetime | None = None) -> dict:
        """Record a confirmed Notion write and drop the staged file. Idempotent."""
        existing = self.written().get(session_id)
        staged = self.path(session_id)
        topic, cycle = None, None
        if staged.is_file():
            data = json.loads(staged.read_text(encoding="utf-8"))
            topic, cycle = data.get("topic_of"), data.get("cycle")
        if existing is None:
            row = {
                "session_id": session_id,
                "page_id": page_id,
                "topic_of": topic,
                "cycle": cycle,
                "written_at": (now or datetime.now(timezone.utc)).isoformat(),
            }
            self.state_dir.mkdir(parents=True, exist_ok=True)
            with self.ledger.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            existing = row
        staged.unlink(missing_ok=True)
        return existing
