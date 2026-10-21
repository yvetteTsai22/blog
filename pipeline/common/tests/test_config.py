from pathlib import Path

import pytest

from common import paths
from common.config import Config, ConfigError, load_config, load_yaml_file, parse_env


def test_parse_env_handles_quotes_export_and_comments():
    text = '# c\nexport A=1\nB="two words"\nC=\'x\'\nD=val # trailing\nbad line\n=nokey\nE=\n'
    assert parse_env(text) == {"A": "1", "B": "two words", "C": "x", "D": "val", "E": ""}


def test_load_yaml_rejects_non_mapping(tmp_path):
    p = tmp_path / "pipeline.local.yml"
    p.write_text("- a\n- b\n")
    with pytest.raises(ConfigError):
        load_yaml_file(p)


def test_load_yaml_invalid_does_not_echo_content(tmp_path):
    p = tmp_path / "pipeline.local.yml"
    p.write_text("token: SECRETVALUE: [\n")
    with pytest.raises(ConfigError) as exc:
        load_yaml_file(p)
    assert "SECRETVALUE" not in str(exc.value)


def test_load_yaml_empty_file_is_empty_mapping(tmp_path):
    p = tmp_path / "x.yml"
    p.write_text("")
    assert load_yaml_file(p) == {}


def test_load_config_explicit_paths(tmp_path):
    env = tmp_path / ".env"
    env.write_text("JEV_API=abc\n")
    local = tmp_path / "pipeline.local.yml"
    local.write_text('telegram:\n  bot_token: "t"\n  chat_id: ""\n')
    cfg = load_config(repo_root=tmp_path, env_path=env, local_path=local)
    assert cfg.env_value("JEV_API") == "abc"
    assert cfg.get("telegram.bot_token") == "t"
    assert cfg.has("JEV_API")
    assert cfg.has("telegram.bot_token")
    assert not cfg.has("telegram.chat_id")
    assert not cfg.has("missing.key")
    assert cfg.get("telegram.bot_token.deeper", "d") == "d"


def test_config_is_immutable(tmp_path):
    local = tmp_path / "pipeline.local.yml"
    local.write_text("a:\n  b: [1, 2]\n")
    cfg = load_config(repo_root=tmp_path, env_path=tmp_path / "none", local_path=local)
    with pytest.raises(TypeError):
        cfg.local["a"]["b"] = 3  # type: ignore[index]
    assert cfg.get("a.b") == (1, 2)


def test_load_config_missing_files_gives_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, "main_checkout_root", lambda root=tmp_path: tmp_path)
    cfg = load_config(repo_root=tmp_path)
    assert cfg == Config()


def test_load_config_falls_back_to_main_checkout(tmp_path, monkeypatch):
    worktree, main = tmp_path / "wt", tmp_path / "main"
    worktree.mkdir()
    main.mkdir()
    (main / ".env").write_text("JEV_API=k\n")
    (worktree / "pipeline.local.yml").write_text("telegram: {chat_id: '1'}\n")
    (main / "pipeline.local.yml").write_text("telegram: {chat_id: 'main'}\n")
    monkeypatch.setattr(paths, "main_checkout_root", lambda root: main)
    cfg = load_config(repo_root=worktree)
    assert cfg.env_path == main / ".env"
    assert cfg.local_path == worktree / "pipeline.local.yml"
    assert cfg.get("telegram.chat_id") == "1"
