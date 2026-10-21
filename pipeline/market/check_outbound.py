"""Audit the outbound log: every route A query must be a whitelist term, GitHub only on the watchlist.

  uv run python -m market.check_outbound [--day YYYY-MM-DD]

Feed pulls (`kind=feed`) must hit a configured feed host. Prints counts and violations
by log line number only (never the URL: a violating query could hold a denied term). Exit 1 on
any violation.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
from datetime import date
from pathlib import Path

from common import paths

from . import config as market_config
from . import store

FEED_HOSTS_BUILTIN = {"hn.algolia.com", "dev.to", "api.github.com"}


def _feed_hosts(cfg) -> set[str]:
    hosts = set(FEED_HOSTS_BUILTIN)
    for f in cfg.feeds:
        if f.get("url"):
            hosts.add(urllib.parse.urlparse(f["url"]).hostname or "")
    return hosts


def _query_term(url: str) -> tuple[str, str | None, str]:
    """(service, repo or None, term) for a route A URL."""
    u = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(u.query)
    if u.hostname == "hn.algolia.com":
        return "hn", None, qs.get("query", [""])[0].strip('"').lower()
    q = qs.get("q", [""])[0]
    repo = q.split("repo:", 1)[1].split()[0] if "repo:" in q else None
    term = q.split('"')[1].lower() if q.count('"') >= 2 else ""
    return "github", repo, term


def check(rows, whitelist: set[str], watchlist: set[str], feed_hosts: set[str]) -> list[str]:
    bad = []
    for n, r in rows:
        url = r.get("url", "")
        if r.get("kind") == "feed":
            if urllib.parse.urlparse(url).hostname not in feed_hosts:
                bad.append(f"feed host not configured (line {n})")
            elif "api.github.com/repos/" in url and url.split("/repos/", 1)[1].split("/issues")[0].lower() not in watchlist:
                bad.append(f"issues pull outside watchlist (line {n})")
            continue
        service, repo, term = _query_term(url)
        if term not in whitelist:
            bad.append(f"{service} term not whitelisted (line {n})")
        if service == "github" and (repo or "").lower() not in watchlist:
            bad.append(f"github repo not on watchlist (line {n})")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="market.check_outbound")
    ap.add_argument("--day", default=date.today().isoformat())
    a = ap.parse_args(argv)
    state = paths.state_dir()
    cfg = market_config.load()
    rows = [(n, r) for n, r in enumerate(store.read_jsonl(store.market_dir(state) / "outbound.jsonl"), 1) if r.get("at", "").startswith(a.day)]
    wl_file = store.market_dir(state) / "whitelist" / f"{a.day}.json"
    whitelist = set(json.loads(wl_file.read_text())) if wl_file.is_file() else {w.lower() for w in cfg.whitelist}
    bad = check(rows, whitelist, {w.lower() for w in cfg.watchlist}, _feed_hosts(cfg))
    feeds = sum(1 for _, r in rows if r.get("kind") == "feed")
    print(f"outbound {a.day}: {len(rows)} requests ({feeds} feed pulls, {len(rows) - feeds} phrase queries); "
          f"{len(bad)} outside whitelist/watchlist")
    for line in bad:
        print("  VIOLATION", line)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
