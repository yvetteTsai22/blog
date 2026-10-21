"""Post-filter for de-contextualisation: strip paths and denylisted terms from model output."""
from __future__ import annotations

import re
from typing import Iterable

PLACEHOLDER = "[redacted]"
_ABS_PATH = re.compile(r"(?:~|/Users|/home|/private|/var|/opt|/tmp|[A-Za-z]:\\)[^\s'\"`)\]]*")


def basename(path: str) -> str:
    return re.split(r"[\\/]", path.rstrip("/\\"))[-1]


def scrub_text(text: str, deny: Iterable[str] = ()) -> str:
    out = _ABS_PATH.sub(lambda m: basename(m.group(0)) or PLACEHOLDER, text)
    for term in sorted({t for t in deny if t and len(t) >= 3}, key=len, reverse=True):
        out = re.sub(re.escape(term), PLACEHOLDER, out, flags=re.IGNORECASE)
    return out


def scrub(value, deny: Iterable[str] = ()):
    """Recursively scrub every string in a JSON-like value; returns a new value."""
    deny = tuple(deny)
    if isinstance(value, str):
        return scrub_text(value, deny)
    if isinstance(value, list):
        return [scrub(v, deny) for v in value]
    if isinstance(value, dict):
        return {k: scrub(v, deny) for k, v in value.items()}
    return value
