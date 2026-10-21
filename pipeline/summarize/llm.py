"""Headless `claude -p` call on the subscription (no API key), isolated from user hooks and MCP."""
from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass

DEFAULT_MODEL = "haiku"
DEFAULT_TIMEOUT = 300


class LLMError(RuntimeError):
    pass


@dataclass(frozen=True)
class LLMReply:
    text: str
    cost_usd: float | None


def claude_command(model: str) -> list[str]:
    # --setting-sources project from an empty temp cwd: no user settings, so no SessionEnd hook
    # re-queues this call; --no-session-persistence leaves no transcript; no tools, no MCP.
    return [
        "claude", "-p",
        "--model", model,
        "--output-format", "json",
        "--setting-sources", "project",
        "--no-session-persistence",
        "--strict-mcp-config",
        "--tools", "",
    ]


def run_claude(prompt: str, model: str = DEFAULT_MODEL, timeout: int = DEFAULT_TIMEOUT) -> LLMReply:
    with tempfile.TemporaryDirectory(prefix="blog-pipeline-llm-") as cwd:
        try:
            proc = subprocess.run(
                claude_command(model), input=prompt, capture_output=True, text=True,
                cwd=cwd, timeout=timeout,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise LLMError(f"claude -p failed to run: {exc.__class__.__name__}") from None
    if proc.returncode != 0:
        raise LLMError(f"claude -p exit {proc.returncode}: {proc.stderr.strip()[:300]}")
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return LLMReply(text=proc.stdout, cost_usd=None)
    if envelope.get("is_error"):
        raise LLMError(f"claude -p error: {str(envelope.get('result'))[:300]}")
    return LLMReply(text=str(envelope.get("result") or ""), cost_usd=envelope.get("total_cost_usd"))
