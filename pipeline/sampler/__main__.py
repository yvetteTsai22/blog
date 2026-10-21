"""CLI: python -m sampler <session.jsonl|sessionId>... [--stats] [--cap N] [--days N] [--projects-dir DIR]

Prints the capped sample (markdown) or, with --stats, one JSON line of structural features and sizes
per session. --scan-days N samples every main transcript modified in the last N days (stats only)."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .features import DEFAULT_PROJECT_DAYS, extract_features, is_empty
from .sample import DEFAULT_CAP, build_sample, enforce_cap, render, total_tokens
from .transcript import load_session, session_files

PROJECTS_DIR = "~/.claude/projects"


def resolve(arg: str, projects_dir: str) -> Path:
    p = Path(arg).expanduser()
    if p.exists():
        return p
    hits = [f for f in session_files(projects_dir) if f.stem == arg]
    if not hits:
        raise FileNotFoundError(f"no transcript for session {arg!r} under {projects_dir}")
    return hits[0]


def stats(path: Path, cap: int, days: int) -> dict:
    s = load_session(path)
    items = build_sample(s)
    capped = enforce_cap(items, cap)
    return {
        "session_id": s.session_id,
        "empty": is_empty(s),
        **extract_features(s, days).to_dict(),
        "raw_tok": total_tokens(items),
        "capped_tok": total_tokens(capped),
        "dropped": len(items) - len(capped),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sampler")
    ap.add_argument("sessions", nargs="*", help="transcript path or sessionId")
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--cap", type=int, default=DEFAULT_CAP)
    ap.add_argument("--days", type=int, default=DEFAULT_PROJECT_DAYS, help="window for project_days")
    ap.add_argument("--projects-dir", default=PROJECTS_DIR)
    ap.add_argument("--scan-days", type=int, help="stats for all main transcripts modified in last N days")
    a = ap.parse_args(argv)

    if a.scan_days is not None:
        cutoff = time.time() - a.scan_days * 86400
        paths = [p for p in session_files(a.projects_dir) if p.stat().st_mtime >= cutoff]
    else:
        try:
            paths = [resolve(x, a.projects_dir) for x in a.sessions]
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
    if not paths:
        ap.error("no sessions given")

    for path in paths:
        if a.stats or a.scan_days is not None:
            print(json.dumps(stats(path, a.cap, a.days), ensure_ascii=False))
            continue
        s = load_session(path)
        if is_empty(s):
            print(f"# {s.session_id}: empty (0 tool calls, ≤1 real prompt)")
            continue
        print(render(s, enforce_cap(build_sample(s), a.cap)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
