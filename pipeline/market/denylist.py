"""Denylist build (spec §4.2), rebuilt on every batch run. The denylist always wins.

Entries are client-derived. They are held in memory only: never logged, printed or
written anywhere. Callers report `len(denylist)` at most.
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from common.config import parse_env

MIN_TERM_LEN = 3
# Path segments of ~/.claude/projects/<slug> that never identify a client.
GENERIC_SEGMENTS = frozenset({
    "users", "home", "projects", "project", "orca", "workspaces", "workspace", "worktrees",
    "worktree", "code", "src", "repos", "repo", "work", "dev", "github", "claude", "main",
})
DOMAIN_RE = re.compile(r"\b((?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,})\b", re.I)
PUBLIC_DOMAINS = frozenset({"localhost", "github.com", "api.github.com", "googleapis.com", "notion.so"})


@dataclass(frozen=True)
class Denylist:
    terms: frozenset[str]

    def __len__(self) -> int:
        return len(self.terms)

    def __repr__(self) -> str:
        return f"Denylist(<{len(self.terms)} terms>)"

    def blocks(self, text: str) -> bool:
        """True when any term occurs in `text` (case-insensitive) or `text` occurs in a term."""
        t = (text or "").lower().strip()
        if not t:
            return False
        return any(term in t or t in term for term in self.terms)


def _norm(values: Iterable[str]) -> set[str]:
    return {v.strip().lower() for v in values if v and len(v.strip()) >= MIN_TERM_LEN}


def private_repo_names(run: Callable = subprocess.run, timeout: float = 30) -> set[str]:
    """Owner and name of every private repo visible to `gh`. Empty on any failure."""
    try:
        out = run(
            ["gh", "repo", "list", "--visibility", "private", "--limit", "1000",
             "--json", "nameWithOwner", "--jq", ".[].nameWithOwner"],
            capture_output=True, text=True, timeout=timeout, check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    names = set()
    for line in out.splitlines():
        line = line.strip()
        if line:
            names.add(line)
            names.add(line.rsplit("/", 1)[-1])
    return names


def client_dir_terms(projects_dir: Path, client_projects: Iterable[str], home: Path | None = None) -> set[str]:
    """Names from ~/.claude/projects/<slug> dirs that match a client project substring."""
    markers = [c.lower() for c in client_projects if c]
    terms = set(markers)
    if not markers or not projects_dir.is_dir():
        return terms
    home_slug = str(home or Path.home()).replace("/", "-").lower()
    for d in projects_dir.iterdir():
        slug = d.name.lower()
        if not d.is_dir() or not any(m in slug for m in markers):
            continue
        rest = slug[len(home_slug):] if slug.startswith(home_slug) else slug
        terms.update(s for s in rest.split("-") if s not in GENERIC_SEGMENTS)
        terms.add(rest.strip("-"))
    return terms


def env_domains(env_text: str) -> set[str]:
    """Domains appearing in .env values, plus their registrable label (acme.example.com -> acme)."""
    terms = set()
    for value in parse_env(env_text).values():
        for domain in DOMAIN_RE.findall(value):
            d = domain.lower()
            if d in PUBLIC_DOMAINS or any(d.endswith("." + p) for p in PUBLIC_DOMAINS):
                continue
            terms.add(d)
            labels = d.split(".")
            if len(labels) >= 2:
                terms.add(labels[-2])
    return terms


def build(
    hand_written: Iterable[str],
    projects_dir: Path,
    client_projects: Iterable[str],
    env_path: Path | None,
    run: Callable = subprocess.run,
) -> Denylist:
    env_text = env_path.read_text(encoding="utf-8") if env_path and env_path.is_file() else ""
    terms = (
        _norm(hand_written)
        | _norm(private_repo_names(run))
        | _norm(client_dir_terms(projects_dir, client_projects))
        | _norm(env_domains(env_text))
    )
    return Denylist(frozenset(terms))
