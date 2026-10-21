#!/usr/bin/env python3
"""Claude Code SessionEnd hook: append the ended session's id to the pending queue.

Spec §1.2. Stdlib only, no LLM call, no judgement. Reads the hook JSON on stdin,
appends one line (session_id) to <state>/pending-queue.txt and always exits 0.
Errors go to <state>/hooks.log and never block the session from ending.

State dir: ${BLOG_PIPELINE_STATE_DIR:-~/.local/state/blog-pipeline}
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

QUEUE_FILE = "pending-queue.txt"
LOG_FILE = "hooks.log"
SUBAGENT_MARKER = "/subagents/"
SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def state_dir() -> Path:
    override = os.environ.get("BLOG_PIPELINE_STATE_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".local" / "state" / "blog-pipeline"


def is_subagent(payload: dict) -> bool:
    """v1 exclusion: subagent transcripts live under */subagents/*."""
    transcript = str(payload.get("transcript_path") or "")
    return SUBAGENT_MARKER in transcript.replace("\\", "/")


def parse_session_id(payload: dict) -> str:
    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not SESSION_ID_RE.match(session_id):
        raise ValueError(f"invalid or missing session_id: {session_id!r}")
    return session_id


def append_line(path: Path, line: str) -> None:
    """Append one line atomically: O_APPEND + exclusive lock + single write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (line + "\n").encode("utf-8")
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def log(state: Path, message: str) -> None:
    """Best-effort log; never raises."""
    try:
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        append_line(state / LOG_FILE, f"{stamp} session_end {message}")
    except Exception:
        try:
            sys.stderr.write(f"session_end hook: {message}\n")
        except Exception:
            pass


def handle(raw: str, state: Path) -> str:
    """Process one hook payload. Returns a short outcome label."""
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("hook payload is not a JSON object")
    if is_subagent(payload):
        return "skipped-subagent"
    session_id = parse_session_id(payload)
    append_line(state / QUEUE_FILE, session_id)
    return "queued"


def main() -> int:
    state = state_dir()
    try:
        handle(sys.stdin.read(), state)
    except Exception as exc:  # never block session end
        log(state, f"error: {exc!r}\n{traceback.format_exc().rstrip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
