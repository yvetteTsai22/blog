"""Load local secrets and config: ``.env`` plus ``pipeline.local.yml``.

Both files are gitignored. Values are never logged; callers that report on
them should use :meth:`Config.has` rather than printing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

import yaml

from common import paths


class ConfigError(Exception):
    """A local config file exists but cannot be parsed."""


def parse_env(text: str) -> dict[str, str]:
    """Parse dotenv text: KEY=VALUE lines, optional `export`, quotes, # comments."""
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].lstrip()
        key, sep, value = line.partition("=")
        key = key.strip()
        if not sep or not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        elif " #" in value:
            value = value.split(" #", 1)[0].rstrip()
        result[key] = value
    return result


def load_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.is_file():
        return {}
    return parse_env(path.read_text(encoding="utf-8"))


def load_yaml_file(path: Path | None) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path.name} is not valid YAML: {exc.__class__.__name__}") from None
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name} must be a mapping at the top level")
    return data


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    return value


@dataclass(frozen=True)
class Config:
    env: Mapping[str, str] = field(default_factory=dict)
    local: Mapping[str, Any] = field(default_factory=dict)
    env_path: Path | None = None
    local_path: Path | None = None

    def get(self, dotted: str, default: Any = None) -> Any:
        """Look up `a.b.c` in pipeline.local.yml."""
        node: Any = self.local
        for part in dotted.split("."):
            if not isinstance(node, Mapping) or part not in node:
                return default
            node = node[part]
        return node

    def env_value(self, key: str, default: str | None = None) -> str | None:
        return self.env.get(key, default)

    def has(self, dotted_or_env_key: str) -> bool:
        """True when the key is set to a non-empty value (env first, then yml)."""
        value = self.env.get(dotted_or_env_key)
        if value is None:
            value = self.get(dotted_or_env_key)
        return value not in (None, "")


def load_config(
    repo_root: Path = paths.REPO_ROOT,
    env_path: Path | None = None,
    local_path: Path | None = None,
) -> Config:
    """Load config, searching this worktree then the main checkout for each file."""
    env_path = env_path or paths.find_local_file(paths.ENV_FILE, repo_root)
    local_path = local_path or paths.find_local_file(paths.PIPELINE_LOCAL_FILE, repo_root)
    return Config(
        env=_freeze(load_env_file(env_path)),
        local=_freeze(load_yaml_file(local_path)),
        env_path=env_path,
        local_path=local_path,
    )
