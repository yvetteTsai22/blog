"""Spec §1.4 step 2: pool updates for listed topics. Pure; returns the writes to make."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Sequence

from common import notion_schema as ns

from .notes import Note
from .ranking import Topic

ABANDON_AFTER = 2


@dataclass(frozen=True)
class PoolUpdate:
    page_id: str
    topic_key: str
    pick_status: str
    last_listed_at: date
    listed_count: int

    def properties(self) -> dict:
        """Notion REST property payload."""
        return {
            ns.PICK_STATUS: {"select": {"name": self.pick_status}},
            ns.LAST_LISTED_AT: {"date": {"start": self.last_listed_at.isoformat()}},
            ns.LISTED_COUNT: {"number": self.listed_count},
        }


def plan_updates(listed: Sequence[Topic], notes: Iterable[Note], today: date) -> list[PoolUpdate]:
    """Every pool note sharing a listed topic's key is stamped.

    The topic's count is its highest note count plus one, applied to all its notes. A
    topic reaching ABANDON_AFTER listings without a pick becomes 放棄 (it is still
    sent tonight; coordinator decision, TSA-65).
    """
    by_key: dict[str, list[Note]] = {}
    for note in notes:
        if note.pick_status in ns.PICK_POOL_STATES:
            by_key.setdefault(note.topic_key, []).append(note)
    updates = []
    for topic in listed:
        members = by_key.get(topic.key) or list(topic.notes)
        count = max(n.listed_count for n in members) + 1
        status = ns.PICK_ABANDONED if count >= ABANDON_AFTER else ns.PICK_LISTED
        for note in sorted(members, key=lambda n: n.page_id):
            updates.append(PoolUpdate(note.page_id, topic.key, status, today, count))
    return updates
