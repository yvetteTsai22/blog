"""Per-topic `熱度 x · 痛點 y` line from the nightly market requery (spec §1.5, §4).

Display only; ranking never reads it. The core message already prints this line when the
topic's notes carry market properties in Notion, so this provider only fills in for pool
topics whose fresh values live in `<state>/market/signals/` (the batch never writes Notion
for older notes).
"""
from __future__ import annotations

from market import store

NAME = "market_heat"
KIND = "topic"
ORDER = 10


def _num(value) -> str:
    return "—" if value is None else f"{value:g}"


def lines(ctx, topic):
    if any(n.market_heat is not None or n.market_pain is not None for n in topic.notes):
        return []
    sig = store.latest_signals(ctx.state_dir, today=ctx.today).get(topic.key)
    if not sig or (sig.get("market_heat") is None and sig.get("market_pain") is None):
        return []
    return [f"熱度 {_num(sig.get('market_heat'))} · 痛點 {_num(sig.get('market_pain'))}"]
