"""Spec §3: eligibility, session score, topic grouping. Pure functions, no I/O."""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from datetime import date, tzinfo
from typing import Iterable, Sequence

from common import notion_schema as ns

from .notes import Note

THRESHOLD = 0.6
DURATION_WEIGHT = 0.3
DUP_CONFIDENCE = 0.8
DUP_PENALTY = 0.5
MAX_TOPICS = 3
POOL_DAYS = 14
COOLDOWN_DAYS = 7


@dataclass(frozen=True)
class Topic:
    key: str
    notes: tuple[Note, ...]          # sessions over the threshold, best first
    score: float
    best: Note
    active_minutes: float

    @property
    def signal(self) -> str:
        return self.best.argmax_signal


def percentile(value: float, population: Sequence[float]) -> float:
    """Percentile rank in [0, 1], ties at the midpoint; 0 for an empty population."""
    if not population:
        return 0.0
    ordered = sorted(population)
    below = bisect_left(ordered, value)
    equal = bisect_right(ordered, value) - below
    return (below + 0.5 * equal) / len(ordered)


def dup_factor(note: Note) -> float:
    is_dup = note.dup_of not in ("", ns.DUP_OF_NONE) and note.dup_conf >= DUP_CONFIDENCE
    return DUP_PENALTY if is_dup else 1.0


def session_score(note: Note, minutes_population: Sequence[float]) -> float:
    weight = 1 + DURATION_WEIGHT * percentile(note.active_minutes, minutes_population)
    return note.max_p * weight * dup_factor(note)


def is_eligible(note: Note, today: date, tz: tzinfo | None = None) -> bool:
    if note.pick_status not in ns.PICK_POOL_STATES:
        return False
    created = note.created.astimezone(tz).date() if tz else note.created.date()
    if (today - created).days > POOL_DAYS:
        return False
    if note.last_listed_at and (today - note.last_listed_at).days < COOLDOWN_DAYS:
        return False
    return True


def eligible(notes: Iterable[Note], today: date, tz: tzinfo | None = None) -> list[Note]:
    return [n for n in notes if is_eligible(n, today, tz)]


def rank_topics(pool: Sequence[Note]) -> list[Topic]:
    """All topics with at least one session over the threshold, best first.

    The duration weight uses session minutes against the whole pool and topic summed
    minutes against all candidate topics (coordinator decision, TSA-65).
    """
    session_minutes = [n.active_minutes for n in pool]
    groups: dict[str, list[Note]] = {}
    for note in pool:
        if note.max_p >= THRESHOLD:
            groups.setdefault(note.topic_key, []).append(note)
    sums = {k: sum(n.active_minutes for n in g) for k, g in groups.items()}
    population = list(sums.values())
    topics = []
    for key, group in groups.items():
        ordered = sorted(group, key=lambda n: session_score(n, session_minutes), reverse=True)
        best = ordered[0]
        weight = 1 + DURATION_WEIGHT * percentile(sums[key], population)
        topics.append(Topic(key, tuple(ordered), best.max_p * dup_factor(best) * weight, best, sums[key]))
    return sorted(topics, key=lambda t: (-t.score, t.key))


def split(topics: Sequence[Topic], limit: int = MAX_TOPICS) -> tuple[list[Topic], list[Topic]]:
    """(listed, others over the threshold)."""
    return list(topics[:limit]), list(topics[limit:])
