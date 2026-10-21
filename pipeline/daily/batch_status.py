"""Last night's 02:00 / 04:00 batch status from `orca automations runs --json` (spec §1.5, §6)."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Sequence

DEFAULT_NAME_MATCH = ("batch",)
COMPLETED = "completed"
LOOKBACK_HOURS = 24
QUEUE_WARN = 100


@dataclass(frozen=True)
class BatchRun:
    name: str
    status: str
    scheduled_for: datetime | None


def _parse_time(raw) -> datetime | None:
    if not raw:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw / 1000 if raw > 1e11 else raw).astimezone()
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


def _rows(payload: dict, key: str) -> list[dict]:
    result = payload.get("result", payload) if isinstance(payload, dict) else {}
    rows = result.get(key) if isinstance(result, dict) else None
    return rows if isinstance(rows, list) else []


def parse_runs(runs_payload: dict, automations_payload: dict | None = None) -> list[BatchRun]:
    names = {a.get("id"): a.get("name") or a.get("title") or "" for a in _rows(automations_payload or {}, "automations")}
    out = []
    for r in _rows(runs_payload, "runs"):
        name = r.get("automationName") or names.get(r.get("automationId")) or r.get("title") or ""
        when = r.get("scheduledFor") or r.get("startedAt") or r.get("createdAt")
        out.append(BatchRun(str(name), str(r.get("status") or ""), _parse_time(when)))
    return out


def last_night(runs: Sequence[BatchRun], now: datetime, name_match: Sequence[str] = DEFAULT_NAME_MATCH) -> list[BatchRun]:
    """Batch runs scheduled in the 24h before `now`, oldest first."""
    since = now - timedelta(hours=LOOKBACK_HOURS)
    needles = [m.lower() for m in name_match]
    hits = [
        r for r in runs
        if r.scheduled_for and since <= r.scheduled_for <= now and any(n in r.name.lower() for n in needles)
    ]
    return sorted(hits, key=lambda r: r.scheduled_for)


def status_lines(runs: Sequence[BatchRun], queue_length: int, tz) -> list[str]:
    lines = []
    if not any(r.status == COMPLETED for r in runs):
        lines.append(f"昨晚 batch 沒有跑 · last night's batch did not run, {queue_length} sessions pending")
    for r in runs:
        lines.append(f"batch {r.scheduled_for.astimezone(tz):%H:%M} {r.status}")
    lines.append(f"queue: {queue_length}")
    if queue_length > QUEUE_WARN:
        lines.append(f"⚠ queue over {QUEUE_WARN} ({queue_length})")
    return lines


def fetch(run: Callable[[list[str]], str] | None = None) -> tuple[dict, dict] | None:
    """(runs, automations) JSON, or None when the orca CLI fails."""
    def default(cmd: list[str]) -> str:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=True).stdout

    run = run or default
    try:
        runs = json.loads(run(["orca", "automations", "runs", "--json"]))
        autos = json.loads(run(["orca", "automations", "list", "--json"]))
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None
    return runs, autos
