"""Global message line: how to resume the 21:00 drafting session.

Orca automation sessions close after the agent's first idle turn, so drafting resumes with
`claude --continue` in the drafting worktree (`blog-write` is the shell alias). Plain text:
the message is sent without parse_mode, so the command stays copyable as-is.
"""
from __future__ import annotations

KIND = "global"
ORDER = 1000  # after every other global provider

DEFAULT_DRAFTING_DIR = "~/orca/workspaces/blog/draft-blog"


def lines(ctx):
    drafting_dir = ctx.config.get("daily.drafting_dir") or DEFAULT_DRAFTING_DIR
    return [f"接續寫作：cd {drafting_dir} && claude --continue  (或 blog-write)"]
