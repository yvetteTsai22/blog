"""Load a Claude Code transcript (~/.claude/projects/<slug>/<sessionId>.jsonl) into a flat event list."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

NOISE_PREFIX = (
    "Base directory for this skill",
    "<command-",
    "<local-command",
    "<system-reminder",
    "Caveat:",
    "[Request interrupted",
    "<task-notification>",
    "<bash-notification>",
)
EDIT_TOOLS = frozenset({"Edit", "Write", "MultiEdit", "NotebookEdit"})


@dataclass(frozen=True)
class Event:
    """One content block of a user/assistant message, in transcript order."""
    role: str
    meta: bool
    block: dict
    ts: datetime | None


@dataclass(frozen=True)
class Session:
    path: Path
    session_id: str
    project: str
    title: str | None
    turns: int
    events: tuple[Event, ...]
    timestamps: tuple[datetime, ...] = field(default=())


def parse_ts(value) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_real_prompt(ev: Event) -> bool:
    if ev.role != "user" or ev.meta or ev.block.get("type") != "text":
        return False
    s = (ev.block.get("text") or "").strip()
    return bool(s) and not s.startswith(NOISE_PREFIX)


def load_session(path: str | Path) -> Session:
    path = Path(path)
    events: list[Event] = []
    stamps: list[datetime] = []
    title, turns = None, 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(d, dict):
                continue
            ts = parse_ts(d.get("timestamp"))
            if ts is not None:
                stamps.append(ts)
            t = d.get("type")
            if t == "ai-title":
                title = d.get("aiTitle")
            if t not in ("user", "assistant") or d.get("isSidechain"):
                continue
            msg = d.get("message") or {}
            content = msg.get("content")
            blocks = [{"type": "text", "text": content}] if isinstance(content, str) else (content or [])
            turns += 1
            meta = bool(d.get("isMeta", False))
            events.extend(Event(t, meta, b, ts) for b in blocks if isinstance(b, dict))
    return Session(
        path=path,
        session_id=path.stem,
        project=path.parent.name,
        title=title,
        turns=turns,
        events=tuple(events),
        timestamps=tuple(stamps),
    )


def session_files(projects_dir: str | Path) -> list[Path]:
    """Main-session transcripts only: <slug>/<id>.jsonl, never */subagents/*."""
    root = Path(projects_dir).expanduser()
    return sorted(p for p in root.glob("*/*.jsonl") if "subagents" not in p.parts)
