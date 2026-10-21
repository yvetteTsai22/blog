"""Wrapper and precheck scripts for the 02:00 / 04:00 automations (TSA-64)."""
from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
RUN = HERE / "run_batch.sh"
HAS_WORK = HERE / "has_work.sh"
PIPELINE_DIR = HERE.parent.parent


def fake_uv(tmp_path: Path, exit_code: int) -> Path:
    script = tmp_path / "uv"
    script.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "$PWD|$*" >> "{tmp_path}/calls"\n'
        f"exit {exit_code}\n"
    )
    script.chmod(0o755)
    return script


def run(script: Path, tmp_path: Path, *args: str, **env: str) -> subprocess.CompletedProcess:
    full_env = {**os.environ, "BLOG_PIPELINE_STATE_DIR": str(tmp_path / "state"), **env}
    return subprocess.run([str(script), *args], capture_output=True, text=True, env=full_env)


def test_run_batch_calls_batch_run_in_pipeline_dir(tmp_path):
    uv = fake_uv(tmp_path, 0)
    proc = run(RUN, tmp_path, "02:00", UV_BIN=str(uv))
    assert proc.returncode == 0
    assert (tmp_path / "calls").read_text().strip() == f"{PIPELINE_DIR}|run python -m batch run"
    log = (tmp_path / "state" / "batch.log").read_text()
    assert "automation 02:00 start" in log and "automation 02:00 exit 0" in log
    assert proc.stdout.strip() == "batch 02:00 exit 0"


def test_run_batch_propagates_failure(tmp_path):
    uv = fake_uv(tmp_path, 3)
    proc = run(RUN, tmp_path, "04:00", UV_BIN=str(uv))
    assert proc.returncode == 3
    assert "automation 04:00 exit 3" in (tmp_path / "state" / "batch.log").read_text()


def fake_uv_sleeping(tmp_path: Path) -> Path:
    script = tmp_path / "uv"
    script.write_text("#!/usr/bin/env bash\nexec sleep 30\n")
    script.chmod(0o755)
    return script


def test_run_batch_logs_exit_when_killed(tmp_path):
    uv = fake_uv_sleeping(tmp_path)
    env = {**os.environ, "BLOG_PIPELINE_STATE_DIR": str(tmp_path / "state"), "UV_BIN": str(uv)}
    proc = subprocess.Popen([str(RUN), "02:00"], env=env, stdout=subprocess.PIPE, text=True)
    log = tmp_path / "state" / "batch.log"
    deadline = time.time() + 10
    while time.time() < deadline and "start" not in (log.read_text() if log.exists() else ""):
        time.sleep(0.05)
    time.sleep(0.2)
    proc.send_signal(signal.SIGTERM)
    out, _ = proc.communicate(timeout=10)
    assert proc.returncode == 143
    assert "automation 02:00 exit 143 (SIGTERM)" in log.read_text()
    assert out.strip().endswith("batch 02:00 exit 143")
    assert not (tmp_path / "state" / "batch-02:00.running").exists()


def test_wait_reports_finished_run(tmp_path):
    uv = fake_uv(tmp_path, 3)
    run(RUN, tmp_path, "02:00", UV_BIN=str(uv))
    proc = run(RUN, tmp_path, "02:00", "wait")
    assert proc.returncode == 3
    assert proc.stdout.strip() == "batch 02:00 exit 3"


def test_wait_times_out_while_running(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "batch-02:00.running").write_text(f"{os.getpid()}\n")
    proc = run(RUN, tmp_path, "02:00", "wait", WAIT_SECONDS="1", WAIT_POLL_SECONDS="0.2")
    assert proc.returncode == 75
    assert proc.stdout.strip() == "batch 02:00 still running"


def test_wait_detects_dead_run(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    (state / "batch-02:00.running").write_text("999999\n")
    proc = run(RUN, tmp_path, "02:00", "wait")
    assert proc.returncode == 1
    assert "died without an exit line" in proc.stdout


def test_wait_without_run(tmp_path):
    assert run(RUN, tmp_path, "04:00", "wait").returncode == 2


INLINE = (HERE / "precheck.inline").read_text().strip()


def precheck(kind: str, state: Path, cwd: Path) -> int:
    env = {**os.environ, "BLOG_PIPELINE_STATE_DIR": str(state)}
    if kind == "script":
        return subprocess.run([str(HAS_WORK)], env=env, cwd=cwd).returncode
    # Orca runs the precheck with spawn(command, {shell: true}) i.e. /bin/sh -c.
    return subprocess.run(["/bin/sh", "-c", INLINE], env=env, cwd=cwd).returncode


KINDS = pytest.mark.parametrize("kind", ["script", "inline"])


@KINDS
def test_has_work_fails_open_when_state_dir_missing(kind, tmp_path):
    assert precheck(kind, tmp_path / "missing", tmp_path) == 0


@KINDS
def test_has_work_false_for_empty_state_dir(kind, tmp_path):
    assert precheck(kind, tmp_path, tmp_path) == 1


@KINDS
def test_has_work_false_for_blank_queue_and_empty_outbox(kind, tmp_path):
    (tmp_path / "outbox").mkdir()
    (tmp_path / "pending-queue.txt").write_text("\n  \n")
    assert precheck(kind, tmp_path, tmp_path) == 1


@KINDS
def test_has_work_true_for_queued_session(kind, tmp_path):
    (tmp_path / "pending-queue.txt").write_text("00000000-0000-0000-0000-000000000001\n")
    assert precheck(kind, tmp_path, tmp_path) == 0


@KINDS
def test_has_work_true_for_staged_note(kind, tmp_path):
    (tmp_path / "outbox").mkdir()
    (tmp_path / "outbox" / "00000000-0000-0000-0000-000000000002.json").write_text("{}")
    assert precheck(kind, tmp_path, tmp_path) == 0


@KINDS
def test_has_work_fails_open_on_unreadable_queue(kind, tmp_path):
    q = tmp_path / "pending-queue.txt"
    q.write_text("\n")
    q.chmod(0)
    try:
        assert precheck(kind, tmp_path, tmp_path) == 0
    finally:
        q.chmod(0o644)


@KINDS
def test_has_work_fails_open_when_outbox_is_not_a_dir(kind, tmp_path):
    (tmp_path / "outbox").write_text("")
    assert precheck(kind, tmp_path, tmp_path) == 0


def test_inline_precheck_has_no_worktree_path():
    assert "pipeline/" not in INLINE and "has_work" not in INLINE


def test_prompt_has_label_placeholder_and_runs_wrapper():
    text = (HERE / "prompt.md").read_text()
    assert "pipeline/automations/batch/run_batch.sh {{LABEL}}" in text
