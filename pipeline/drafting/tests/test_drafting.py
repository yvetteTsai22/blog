"""Opening context, change mapping and idle-only close, on synthetic data."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from drafting import context, sessions
from drafting.__main__ import INSTRUCTIONS, articles_filter

ART = context.Article(title="Hooks post", days=16, draft_path="_drafts/hooks-post.md",
                      slug="hooks-post", note_pending=False, writing=True)
PENDING = context.Article(title="Empty note", days=2, draft_path="", slug="", note_pending=True, writing=True)
NOTES = [
    context.LitNote("lesson a", "https://www.notion.so/aaa", "personal", "topic one"),
    context.LitNote("lesson b", "https://www.notion.so/bbb", "client", "topic one"),
]


def _render(tmp_path, scrub=False, changes=()):
    return context.render(
        articles=[ART, PENDING], message="📝 Blog topics 2026-10-20\n1. topic one", notes=NOTES,
        repo=tmp_path, samples=["_posts/2026-09-29-b.md", "_posts/2026-06-25-a.md"],
        changes=list(changes), instructions="## How this session works", close_lines=["closed x"],
        scrub=scrub,
    )


# --- opening context ---------------------------------------------------------

def test_sections_in_spec_order(tmp_path):
    text = _render(tmp_path)
    heads = [text.index(f"## {i}.") for i in range(1, 7)]
    assert heads == sorted(heads)
    assert text.index("closed x") < heads[0] < text.index("## How this session works")


def test_articles_show_title_days_path_and_pending(tmp_path):
    text = _render(tmp_path)
    assert "- Hooks post — 寫作中 16 days — _drafts/hooks-post.md" in text
    assert "- Empty note — 寫作中 2 days, note pending — (no draft yet)" in text


def test_today_list_is_message_verbatim(tmp_path):
    assert "📝 Blog topics 2026-10-20\n1. topic one" in _render(tmp_path)


def test_links_not_bodies_and_client_highlight(tmp_path):
    text = _render(tmp_path)
    assert "- [topic one] lesson a — https://www.notion.so/aaa" in text
    client = text.split("## 6.")[1]
    assert "lesson b" in client and "lesson a" not in client and "⚠ client" in client


def test_tools_section(tmp_path):
    text = _render(tmp_path)
    assert ".claude/CLAUDE.md" in text and "article-writing" in text
    assert text.count("- Voice sample: _posts/") == 2


def test_scrub_hides_titles_links_and_article_paths(tmp_path):
    changes = [context.Change("M", "_drafts/hooks-post.md", "hooks-post"),
               context.Change("M", "_config.yml", "")]
    text = _render(tmp_path, scrub=True, changes=changes)
    for secret in ("Hooks post", "lesson a", "notion.so/aaa", "hooks-post"):
        assert secret not in text
    assert "- M _config.yml — (not an article)" in text


def test_voice_samples_two_most_recent(tmp_path):
    posts = tmp_path / "_posts"
    posts.mkdir()
    for name in ("2023-08-30-old.md", "2026-06-25-mid.md", "2026-09-29-new.md", "template.md"):
        (posts / name).write_text("x")
    assert context.voice_samples(tmp_path) == ["_posts/2026-09-29-new.md", "_posts/2026-06-25-mid.md"]


# --- uncommitted changes -------------------------------------------------------

def test_parse_changes_maps_articles_and_ignores_other_ignored_files():
    porcelain = "\n".join([
        " M _posts/2026-06-25-everything-returned-true.md",
        "!! _drafts/hooks-post.md",
        "!! .env",
        "?? _drafts/new-one.md",
        "R  old.md -> about.md",
        "!! node_modules/",
    ])
    changes = context.parse_changes(porcelain, [ART])
    assert [(c.path, c.article) for c in changes] == [
        ("_posts/2026-06-25-everything-returned-true.md", "everything-returned-true"),
        ("_drafts/hooks-post.md", "hooks-post"),
        ("_drafts/new-one.md", "new-one"),
        ("about.md", ""),
    ]


def test_git_status_on_real_repo_sees_ignored_draft(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("_drafts\n")
    (tmp_path / "_drafts").mkdir()
    (tmp_path / "_drafts" / "a-b.md").write_text("draft")
    changes = context.parse_changes(context.git_status(tmp_path), [])
    assert ("_drafts/a-b.md", "a-b") in [(c.path, c.article) for c in changes]


# --- idle-only close -----------------------------------------------------------

def _ps(path, agents):
    return json.dumps({"ok": True, "result": {"worktrees": [
        {"path": "/elsewhere", "agents": [{"paneKey": "t9:l9", "state": "done"}]},
        {"path": path, "agents": [{"paneKey": k, "state": s} for k, s in agents]},
    ]}})


def _terms(keys):
    return json.dumps({"ok": True, "result": {"terminals": [
        {"handle": f"term_{k.replace(':', '_')}", "tabId": k.split(":")[0], "leafId": k.split(":")[1]}
        for k in keys
    ]}})


class FakeOrca:
    def __init__(self, path, agents, live):
        self.calls, self.path, self.agents, self.live = [], path, agents, live

    def __call__(self, args):
        self.calls.append(args)
        if args[:2] == ["worktree", "ps"]:
            return _ps(self.path, self.agents)
        if args[:2] == ["terminal", "list"]:
            return _terms(self.live)
        return json.dumps({"ok": True, "result": {}})


def test_close_only_idle_and_never_self(tmp_path):
    p = str(tmp_path)
    fake = FakeOrca(p, [("t1:l1", "done"), ("t2:l2", "working"), ("t3:l3", "waiting"), ("me:me", "done")],
                    ["t1:l1", "t2:l2", "t3:l3", "me:me"])
    decisions = sessions.close_previous(p, run=fake, self_pane="me:me")
    assert {d.pane.pane_key: d.action for d in decisions} == {
        "t1:l1": "close", "t2:l2": "keep", "t3:l3": "keep", "me:me": "keep"}
    closes = [c for c in fake.calls if c[:2] == ["terminal", "close"]]
    assert closes == [["terminal", "close", "--terminal", "term_t1_l1", "--json"]]
    assert all(c[0] in ("worktree", "terminal") for c in fake.calls)  # no git, no stash


def test_close_dry_run_and_dead_terminal(tmp_path):
    p = str(tmp_path)
    fake = FakeOrca(p, [("t1:l1", "done"), ("t4:l4", "done")], ["t1:l1"])
    decisions = sessions.close_previous(p, dry_run=True, run=fake, self_pane="")
    assert [d.action for d in decisions] == ["close", "keep"]
    assert not [c for c in fake.calls if c[:2] == ["terminal", "close"]]
    assert "would close" in sessions.describe(decisions, dry_run=True)[0]


def test_orca_not_ok_raises(tmp_path):
    with pytest.raises(RuntimeError):
        sessions.close_previous(str(tmp_path), run=lambda a: json.dumps({"ok": False}), self_pane="")


# --- instructions and filters --------------------------------------------------

def test_session_instructions_cover_pick_and_publish():
    text = INSTRUCTIONS.read_text(encoding="utf-8")
    for needle in ("pick_status=挑中", "git merge master", "note pending=true", "_drafts/<slug>.md",
                   "git add -f _drafts/<slug>.md", "One commit touches one article", "draft path=",
                   'says "publish"', "blocked", "w=2670", "_data/tags.yml", "+0800"):
        assert needle in text, needle
    assert "git push" not in text.split("### Publish")[0]


def test_articles_filter_covers_writing_and_pending():
    f = json.dumps(articles_filter(), ensure_ascii=False)
    assert "寫作中" in f and "note pending" in f


def test_prompt_template_has_single_path_placeholder():
    prompt = (Path(__file__).parents[1] / "automation" / "prompt.md").read_text(encoding="utf-8")
    assert prompt.count("{{PIPELINE_DIR}}") == 1
    assert "/Users/" not in prompt
