"""Publish reconciliation on a synthetic git repo and synthetic Notion pages."""
from __future__ import annotations

import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from common import notion_schema as ns
from common.config import Config
from daily.lines import reconcile as reconcile_line
from daily.runner import Context
from daily.steps import reconcile as step
from reconcile import core, posts

CONFIG_YML = 'baseurl: "/blog"\nurl: "https://example.test"\npermalink: /:title/\n'


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "master")
    git(tmp_path, "config", "user.email", "t@example.test")
    git(tmp_path, "config", "user.name", "t")
    (tmp_path / "_posts").mkdir()
    (tmp_path / "_config.yml").write_text(CONFIG_YML)
    (tmp_path / "_posts/2026-10-01-alpha-post.md").write_text("---\ntitle: A\n---\nbody\n")
    (tmp_path / "_posts/2026-10-02-long-file-name.md").write_text("---\ntitle: B\nslug: beta\n---\n")
    (tmp_path / "_posts/template.md").write_text("---\ntitle: T\n---\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "init")
    # Work on another branch must not count: only master is read.
    git(tmp_path, "checkout", "-qb", "draft")
    (tmp_path / "_posts/2026-10-03-gamma.md").write_text("---\ntitle: G\n---\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "draft")
    return tmp_path


def page(pid: str, slug: str) -> dict:
    return {
        "id": pid, "created_time": "2026-10-01T00:00:00.000Z", "url": "",
        "properties": {
            ns.TITLE: {"type": "title", "title": [{"plain_text": f"note {pid}"}]},
            ns.BLOG_STATUS: {"type": "select", "select": {"name": ns.BLOG_WRITING}},
            ns.SLUG: {"type": "rich_text", "rich_text": [{"plain_text": slug}] if slug else []},
        },
    }


class FakeNotion:
    def __init__(self, pages):
        self.pages, self.updates = pages, []

    def query(self, filter_):
        assert filter_["property"] == ns.BLOG_STATUS
        return iter(self.pages)

    def update_page(self, page_id, properties):
        self.updates.append((page_id, properties))


def ctx_for(repo: Path, notion, dry_run=False) -> Context:
    cfg = Config(env={}, local={"reconcile": {"repo": str(repo)}})
    return Context(config=cfg, state_dir=repo / "state", now=datetime(2026, 10, 20, 20, tzinfo=timezone.utc),
                   dry_run=dry_run, notion=notion)


def test_parse_post_uses_front_matter_slug_then_filename():
    assert posts.parse_post("_posts/2026-10-02-x-y.md", "---\nslug: z\n---\n").slug == "z"
    p = posts.parse_post("_posts/2026-10-02-x-y.md", "no front matter")
    assert (p.slug, p.published) == ("x-y", date(2026, 10, 2))
    assert posts.parse_post("_posts/template.md", "") is None


def test_site_base_joins_url_and_baseurl():
    assert posts.site_base(CONFIG_YML) == "https://example.test/blog"
    assert posts.site_base('url: "https://e.test/"\n') == "https://e.test"
    with pytest.raises(ValueError):
        posts.site_base("baseurl: /x\n")


def test_master_posts_reads_master_only(repo):
    found = posts.master_posts(repo)
    assert set(found) == {"alpha-post", "beta"}
    assert posts.master_site_base(repo) == "https://example.test/blog"


def test_master_posts_bad_ref(repo):
    with pytest.raises(posts.GitError):
        posts.master_posts(repo, "no-such-branch")


def test_plan_matches_slug_only():
    ps = {"alpha": posts.Post("alpha", date(2026, 10, 1), "p")}
    notes = [{"page_id": "1", "slug": "alpha"}, {"page_id": "2", "slug": "other"},
             {"page_id": "3", "slug": ""}, {"page_id": "4", "slug": " /alpha/ "}]
    result = core.plan(notes, ps, "https://e.test/blog")
    assert [f.page_id for f in result.flips] == ["1", "4"]
    assert (result.writing, result.no_slug) == (4, 1)
    assert result.flips[0].properties() == {
        ns.BLOG_STATUS: {"select": {"name": ns.BLOG_PUBLISHED}},
        ns.PUBLISHED_URL: {"url": "https://e.test/blog/alpha/"},
        ns.PUBLISHED_DATE: {"date": {"start": "2026-10-01"}},
    }


def test_step_flips_and_line(repo):
    notion = FakeNotion([page("p1", "alpha-post"), page("p2", "gamma"), page("p3", "")])
    ctx = ctx_for(repo, notion)
    step.run(ctx)
    assert [u[0] for u in notion.updates] == ["p1"]
    assert notion.updates[0][1][ns.PUBLISHED_URL] == {"url": "https://example.test/blog/alpha-post/"}
    assert reconcile_line.lines(ctx) == ["發表對帳: 已標記 1 篇已發表 — alpha-post"]


def test_step_dry_run_writes_nothing(repo):
    notion = FakeNotion([page("p1", "beta")])
    ctx = ctx_for(repo, notion, dry_run=True)
    step.run(ctx)
    assert notion.updates == []
    assert reconcile_line.lines(ctx) == ["發表對帳: 會標記 1 篇已發表 — beta"]


def test_step_nothing_to_flip(repo):
    ctx = ctx_for(repo, FakeNotion([page("p1", "gamma")]))
    step.run(ctx)
    assert reconcile_line.lines(ctx) == ["發表對帳: 0 篇新發表 (寫作中 1 篇)"]


def test_step_git_failure_is_reported(tmp_path):
    ctx = ctx_for(tmp_path, FakeNotion([]))
    step.run(ctx)
    assert reconcile_line.lines(ctx)[0].startswith("發表對帳: 失敗")


def test_line_absent_without_result():
    assert core.result_line(None) == []
