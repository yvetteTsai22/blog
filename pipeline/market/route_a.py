"""Route A (spec §4.3): whitelisted phrase queries to HN Algolia and GitHub search.

Only a whitelist term is ever sent: a manual seed entry found inside a topic phrase (the
seed entry itself is sent, not the surrounding words), or a whole topic phrase that was
seen in at least two pulled feed items. The denylist always wins. GitHub runs only for a
watchlist `domain_repo`, scoped with `repo:`.
"""
from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass, field
from typing import Iterable, Sequence

from .denylist import Denylist
from .feeds import FeedItem
from .match import TopicText, phrase_seen_count
from .net import Net

FEED_SEEN_MIN = 2
NONE_REPO = "none"


@dataclass
class RouteAResult:
    ran: bool = False
    failed: bool = False
    off_watchlist_repo: str | None = None
    queries: list[str] = field(default_factory=list)
    hn_hits: int = 0
    github_thumbs: int = 0
    denied: int = 0
    feed_derived: list[str] = field(default_factory=list)


def whitelist_terms(topic: TopicText, seed: Iterable[str], items: Sequence[FeedItem], deny: Denylist):
    """Return (terms to query, denied count, feed-derived whitelist terms)."""
    seed_l = [s.lower().strip() for s in seed if s.strip()]
    terms, denied, derived = [], 0, []
    for phrase in topic.phrases:
        p = phrase.lower().strip()
        candidates = [s for s in seed_l if re.search(rf"\b{re.escape(s)}\b", p)]
        if not candidates and phrase_seen_count(p, items) >= FEED_SEEN_MIN:
            candidates = [p]
            derived.append(p)
        for term in candidates:
            if deny.blocks(term) or deny.blocks(p):
                denied += 1
            elif term not in terms:
                terms.append(term)
    return terms, denied, [d for d in derived if d in terms]


def hn_query(net: Net, term: str, since_ts: int) -> int:
    q = urllib.parse.urlencode({"query": f'"{term}"', "numericFilters": f"created_at_i>{since_ts}", "hitsPerPage": 0})
    return int(net.get_json(f"https://hn.algolia.com/api/v1/search?{q}", "query", "hn_phrase").get("nbHits", 0))


def github_query(net: Net, repo: str, term: str) -> int:
    """Sum of 👍 on open bug issues in `repo` matching the quoted term."""
    q = urllib.parse.urlencode({"q": f'repo:{repo} "{term}" is:issue is:open label:bug', "per_page": 50})
    data = net.get_json(f"https://api.github.com/search/issues?{q}", "query", "github_phrase")
    return sum(int((i.get("reactions") or {}).get("+1", 0)) for i in data.get("items", []))


def run(net: Net, topic: TopicText, seed, watchlist, items, deny: Denylist, since_ts: int, log=print) -> RouteAResult:
    res = RouteAResult()
    repo = (topic.domain_repo or NONE_REPO).strip()
    on_watchlist = repo.lower() in {w.lower() for w in watchlist}
    if repo.lower() != NONE_REPO and not on_watchlist:
        # Spec: off-watchlist repo => insufficient + local candidate log. Denied repos are dropped.
        res.off_watchlist_repo = None if deny.blocks(repo) else repo
        res.failed = True
    terms, res.denied, res.feed_derived = whitelist_terms(topic, seed, items, deny)
    if not terms:
        return res
    for term in terms:
        try:
            res.hn_hits += hn_query(net, term, since_ts)
            res.queries.append(f"hn:{term}")
            if on_watchlist:
                res.github_thumbs += github_query(net, repo, term)
                res.queries.append(f"github:{repo}:{term}")
            res.ran = True
        except Exception as exc:  # failed source => insufficient, never fatal
            res.failed = True
            log(f"market: route A query failed for a topic: {type(exc).__name__}")
    return res
