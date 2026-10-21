"""Prompt parsing with synthetic replies only."""
import json

import pytest

from summarize import ParseError, build_prompt, parse_output
from summarize.posts import load_post_options
from summarize.scrub import scrub_text


def reply(**over):
    base = {
        "title": "Hooks fire for headless runs too",
        "request": "make a nightly job", "investigated": "hook config", "learned": "use project sources",
        "completed": "runner", "next_steps": ["tests", "docs"], "notes": "",
        "files_read": ["/Users/someone/work/acme-app/src/a.py"], "files_edited": ["b.py"],
        "generality": "general", "p_trap": 0.8, "p_insight": "0.4", "p_pattern": 1.7,
        "dup_of": "none", "dup_of_confidence": 0.9, "topic_of": "new",
        "privacy_flag": "false", "privacy_reason": "",
        "reader_questions": [{"question": "q1", "kind": "fix"}, {"question": "q2", "kind": "bogus"},
                             "q3", {"question": "q4", "kind": "decide"}],
        "phrases": ["claude code hooks", "headless claude -p", "x", "y"],
        "domain_repo": "anthropics/claude-code", "origin": "personal",
    }
    base.update(over)
    return "Here you go:\n```json\n" + json.dumps(base) + "\n```"


def test_parses_and_normalises():
    s = parse_output(reply())
    assert s.p_trap == 0.8 and s.p_insight == 0.4 and s.p_pattern == 1.0
    assert s.files_read == ["a.py"]
    assert s.next_steps == "- tests\n- docs"
    assert [q["kind"] for q in s.reader_questions] == ["fix", "none", "none"]
    assert len(s.phrases) == 3
    assert s.dup_of == "none" and s.dup_of_confidence == 0.0
    assert s.privacy_flag is False


def test_generality_rule_caps_project_only():
    s = parse_output(reply(generality="project_only"))
    assert max(s.p_trap, s.p_insight, s.p_pattern) == 0.3
    assert "project_only scores capped" in s.warnings


def test_dup_of_must_be_known_slug():
    assert parse_output(reply(dup_of="my-post"), post_slugs=["my-post"]).dup_of == "my-post"
    s = parse_output(reply(dup_of="invented"), post_slugs=["my-post"])
    assert s.dup_of == "none" and s.warnings


def test_topic_of_unknown_becomes_new():
    assert parse_output(reply(topic_of="t-1"), topic_ids=["t-1"]).topic_of == "t-1"
    assert parse_output(reply(topic_of="t-9"), topic_ids=["t-1"]).topic_of == "new"


def test_denylist_and_paths_scrubbed():
    s = parse_output(reply(learned="Acme-App broke at /Users/someone/work/acme-app/x.py"), deny=["acme-app"])
    assert "acme" not in s.learned.lower() and "/Users" not in s.learned


def test_bad_origin_and_repo_default():
    s = parse_output(reply(origin="corp", domain_repo="not a repo"))
    assert s.origin == "personal" and s.domain_repo == "none"


@pytest.mark.parametrize("bad", ["no json here", "[1, 2]", "{broken"])
def test_parse_errors(bad):
    with pytest.raises(ParseError):
        parse_output(bad)


def test_scrub_text_keeps_basename():
    assert scrub_text("see ~/x/y/z.md now") == "see z.md now"


def test_prompt_carries_options_and_denylist(tmp_path):
    posts = tmp_path / "_posts"
    posts.mkdir()
    (posts / "2026-01-01-demo-post.md").write_text(
        "---\ntitle: Demo\ndescription: A demo post\n---\n" + "Body text. " * 200, encoding="utf-8")
    (posts / "template.md").write_text("---\ntitle: T\n---\nx", encoding="utf-8")
    opts = load_post_options(posts)
    assert [o.slug for o in opts] == ["demo-post"]
    assert len(opts[0].opening) == 600
    p = build_prompt("SAMPLE", {"turns": 3}, opts, ["topic-a"], ["secretco"])
    for needle in ("demo-post", "A demo post", "topic-a", "secretco", "SAMPLE", '"turns": 3', "English"):
        assert needle in p
