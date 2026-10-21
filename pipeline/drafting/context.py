"""Spec §1.6: the drafting session's opening context, in order. Pure renderers plus small readers."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from common import notion_schema as ns

SCRUBBED = "[scrubbed]"
VOICE_SAMPLES = 2
POST_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.md$")
DRAFT_RE = re.compile(r"^_drafts/(.+)\.md$")
SKILL_PATH = Path("~/.claude/skills/article-writing/SKILL.md")
BLOG_CLAUDE_MD = ".claude/CLAUDE.md"


@dataclass(frozen=True)
class Article:
    """A permanent note in 寫作中 and/or with `note pending`."""
    title: str
    days: int
    draft_path: str
    slug: str
    note_pending: bool
    writing: bool


@dataclass(frozen=True)
class LitNote:
    title: str
    url: str
    origin: str
    topic: str


@dataclass(frozen=True)
class Change:
    status: str
    path: str
    article: str


# --- readers ----------------------------------------------------------------

def voice_samples(repo: Path, n: int = VOICE_SAMPLES) -> list[str]:
    """The n most recent published posts in `_posts/` (by file-name date), repo-relative."""
    posts = sorted((p.name for p in (repo / "_posts").glob("*.md") if POST_RE.match(p.name)), reverse=True)
    return [f"_posts/{name}" for name in posts[:n]]


def git_status(repo: Path) -> str:
    """Read-only porcelain status of the worktree (never stages, commits or stashes)."""
    def status(*extra: str) -> str:
        return subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", *extra],
            cwd=repo, capture_output=True, text=True, check=True, timeout=30,
        ).stdout

    # `_drafts/` is gitignored, so its files show only with --ignored; scope that to `_drafts`.
    drafts = [l for l in status("--ignored=traditional", "--", "_drafts").splitlines() if l.startswith("!!")]
    return status() + "".join(f"{l}\n" for l in drafts)


def article_for(path: str, by_draft: dict[str, str]) -> str:
    """Slug of the article a changed path belongs to, or '' when it is not article content."""
    if path in by_draft:
        return by_draft[path]
    m = DRAFT_RE.match(path)
    if m:
        return m.group(1)
    if path.startswith("_posts/"):
        pm = POST_RE.match(path.removeprefix("_posts/"))
        return pm.group(2) if pm else ""
    return ""


def parse_changes(porcelain: str, articles: list[Article]) -> list[Change]:
    """Uncommitted changes. Ignored files count only under `_drafts/` (it is gitignored)."""
    by_draft = {a.draft_path: a.slug or a.title for a in articles if a.draft_path}
    out = []
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        status, path = line[:2], line[3:].split(" -> ")[-1].strip('"')
        if status == "!!" and not path.startswith("_drafts/"):
            continue
        if path.endswith("/"):
            continue
        out.append(Change(status.strip() or status, path, article_for(path, by_draft)))
    return out


# --- rendering --------------------------------------------------------------

def _s(value: str, scrub: bool) -> str:
    return SCRUBBED if scrub and value else value


def section_articles(articles: list[Article], scrub: bool = False) -> list[str]:
    out = ["## 1. Unfinished articles (listed, not pushed)"]
    if not articles:
        return out + ["(none)"]
    for a in sorted(articles, key=lambda a: -a.days):
        flags = []
        if a.writing:
            flags.append(f"寫作中 {a.days} days")
        if a.note_pending:
            flags.append("note pending")
        draft = _s(a.draft_path, scrub) or "(no draft yet)"
        out.append(f"- {_s(a.title, scrub) or '(untitled)'} — {', '.join(flags)} — {draft}")
    return out


def section_today(message: str) -> list[str]:
    return ["## 2. Today's list (same text as the Telegram message)", "", message.rstrip()]


def section_links(notes: list[LitNote], scrub: bool = False) -> list[str]:
    out = ["## 3. Literature notes (links only; read bodies through Notion MCP after a pick)"]
    if not notes:
        return out + ["(none listed today)"]
    return out + [f"- [{_s(n.topic, scrub)}] {_s(n.title, scrub)} — {_s(n.url, scrub)}" for n in notes]


def section_tools(repo: Path, samples: list[str], skill: Path = SKILL_PATH) -> list[str]:
    out = [
        "## 4. Writing tools (read these before drafting)",
        f"- Blog repo guide: {BLOG_CLAUDE_MD}",
        f"- Skill: article-writing ({skill})",
    ]
    out += [f"- Voice sample: {s}" for s in samples] or ["- Voice sample: (no published posts found)"]
    return out


def section_changes(changes: list[Change], scrub: bool = False) -> list[str]:
    out = ["## 5. Uncommitted changes in this worktree"]
    if not changes:
        return out + ["(clean)"]
    return out + [
        f"- {c.status} {_s(c.path, scrub and bool(c.article))} — "
        f"{_s(c.article, scrub) if c.article else '(not an article)'}"
        for c in changes
    ]


def section_client(notes: list[LitNote], scrub: bool = False) -> list[str]:
    out = ["## 6. Client-origin notes (human look before publish)"]
    client = [n for n in notes if n.origin == ns.ORIGIN_CLIENT]
    if not client:
        return out + ["(none)"]
    return out + [
        f"- ⚠ client: {_s(n.title, scrub)} — {_s(n.url, scrub)}. Check that nothing identifies the client "
        "before this goes into a draft or a post."
        for n in client
    ]


def render(*, articles, message, notes, repo, samples, changes, instructions, close_lines, scrub=False) -> str:
    parts = [
        "# Drafting session",
        "",
        *close_lines,
        "",
        *section_articles(articles, scrub), "",
        *section_today(message), "",
        *section_links(notes, scrub), "",
        *section_tools(repo, samples), "",
        *section_changes(changes, scrub), "",
        *section_client(notes, scrub), "",
        instructions.rstrip(),
    ]
    return "\n".join(parts) + "\n"
