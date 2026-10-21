"""CLI for the 21:00 drafting session (spec §1.4 steps 5–6, §1.6).

  uv run python -m drafting open --repo <draft-blog worktree>
      run the 21:00 daily run (TSA-65), close the previous drafting session if idle,
      and print the opening context for the new session
  ... open --dry-run [--scrub]   daily run in dry-run (no Telegram, no Notion writes), no close;
                                 --scrub replaces titles, links and paths with placeholders
  uv run python -m drafting close-previous --repo <worktree> [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import notion_schema as ns
from common import paths
from common.config import load_config
from daily.notes import from_page
from daily.notion import Notion, NotionError
from daily.runner import Context, run as daily_run
from daily.telegram import TelegramError

from . import context, sessions

INSTRUCTIONS = Path(__file__).with_name("session.md")
OPENING_DIR = "drafting"


def articles_filter() -> dict:
    return {
        "or": [
            {"property": ns.BLOG_STATUS, "select": {"equals": ns.BLOG_WRITING}},
            {"property": ns.NOTE_PENDING, "checkbox": {"equals": True}},
        ]
    }


def load_articles(ctx: Context) -> list[context.Article]:
    out = []
    for page in ctx.notion.query(articles_filter()):
        n = from_page(page)
        out.append(context.Article(
            title=n.title,
            days=(ctx.today - n.created.astimezone(ctx.tz).date()).days,
            draft_path=n.props.get(ns.DRAFT_PATH) or "",
            slug=n.props.get(ns.SLUG) or "",
            note_pending=bool(n.props.get(ns.NOTE_PENDING)),
            writing=n.props.get(ns.BLOG_STATUS) == ns.BLOG_WRITING,
        ))
    return out


def listed_notes(ctx: Context) -> list[context.LitNote]:
    return [
        context.LitNote(title=n.title, url=n.url, origin=n.origin, topic=t.best.title or t.key)
        for t in ctx.listed for n in t.notes
    ]


def close_lines(repo: Path, skip: bool) -> list[str]:
    if skip:
        return sessions.describe(sessions.close_previous(str(repo), dry_run=True), dry_run=True)
    try:
        return sessions.describe(sessions.close_previous(str(repo)), dry_run=False)
    except Exception as exc:  # closing is best-effort; the new session still opens
        return [f"previous drafting session: not checked ({exc.__class__.__name__})"]


def open_session(repo: Path, dry_run: bool, scrub: bool) -> str:
    config = load_config()
    ctx = Context(
        config=config, state_dir=paths.state_dir(), now=datetime.now(timezone.utc),
        dry_run=dry_run, notion=Notion.from_config(config),
    )
    result = daily_run(ctx, scrub=scrub)
    articles = load_articles(ctx)
    text = context.render(
        articles=articles,
        message=result["message"],
        notes=listed_notes(ctx),
        repo=repo,
        samples=context.voice_samples(repo),
        changes=context.parse_changes(context.git_status(repo), articles),
        instructions=INSTRUCTIONS.read_text(encoding="utf-8"),
        close_lines=close_lines(repo, skip=dry_run),
        scrub=scrub,
    )
    if not dry_run:
        out = ctx.state_dir / OPENING_DIR / f"opening-{ctx.today.isoformat()}.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="drafting")
    sub = parser.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("open")
    o.add_argument("--repo", type=Path, required=True, help="the draft-blog worktree")
    o.add_argument("--dry-run", action="store_true")
    o.add_argument("--scrub", action="store_true")
    c = sub.add_parser("close-previous")
    c.add_argument("--repo", type=Path, required=True)
    c.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo.expanduser().resolve()

    if args.cmd == "close-previous":
        print("\n".join(sessions.describe(sessions.close_previous(str(repo), args.dry_run), args.dry_run)))
        return 0
    if args.scrub and not args.dry_run:
        parser.error("--scrub only makes sense with --dry-run")
    try:
        print(open_session(repo, args.dry_run, args.scrub), end="")
    except (NotionError, TelegramError) as exc:
        print(f"drafting: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
