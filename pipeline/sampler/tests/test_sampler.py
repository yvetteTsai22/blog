from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone

from sampler import build_sample, enforce_cap, extract_features, is_empty, load_session, session_files, tok
from sampler.__main__ import main
from sampler.features import active_minutes
from sampler.sample import ANSWER_MAX, PROMPT_MAX, Item


def rules(items):
    return [it.rule for it in items]


# --- loading ---------------------------------------------------------------

def test_load_skips_bad_lines_and_reads_title(tx, proj):
    s = load_session(tx.title("Demo").user("hi").say("hello").write(proj / "abc.jsonl"))
    assert (s.session_id, s.project, s.title, s.turns) == ("abc", "-tmp-demo-project", "Demo", 2)


def test_session_files_excludes_subagents(tx, proj):
    tx.user("x").write(proj / "main.jsonl")
    tx.write(proj / "subagents" / "agent-1.jsonl")
    tx.write(proj / "main" / "subagents" / "agent-2.jsonl")
    assert [p.name for p in session_files(proj.parent)] == ["main.jsonl"]


# --- empty check -----------------------------------------------------------

def test_empty_one_prompt_no_tools(tx, proj):
    assert is_empty(load_session(tx.user("hi").say("hello").write(proj / "a.jsonl")))


def test_noise_prompts_do_not_count(tx, proj):
    tx.user("<command-name>/clear</command-name>").user("<task-notification>x").user("real one")
    tx.user("Base directory for this skill: /x").user("meta prompt", meta=True)
    assert is_empty(load_session(tx.write(proj / "a.jsonl")))


def test_not_empty_two_prompts(tx, proj):
    assert not is_empty(load_session(tx.user("a").say("b").user("c").write(proj / "a.jsonl")))


def test_not_empty_with_tool_call(tx, proj):
    assert not is_empty(load_session(tx.user("a").tool("Bash", {"command": "ls"}).write(proj / "a.jsonl")))


# --- features --------------------------------------------------------------

def test_active_minutes_caps_gaps_at_five_minutes():
    t = datetime(2026, 1, 1, tzinfo=timezone.utc)
    stamps = [t, t + timedelta(minutes=2), t + timedelta(minutes=62), t + timedelta(minutes=63)]
    assert active_minutes(stamps) == 2 + 5 + 1
    assert active_minutes([]) == 0
    assert active_minutes([t]) == 0


def test_features(tx, proj):
    tx.user("fix it")
    for _ in range(3):
        tx.tool("Edit", {"file_path": "/a.py", "old_string": "x", "new_string": "y"})
    tx.tool("Edit", {"file_path": "/b.py", "old_string": "x", "new_string": "y"})
    tx.tool("Bash", {"command": "pytest"}, result="1 failed", error=True)
    tx.tool("Bash", {"command": "pytest -x"})
    tx.tool("Read", {"file_path": "/c"}, result="file missing", error=True)  # no retry follows
    tx.tool("Write", {"file_path": "/d"}, result="The user doesn't want to proceed", error=True)
    tx.tool("Write", {"file_path": "/d"})
    tx.user("thanks", gap=3600).say("done")
    path = tx.write(proj / "s.jsonl")
    now = datetime.now(timezone.utc)
    f = extract_features(load_session(path), days=7, now=now)
    assert f.tool_calls == 9
    assert f.real_prompts == 2
    assert f.max_edits_one_file == 3
    assert f.retries_after_failure == 1  # permission denial excluded; Read has no retry
    assert f.project_days == 1
    assert f.turns == len(tx.lines)
    assert 0 < f.active_minutes < 10


def test_project_days_counts_distinct_recent_dates(tx, proj):
    now = datetime(2026, 3, 10, 12, tzinfo=timezone.utc)
    for name, days_ago in (("a", 0), ("b", 0), ("c", 2), ("d", 20)):
        p = tx.write(proj / f"{name}.jsonl")
        ts = (now - timedelta(days=days_ago)).timestamp()
        os.utime(p, (ts, ts))
    s = load_session(proj / "a.jsonl")
    assert extract_features(s, days=7, now=now).project_days == 2
    assert extract_features(s, days=30, now=now).project_days == 3


# --- targeted sample -------------------------------------------------------

