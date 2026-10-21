"""Filesystem locations shared by every pipeline step.

Local state lives outside the repo so worktrees never see it:
``${BLOG_PIPELINE_STATE_DIR:-~/.local/state/blog-pipeline}/``.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

STATE_DIR_ENV = "BLOG_PIPELINE_STATE_DIR"
DEFAULT_STATE_DIR = Path("~/.local/state/blog-pipeline")

PENDING_QUEUE_FILE = "pending-queue.txt"

ENV_FILE = ".env"
PIPELINE_LOCAL_FILE = "pipeline.local.yml"
MARKET_SIGNALS_LOCAL_FILE = "market-signals.local.yml"

PIPELINE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PIPELINE_DIR.parent


def state_dir(environ: dict[str, str] | None = None) -> Path:
    """Return the local state dir; not created here."""
    env = os.environ if environ is None else environ
    raw = env.get(STATE_DIR_ENV) or str(DEFAULT_STATE_DIR)
    return Path(raw).expanduser()


def pending_queue_path(environ: dict[str, str] | None = None) -> Path:
    """One sessionId per line, appended by the SessionEnd hook."""
    return state_dir(environ) / PENDING_QUEUE_FILE


def main_checkout_root(repo_root: Path = REPO_ROOT) -> Path:
    """Return the main checkout of this repo (differs from repo_root in a git worktree).

    Falls back to repo_root when git is unavailable.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return repo_root
    return Path(out).parent


def local_file_candidates(name: str, repo_root: Path = REPO_ROOT) -> list[Path]:
    """Where a gitignored local file may live: this worktree first, then the main checkout."""
    roots = [repo_root]
    main = main_checkout_root(repo_root)
    if main.resolve() != repo_root.resolve():
        roots.append(main)
    return [root / name for root in roots]


def find_local_file(name: str, repo_root: Path = REPO_ROOT) -> Path | None:
    """Return the first existing candidate for a local file, or None."""
    return next((p for p in local_file_candidates(name, repo_root) if p.is_file()), None)
