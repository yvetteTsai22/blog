"""CLI for the nightly batch.

  uv run python -m batch stage [--only SID ...]   sample + summarise + stage notes (no Notion I/O)
  uv run python -m batch pending                  staged notes as JSON for the writer agent
  uv run python -m batch commit SID --page-id ID  record a confirmed Notion write; clears queue/outbox
  uv run python -m batch write-notes              one headless agent pass that writes all staged notes via MCP
  uv run python -m batch run                      stage, then write-notes
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from common import paths
from common.config import load_config
from notes import Outbox

from .runner import commit_written, context_from_config, stage_queue

PROMPT_FILE = Path(__file__).with_name("write_notes_prompt.md")
WRITER_TOOLS = (
    "mcp__notion-personal__notion-query-data-sources",
    "mcp__notion-personal__notion-create-pages",
    "Bash(uv run python -m batch pending)",
    "Bash(uv run python -m batch commit:*)",
)
DEFAULT_WRITER_MODEL = "haiku"
WRITER_TIMEOUT = 1800


def cmd_pending(ctx) -> int:
    rows = [
        {"session_id": r["session_id"], **r["notion"]}
        for r in Outbox(ctx.state_dir).pending()
    ]
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0


def cmd_write_notes(ctx) -> int:
    """One agent pass per batch (not per note), with only the tools the prompt needs."""
    if not any(True for _ in Outbox(ctx.state_dir).pending()):
        print("nothing staged", file=sys.stderr)
        return 0
    model = str(ctx.config.get("batch.writer_model", DEFAULT_WRITER_MODEL))
    cmd = ["claude", "-p", "--model", model, "--no-session-persistence",
           "--allowedTools", *WRITER_TOOLS]
    proc = subprocess.run(cmd, input=PROMPT_FILE.read_text(encoding="utf-8"), text=True,
                          cwd=paths.PIPELINE_DIR, timeout=WRITER_TIMEOUT)
    remaining = sum(1 for _ in Outbox(ctx.state_dir).pending())
    print(f"writer exit {proc.returncode}; {remaining} staged notes left", file=sys.stderr)
    return proc.returncode or (1 if remaining else 0)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="batch")
    sub = ap.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("stage")
    st.add_argument("--only", nargs="+", default=())
    st.add_argument("--max-notes", type=int)
    sub.add_parser("pending")
    cm = sub.add_parser("commit")
    cm.add_argument("session_id")
    cm.add_argument("--page-id", required=True)
    sub.add_parser("write-notes")
    rn = sub.add_parser("run")
    rn.add_argument("--only", nargs="+", default=())
    a = ap.parse_args(argv)

    ctx = context_from_config(load_config())
    if getattr(a, "only", None):
        ctx.only = tuple(a.only)
    if getattr(a, "max_notes", None):
        ctx.max_notes = a.max_notes

    if a.cmd == "pending":
        return cmd_pending(ctx)
    if a.cmd == "commit":
        print(json.dumps(commit_written(ctx, a.session_id, a.page_id)))
        return 0
    if a.cmd == "write-notes":
        return cmd_write_notes(ctx)
    status = stage_queue(ctx)
    print(json.dumps({k: v for k, v in status.items()}, ensure_ascii=False))
    if a.cmd == "run":
        return cmd_write_notes(ctx)
    return 1 if status["failed"] else 0


if __name__ == "__main__":
    sys.exit(main())
