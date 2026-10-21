"""The 21:00 run (spec §1.4 steps 1, 2, 4): rank, update the pool, run extra steps, send. No LLM."""
from __future__ import annotations

import json
import os
import sys
import traceback
from dataclasses import dataclass, field, replace
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from batch.queue import read_queue
from common import notion_schema as ns
from common import paths
from common.config import Config

from . import batch_status, message, pool, ranking, telegram
from .discovery import discover_lines, discover_steps
from .notes import Note, from_page, parse_body, with_body
from .notion import Notion, agent_session_filter, writing_filter

DEFAULT_TZ = "Europe/London"
DAILY_DIR = "daily"
BODY_CACHE = "body-cache.json"
LAST_RUN = "last-run.json"
LOG_FILE = "daily.log"
SCRUBBED = "[scrubbed]"


@dataclass
class Context:
    """Shared state for the run, extra steps and line providers (see README)."""

    config: Config
    state_dir: Path
    now: datetime
    dry_run: bool = False
    notion: Notion | None = None
    notes: list[Note] = field(default_factory=list)      # every recent agent-session note
    pool: list[Note] = field(default_factory=list)       # eligible notes, with body fields
    topics: list[ranking.Topic] = field(default_factory=list)
    listed: list[ranking.Topic] = field(default_factory=list)
    others: list[ranking.Topic] = field(default_factory=list)
    updates: list[pool.PoolUpdate] = field(default_factory=list)
    results: dict[str, Any] = field(default_factory=dict)  # free slot for steps -> line providers
    log_lines: list[str] = field(default_factory=list)

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.config.get("daily.timezone") or DEFAULT_TZ)

    @property
    def today(self) -> date:
        return self.now.astimezone(self.tz).date()

    @property
    def daily_dir(self) -> Path:
        return self.state_dir / DAILY_DIR

    def log(self, msg: str) -> None:
        line = f"{datetime.now().astimezone().isoformat(timespec='seconds')} {msg}"
        self.log_lines.append(line)
        print(line, file=sys.stderr)


def _load_cache(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    os.replace(tmp, path)


def load_notes(ctx: Context) -> None:
    since = (ctx.today - timedelta(days=ranking.POOL_DAYS + 1)).isoformat()
    ctx.notes = [from_page(p) for p in ctx.notion.query(agent_session_filter(since))]
    eligible = ranking.eligible(ctx.notes, ctx.today, ctx.tz)
    cache_path = ctx.daily_dir / BODY_CACHE
    cache = _load_cache(cache_path)
    filled = []
    for note in eligible:
        if note.page_id not in cache:
            cache[note.page_id] = parse_body(ctx.notion.page_text(note.page_id))
        filled.append(with_body(note, cache[note.page_id]))
    _save_json(cache_path, cache)
    ctx.pool = filled
    ctx.log(f"notes={len(ctx.notes)} eligible={len(ctx.pool)}")


def rank(ctx: Context) -> None:
    ctx.topics = ranking.rank_topics(ctx.pool)
    ctx.listed, ctx.others = ranking.split(ctx.topics)
    ctx.updates = pool.plan_updates(ctx.listed, ctx.notes, ctx.today)
    ctx.log(f"topics={len(ctx.topics)} listed={len(ctx.listed)} updates={len(ctx.updates)}")


def apply_updates(ctx: Context) -> list[str]:
    if ctx.dry_run:
        return []
    done = []
    for u in ctx.updates:
        ctx.notion.update_page(u.page_id, u.properties())
        done.append(u.page_id)
    return done


def run_steps(ctx: Context, steps=None) -> None:
    for step in steps if steps is not None else discover_steps():
        try:
            step.fn(ctx)
        except Exception:  # an extra step never fails the run
            ctx.log(f"step {step.name} failed:\n{traceback.format_exc(limit=3)}")


def writing_rows(ctx: Context) -> list[dict]:
    rows = []
    for page in ctx.notion.query(writing_filter()):
        n = from_page(page)
        rows.append({
            "title": n.title,
            "days": (ctx.today - n.created.astimezone(ctx.tz).date()).days,
            "draft_path": n.props.get(ns.DRAFT_PATH) or "",
        })
    return rows


def batch_lines(ctx: Context, fetch: Callable = batch_status.fetch) -> list[str]:
    queue_length = len(read_queue(paths.pending_queue_path()))
    fetched = fetch()
    if fetched is None:
        return ["batch status unavailable (orca automations runs failed)", f"queue: {queue_length}"]
    names = tuple(ctx.config.get("daily.batch_automation_names") or batch_status.DEFAULT_NAME_MATCH)
    runs = batch_status.last_night(batch_status.parse_runs(*fetched), ctx.now, names)
    return batch_status.status_lines(runs, queue_length, ctx.tz)


def scrub_topic(topic: ranking.Topic) -> ranking.Topic:
    """Replace session content with placeholders, for showing a dry run to a reviewer."""
    def s(n: Note) -> Note:
        return replace(
            n, title=SCRUBBED, lesson=SCRUBBED, privacy_reason=SCRUBBED, session_id=SCRUBBED,
            dup_of=SCRUBBED if n.dup_of not in ("", ns.DUP_OF_NONE) else n.dup_of,
            reader_questions=tuple({"kind": q["kind"], "question": SCRUBBED} for q in n.reader_questions),
            link=SCRUBBED if n.link else "",
        )
    notes = tuple(s(n) for n in topic.notes)
    return replace(topic, key=SCRUBBED, notes=notes, best=notes[0])


def build_message(ctx: Context, writing: list[dict], batch: list[str], scrub: bool = False) -> str:
    providers = discover_lines()
    listed = [scrub_topic(t) for t in ctx.listed] if scrub else ctx.listed
    others = [scrub_topic(t) for t in ctx.others] if scrub else ctx.others
    if scrub:
        writing = [{**w, "title": SCRUBBED, "draft_path": ""} for w in writing]

    def safe(name, fn):
        def call(*args):
            try:
                return list(fn(ctx, *args) or [])
            except Exception:
                ctx.log(f"line provider {name} failed:\n{traceback.format_exc(limit=3)}")
                return []
        return call

    header = f"📝 Blog topics {ctx.today.isoformat()}" + (" (dry run)" if ctx.dry_run else "")
    return message.render(
        header, batch, listed, others, writing,
        topic_providers=[safe(p.name, p.fn) for p in providers["topic"]],
        global_providers=[safe(p.name, p.fn) for p in providers["global"]],
    )


def run(ctx: Context, scrub: bool = False) -> dict:
    load_notes(ctx)
    rank(ctx)
    written = apply_updates(ctx)
    run_steps(ctx)
    text = build_message(ctx, writing_rows(ctx), batch_lines(ctx), scrub=scrub)
    sent = [] if ctx.dry_run else telegram.send(ctx.config, text)
    summary = {
        "at": ctx.now.isoformat(),
        "dry_run": ctx.dry_run,
        "listed": [{"key": t.key, "score": round(t.score, 4), "pages": [n.page_id for n in t.notes]} for t in ctx.listed],
        "others": [t.key for t in ctx.others],
        "updates": [u.__dict__ for u in ctx.updates],
        "notion_written": written,
        "telegram_message_ids": sent,
    }
    if not ctx.dry_run:
        _save_json(ctx.daily_dir / LAST_RUN, summary)
        with (ctx.daily_dir / LOG_FILE).open("a", encoding="utf-8") as fh:
            fh.write("\n".join(ctx.log_lines) + "\n")
    return {"message": text, **summary}
