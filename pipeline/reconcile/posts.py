"""Read published posts and site url from the blog's master branch via git (no checkout)."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

POSTS_DIR = "_posts"
CONFIG_FILE = "_config.yml"  # generated from src/yml/ by gulp; read, never edited
POST_NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.+)\.(?:md|markdown|html)$")
FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.S)


class GitError(Exception):
    """A git read against the blog repo failed."""


@dataclass(frozen=True)
class Post:
    slug: str
    published: date
    path: str


def _git(repo: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        raise GitError(f"git {' '.join(args[:2])} failed: {exc.__class__.__name__}") from None
    return out.stdout


def front_matter_slug(text: str) -> str:
    m = FRONT_MATTER_RE.match(text)
    if not m:
        return ""
    try:
        data = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError:
        return ""
    slug = data.get("slug") if isinstance(data, dict) else None
    return str(slug).strip() if slug else ""


def parse_post(path: str, text: str) -> Post | None:
    """Jekyll's :title is the front matter `slug` if set, else the filename suffix."""
    m = POST_NAME_RE.match(path.rsplit("/", 1)[-1])
    if not m:
        return None
    return Post(slug=front_matter_slug(text) or m.group(2), published=date.fromisoformat(m.group(1)), path=path)


def site_base(config_text: str) -> str:
    """`url` + `baseurl` from _config.yml, without a trailing slash."""
    data = yaml.safe_load(config_text) or {}
    url = str(data.get("url") or "").rstrip("/")
    if not url:
        raise ValueError("_config.yml has no url")
    baseurl = str(data.get("baseurl") or "").strip("/")
    return f"{url}/{baseurl}" if baseurl else url


def post_url(base: str, slug: str) -> str:
    return f"{base}/{slug}/"


def master_posts(repo: Path, ref: str = "master") -> dict[str, Post]:
    names = _git(repo, "ls-tree", "--name-only", ref, f"{POSTS_DIR}/").splitlines()
    posts: dict[str, Post] = {}
    for path in names:
        if not POST_NAME_RE.match(path.rsplit("/", 1)[-1]):
            continue
        post = parse_post(path, _git(repo, "show", f"{ref}:{path}"))
        if post:
            posts[post.slug] = post
    return posts


def master_site_base(repo: Path, ref: str = "master") -> str:
    return site_base(_git(repo, "show", f"{ref}:{CONFIG_FILE}"))
