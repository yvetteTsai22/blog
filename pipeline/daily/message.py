"""Spec §1.5: render the nightly Telegram message (plain text). Pure, except provider calls."""
from __future__ import annotations

from typing import Callable, Sequence

from common import notion_schema as ns

from .ranking import Topic

SIGNAL_LABEL = {ns.P_TRAP: "trap", ns.P_INSIGHT: "insight", ns.P_PATTERN: "pattern"}
WRITING_REMINDER_DAYS = 14


def _num(value) -> str:
    return "—" if value is None else f"{value:g}"


def topic_lines(i: int, topic: Topic) -> list[str]:
    best = topic.best
    out = [
        f"{i}. {best.title or topic.key}",
        f"{SIGNAL_LABEL[topic.signal]} {topic.score:.2f} · {len(topic.notes)} sessions · {topic.active_minutes:.0f} min",
    ]
    heat = next((n.market_heat for n in topic.notes if n.market_heat is not None), None)
    pain = next((n.market_pain for n in topic.notes if n.market_pain is not None), None)
    if heat is not None or pain is not None:
        out.append(f"熱度 {_num(heat)} · 痛點 {_num(pain)}")
    question = next((n.reader_questions[0] for n in topic.notes if n.reader_questions), None)
    if question:
        out.append(f"Q ({question['kind']}): {question['question']}")
    dups = sorted({n.dup_of for n in topic.notes if n.dup_of not in ("", ns.DUP_OF_NONE)})
    if dups:
        out.append("延續" + "".join(f"〈{d}〉" for d in dups))
    for n in topic.notes:
        if n.privacy_flag:
            out.append(f"⚠ {n.privacy_reason or 'privacy flag'}")
    return out


def session_lines(topic: Topic) -> list[str]:
    out = []
    for n in topic.notes:
        out.append(f"  • {n.lesson or n.title}")
        out.append(f"    {n.link or 'no PR/commit link'}")
        out.append(f"    claude --resume {n.session_id}")
    return out


def others_line(others: Sequence[Topic]) -> str | None:
    if not others:
        return None
    return "其他題目: " + "; ".join(f"{t.best.title or t.key} {t.score:.2f}" for t in others)


def reminder_lines(writing: Sequence[dict]) -> list[str]:
    """`writing` rows: {title, days, draft_path}; only those over the limit are listed."""
    return [
        f"⏳ 寫作中 {w['days']} 天: {w['title']}" + (f" ({w['draft_path']})" if w.get("draft_path") else "")
        for w in writing
        if w["days"] > WRITING_REMINDER_DAYS
    ]


def render(
    header: str,
    batch_lines: Sequence[str],
    listed: Sequence[Topic],
    others: Sequence[Topic],
    writing: Sequence[dict],
    topic_providers: Sequence[Callable[[Topic], list[str]]] = (),
    global_providers: Sequence[Callable[[], list[str]]] = (),
) -> str:
    out = [header, *batch_lines, ""]
    if not listed:
        out.append("今天沒有題目過門檻 (0 topics).")
    for i, topic in enumerate(listed, 1):
        out.extend(topic_lines(i, topic))
        for provider in topic_providers:
            out.extend(provider(topic))
        out.extend(session_lines(topic))
        out.append("")
    other = others_line(others)
    if other:
        out.append(other)
    for provider in global_providers:
        out.extend(provider())
    out.extend(reminder_lines(writing))
    return "\n".join(out).strip() + "\n"
