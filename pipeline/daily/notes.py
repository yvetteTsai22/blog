"""Literature notes as the 21:00 run sees them: Slip box properties plus a few body fields."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date, datetime

from common import notion_schema as ns
from notes.mapping import parse_reader_questions

LINK_RE = re.compile(r"https://github\.com/[\w.-]+/[\w.-]+/(?:pull/\d+|commit/[0-9a-f]{7,40})")
ACTIVE_MINUTES_RE = re.compile(r"active_minutes:\s*([0-9.]+)")


@dataclass(frozen=True)
class Note:
    page_id: str
    title: str
    session_id: str
    created: datetime
    topic_of: str
    p: dict[str, float]
    dup_of: str = ns.DUP_OF_NONE
    dup_conf: float = 0.0
    pick_status: str = ns.PICK_NOT_LISTED
    last_listed_at: date | None = None
    listed_count: int = 0
    privacy_flag: bool = False
    privacy_reason: str = ""
    reader_questions: tuple[dict, ...] = ()
    market_heat: float | None = None
    market_pain: float | None = None
    origin: str = ns.ORIGIN_PERSONAL
    url: str = ""
    # Body fields; filled by `with_body` for eligible notes only.
    active_minutes: float = 0.0
    lesson: str = ""
    link: str = ""
    props: dict = field(default_factory=dict, compare=False, repr=False)

    @property
    def max_p(self) -> float:
        return max(self.p.values(), default=0.0)

    @property
    def argmax_signal(self) -> str:
        return max(ns.P_SIGNALS, key=lambda k: self.p.get(k, 0.0))

    @property
    def topic_key(self) -> str:
        t = (self.topic_of or "").strip()
        return self.page_id if t in ("", ns.TOPIC_NEW) else t


def _plain(prop: dict | None):
    """Plain Python value of one Notion REST property."""
    if not prop:
        return None
    kind = prop.get("type")
    value = prop.get(kind)
    if kind in ("title", "rich_text"):
        return "".join(part.get("plain_text", "") for part in value or [])
    if kind == "select":
        return value and value.get("name")
    if kind == "date":
        return value and value.get("start")
    return value


def _date(raw: str | None) -> date | None:
    return date.fromisoformat(raw[:10]) if raw else None


def from_page(page: dict) -> Note:
    props = page.get("properties") or {}
    v = {name: _plain(p) for name, p in props.items()}
    return Note(
        page_id=page["id"],
        title=v.get(ns.TITLE) or "",
        session_id=v.get(ns.SESSION_ID) or "",
        created=datetime.fromisoformat(page["created_time"].replace("Z", "+00:00")),
        topic_of=v.get(ns.TOPIC_OF) or "",
        p={k: float(v.get(k) or 0.0) for k in ns.P_SIGNALS},
        dup_of=(v.get(ns.DUP_OF) or ns.DUP_OF_NONE).strip() or ns.DUP_OF_NONE,
        dup_conf=float(v.get(ns.DUP_OF_CONFIDENCE) or 0.0),
        pick_status=v.get(ns.PICK_STATUS) or ns.PICK_NOT_LISTED,
        last_listed_at=_date(v.get(ns.LAST_LISTED_AT)),
        listed_count=int(v.get(ns.LISTED_COUNT) or 0),
        privacy_flag=bool(v.get(ns.PRIVACY_FLAG)),
        privacy_reason=v.get(ns.PRIVACY_REASON) or "",
        reader_questions=tuple(parse_reader_questions(v.get(ns.READER_QUESTIONS))),
        market_heat=v.get(ns.MARKET_HEAT),
        market_pain=v.get(ns.MARKET_PAIN),
        origin=v.get(ns.ORIGIN) or ns.ORIGIN_PERSONAL,
        url=page.get("url") or "",
        props=v,
    )


def parse_body(text: str) -> dict:
    """active_minutes, lesson (first sentence of 'Learned') and first PR/commit link."""
    minutes = ACTIVE_MINUTES_RE.search(text)
    learned = re.search(r"^## Learned\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    lesson = ""
    if learned:
        body = " ".join(learned.group(1).split())
        lesson = re.split(r"(?<=[.!?。])\s", body, maxsplit=1)[0] if body and body != "(none)" else ""
    link = LINK_RE.search(text)
    return {
        "active_minutes": float(minutes.group(1)) if minutes else 0.0,
        "lesson": lesson,
        "link": link.group(0) if link else "",
    }


def with_body(note: Note, body: dict) -> Note:
    return replace(
        note,
        active_minutes=float(body.get("active_minutes") or 0.0),
        lesson=body.get("lesson") or "",
        link=body.get("link") or "",
    )
