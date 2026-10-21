"""dup_of options: existing `_posts` with title, description and ~600 chars of the opening (spec §1.3 step 4)."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

OPENING_CHARS = 600
_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}-")
_SKIP = {"template"}


@dataclass(frozen=True)
class PostOption:
    slug: str
    title: str
    description: str
    opening: str


def split_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        meta = {}
    return (meta if isinstance(meta, dict) else {}), parts[2]


def slug_of(path: Path, meta: dict) -> str:
    return str(meta.get("slug") or _DATE_PREFIX.sub("", path.stem))


def opening_of(body: str, limit: int = OPENING_CHARS) -> str:
    text = re.sub(r"<[^>]+>|!\[[^\]]*\]\([^)]*\)", " ", body)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def load_post_options(posts_dir: Path) -> list[PostOption]:
    out = []
    for path in sorted(posts_dir.glob("*.md")):
        meta, body = split_front_matter(path.read_text(encoding="utf-8"))
        slug = slug_of(path, meta)
        if slug in _SKIP:
            continue
        out.append(PostOption(
            slug=slug,
            title=str(meta.get("title") or slug),
            description=" ".join(str(meta.get("description") or "").split()),
            opening=opening_of(body),
        ))
    return out
