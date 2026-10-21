"""Drain the pending queue: sample, summarise, run steps, stage one note per session (spec §1.3)."""
from __future__ import annotations

import json
import re
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Mapping

from common import notion_schema as ns
from common import paths
from common.config import Config
from notes import Outbox, OutboxSink
from sampler import build_sample, enforce_cap, extract_features, is_empty, load_session, render, session_files
from summarize import build_prompt, load_post_options, parse_output
from summarize.llm import DEFAULT_MODEL, run_claude

from .discovery import discover
from .queue import read_queue, remove_ids

MAX_NOTES_PER_NIGHT = 60
QUEUE_WARN_THRESHOLD = 100
TOPIC_LOOKBACK_DAYS = 14
CYCLE_START_HOUR = 2
STATUS_FILE = "batch-status.json"
LOG_FILE = "batch.log"


@dataclass
class Context:
    state_dir: Path
    config: Config
    now: datetime
    model: str = DEFAULT_MODEL
    max_notes: int = MAX_NOTES_PER_NIGHT
    projects_dir: Path = Path("~/.claude/projects").expanduser()
    posts_dir: Path = paths.REPO_ROOT / "_posts"
    client_projects: tuple[str, ...] = ()
    denylist: tuple[str, ...] = ()
    llm: Callable[[str, str], str] | None = None
    only: tuple[str, ...] = ()
    log_lines: list[str] = field(default_factory=list)

    @property
    def cycle(self) -> str:
        """The 02:00-to-02:00 cycle this run belongs to, as the date it started."""
        local = self.now.astimezone()
        return (local - timedelta(hours=CYCLE_START_HOUR)).date().isoformat()

    def log(self, msg: str) -> None:
        line = f"{self.now.isoformat(timespec='seconds')} {msg}"
        self.log_lines.append(line)
        print(line, file=sys.stderr)


def context_from_config(config: Config, state_dir: Path | None = None, now: datetime | None = None) -> Context:
    get = config.get
    return Context(
        state_dir=state_dir or paths.state_dir(),
        config=config,
        now=now or datetime.now(timezone.utc),
        model=str(get("batch.model", DEFAULT_MODEL)),
        max_notes=int(get("batch.max_notes_per_night", MAX_NOTES_PER_NIGHT)),
        projects_dir=Path(str(get("batch.projects_dir", "~/.claude/projects"))).expanduser(),
        client_projects=tuple(get("batch.client_projects", ()) or ()),
        denylist=tuple(get("batch.denylist", ()) or ()),
    )


def is_client_project(project: str, client_projects) -> bool:
    p = project.lower()
    return any(c and c.lower() in p for c in client_projects)


def never_mention(ctx: Context, project: str) -> list[str]:
    terms = list(ctx.denylist)
    if is_client_project(project, ctx.client_projects):
        terms += [c for c in ctx.client_projects if c.lower() in project.lower()]
    return terms


def slugify(text: str, words: int = 6) -> str:
    parts = re.findall(r"[a-z0-9]+", text.lower())[:words]
    return "-".join(parts) or "topic"


def known_topics(ctx: Context, outbox: Outbox) -> set[str]:
    since = ctx.now - timedelta(days=TOPIC_LOOKBACK_DAYS)
    topics = set()
    for row in outbox.written().values():
        try:
            when = datetime.fromisoformat(row.get("written_at", ""))
        except ValueError:
            continue
        if when >= since and row.get("topic_of"):
            topics.add(row["topic_of"])
    topics.update(r["topic_of"] for r in outbox.pending() if r.get("topic_of"))
    return topics


def notes_this_cycle(ctx: Context, outbox: Outbox) -> int:
    written = sum(1 for r in outbox.written().values() if r.get("cycle") == ctx.cycle)
    staged = sum(1 for r in outbox.pending() if r.get("cycle") == ctx.cycle)
    return written + staged


def find_transcript(ctx: Context, session_id: str) -> Path | None:
    return next((p for p in session_files(str(ctx.projects_dir)) if p.stem == session_id), None)


