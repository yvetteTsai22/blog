"""Verify the pipeline's local prerequisites (spec §7 items 1-4, 9).

Prints one PASS/FAIL line per check and never prints secret values.

    cd pipeline && uv run python -m setup.check_prereqs [--live]

`--live` also sends one trivial prompt through headless `claude -p` (haiku).
The Notion schema (§7 item 8) is checked through Notion MCP, not here.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from common import paths
from common.config import Config, ConfigError, load_config

POOL_WINDOW_DAYS = 14
RETENTION_MARGIN_DAYS = 7
MIN_CLEANUP_PERIOD_DAYS = POOL_WINDOW_DAYS + RETENTION_MARGIN_DAYS

CLAUDE_SETTINGS = Path("~/.claude/settings.json").expanduser()
BLOG_CHECKOUT = Path("~/projects/blog").expanduser()
JEV_KEY = "JEV_API"
TELEGRAM_KEYS = ("telegram.bot_token", "telegram.chat_id")
GITIGNORED_FILES = (
    paths.ENV_FILE,
    paths.PIPELINE_LOCAL_FILE,
    paths.MARKET_SIGNALS_LOCAL_FILE,
    "pipeline/.venv/",
)
CLI_TIMEOUT_S = 30
LIVE_TIMEOUT_S = 180


@dataclass(frozen=True)
class Result:
    name: str
    ok: bool
    detail: str


Runner = Callable[..., subprocess.CompletedProcess]


def _run(cmd: list[str], runner: Runner, timeout: int = CLI_TIMEOUT_S, **kw) -> subprocess.CompletedProcess:
    return runner(cmd, capture_output=True, text=True, timeout=timeout, **kw)


def check_cleanup_period(settings_path: Path = CLAUDE_SETTINGS) -> Result:
    name = "claude transcript retention"
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return Result(name, False, f"cannot read {settings_path.name}: {exc.__class__.__name__}")
    days = settings.get("cleanupPeriodDays")
    if not isinstance(days, int):
        return Result(name, False, f"cleanupPeriodDays not set (need >= {MIN_CLEANUP_PERIOD_DAYS})")
    ok = days >= MIN_CLEANUP_PERIOD_DAYS
    return Result(name, ok, f"cleanupPeriodDays={days} (need >= {MIN_CLEANUP_PERIOD_DAYS})")


def check_orca_repo(runner: Runner = subprocess.run, checkout: Path = BLOG_CHECKOUT) -> Result:
    name = "orca repo registered"
    try:
        proc = _run(["orca", "repo", "list"], runner)
    except (OSError, subprocess.SubprocessError) as exc:
        return Result(name, False, f"orca repo list failed: {exc.__class__.__name__}")
    if proc.returncode != 0:
        return Result(name, False, f"orca repo list exit {proc.returncode}")
    target = str(checkout.resolve())
    found = any(line.split()[-1:] == [target] for line in proc.stdout.splitlines())
    return Result(name, found, target if found else f"{target} not in orca repo list")


def check_telegram(config: Config) -> Result:
    missing = [k for k in TELEGRAM_KEYS if not config.has(k)]
    if config.local_path is None:
        return Result("telegram credentials", False, f"{paths.PIPELINE_LOCAL_FILE} not found")
    if missing:
        return Result("telegram credentials", False, f"empty in {paths.PIPELINE_LOCAL_FILE}: {', '.join(missing)}")
    return Result("telegram credentials", True, f"{', '.join(TELEGRAM_KEYS)} set")


def check_jev_key(config: Config) -> Result:
    if config.env_path is None:
        return Result("JEV_API key", False, f"{paths.ENV_FILE} not found")
    ok = config.has(JEV_KEY)
    return Result("JEV_API key", ok, f"{JEV_KEY} {'present' if ok else 'missing or empty'} in {config.env_path}")


def check_env_untracked(config: Config, runner: Runner = subprocess.run) -> Result:
    name = ".env untracked"
    env_path = config.env_path
    if env_path is None:
        return Result(name, False, f"{paths.ENV_FILE} not found")
    try:
        proc = _run(["git", "ls-files", "--error-unmatch", env_path.name], runner, cwd=env_path.parent)
    except (OSError, subprocess.SubprocessError) as exc:
        return Result(name, False, f"git ls-files failed: {exc.__class__.__name__}")
    tracked = proc.returncode == 0
    return Result(name, not tracked, "tracked by git!" if tracked else "not tracked")


def check_gitignored(repo_root: Path = paths.REPO_ROOT, runner: Runner = subprocess.run) -> Result:
    name = "local files gitignored"
    try:
        proc = _run(["git", "check-ignore", "--no-index", *GITIGNORED_FILES], runner, cwd=repo_root)
    except (OSError, subprocess.SubprocessError) as exc:
        return Result(name, False, f"git check-ignore failed: {exc.__class__.__name__}")
    ignored = {line.strip() for line in proc.stdout.splitlines()}
    missing = [f for f in GITIGNORED_FILES if f not in ignored]
    return Result(name, not missing, "all ignored" if not missing else f"not ignored: {', '.join(missing)}")


def check_claude_cli(runner: Runner = subprocess.run, live: bool = False) -> Result:
    name = "headless claude -p"
    try:
        if not live:
            proc = _run(["claude", "--version"], runner)
            ok = proc.returncode == 0
            return Result(name, ok, (proc.stdout.strip() or "no version") + " (use --live for a prompt test)")
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        proc = _run(
            ["claude", "-p", "--model", "haiku", "--output-format", "json", "reply OK"],
            runner,
            timeout=LIVE_TIMEOUT_S,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return Result(name, False, f"claude failed: {exc.__class__.__name__}")
    if proc.returncode != 0:
        return Result(name, False, f"exit {proc.returncode}")
    try:
        reply = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return Result(name, False, "non-JSON output")
    ok = not reply.get("is_error") and "OK" in str(reply.get("result", ""))
    return Result(name, ok, "haiku replied OK on subscription login" if ok else "unexpected reply")


def run_checks(live: bool = False) -> list[Result]:
    try:
        config = load_config()
    except ConfigError as exc:
        return [Result("local config", False, str(exc))]
    return [
        check_cleanup_period(),
        check_orca_repo(),
        check_telegram(config),
        check_jev_key(config),
        check_env_untracked(config),
        check_gitignored(),
        check_claude_cli(live=live),
    ]


def format_result(result: Result) -> str:
    return f"{'PASS' if result.ok else 'FAIL'}  {result.name}: {result.detail}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--live", action="store_true", help="send one haiku prompt via claude -p")
    args = parser.parse_args(argv)
    results = run_checks(live=args.live)
    for result in results:
        print(format_result(result))
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
