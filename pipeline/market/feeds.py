"""Route B feed pulls (spec §4.1): HN Algolia, RSS/Atom, dev.to, Discourse, watchlist issues.

Each source returns `FeedItem`s from the lookback window. A failing source is reported in
`PullResult.failed` and skipped; it never raises out of `pull_all`.
"""
from __future__ import annotations

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Callable, Mapping

from .net import Net, SourceError

TAG_RE = re.compile(r"<[^>]+>")
TEXT_CLIP = 600


@dataclass(frozen=True)
class FeedItem:
    source: str
    id: str
    title: str
    text: str
    url: str
    created: datetime
    help: bool = False

    def passage(self) -> str:
        return f"{self.title}. {self.text}"[:TEXT_CLIP]


@dataclass
class PullResult:
    items: list[FeedItem] = field(default_factory=list)
    ok: list[str] = field(default_factory=list)
    failed: dict[str, str] = field(default_factory=dict)


def _clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", html.unescape(TAG_RE.sub(" ", text or ""))).strip()


def _parse_date(text: str | None) -> datetime | None:
    if not text:
        return None
    text = text.strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = parsedate_to_datetime(text)
        except (TypeError, ValueError):
            return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def hn(net: Net, feed: Mapping, since: datetime) -> list[FeedItem]:
    q = urllib.parse.urlencode({
        "tags": feed.get("tags", "front_page"),
        "numericFilters": f"created_at_i>{int(since.timestamp())}",
        "hitsPerPage": int(feed.get("limit", 200)),
    })
    data = net.get_json(f"https://hn.algolia.com/api/v1/search_by_date?{q}", "feed", feed["name"])
    return [
        FeedItem(feed["name"], str(h.get("objectID")), _clean(h.get("title") or h.get("story_title")),
                 _clean(h.get("story_text") or "")[:TEXT_CLIP],
                 f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                 _parse_date(h.get("created_at")) or since, bool(feed.get("help")))
        for h in data.get("hits", [])
    ]


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _child(el, *names) -> str:
    for c in el:
        if _local(c.tag) in names:
            if _local(c.tag) == "link" and c.get("href"):
                return c.get("href")
            return c.text or ""
    return ""


def parse_rss(text: str, name: str, help_: bool = False) -> list[FeedItem]:
    try:
        root = ET.fromstring(text.encode("utf-8"))
    except ET.ParseError:
        raise SourceError("invalid XML") from None
    out = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        link = _child(el, "link")
        created = _parse_date(_child(el, "pubDate", "published", "updated", "date"))
        if created is None:
            continue
        out.append(FeedItem(name, _child(el, "guid", "id") or link, _clean(_child(el, "title")),
                            _clean(_child(el, "description", "summary", "content"))[:TEXT_CLIP],
                            link, created, help_))
    return out


def rss(net: Net, feed: Mapping, since: datetime) -> list[FeedItem]:
    return parse_rss(net.get_text(feed["url"], "feed", feed["name"]), feed["name"], bool(feed.get("help")))


def devto(net: Net, feed: Mapping, since: datetime) -> list[FeedItem]:
    days = max(1, (datetime.now(timezone.utc) - since).days)
    out = []
    for tag in feed.get("tags") or ():
        q = urllib.parse.urlencode({"tag": tag, "top": days, "per_page": 100})
        for a in net.get_json(f"https://dev.to/api/articles?{q}", "feed", feed["name"]):
            out.append(FeedItem(feed["name"], str(a.get("id")), _clean(a.get("title")),
                                _clean(a.get("description")), a.get("url") or "",
                                _parse_date(a.get("published_at")) or since))
    return out


def discourse(net: Net, feed: Mapping, since: datetime) -> list[FeedItem]:
    data = net.get_json(feed["url"], "feed", feed["name"])
    base = feed["url"].split("/c/", 1)[0]
    return [
        FeedItem(feed["name"], str(t.get("id")), _clean(t.get("title")), _clean(t.get("excerpt")),
                 f"{base}/t/{t.get('slug')}/{t.get('id')}",
                 _parse_date(t.get("created_at")) or since, bool(feed.get("help", True)))
        for t in (data.get("topic_list") or {}).get("topics", [])
    ]


def github_issues(net: Net, feed: Mapping, since: datetime, watchlist=()) -> list[FeedItem]:
    out = []
    for repo in watchlist:
        q = urllib.parse.urlencode({"state": "all", "since": since.strftime("%Y-%m-%dT00:00:00Z"),
                                    "per_page": 100, "sort": "created"})
        for i in net.get_json(f"https://api.github.com/repos/{repo}/issues?{q}", "feed", feed["name"]):
            if "pull_request" in i:
                continue
            out.append(FeedItem(feed["name"], f"{repo}#{i.get('number')}", _clean(i.get("title")),
                                _clean(i.get("body"))[:TEXT_CLIP], i.get("html_url") or "",
                                _parse_date(i.get("created_at")) or since))
    return out


PULLERS: dict[str, Callable] = {"hn": hn, "rss": rss, "devto": devto, "discourse": discourse}


def pull_all(net: Net, feeds, watchlist, now: datetime, lookback_days: int, log: Callable = print) -> PullResult:
    since = (now - timedelta(days=lookback_days)).replace(hour=0, minute=0, second=0, microsecond=0)
    result = PullResult()
    seen = set()
    for feed in feeds:
        name, kind = feed.get("name", "?"), feed.get("type")
        try:
            if kind == "github_issues":
                items = github_issues(net, feed, since, watchlist)
            elif kind in PULLERS:
                items = PULLERS[kind](net, feed, since)
            else:
                raise SourceError(f"unknown feed type {kind!r}")
        except Exception as exc:  # a failed source is skipped, never fatal
            result.failed[name] = f"{type(exc).__name__}: {exc}"[:200]
            log(f"market: feed {name} failed: {result.failed[name]}")
            continue
        result.ok.append(name)
        for it in items:
            key = (it.source, it.id)
            if it.created >= since and it.title and key not in seen:
                seen.add(key)
                result.items.append(it)
    return result
