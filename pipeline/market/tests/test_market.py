"""Market signals tests. All fixtures are synthetic; no network, no real embedding model."""
from __future__ import annotations

import json
import subprocess
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from common import notion_schema as ns
from market import check_outbound, denylist, route_a, store
from market.config import from_mapping
from market.feeds import FeedItem, parse_rss, pull_all
from market.match import TopicText, match_topic, percentile
from market.net import Net, SourceError
from market.pipeline import Inputs, run_nightly
from notes import Outbox

NOW = datetime(2026, 10, 20, 18, 0, tzinfo=timezone.utc)
CYCLE = "2026-10-20"


# --- fakes ------------------------------------------------------------------

class KeywordEmbedder:
    """Bag-of-keywords vectors: texts sharing a keyword are similar (cosine 1 on one shared word)."""
    VOCAB = ("worktree", "hooks", "electron", "jekyll", "cooking")

    def _vec(self, t):
        v = np.array([1.0 if w in t.lower() else 0.0 for w in self.VOCAB] + [0.01])
        return v / np.linalg.norm(v)

    def queries(self, texts):
        return np.array([self._vec(t) for t in texts])

    passages = queries


def hn_hit(i, title, days_ago=1):
    return {"objectID": str(i), "title": title, "created_at": (NOW - timedelta(days=days_ago)).isoformat()}


class FakeWeb:
    """Routes URLs to canned JSON; records every URL. `fail` hosts raise SourceError."""

    def __init__(self, fail=()):
        self.urls, self.fail = [], set(fail)

    def __call__(self, url, headers, timeout):
        assert timeout > 0
        self.urls.append(url)
        host = urllib.parse.urlparse(url).hostname
        if host in self.fail:
            raise SourceError("boom")
        if "search_by_date" in url and "ask_hn" in url:
            body = {"hits": [hn_hit(10, "Ask HN: git worktree breaks my agent"),
                             hn_hit(11, "Ask HN: git worktree and hooks")]}
        elif "search_by_date" in url:
            body = {"hits": [hn_hit(1, "Electron app memory"), hn_hit(2, "Cooking with git worktree"),
                             hn_hit(3, "Old worktree post", days_ago=40)]}
        elif "/search?" in url and host == "hn.algolia.com":
            body = {"nbHits": 7}
        elif "search/issues" in url:
            body = {"items": [{"reactions": {"+1": 4}}, {"reactions": {"+1": 1}}]}
        else:
            body = {}
        return json.dumps(body).encode()


def make_net(tmp_path, web, token="t0k"):
    return Net(tmp_path, timeout_s=5, keychain_service="svc", fetch=web,
               token_reader=lambda s: token, sleep=lambda s: None)


HN_FEEDS = ({"name": "hn_front_page", "type": "hn", "tags": "front_page"},
            {"name": "hn_ask_hn", "type": "hn", "tags": "ask_hn", "help": True})


def stage_note(state, sid, topic, phrases, repo="none", questions=("How do worktrees work?",)):
    Outbox(state).stage({
        "session_id": sid, "cycle": CYCLE, "origin": "personal", "topic_of": topic,
        "summary": {"title": "t", "p_trap": 0.1, "p_insight": 0.7, "p_pattern": 0.2, "dup_of": "none",
                    "dup_of_confidence": 0, "privacy_flag": False, "privacy_reason": "",
                    "reader_questions": [{"question": q, "kind": "understand"} for q in questions],
                    "phrases": list(phrases), "domain_repo": repo},
        "features": {}, "extra_properties": {}, "extra_body": [],
    })


def inputs(tmp_path, web, **cfg):
    return Inputs(
        state_dir=tmp_path, cfg=from_mapping({"feeds": list(HN_FEEDS), "settings": {"match_threshold": 0.6}, **cfg}),
        now=NOW, cycle=CYCLE, projects_dir=tmp_path / "projects", client_projects=(), env_path=None,
        log=lambda m: None, net=make_net(tmp_path, web), embedder=KeywordEmbedder(),
        gh_run=lambda *a, **k: SimpleNamespace(stdout=""),
    )


# --- config -------------------------------------------------------------------

