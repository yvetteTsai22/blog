"""Route B matching (spec §4.3): multi-vector topics, max-similarity per feed item."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from .feeds import FeedItem

MAX_VECTORS = 6
TOP_K = 5


@dataclass(frozen=True)
class TopicText:
    key: str
    questions: tuple[str, ...]
    phrases: tuple[str, ...]
    domain_repo: str = "none"

    def texts(self) -> list[str]:
        return [t for t in (*self.questions[:3], *self.phrases[:3]) if t][:MAX_VECTORS]


@dataclass(frozen=True)
class MatchResult:
    matched: tuple[int, ...]           # indices into the item list, each counted once
    top: tuple[tuple[int, float], ...]  # best TOP_K (index, score), matched or not


def match_topic(topic_vecs: np.ndarray, item_vecs: np.ndarray, threshold: float) -> MatchResult:
    if topic_vecs.size == 0 or item_vecs.size == 0:
        return MatchResult((), ())
    best = (topic_vecs @ item_vecs.T).max(axis=0)
    order = np.argsort(-best)
    top = tuple((int(i), round(float(best[i]), 4)) for i in order[:TOP_K])
    matched = tuple(int(i) for i in order if best[i] >= threshold)
    return MatchResult(matched, top)


def percentile(counts: Sequence[int]) -> list[float]:
    """Mid-rank percentile (0-100) of each count among today's topics; a zero count is 0."""
    n = len(counts)
    out = []
    for c in counts:
        if c <= 0:
            out.append(0.0)
            continue
        below = sum(1 for x in counts if x < c)
        equal = sum(1 for x in counts if x == c)
        out.append(round(100 * (below + 0.5 * equal) / n))
    return out


def phrase_seen_count(phrase: str, items: Sequence[FeedItem]) -> int:
    p = phrase.lower().strip()
    return sum(1 for it in items if p and p in f"{it.title} {it.text}".lower())
