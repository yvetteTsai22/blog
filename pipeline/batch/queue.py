"""Pending queue: <state>/pending-queue.txt, one sessionId per line (written by the SessionEnd hook)."""
from __future__ import annotations

import fcntl
import os
from pathlib import Path
from typing import Iterable


def read_queue(path: Path) -> list[str]:
    """Session ids in first-seen order, duplicates and blanks dropped."""
    if not path.is_file():
        return []
    seen: dict[str, None] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        sid = line.strip()
        if sid:
            seen.setdefault(sid, None)
    return list(seen)


def remove_ids(path: Path, ids: Iterable[str]) -> None:
    """Drop ids under the same flock the hook uses, keeping lines appended meanwhile."""
    drop = set(ids)
    if not drop or not path.is_file():
        return
    fd = os.open(path, os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        with os.fdopen(os.dup(fd), "r+", encoding="utf-8") as fh:
            lines = fh.read().splitlines()
            kept = [l for l in lines if l.strip() and l.strip() not in drop]
            fh.seek(0)
            fh.write("".join(f"{l}\n" for l in kept))
            fh.truncate()
            fh.flush()
            os.fsync(fh.fileno())
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
