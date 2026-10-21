"""Map a staged session record to Slip box properties and a markdown body (spec §2).

Property values use the notion-personal MCP `create-pages` format: numbers as numbers,
selects as option strings, checkboxes as "__YES__"/"__NO__".
"""
from __future__ import annotations

import re
from typing import Mapping

from common import notion_schema as ns

SUMMARY_SECTIONS = (
    ("request", "Request"),
    ("investigated", "Investigated"),
    ("learned", "Learned"),
    ("completed", "Completed"),
    ("next_steps", "Next steps"),
    ("notes", "Notes"),
)


def format_reader_questions(questions) -> str:
    """One `kind: question` per line, primary first.

    Not JSON: the notion-personal MCP coerces JSON-parseable strings and rejects them.
    """
    return "\n".join(f"{q['kind']}: {q['question']}" for q in questions or [])


def parse_reader_questions(text: str | None) -> list[dict]:
    """Inverse of format_reader_questions, for readers of the Slip box (e.g. the 21:00 run)."""
    out = []
    # Notion rows-mode queries return the newlines as <br>.
    for line in re.split(r"\n|<br\s*/?>", text or ""):
        kind, sep, question = line.partition(":")
        kind = kind.strip().lower()
        if sep and kind in ns.READER_QUESTION_KINDS and question.strip():
            out.append({"question": question.strip(), "kind": kind})
        elif line.strip():
            out.append({"question": line.strip(), "kind": "none"})
    return out


def checkbox(value: bool) -> str:
    return "__YES__" if value else "__NO__"


def to_properties(record: Mapping) -> dict:
    s = record["summary"]
    props = {
        ns.TITLE: s["title"],
        ns.NOTE_TYPE: ns.NOTE_TYPE_LITERATURE,
        ns.STATUS: ns.STATUS_LITERATURE,
        ns.SOURCE: ns.SOURCE_AGENT_SESSION,
        ns.SESSION_ID: record["session_id"],
        ns.ORIGIN: record["origin"],
        ns.P_TRAP: s["p_trap"],
        ns.P_INSIGHT: s["p_insight"],
        ns.P_PATTERN: s["p_pattern"],
        ns.DUP_OF: s["dup_of"],
        ns.DUP_OF_CONFIDENCE: s["dup_of_confidence"],
        ns.TOPIC_OF: record["topic_of"],
        ns.PRIVACY_FLAG: checkbox(s["privacy_flag"]),
        ns.PRIVACY_REASON: s["privacy_reason"],
        ns.READER_QUESTIONS: format_reader_questions(s["reader_questions"]),
        ns.PICK_STATUS: ns.PICK_NOT_LISTED,
        ns.LISTED_COUNT: 0,
    }
    # Later steps (Jev, market) add their own properties without touching this mapping.
    props.update(record.get("extra_properties") or {})
    return props


def _bullets(items) -> str:
    items = list(items or [])
    return "\n".join(f"- {x}" for x in items) if items else "- (none)"


def render_body(record: Mapping) -> str:
    s = record["summary"]
    f = record.get("features") or {}
    parts = []
    for key, heading in SUMMARY_SECTIONS:
        parts.append(f"## {heading}\n{s.get(key) or '(none)'}")
    # Backticks stop Notion auto-linking names like `queue_session.py` as domains.
    parts.append(f"## Files read\n{_bullets(f'`{x}`' for x in s.get('files_read') or [])}")
    parts.append(f"## Files edited\n{_bullets(f'`{x}`' for x in s.get('files_edited') or [])}")
    parts.append("## Structural features\n" + _bullets(f"{k}: {v}" for k, v in f.items()))
    parts.append(f"## Phrases\n{_bullets(s.get('phrases'))}")
    parts.append(f"## domain_repo\n{s.get('domain_repo') or 'none'}")
    parts.append(
        "## Reader questions\n"
        + _bullets(f"{q['question']} ({q['kind']})" for q in s.get("reader_questions") or [])
    )
    for section in record.get("extra_body") or []:
        parts.append(section)
    parts.append(
        "## source_reference\n"
        f"- session: `{record['session_id']}`\n"
        f"- resume: `claude --resume {record['session_id']}`\n"
        f"- model: {record.get('model', '')}"
    )
    return "\n\n".join(parts)
