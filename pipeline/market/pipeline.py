"""Nightly market-signal run (spec §1.3 step 8, §4). Never raises: failures become `insufficient`."""
from __future__ import annotations

import traceback
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Mapping

from common import notion_schema as ns
from notes import Outbox

from . import denylist as denylist_mod
from . import route_a, store
from .config import MarketConfig
from .embed import Embedder, FastEmbedE5
from .feeds import PullResult, pull_all
from .match import TopicText, match_topic, percentile
from .net import Net


@dataclass
class Inputs:
    state_dir: Path
    cfg: MarketConfig
    now: datetime
    cycle: str
    projects_dir: Path
    client_projects: tuple[str, ...]
    env_path: Path | None
    log: Callable[[str], None]
    net: Net | None = None
    embedder: Embedder | None = None
    gh_run: Callable | None = None


def _topic_texts(topics: Mapping[str, Mapping]) -> list[TopicText]:
    return [
        TopicText(k, tuple(v.get("questions") or ()), tuple(v.get("phrases") or ()), v.get("domain_repo") or "none")
        for k, v in sorted(topics.items())
    ]


def _status(b_ok: bool, a: route_a.RouteAResult) -> str:
    if not b_ok or a.failed:
        return ns.MARKET_STATUS_INSUFFICIENT
    return ns.MARKET_STATUS_A_B if a.ran else ns.MARKET_STATUS_B


def compute(inp: Inputs, topics: list[TopicText], pulled: PullResult, deny) -> dict:
    """Return {topic_key: signal dict}; writes the top-5 log and candidate log."""
    today = inp.now.date()
    items = pulled.items
    b_ok = bool(pulled.ok) and bool(items)
    counts, pains, details = {}, {}, {}
    if b_ok:
        try:
            embedder = inp.embedder or FastEmbedE5(inp.cfg.embedding_model, str(store.market_dir(inp.state_dir) / "models"))
            item_vecs = embedder.passages([it.passage() for it in items])
        except Exception:
            inp.log(f"market: embedding failed: {traceback.format_exc(limit=1)}")
            b_ok = False
    matches_log, candidates = [], []
    since_ts = int((inp.now - timedelta(days=inp.cfg.lookback_days)).replace(hour=0, minute=0, second=0).timestamp())
    for t in topics:
        matched = ()
        if b_ok and t.texts():
            res = match_topic(embedder.queries(t.texts()), item_vecs, inp.cfg.match_threshold)
            matched = res.matched
            matches_log.append({
                "day": today.isoformat(), "topic": t.key,
                "top": [{"score": s, "source": items[i].source, "title": items[i].title, "url": items[i].url}
                        for i, s in res.top],
            })
        a = route_a.run(inp.net, t, inp.cfg.whitelist, inp.cfg.watchlist, items, deny, since_ts, inp.log)
        if a.off_watchlist_repo:
            candidates.append({"day": today.isoformat(), "topic": t.key, "repo": a.off_watchlist_repo})
        counts[t.key] = len(matched)
        pains[t.key] = sum(1 for i in matched if items[i].help) + a.github_thumbs
        details[t.key] = {"status": _status(b_ok, a), "matched": len(matched), "hn_hits": a.hn_hits,
                          "github_thumbs": a.github_thumbs, "queries": a.queries, "denied": a.denied,
                          "feed_derived": a.feed_derived}
    heat = dict(zip(counts, percentile(list(counts.values()))))
    store.append_jsonl(store.market_dir(inp.state_dir) / "matches" / f"{today.isoformat()}.jsonl", matches_log)
    store.append_jsonl(store.market_dir(inp.state_dir) / "candidates.jsonl", candidates)
    return {
        k: {
            ns.MARKET_HEAT: heat[k] if b_ok else None,
            ns.MARKET_PAIN: pains[k] if b_ok else None,
            ns.MARKET_STATUS: details[k]["status"],
            **{f"_{dk}": dv for dk, dv in details[k].items() if dk != "status"},
        }
        for k in counts
    }


def restage(state_dir: Path, cycle: str, signals: Mapping[str, Mapping]) -> list[str]:
    """Add market properties to this cycle's staged notes (outbox), before the Notion write pass."""
    outbox, done = Outbox(state_dir), []
    for payload in list(outbox.pending()):
        if payload.get("cycle") != cycle:
            continue
        sig = signals.get(payload.get("topic_of"))
        if not sig:
            continue
        props = {k: sig[k] for k in (ns.MARKET_HEAT, ns.MARKET_PAIN, ns.MARKET_STATUS) if sig.get(k) is not None}
        record = {k: v for k, v in payload.items() if k != "notion"}
        outbox.stage({**record, "extra_properties": {**(record.get("extra_properties") or {}), **props}})
        done.append(payload["session_id"])
    return done


def _empty_signals(topics: list[TopicText]) -> dict:
    return {t.key: {ns.MARKET_HEAT: None, ns.MARKET_PAIN: None, ns.MARKET_STATUS: ns.MARKET_STATUS_INSUFFICIENT}
            for t in topics}


def run_nightly(inp: Inputs) -> dict:
    today: date = inp.now.date()
    outbox = Outbox(inp.state_dir)
    staged = [p for p in outbox.pending() if p.get("cycle") == inp.cycle]
    all_topics = store.register_topics(inp.state_dir, staged, today)
    topics = _topic_texts(store.pool_topics(all_topics, today, inp.cfg.pool_days))
    if inp.net is None:
        inp.net = Net(inp.state_dir, inp.cfg.timeout_s, inp.cfg.github_per_minute, inp.cfg.keychain_service)
    try:
        deny = denylist_mod.build(inp.cfg.denylist, inp.projects_dir, inp.client_projects, inp.env_path,
                                  **({"run": inp.gh_run} if inp.gh_run else {}))
        inp.log(f"market: denylist rebuilt ({len(deny)} terms)")
        pulled = pull_all(inp.net, inp.cfg.feeds, inp.cfg.watchlist, inp.now, inp.cfg.lookback_days, inp.log)
        inp.log(f"market: {len(pulled.items)} feed items, {len(pulled.ok)} sources ok, {len(pulled.failed)} failed")
        signals = compute(inp, topics, pulled, deny)
        derived = [t for s in signals.values() for t in s.get("_feed_derived", [])]
        store.save_whitelist(inp.state_dir, today, [*(w.lower() for w in inp.cfg.whitelist), *derived])
    except Exception:
        inp.log(f"market: run failed, all topics insufficient: {traceback.format_exc(limit=2)}")
        signals = _empty_signals(topics)
    store.save_signals(inp.state_dir, today, signals)
    restaged = restage(inp.state_dir, inp.cycle, signals)
    summary = {"topics": len(signals), "restaged": len(restaged),
               "status": {s: sum(1 for v in signals.values() if v[ns.MARKET_STATUS] == s) for s in ns.MARKET_STATUS_OPTIONS}}
    inp.log(f"market: {summary}")
    return summary
