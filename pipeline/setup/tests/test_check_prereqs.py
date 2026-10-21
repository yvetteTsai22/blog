import json
import subprocess

from common.config import Config
from setup import check_prereqs as cp


def fake_runner(returncode=0, stdout=""):
    calls = []

    def run(cmd, **kw):
        calls.append((cmd, kw))
        return subprocess.CompletedProcess(cmd, returncode, stdout=stdout, stderr="")

    run.calls = calls
    return run


def test_cleanup_period(tmp_path):
    s = tmp_path / "settings.json"
    s.write_text(json.dumps({"cleanupPeriodDays": 45}))
    assert cp.check_cleanup_period(s).ok
    s.write_text(json.dumps({"cleanupPeriodDays": 14}))
    assert not cp.check_cleanup_period(s).ok
    s.write_text("{}")
    assert not cp.check_cleanup_period(s).ok
    assert not cp.check_cleanup_period(tmp_path / "missing.json").ok


def test_orca_repo(tmp_path):
    out = f"id1  other  /x/y\nid2  blog  {tmp_path.resolve()}\n"
    assert cp.check_orca_repo(fake_runner(stdout=out), tmp_path).ok
    assert not cp.check_orca_repo(fake_runner(stdout="id  o  /x\n"), tmp_path).ok
    assert not cp.check_orca_repo(fake_runner(returncode=1), tmp_path).ok


def test_telegram_never_prints_values(tmp_path):
    cfg = Config(local={"telegram": {"bot_token": "SECRET1", "chat_id": "SECRET2"}}, local_path=tmp_path)
    r = cp.check_telegram(cfg)
    assert r.ok and "SECRET" not in cp.format_result(r)
    empty = Config(local={"telegram": {"bot_token": "", "chat_id": ""}}, local_path=tmp_path)
    assert not cp.check_telegram(empty).ok
    assert not cp.check_telegram(Config()).ok


def test_jev_key_presence_only(tmp_path):
    r = cp.check_jev_key(Config(env={"JEV_API": "SECRET"}, env_path=tmp_path / ".env"))
    assert r.ok and "SECRET" not in cp.format_result(r)
    assert not cp.check_jev_key(Config(env={"JEV_API": ""}, env_path=tmp_path / ".env")).ok
    assert not cp.check_jev_key(Config()).ok


def test_env_untracked(tmp_path):
    cfg = Config(env_path=tmp_path / ".env")
    assert cp.check_env_untracked(cfg, fake_runner(returncode=1)).ok
    assert not cp.check_env_untracked(cfg, fake_runner(returncode=0)).ok
    assert not cp.check_env_untracked(Config(), fake_runner()).ok


def test_gitignored(tmp_path):
    all_out = "\n".join(cp.GITIGNORED_FILES)
    assert cp.check_gitignored(tmp_path, fake_runner(stdout=all_out)).ok
    r = cp.check_gitignored(tmp_path, fake_runner(returncode=1, stdout=".env\n"))
    assert not r.ok and "pipeline.local.yml" in r.detail


def test_claude_cli_version_and_live():
    assert cp.check_claude_cli(fake_runner(stdout="2.0.0"), live=False).ok
    live = fake_runner(stdout=json.dumps({"result": "OK.", "is_error": False}))
    assert cp.check_claude_cli(live, live=True).ok
    assert "ANTHROPIC_API_KEY" not in live.calls[0][1]["env"]
    assert "haiku" in live.calls[0][0]
    assert not cp.check_claude_cli(fake_runner(stdout="nope"), live=True).ok
    assert not cp.check_claude_cli(fake_runner(stdout=json.dumps({"result": "OK", "is_error": True})), live=True).ok


def test_runner_errors_become_fail():
    def boom(cmd, **kw):
        raise FileNotFoundError

    assert not cp.check_orca_repo(boom).ok
    assert not cp.check_claude_cli(boom).ok


def test_main_exit_code(monkeypatch, capsys):
    monkeypatch.setattr(cp, "run_checks", lambda live: [cp.Result("a", True, "x"), cp.Result("b", False, "y")])
    assert cp.main([]) == 1
    out = capsys.readouterr().out
    assert "PASS  a: x" in out and "FAIL  b: y" in out
