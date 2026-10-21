"""CLI for the 21:00 run.

  uv run python -m daily run              rank, update Notion pool, run steps, send Telegram
  uv run python -m daily run --dry-run    print the message; no Telegram send, no Notion writes
  uv run python -m daily run --dry-run --scrub   same, with session content replaced by placeholders
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from common import paths
from common.config import load_config

from .notion import Notion, NotionError
from .runner import Context, run
from .telegram import TelegramError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="daily")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("run")
    p.add_argument("--dry-run", action="store_true", help="print only; no Telegram, no Notion writes")
    p.add_argument("--scrub", action="store_true", help="replace session content in the printed message")
    p.add_argument("--json", action="store_true", help="print the run summary as JSON after the message")
    args = parser.parse_args(argv)
    if args.scrub and not args.dry_run:
        parser.error("--scrub only makes sense with --dry-run")

    config = load_config()
    try:
        ctx = Context(
            config=config,
            state_dir=paths.state_dir(),
            now=datetime.now(timezone.utc),
            dry_run=args.dry_run,
            notion=Notion.from_config(config),
        )
        result = run(ctx, scrub=args.scrub)
    except (NotionError, TelegramError) as exc:
        print(f"daily: {exc}", file=sys.stderr)
        return 1
    print(result["message"])
    if args.json:
        print(json.dumps({k: v for k, v in result.items() if k != "message"}, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
