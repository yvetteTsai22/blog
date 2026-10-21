"""Spec §1.4 step 5: close the previous drafting session only if it is idle.

Idle means Orca reports the agent pane's state as `done`. Any other state (working, waiting,
blocked, unknown) leaves the session open. This module never touches git: no commit, no stash.
"""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Callable

IDLE_STATES = frozenset({"done"})
ORCA_TIMEOUT = 30

Runner = Callable[[list[str]], str]


@dataclass(frozen=True)
class Pane:
    pane_key: str          # "<tabId>:<leafId>"
    state: str
    handle: str = ""       # terminal handle, when a live terminal matches the pane


@dataclass(frozen=True)
class Decision:
    pane: Pane
    action: str            # "close" | "keep"
    reason: str


def run_orca(args: list[str]) -> str:
    out = subprocess.run(
        ["orca", *args], capture_output=True, text=True, check=True, timeout=ORCA_TIMEOUT
    )
    return out.stdout


def _result(raw: str) -> dict:
    data = json.loads(raw)
    if not data.get("ok", False):
        raise RuntimeError("orca call returned ok=false")
    return data.get("result") or {}


def worktree_agents(ps_raw: str, worktree_path: str) -> list[tuple[str, str]]:
    """(pane_key, state) for every agent pane Orca tracks in the worktree."""
    for wt in _result(ps_raw).get("worktrees") or []:
        if os.path.realpath(wt.get("path") or "") == os.path.realpath(worktree_path):
            return [(a.get("paneKey") or "", a.get("state") or "") for a in wt.get("agents") or []]
    return []


def terminal_handles(list_raw: str) -> dict[str, str]:
    """pane_key -> terminal handle for live terminals."""
    out = {}
    for t in _result(list_raw).get("terminals") or []:
        if t.get("tabId") and t.get("leafId") and t.get("handle"):
            out[f"{t['tabId']}:{t['leafId']}"] = t["handle"]
    return out


def decide(agents: list[tuple[str, str]], handles: dict[str, str], self_pane: str) -> list[Decision]:
    decisions = []
    for key, state in agents:
        pane = Pane(key, state, handles.get(key, ""))
        if key == self_pane:
            decisions.append(Decision(pane, "keep", "this session"))
        elif not pane.handle:
            decisions.append(Decision(pane, "keep", "no live terminal"))
        elif state in IDLE_STATES:
            decisions.append(Decision(pane, "close", f"idle ({state})"))
        else:
            decisions.append(Decision(pane, "keep", f"not idle ({state or 'unknown'})"))
    return decisions


def close_previous(worktree_path: str, dry_run: bool = False, run: Runner = run_orca,
                   self_pane: str | None = None) -> list[Decision]:
    self_pane = os.environ.get("ORCA_PANE_KEY", "") if self_pane is None else self_pane
    agents = worktree_agents(run(["worktree", "ps", "--json"]), worktree_path)
    handles = terminal_handles(run(["terminal", "list", "--worktree", f"path:{worktree_path}", "--json"]))
    decisions = decide(agents, handles, self_pane)
    if not dry_run:
        for d in decisions:
            if d.action == "close":
                run(["terminal", "close", "--terminal", d.pane.handle, "--json"])
    return decisions


def describe(decisions: list[Decision], dry_run: bool) -> list[str]:
    if not decisions:
        return ["previous drafting session: none"]
    verb = "would close" if dry_run else "closed"
    return [
        f"previous drafting session {d.pane.handle or d.pane.pane_key}: "
        f"{verb if d.action == 'close' else 'kept'} — {d.reason}"
        for d in decisions
    ]
