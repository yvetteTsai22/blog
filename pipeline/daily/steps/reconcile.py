"""21:00 step: publish reconciliation (spec §1.4 step 3). See reconcile/."""
from __future__ import annotations

from pathlib import Path

from common import notion_schema as ns
from common import paths
from daily.notes import from_page
from daily.notion import writing_filter
from reconcile import core, posts

NAME = "reconcile"
ORDER = 50
DEFAULT_REF = "master"


def run(ctx) -> None:
    repo = Path(ctx.config.get("reconcile.repo") or paths.REPO_ROOT).expanduser()
    ref = ctx.config.get("reconcile.ref") or DEFAULT_REF
    try:
        published = posts.master_posts(repo, ref)
        base = posts.master_site_base(repo, ref)
    except (posts.GitError, ValueError) as exc:
        ctx.results[NAME] = {"error": str(exc), "dry_run": ctx.dry_run}
        ctx.log(f"reconcile: {exc}")
        return
    writing = []
    for page in ctx.notion.query(writing_filter()):
        n = from_page(page)
        writing.append({"page_id": n.page_id, "title": n.title, "slug": n.props.get(ns.SLUG) or ""})
    result = core.plan(writing, published, base)
    flipped = []
    for flip in result.flips:
        if not ctx.dry_run:
            ctx.notion.update_page(flip.page_id, flip.properties())
        flipped.append({"page_id": flip.page_id, "slug": flip.slug, "url": flip.url,
                        "published": flip.published.isoformat()})
    ctx.results[NAME] = {"dry_run": ctx.dry_run, "writing": result.writing,
                         "no_slug": result.no_slug, "flipped": flipped}
    ctx.log(f"reconcile: writing={result.writing} flipped={len(flipped)} dry_run={ctx.dry_run}")
