"""Note mapping and outbox idempotency with synthetic records."""
import json

import pytest

from common import notion_schema as ns
from notes import Outbox, format_reader_questions, parse_reader_questions, render_body, to_properties


def record(sid="sess-1", **over):
    r = {
        "session_id": sid, "cycle": "2026-01-01", "model": "haiku", "origin": "personal",
        "topic_of": "hooks-abc123",
        "summary": {
            "title": "T", "request": "r", "investigated": "i", "learned": "l", "completed": "c",
            "next_steps": "n", "notes": "", "files_read": ["a.py"], "files_edited": [],
            "generality": "general", "p_trap": 0.7, "p_insight": 0.2, "p_pattern": 0.1,
            "dup_of": "none", "dup_of_confidence": 0.0, "topic_of": "new",
            "privacy_flag": True, "privacy_reason": "mentions infra",
            "reader_questions": [{"question": "why?", "kind": "understand"}],
            "phrases": ["p1", "p2"], "domain_repo": "o/r", "origin": "personal", "warnings": [],
        },
        "features": {"turns": 4, "active_minutes": 12.5},
        "extra_properties": {}, "extra_body": [],
    }
    r.update(over)
    return r


def test_properties_follow_spec():
    p = to_properties(record())
    assert p[ns.NOTE_TYPE] == "literature note"
    assert p[ns.STATUS] == ns.STATUS_LITERATURE
    assert p[ns.SOURCE] == "agent-session"
    assert p[ns.PICK_STATUS] == "未推薦"
    assert p[ns.SESSION_ID] == "sess-1"
    assert p[ns.PRIVACY_FLAG] == "__YES__"
    assert p[ns.P_TRAP] == 0.7 and p[ns.TOPIC_OF] == "hooks-abc123"
    assert p[ns.READER_QUESTIONS] == "understand: why?"
    with pytest.raises(ValueError):
        json.loads(p[ns.READER_QUESTIONS])  # must not be JSON-parseable for the MCP
    assert set(p) - {ns.TITLE, ns.NOTE_TYPE, ns.STATUS} <= set(ns.ADDED_PROPERTIES)


def test_reader_questions_round_trip():
    qs = [{"question": "How: does it work?", "kind": "understand"}, {"question": "fix it", "kind": "fix"}]
    assert parse_reader_questions(format_reader_questions(qs)) == qs
    assert parse_reader_questions("free text") == [{"question": "free text", "kind": "none"}]
    assert parse_reader_questions(None) == []
    assert parse_reader_questions("fix: a<br>decide: b") == [
        {"question": "a", "kind": "fix"}, {"question": "b", "kind": "decide"}]


def test_extra_properties_from_steps():
    p = to_properties(record(extra_properties={ns.JEV_P_TRAP: 0.5}))
    assert p[ns.JEV_P_TRAP] == 0.5


def test_body_sections():
    body = render_body(record(extra_body=["## Jev\nshadow"]))
    for needle in ("## Request", "## Learned", "active_minutes: 12.5", "- p1", "o/r",
                   "## source_reference", "claude --resume sess-1", "## Jev"):
        assert needle in body


def test_outbox_stage_commit_idempotent(tmp_path):
    ob = Outbox(tmp_path)
    ob.stage(record())
    assert ob.is_staged("sess-1")
    [pending] = list(ob.pending())
    assert pending["notion"]["properties"][ns.SESSION_ID] == "sess-1"
    ob.mark_written("sess-1", "page-1")
    ob.mark_written("sess-1", "page-2")
    assert not ob.is_staged("sess-1")
    assert ob.written()["sess-1"]["page_id"] == "page-1"
    assert len(ob.ledger.read_text().splitlines()) == 1
    assert ob.written()["sess-1"]["topic_of"] == "hooks-abc123"
