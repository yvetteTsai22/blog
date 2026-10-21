"""Load `market-signals.local.yml` (spec §4.1). Gitignored; holds the hand-written denylist.

Defaults below are the spec's public seed values. They are used for any section the local
file leaves out, so a missing file still gives a working (feeds-only) setup. Denylist
entries never have a default and are never logged.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from common import paths
from common.config import load_yaml_file

DEFAULT_FEEDS: tuple[dict, ...] = (
    {"name": "hn_front_page", "type": "hn", "tags": "front_page"},
    {"name": "hn_ask_hn", "type": "hn", "tags": "ask_hn", "help": True},
    {"name": "r_claudeai", "type": "rss", "url": "https://www.reddit.com/r/ClaudeAI/.rss"},
    {"name": "r_localllama", "type": "rss", "url": "https://www.reddit.com/r/LocalLLaMA/.rss"},
    {"name": "r_chatgptcoding", "type": "rss", "url": "https://www.reddit.com/r/ChatGPTCoding/.rss"},
    {"name": "devto", "type": "devto", "tags": ["ai", "claudecode", "llm", "devtools"]},
    {"name": "cursor_help", "type": "discourse", "url": "https://forum.cursor.com/c/help/5.json", "help": True},
    {"name": "openai_help", "type": "discourse",
     "url": "https://community.openai.com/c/api/help/27.json", "help": True},
    {"name": "ithome", "type": "rss", "url": "https://www.ithome.com.tw/rss"},
    {"name": "simonwillison", "type": "rss", "url": "https://simonwillison.net/atom/everything/"},
    {"name": "latent_space", "type": "rss", "url": "https://www.latent.space/feed"},
    {"name": "watchlist_issues", "type": "github_issues"},
)

DEFAULT_WATCHLIST: tuple[str, ...] = (
    "anthropics/claude-code",
    "openai/codex",
    "google-gemini/gemini-cli",
    "modelcontextprotocol/servers",
    "modelcontextprotocol/typescript-sdk",
    "electron/electron",
    "microsoft/playwright",
    "jekyll/jekyll",
    "stablyai/orca",
)

DEFAULT_WHITELIST: tuple[str, ...] = (
    "claude code hooks",
    "mcp",
    "git worktree",
    "electron",
    "subagent",
    "prompt caching",
    "codex cli",
    "jekyll",
    "rate limit",
    "agent workflow",
)

DEFAULT_MODEL = "intfloat/multilingual-e5-small"


@dataclass(frozen=True)
class MarketConfig:
    feeds: tuple[Mapping[str, Any], ...] = DEFAULT_FEEDS
    watchlist: tuple[str, ...] = DEFAULT_WATCHLIST
    whitelist: tuple[str, ...] = DEFAULT_WHITELIST
    denylist: tuple[str, ...] = field(default=(), repr=False)
    lookback_days: int = 30
    match_threshold: float = 0.83  # provisional (spec §4.3)
    embedding_model: str = DEFAULT_MODEL
    keychain_service: str = "blog-pipeline-github"
    timeout_s: float = 15.0
    github_per_minute: int = 30
    pool_days: int = 14
    candidate_weekday: int = 0  # Monday; the weekly candidate line (spec §1.5)
    path: Path | None = None

    def __repr__(self) -> str:  # never show denylist entries
        return f"MarketConfig(path={self.path}, feeds={len(self.feeds)}, watchlist={len(self.watchlist)})"


def _strings(value) -> tuple[str, ...]:
    return tuple(str(v).strip() for v in value or () if str(v).strip())


def from_mapping(data: Mapping[str, Any], path: Path | None = None) -> MarketConfig:
    base = MarketConfig()
    settings = data.get("settings") or {}
    return MarketConfig(
        feeds=tuple(data.get("feeds") or base.feeds),
        watchlist=_strings(data.get("watchlist")) or base.watchlist,
        whitelist=_strings(data.get("whitelist")) or base.whitelist,
        denylist=_strings(data.get("denylist")),
        lookback_days=int(settings.get("lookback_days", base.lookback_days)),
        match_threshold=float(settings.get("match_threshold", base.match_threshold)),
        embedding_model=str(settings.get("embedding_model", base.embedding_model)),
        keychain_service=str(settings.get("keychain_service", base.keychain_service) or ""),
        timeout_s=float(settings.get("timeout_s", base.timeout_s)),
        github_per_minute=int(settings.get("github_per_minute", base.github_per_minute)),
        pool_days=int(settings.get("pool_days", base.pool_days)),
        candidate_weekday=int(settings.get("candidate_weekday", base.candidate_weekday)),
        path=path,
    )


def load(path: Path | None = None) -> MarketConfig:
    path = path or paths.find_local_file(paths.MARKET_SIGNALS_LOCAL_FILE)
    return from_mapping(load_yaml_file(path), path)
