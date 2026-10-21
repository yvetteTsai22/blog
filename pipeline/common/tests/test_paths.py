from pathlib import Path

from common import paths


def test_state_dir_default():
    assert paths.state_dir({}) == Path("~/.local/state/blog-pipeline").expanduser()


def test_state_dir_override_and_queue(tmp_path):
    env = {paths.STATE_DIR_ENV: str(tmp_path)}
    assert paths.state_dir(env) == tmp_path
    assert paths.pending_queue_path(env) == tmp_path / "pending-queue.txt"


def test_empty_override_uses_default():
    assert paths.state_dir({paths.STATE_DIR_ENV: ""}) == paths.state_dir({})


def test_repo_root_contains_pipeline():
    assert (paths.REPO_ROOT / "pipeline" / "pyproject.toml").is_file()


def test_main_checkout_root_non_git_dir_falls_back(tmp_path):
    assert paths.main_checkout_root(tmp_path) == tmp_path


def test_local_file_candidates_dedupes_same_root(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "main_checkout_root", lambda root: tmp_path)
    assert paths.local_file_candidates(".env", tmp_path) == [tmp_path / ".env"]
    assert paths.find_local_file(".env", tmp_path) is None