def test_config_defaults_and_denylist_hidden_in_repr():
    cfg = from_mapping({"denylist": ["SecretCo"]})
    assert "anthropics/claude-code" in cfg.watchlist and "mcp" in cfg.whitelist
    assert cfg.denylist == ("SecretCo",)
    assert "SecretCo" not in repr(cfg)


# --- denylist -----------------------------------------------------------------

def test_denylist_sources_and_blocking(tmp_path):
    proj = tmp_path / "projects"
    (proj / "-Users-me-work-acmeclient-api").mkdir(parents=True)
    (proj / "-Users-me-projects-blog").mkdir()
    env = tmp_path / ".env"
    env.write_text("API=https://portal.examplecorp.io/v1\nGH=https://api.github.com\n")
    gh = lambda *a, **k: SimpleNamespace(stdout="me/privaterepo\n")
    d = denylist.build(["Hand Written"], proj, ["acmeclient"], env, run=gh)
    for phrase in ("hand written issue", "privaterepo hooks", "acmeclient", "examplecorp sso", "portal.examplecorp.io"):
        assert d.blocks(phrase), phrase
    assert not d.blocks("git worktree")
    assert not d.blocks("blog")
    assert "acmeclient" not in repr(d)


def test_private_repo_names_failure_is_empty():
    def boom(*a, **k):
        raise subprocess.TimeoutExpired("gh", 1)
    assert denylist.private_repo_names(boom) == set()


# --- feeds --------------------------------------------------------------------

def test_parse_rss_and_atom():
    rss = ("<rss><channel><item><title>A &amp; B</title><link>https://x/1</link>"
           "<description>&lt;p&gt;hi&lt;/p&gt;</description><pubDate>Mon, 19 Oct 2026 10:00:00 GMT</pubDate></item>"
           "</channel></rss>")
    atom = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>T</title><link href="https://y/2"/>'
            "<id>y2</id><updated>2026-10-18T00:00:00Z</updated><summary>s</summary></entry></feed>")
    a, = parse_rss(rss, "r")
    assert (a.title, a.text, a.url) == ("A & B", "hi", "https://x/1")
    b, = parse_rss(atom, "s")
    assert (b.url, b.id) == ("https://y/2", "y2")
    with pytest.raises(SourceError):
        parse_rss("not xml", "r")


def test_pull_all_lookback_and_failed_source(tmp_path):
    web = FakeWeb()
    feeds = (*HN_FEEDS, {"name": "bad", "type": "rss", "url": "https://down.example/rss"}, {"name": "x", "type": "nope"})
    web.fail = {"down.example"}
    res = pull_all(make_net(tmp_path, web), feeds, (), NOW, 30, log=lambda m: None)
    assert set(res.failed) == {"bad", "x"}
    assert "Old worktree post" not in [i.title for i in res.items]
    assert sum(i.help for i in res.items) == 2


# --- net ----------------------------------------------------------------------

def test_net_cache_log_and_github_rate_limit(tmp_path):
    web, slept = FakeWeb(), []
    t = [1000.0]
    net = Net(tmp_path, keychain_service="svc", github_per_minute=2, fetch=web,
              token_reader=lambda s: "tok", clock=lambda: t[0], sleep=slept.append)
    net.get_json("https://hn.algolia.com/api/v1/search?query=a", "query", "p")
    net.get_json("https://hn.algolia.com/api/v1/search?query=a", "query", "p")
    assert len(web.urls) == 1  # cached
    for i in range(3):
        net.get_json(f"https://api.github.com/search/issues?q={i}", "query", "p")
    assert slept, "third GitHub call within a minute must wait"
    rows = store.read_jsonl(tmp_path / "market" / "outbound.jsonl")
    assert len(rows) == 5 and rows[1]["cached"] is True
    assert "tok" not in (tmp_path / "market" / "outbound.jsonl").read_text()


def test_missing_keychain_token_raises_clear_error():
    run = lambda *a, **k: SimpleNamespace(returncode=44, stdout="")
    from market.net import keychain_token
    with pytest.raises(SourceError, match="missing from Keychain"):
        keychain_token("blog-pipeline-github", run)


# --- matching -----------------------------------------------------------------