def test_sample_rules_and_order(tx, proj):
    tx.user("first ask").say("thinking").say("answer one")
    tx.tool("Bash", {"command": "make"}, result="boom", error=True)
    tx.tool("Bash", {"command": "make -B"})
    tx.user("second ask").say("t1").say("t2").say("t3")
    items = build_sample(load_session(tx.write(proj / "s.jsonl")))
    texts = {(it.rule, it.text) for it in items}
    assert ("R1 prompt", "first ask") in texts and ("R1 prompt", "second ask") in texts
    assert ("R5 answer", "answer one") in texts
    assert any(r == "R3 fail" and "boom" in t for r, t in texts)
    assert any(r == "R3 retry" and "make -B" in t for r, t in texts)
    assert [it.text for it in items if it.rule == "R4 tail"] == ["t1", "t2", "t3"]
    assert [it.order for it in items] == sorted(it.order for it in items)


def test_r5_only_for_later_prompts_and_dedup(tx, proj):
    tx.say("pre").user("p1").say("a1").user("p2").say("a2")
    items = build_sample(load_session(tx.write(proj / "s.jsonl")))
    assert [it.text for it in items if it.rule == "R5 answer"] == ["a1"]
    # a1 is both R5 and R4 with same text at same order: kept once
    assert sum(1 for it in items if it.text == "a1") == 1


def test_clips(tx, proj):
    tx.user("p" * 5000).say("a" * 5000).user("q")
    tx.tool("Grep", {"pattern": "z" * 2000}, result="e" * 5000, error=True)
    tx.say("tail " * 1000)
    items = build_sample(load_session(tx.write(proj / "s.jsonl")))
    by = {it.rule: it.text for it in items}
    marker = len(" …[clip]… ")
    assert len(by["R1 prompt"]) <= PROMPT_MAX + marker
    assert len(by["R5 answer"]) <= ANSWER_MAX + marker
    assert all(len(it.text) <= ANSWER_MAX + marker for it in items if it.rule == "R4 tail")
    fail = by["R3 fail"]
    tool_part, err_part = fail.split(" → ")
    assert len(tool_part) <= len("Grep ") + 300 + marker
    assert len(err_part) <= 400 + marker


def test_cjk_token_estimate():
    assert tok("abcd" * 10) == 10
    assert tok("中文字") == 3


# --- cap -------------------------------------------------------------------

def _items(spec):
    return [Item(i, r, "x" * (4 * n)) for i, (r, n) in enumerate(spec)]


def test_cap_untouched_when_under():
    items = _items([("R1 prompt", 10), ("R4 tail", 10)])
    assert enforce_cap(items, 100) == items


def test_cap_cut_order_retries_then_middle_answers():
    items = _items([("R1 prompt", 10), ("R3 retry", 50), ("R5 answer", 10), ("R5 answer", 10),
                    ("R5 answer", 10), ("R4 tail", 10)])
    out = enforce_cap(items, 45)
    assert "R3 retry" not in rules(out)
    assert [it.order for it in out if it.rule == "R5 answer"] == [2, 4]  # middle dropped first


def test_cap_keeps_first_and_last_prompt_then_cuts_failures_then_tail():
    items = _items([("R1 prompt", 10), ("R1 prompt", 10), ("R1 prompt", 10), ("R3 fail", 10),
                    ("R1 prompt", 10), ("R4 tail", 10), ("R4 tail", 10)])
    out = enforce_cap(items, 35)
    assert [it.order for it in out if it.rule == "R1 prompt"] == [0, 4]
    assert "R3 fail" not in rules(out)
    assert sum(tok(it.text) for it in out) <= 35
    assert rules(out).count("R4 tail") == 1  # final turns cut last
    assert items[0].rule == "R1 prompt" and len(items) == 7  # input not mutated


# --- CLI -------------------------------------------------------------------

def test_cli_stats_and_render(tx, proj, capsys):
    path = tx.user("alpha ask").tool("Bash", {"command": "ls"}).user("beta ask").say("gamma reply").write(proj / "s1.jsonl")
    assert main(["--stats", str(path)]) == 0
    row = json.loads(capsys.readouterr().out)
    assert row["session_id"] == "s1" and row["empty"] is False and row["tool_calls"] == 1
    assert row["capped_tok"] == row["raw_tok"] > 0
    assert main(["s1", "--projects-dir", str(proj.parent)]) == 0
    assert "[R1 prompt] alpha ask" in capsys.readouterr().out


def test_cli_empty_and_missing(tx, proj, capsys):
    path = tx.user("only").write(proj / "e.jsonl")
    assert main([str(path)]) == 0
    assert "empty" in capsys.readouterr().out
    assert main(["nope", "--projects-dir", str(proj.parent)]) == 2
