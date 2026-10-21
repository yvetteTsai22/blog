"""Empty check (§1.3 step 1) and structural features (§1.3 step 2, §1.1 active minutes)."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .transcript import EDIT_TOOLS, Session, is_real_prompt

GAP_CAP_SECONDS = 5 * 60
DEFAULT_PROJECT_DAYS = 14


@dataclass(frozen=True)
class Features:
    turns: int
    tool_calls: int
    real_prompts: int
    active_minutes: float
    max_edits_one_file: int
    retries_after_failure: int
    project_days: int

    def to_dict(self) -> dict:
        return asdict(self)


def tool_uses(session: Session) -> list[tuple[int, dict]]:
    return [(i, e.block) for i, e in enumerate(session.events) if e.block.get("type") == "tool_use"]


def tool_results(session: Session) -> dict[str, dict]:
    return {
        e.block.get("tool_use_id"): e.block
        for e in session.events
        if e.block.get("type") == "tool_result"
    }


def result_text(block: dict) -> str:
    c = block.get("content")
    if isinstance(c, list):
        c = " ".join(x.get("text", "") for x in c if isinstance(x, dict))
    return str(c or "")


def is_permission_denial(err: str) -> bool:
    return "user doesn't want" in err or "rejected" in err.lower()


def failures(session: Session) -> list[tuple[int, dict, str, tuple[int, dict] | None]]:
    """Failed tool calls (permission denials excluded) with the next call of the same tool, if any."""
    uses = tool_uses(session)
    results = tool_results(session)
    out = []
    for k, (i, b) in enumerate(uses):
        r = results.get(b.get("id"))
        if not r or not r.get("is_error"):
            continue
        err = result_text(r)
        if is_permission_denial(err):
            continue
        retry = next(((i2, b2) for i2, b2 in uses[k + 1:] if b2.get("name") == b.get("name")), None)
        out.append((i, b, err, retry))
    return out


def count_real_prompts(session: Session) -> int:
    return sum(1 for e in session.events if is_real_prompt(e))


def is_empty(session: Session) -> bool:
    """§1.3 step 1: zero tool calls and at most one real prompt."""
    return not tool_uses(session) and count_real_prompts(session) <= 1


def active_minutes(stamps) -> float:
    """§1.1: sum of gaps between consecutive events, each capped at 5 min."""
    ordered = sorted(stamps)
    total = sum(
        min((b - a).total_seconds(), GAP_CAP_SECONDS) for a, b in zip(ordered, ordered[1:])
    )
    return round(total / 60, 1)


def max_edits_one_file(session: Session) -> int:
    counts = Counter(
        (b.get("input") or {}).get("file_path") or (b.get("input") or {}).get("notebook_path")
        for _, b in tool_uses(session)
        if b.get("name") in EDIT_TOOLS
    )
    counts.pop(None, None)
    return max(counts.values(), default=0)


def project_days(session: Session, days: int = DEFAULT_PROJECT_DAYS, now: datetime | None = None) -> int:
    """Distinct local dates in the last `days` days on which the session's project dir has a main transcript."""
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    seen = set()
    for p in Path(session.path).parent.glob("*.jsonl"):
        mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
        if since <= mtime <= now:
            seen.add(mtime.astimezone().date())
    return len(seen)


def extract_features(session: Session, days: int = DEFAULT_PROJECT_DAYS, now: datetime | None = None) -> Features:
    return Features(
        turns=session.turns,
        tool_calls=len(tool_uses(session)),
        real_prompts=count_real_prompts(session),
        active_minutes=active_minutes(session.timestamps),
        max_edits_one_file=max_edits_one_file(session),
        retries_after_failure=sum(1 for *_, retry in failures(session) if retry),
        project_days=project_days(session, days, now),
    )