def test_match_max_sim_counts_once_and_top5():
    e = KeywordEmbedder()
    items = e.passages(["worktree a", "worktree hooks", "cooking", "electron"])
    topic = e.queries(["worktree?", "hooks?"])  # two vectors both matching item 1: counted once
    res = match_topic(topic, items, 0.6)
    assert sorted(res.matched) == [0, 1]
    assert len(res.top) == 4 and res.top[0][1] >= res.top[-1][1]


def test_percentile():
    assert percentile([0, 2, 5, 5]) == [0.0, 38, 75, 75]


# --- route A ------------------------------------------------------------------

def test_route_a_only_whitelist_terms_and_denylist_wins(tmp_path):
    web = FakeWeb()
    deny = denylist.Denylist(frozenset({"secretco"}))
    t = TopicText("k", (), ("Claude Code hooks not firing in secretco repo", "git worktree cleanup", "random words"),
                  "anthropics/claude-code")
    res = route_a.run(make_net(tmp_path, web), t, ("claude code hooks", "git worktree"),
                      ("anthropics/claude-code",), [], deny, 0, log=lambda m: None)
    assert res.ran and res.denied == 1
    assert res.queries == ["hn:git worktree", "github:anthropics/claude-code:git worktree"]
    assert res.github_thumbs == 5
    assert all("secretco" not in u.lower() and "random" not in u for u in web.urls)
    hn_url = next(u for u in web.urls if "hn.algolia" in u)
    assert urllib.parse.parse_qs(urllib.parse.urlparse(hn_url).query)["query"] == ['"git worktree"']


def test_route_a_off_watchlist_is_insufficient_and_candidate(tmp_path):
    t = TopicText("k", (), ("mcp server crash",), "someone/tool")
    res = route_a.run(make_net(tmp_path, FakeWeb()), t, ("mcp",), (), [], denylist.Denylist(frozenset()), 0)
    assert res.failed and res.off_watchlist_repo == "someone/tool"
    assert not any("api.github.com" in u for u in [])  # no GitHub call off-watchlist
    denied = route_a.run(make_net(tmp_path, FakeWeb()), t, (), (), [], denylist.Denylist(frozenset({"someone"})), 0)
    assert denied.off_watchlist_repo is None


def test_feed_seen_twice_phrase_is_whitelisted():
    items = [FeedItem("s", str(i), "git worktree tips", "", "", NOW) for i in range(2)]
    t = TopicText("k", (), ("git worktree tips", "unseen phrase"))
    terms, denied, derived = route_a.whitelist_terms(t, (), items, denylist.Denylist(frozenset()))
    assert terms == derived == ["git worktree tips"]


# --- nightly pipeline ---------------------------------------------------------

def test_run_nightly_writes_market_fields_and_log_passes_check(tmp_path):
    stage_note(tmp_path, "s1", "worktree-topic", ["git worktree conflicts"], "anthropics/claude-code")
    stage_note(tmp_path, "s2", "electron-topic", ["electron hooks"], "electron/electron",
               questions=("Why electron?",))
    stage_note(tmp_path, "s3", "other-topic", ["cooking"], "someone/elsewhere", questions=("cooking?",))
    web = FakeWeb()
    inp = inputs(tmp_path, web)
    summary = run_nightly(inp)
    assert summary["restaged"] == 3
    staged = {r["session_id"]: r for r in Outbox(tmp_path).pending()}
    props = {sid: r["notion"]["properties"] for sid, r in staged.items()}
    assert props["s1"][ns.MARKET_STATUS] == ns.MARKET_STATUS_A_B
    assert props["s1"][ns.MARKET_HEAT] > 0 and props["s1"][ns.MARKET_PAIN] >= 2 + 5
    assert props["s2"][ns.MARKET_STATUS] == ns.MARKET_STATUS_A_B
    assert props["s3"][ns.MARKET_STATUS] == ns.MARKET_STATUS_INSUFFICIENT
    assert store.candidates_since(tmp_path, NOW.date()) == ["someone/elsewhere"]
    top = store.read_jsonl(tmp_path / "market" / "matches" / f"{NOW.date()}.jsonl")
    assert {r["topic"] for r in top} == {"worktree-topic", "electron-topic", "other-topic"}
    assert all(len(r["top"]) <= 5 for r in top)
    # Outbound audit over the produced log.
    rows = list(enumerate(store.read_jsonl(tmp_path / "market" / "outbound.jsonl"), 1))
    wl = set(json.loads((tmp_path / "market" / "whitelist" / f"{NOW.date()}.json").read_text()))
    cfg = inp.cfg
    assert check_outbound.check(rows, wl, {w.lower() for w in cfg.watchlist}, check_outbound._feed_hosts(cfg)) == []
    assert any(r["kind"] == "query" for _, r in rows)