def summarise_session(ctx: Context, session, topics: set[str]) -> dict:
    features = extract_features(session).to_dict()
    sample = render(session, enforce_cap(build_sample(session)))
    posts = load_post_options(ctx.posts_dir) if ctx.posts_dir.is_dir() else []
    deny = never_mention(ctx, session.project)
    prompt = build_prompt(sample, features, posts, topics, deny)
    reply = ctx.llm(prompt, ctx.model) if ctx.llm else run_claude(prompt, ctx.model).text
    summary = parse_output(reply, [p.slug for p in posts], topics, deny).to_dict()
    origin = ns.ORIGIN_CLIENT if is_client_project(session.project, ctx.client_projects) else summary["origin"]
    topic_of = summary["topic_of"]
    if topic_of == ns.TOPIC_NEW:
        topic_of = f"{slugify(summary['title'])}-{session.session_id[:6]}"
    return {
        "session_id": session.session_id,
        "cycle": ctx.cycle,
        "staged_at": ctx.now.isoformat(),
        "model": ctx.model,
        "origin": origin,
        "topic_of": topic_of,
        "summary": summary,
        "features": features,
        "extra_properties": {},
        "extra_body": [],
    }


def run_session_steps(ctx: Context, steps, session, record: dict) -> dict:
    for step in steps:
        try:
            updated = step.run(ctx, session, record)
        except Exception:  # a failing extension step never loses the note
            ctx.log(f"step {step.name} failed for {record['session_id']}: {traceback.format_exc(limit=2)}")
            continue
        if isinstance(updated, Mapping):
            record = dict(updated)
    return record


def write_status(ctx: Context, status: dict) -> None:
    ctx.state_dir.mkdir(parents=True, exist_ok=True)
    (ctx.state_dir / STATUS_FILE).write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    with (ctx.state_dir / LOG_FILE).open("a", encoding="utf-8") as fh:
        fh.write("".join(f"{l}\n" for l in ctx.log_lines))


def stage_queue(ctx: Context) -> dict:
    """Process the queue in order; stage notes to the outbox. No Notion I/O here."""
    queue_path = ctx.state_dir / paths.PENDING_QUEUE_FILE
    outbox = Outbox(ctx.state_dir)
    sink = OutboxSink(outbox)
    steps = discover()
    queue = read_queue(queue_path)
    status = {
        "cycle": ctx.cycle,
        "started_at": ctx.now.isoformat(),
        "queue_length": len(queue),
        "queue_warning": len(queue) > QUEUE_WARN_THRESHOLD,
        "staged": [], "already_written": [], "already_staged": [],
        "empty": [], "missing": [], "failed": [], "deferred_by_cap": 0,
    }
    topics = known_topics(ctx, outbox)
    used = notes_this_cycle(ctx, outbox)
    drop: list[str] = []
    for sid in queue:
        if ctx.only and sid not in ctx.only:
            continue
        if outbox.is_written(sid):
            status["already_written"].append(sid)
            drop.append(sid)
            continue
        if outbox.is_staged(sid):
            status["already_staged"].append(sid)
            continue
        if used >= ctx.max_notes:
            status["deferred_by_cap"] += 1
            continue
        path = find_transcript(ctx, sid)
        if path is None:
            ctx.log(f"no transcript for {sid}; dropped")
            status["missing"].append(sid)
            drop.append(sid)
            continue
        try:
            session = load_session(path)
            if is_empty(session):
                status["empty"].append(sid)
                drop.append(sid)
                continue
            record = summarise_session(ctx, session, topics)
            record = run_session_steps(ctx, steps["session"], session, record)
            sink.write(record)
        except Exception as exc:
            ctx.log(f"session {sid} failed, left in queue: {exc.__class__.__name__}: {str(exc)[:200]}")
            status["failed"].append(sid)
            continue
        topics.add(record["topic_of"])
        status["staged"].append(sid)
        used += 1
    remove_ids(queue_path, drop)

    for step in steps["nightly"]:
        try:
            step.run(ctx, status)
        except Exception:
            ctx.log(f"nightly step {step.name} failed: {traceback.format_exc(limit=2)}")
    status["queue_length_after"] = len(read_queue(queue_path))
    status["outbox_pending"] = sum(1 for _ in outbox.pending())
    write_status(ctx, status)
    return status


def commit_written(ctx: Context, session_id: str, page_id: str) -> dict:
    """Called after a confirmed Notion write: ledger it, drop outbox entry and queue line."""
    row = Outbox(ctx.state_dir).mark_written(session_id, page_id, ctx.now)
    remove_ids(ctx.state_dir / paths.PENDING_QUEUE_FILE, [session_id])
    return row
