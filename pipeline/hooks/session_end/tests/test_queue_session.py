import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "queue_session.py"
SID = "11111111-2222-3333-4444-555555555555"


def run_hook(payload, state_dir: Path) -> subprocess.CompletedProcess:
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    env = {**os.environ, "BLOG_PIPELINE_STATE_DIR": str(state_dir)}
    return subprocess.run(
        [sys.executable, str(SCRIPT)], input=raw, text=True,
        capture_output=True, env=env, timeout=10,
    )


def main_payload(sid=SID):
    return {
        "session_id": sid,
        "transcript_path": f"/home/user/.claude/projects/-home-user-demo/{sid}.jsonl",
        "cwd": "/home/user/demo",
        "hook_event_name": "SessionEnd",
        "reason": "other",
    }


def queue_lines(state: Path):
    return (state / "pending-queue.txt").read_text().splitlines()


def test_main_session_appends_exactly_one_line(tmp_path):
    state = tmp_path / "nested" / "state"  # dirs are created
    result = run_hook(main_payload(), state)
    assert result.returncode == 0
    assert queue_lines(state) == [SID]
    assert not (state / "hooks.log").exists()


def test_appends_without_clobbering_existing_queue(tmp_path):
    (tmp_path / "pending-queue.txt").write_text("existing-id\n")
    run_hook(main_payload(), tmp_path)
    run_hook(main_payload("second-id"), tmp_path)
    assert queue_lines(tmp_path) == ["existing-id", SID, "second-id"]


def test_subagent_session_is_skipped(tmp_path):
    payload = main_payload()
    payload["transcript_path"] = (
        f"/home/user/.claude/projects/-home-user-demo/{SID}/subagents/agent-abc.jsonl"
    )
    result = run_hook(payload, tmp_path)
    assert result.returncode == 0
    assert not (tmp_path / "pending-queue.txt").exists()


@pytest.mark.parametrize(
    "payload",
    [
        "not json",
        "",
        "[1, 2]",
        {"transcript_path": "/x.jsonl"},
        {"session_id": "evil\nsecond-line"},
        {"session_id": 42},
    ],
)
def test_bad_payload_logs_and_exits_zero(tmp_path, payload):
    result = run_hook(payload, tmp_path)
    assert result.returncode == 0
    assert not (tmp_path / "pending-queue.txt").exists()
    assert "error" in (tmp_path / "hooks.log").read_text()


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignores permissions")
def test_unwritable_state_dir_exits_zero(tmp_path):
    state = tmp_path / "locked"
    state.mkdir()
    state.chmod(stat.S_IRUSR | stat.S_IXUSR)
    try:
        result = run_hook(main_payload(), state)
    finally:
        state.chmod(stat.S_IRWXU)
    assert result.returncode == 0
    assert not (state / "pending-queue.txt").exists()
    assert "session_end hook" in result.stderr


def test_concurrent_appends_keep_one_line_each(tmp_path):
    env = {**os.environ, "BLOG_PIPELINE_STATE_DIR": str(tmp_path)}
    procs = [
        subprocess.Popen([sys.executable, str(SCRIPT)], stdin=subprocess.PIPE,
                         text=True, env=env)
        for _ in range(20)
    ]
    for i, p in enumerate(procs):
        p.communicate(json.dumps(main_payload(f"sid-{i}")), timeout=10)
    assert sorted(queue_lines(tmp_path)) == sorted(f"sid-{i}" for i in range(20))