def test_requery_pool_topic_without_new_notes(tmp_path):
    stage_note(tmp_path, "s1", "worktree-topic", ["git worktree conflicts"])
    run_nightly(inputs(tmp_path, FakeWeb()))
    for p in (tmp_path / "outbox").glob("*.json"):
        p.unlink()  # written to Notion; next night has no new notes
    later = inputs(tmp_path, FakeWeb())
    later.now, later.cycle = NOW + timedelta(days=1), "2026-10-21"
    summary = run_nightly(later)
    assert summary["topics"] == 1 and summary["restaged"] == 0
    assert "worktree-topic" in store.latest_signals(tmp_path)


def test_all_sources_failed_gives_insufficient_never_raises(tmp_path):
    stage_note(tmp_path, "s1", "worktree-topic", ["git worktree conflicts"])
    summary = run_nightly(inputs(tmp_path, FakeWeb(fail={"hn.algolia.com"})))
    assert summary["status"][ns.MARKET_STATUS_INSUFFICIENT] == 1
    props = next(Outbox(tmp_path).pending())["notion"]["properties"]
    assert props[ns.MARKET_STATUS] == ns.MARKET_STATUS_INSUFFICIENT and ns.MARKET_HEAT not in props


def test_check_outbound_flags_violations():
    rows = [(1, {"kind": "query", "url": "https://hn.algolia.com/api/v1/search?query=%22leak%22"}),
            (2, {"kind": "query", "url": "https://api.github.com/search/issues?q=repo%3Ax%2Fy+%22mcp%22"}),
            (3, {"kind": "feed", "url": "https://evil.example/rss"})]
    bad = check_outbound.check(rows, {"mcp"}, {"a/b"}, {"hn.algolia.com"})
    assert len(bad) == 3 and all("leak" not in b for b in bad)


# --- batch step + daily lines ---------------------------------------------------

def test_batch_step_and_daily_lines_are_discovered():
    from batch.discovery import discover
    from daily.discovery import discover_lines
    assert "market_signals" in [s.name for s in discover()["nightly"]]
    found = discover_lines()
    assert "market_heat" in [p.name for p in found["topic"]]
    assert "market_candidates" in [p.name for p in found["global"]]


def test_topic_line_uses_local_signals_only_when_notion_has_none(tmp_path):
    from daily.lines import market_heat
    store.save_signals(tmp_path, NOW.date(), {"k": {"market_heat": 50, "market_pain": 3, "market_status": "b"}})
    ctx = SimpleNamespace(state_dir=tmp_path, today=NOW.date())
    bare = SimpleNamespace(key="k", notes=[SimpleNamespace(market_heat=None, market_pain=None)])
    assert market_heat.lines(ctx, bare) == ["熱度 50 · 痛點 3"]
    has = SimpleNamespace(key="k", notes=[SimpleNamespace(market_heat=10, market_pain=None)])
    assert market_heat.lines(ctx, has) == []


def test_weekly_candidate_line(tmp_path, monkeypatch):
    from daily.lines import market_candidates
    store.append_jsonl(tmp_path / "market" / "candidates.jsonl", [{"day": "2026-10-18", "repo": "a/b"}])
    monkeypatch.setattr(market_candidates.market_config, "load", lambda: from_mapping({}))
    monday = datetime(2026, 10, 19).date()
    assert market_candidates.lines(SimpleNamespace(state_dir=tmp_path, today=monday)) == ["watchlist 候選: a/b"]
    assert market_candidates.lines(SimpleNamespace(state_dir=tmp_path, today=monday + timedelta(days=1))) == []
