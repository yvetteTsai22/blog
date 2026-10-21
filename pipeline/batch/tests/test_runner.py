"""Runner, queue and step discovery with synthetic transcripts and a fake LLM."""
import json
import types
from datetime import datetime, timezone

import pytest

from batch import discovery
from batch.queue import read_queue, remove_ids
from batch.runner import Context, commit_written, stage_queue
from common.config import Config
from notes import Outbox
from sampler.tests.conftest import Transcript

NOW = datetime(2026, 1, 2, 3, 0, tzinfo=timezone.utc)
REPLY = json.dumps({
    "title": "A reusable lesson", "request": "r", "investigated": "i", "learned": "l",
    "completed": "c", "next_steps": "n", "notes": "", "files_read": [], "files_edited": [],
    "generality": "general", "p_trap": 0.7, "p_insight": 0.1, "p_pattern": 0.1,
    "dup_of": "none", "dup_of_confidence": 0, "topic_of": "new", "privacy_flag": False,
    "privacy_reason": "", "reader_questions": [], "phrases": ["a b", "c d"],
    "domain_repo": "none", "origin": "personal",
})


def busy(path):
    return (Transcript().title("t").user("do the thing").tool("Bash", {"command": "ls"})
            .say("done").user("thanks").write(path))


@pytest.fixture
def env(tmp_path):
    projects = tmp_path / "projects"
    state = tmp_path / "state"
    state.mkdir()
    busy(projects / "-p-demo" / "s-busy.jsonl")
    Transcript().user("hi").say("hello").write(projects / "-p-demo" / "s-empty.jsonl")
    busy(projects / "-p-clientco-app" / "s-client.jsonl")
    calls = []

    def llm(prompt, model):
        calls.append(prompt)
        return REPLY

    ctx = Context(state_dir=state, config=Config(), now=NOW, projects_dir=projects,
                  posts_dir=tmp_path / "none", client_projects=("clientco",), llm=llm)
    return ctx, calls


def write_queue(ctx, ids):
    (ctx.state_dir / "pending-queue.txt").write_text("".join(f"{i}\n" for i in ids))


def test_queue_read_dedupes_and_remove_keeps_order(tmp_path):
    q = tmp_path / "q.txt"
    q.write_text("a\nb\n\na\nc\n")
    assert read_queue(q) == ["a", "b", "c"]
    remove_ids(q, ["b"])
    assert q.read_text() == "a\na\nc\n"


def test_stage_then_rerun_does_not_duplicate(env):
    ctx, calls = env
    write_queue(ctx, ["s-busy", "s-empty", "s-missing", "s-client"])
    st = stage_queue(ctx)
    assert st["staged"] == ["s-busy", "s-client"]
    assert st["empty"] == ["s-empty"] and st["missing"] == ["s-missing"]
    assert st["queue_length"] == 4
    assert read_queue(ctx.state_dir / "pending-queue.txt") == ["s-busy", "s-client"]
    assert "clientco" in calls[1]  # never-mention list passed for client project
    outbox = Outbox(ctx.state_dir)
    staged = {r["session_id"]: r for r in outbox.pending()}
    assert staged["s-client"]["origin"] == "client"
    assert staged["s-busy"]["topic_of"].startswith("a-reusable-lesson-")

    st2 = stage_queue(ctx)  # rerun before write: nothing re-summarised
    assert st2["already_staged"] == ["s-busy", "s-client"] and len(calls) == 2

    commit_written(ctx, "s-busy", "page-1")
    assert read_queue(ctx.state_dir / "pending-queue.txt") == ["s-client"]
    write_queue(ctx, ["s-busy", "s-client"])  # hook re-queued it
    st3 = stage_queue(ctx)
    assert st3["already_written"] == ["s-busy"] and len(calls) == 2
    assert read_queue(ctx.state_dir / "pending-queue.txt") == ["s-client"]
    status = json.loads((ctx.state_dir / "batch-status.json").read_text())
    assert status["queue_length"] == 2


def test_cap_defers(env):
    ctx, calls = env
    ctx.max_notes = 1
    write_queue(ctx, ["s-busy", "s-client"])
    st = stage_queue(ctx)
    assert st["staged"] == ["s-busy"] and st["deferred_by_cap"] == 1


def test_llm_failure_leaves_session_queued(env):
    ctx, _ = env
    ctx.llm = lambda p, m: "not json"
    write_queue(ctx, ["s-busy"])
    st = stage_queue(ctx)
    assert st["failed"] == ["s-busy"]
    assert read_queue(ctx.state_dir / "pending-queue.txt") == ["s-busy"]


def test_discovery_and_steps(env, monkeypatch):
    ctx, _ = env
    seen = []
    sess = types.SimpleNamespace(KIND="session", ORDER=5, NAME="jev",
                                 run=lambda c, s, r: {**r, "extra_properties": {"jev_p_trap": 0.4}})
    boom = types.SimpleNamespace(KIND="session", ORDER=9, NAME="boom", run=lambda c, s, r: 1 / 0)
    night = types.SimpleNamespace(KIND="nightly", NAME="night", run=lambda c, status: seen.append(status["cycle"]))
    steps = {"session": [discovery._as_step(sess), discovery._as_step(boom)],
             "nightly": [discovery._as_step(night)]}
    monkeypatch.setattr("batch.runner.discover", lambda: steps)
    write_queue(ctx, ["s-busy"])
    stage_queue(ctx)
    [rec] = Outbox(ctx.state_dir).pending()
    assert rec["notion"]["properties"]["jev_p_trap"] == 0.4
    assert seen == [ctx.cycle]


def test_discover_real_package_is_clean():
    found = discovery.discover()
    assert set(found) == {"session", "nightly"}
    assert discovery._as_step(types.SimpleNamespace(KIND="bogus", run=print)) is None
