"""Weekly line: candidate `domain_repo`s seen outside the GitHub watchlist (spec §1.5, §4.3).

Shown once a week (default Monday). Repos matching the denylist never reach the candidate
log, so this line carries only public repo names.
"""
from __future__ import annotations

from datetime import timedelta

from market import config as market_config
from market import store

NAME = "market_candidates"
KIND = "global"
ORDER = 80


def lines(ctx):
    cfg = market_config.load()
    if ctx.today.weekday() != cfg.candidate_weekday:
        return []
    repos = store.candidates_since(ctx.state_dir, ctx.today - timedelta(days=7))
    return [f"watchlist 候選: {', '.join(repos)}"] if repos else []
