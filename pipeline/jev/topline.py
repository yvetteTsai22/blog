""""Jev 另外推": Jev's top-3 topics that Haiku did not list (spec §1.5). Pure, no I/O."""
from __future__ import annotations

from typing import Iterable, Sequence

from common import notion_schema as ns

LABEL = "Jev 另外推"
MAX_TOPICS = 3


def jev_max_p(props: dict) -> float | None:
    values = [props.get(k) for k in ns.JEV_P_SIGNALS]
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    return max(nums) if nums else None


def jev_top_topics(pool: Iterable, listed_keys: set[str], limit: int = MAX_TOPICS) -> list[tuple[str, object, float]]:
    """(topic key, best note, Jev max p) for the best Jev-scored topics outside `listed_keys`.

    Shadow display only: no threshold, no duration weight; the 21:00 ranking never reads these.
    """
    best: dict[str, tuple[object, float]] = {}
    for note in pool:
        if note.origin == ns.ORIGIN_CLIENT or note.topic_key in listed_keys:
            continue
        score = jev_max_p(note.props)
        if score is None:
            continue
        if note.topic_key not in best or score > best[note.topic_key][1]:
            best[note.topic_key] = (note, score)
    ranked = sorted(best.items(), key=lambda kv: (-kv[1][1], kv[0]))[:limit]
    return [(k, n, s) for k, (n, s) in ranked]


def render(picks: Sequence[tuple[str, object, float]]) -> list[str]:
    if not picks:
        return [f"{LABEL}: (none)"]
    items = [f"{n.title} {s:.2f} {n.url}".rstrip() for _, n, s in picks]
    return [f"{LABEL}:", *(f"• {i}" for i in items)]
