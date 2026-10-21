"""Plan which 寫作中 permanent notes flip to 已發表 (pure; no I/O)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from common import notion_schema as ns

from .posts import Post, post_url


@dataclass(frozen=True)
class Flip:
    page_id: str
    title: str
    slug: str
    url: str
    published: date

    def properties(self) -> dict:
        return {
            ns.BLOG_STATUS: {"select": {"name": ns.BLOG_PUBLISHED}},
            ns.PUBLISHED_URL: {"url": self.url},
            ns.PUBLISHED_DATE: {"date": {"start": self.published.isoformat()}},
        }


@dataclass(frozen=True)
class Plan:
    flips: tuple[Flip, ...]
    writing: int          # 寫作中 notes checked
    no_slug: int          # of those, notes without a slug


def plan(writing_notes: list[dict], posts: dict[str, Post], base: str) -> Plan:
    """`writing_notes`: dicts with page_id, title, slug (plain values)."""
    flips, no_slug = [], 0
    for n in writing_notes:
        slug = (n.get("slug") or "").strip().strip("/")
        if not slug:
            no_slug += 1
            continue
        post = posts.get(slug)
        if post:
            flips.append(Flip(n["page_id"], n.get("title") or "", slug, post_url(base, slug), post.published))
    return Plan(tuple(flips), len(writing_notes), no_slug)


def result_line(result: dict | None) -> list[str]:
    """Telegram line for the reconcile result stored in ctx.results."""
    if not result:
        return []
    if result.get("error"):
        return [f"發表對帳: 失敗 ({result['error']})"]
    flipped = result.get("flipped") or []
    verb = "會標記" if result.get("dry_run") else "已標記"
    if not flipped:
        return [f"發表對帳: 0 篇新發表 (寫作中 {result.get('writing', 0)} 篇)"]
    slugs = ", ".join(f["slug"] for f in flipped)
    return [f"發表對帳: {verb} {len(flipped)} 篇已發表 — {slugs}"]
