"""Local market state under `<state>/market/` (outside the repo; may hold derived phrases).

- topics.json            topic key -> stored phrases / questions / domain_repo, for the daily requery
- signals/<date>.json     that night's market_heat / market_pain / market_status per topic
- matches/<date>.jsonl    top-5 route B matches per topic
- candidates.jsonl        off-watchlist domain_repo candidates (weekly line)
- outbound.jsonl          every outbound URL (written by net.Net)
- whitelist/<date>.json   the effective whitelist used that night
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Mapping

MARKET_DIR = "market"


def market_dir(state_dir: Path) -> Path:
    return Path(state_dir) / MARKET_DIR


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def load_topics(state_dir: Path) -> dict:
    return _read_json(market_dir(state_dir) / "topics.json", {})


def register_topics(state_dir: Path, records: Iterable[Mapping], today: date) -> dict:
    """Merge staged note records into topics.json; returns the new mapping (file rewritten)."""
    topics = dict(load_topics(state_dir))
    for r in records:
        s = r.get("summary") or {}
        key = r.get("topic_of")
        if not key:
            continue
        old = topics.get(key, {})
        questions = [q["question"] for q in s.get("reader_questions") or [] if q.get("question")]
        topics[key] = {
            "questions": list(dict.fromkeys([*old.get("questions", []), *questions]))[:3],
            "phrases": list(dict.fromkeys([*old.get("phrases", []), *(s.get("phrases") or [])]))[:3],
            "domain_repo": s.get("domain_repo") or old.get("domain_repo") or "none",
            "first_seen": old.get("first_seen") or today.isoformat(),
            "last_seen": today.isoformat(),
        }
    _write_json(market_dir(state_dir) / "topics.json", topics)
    return topics


def pool_topics(topics: Mapping, today: date, pool_days: int) -> dict:
    """Unexpired topics: last staged within the pool window (spec §3)."""
    cutoff = (today - timedelta(days=pool_days)).isoformat()
    return {k: v for k, v in topics.items() if v.get("last_seen", "") >= cutoff}


def save_signals(state_dir: Path, day: date, signals: Mapping) -> Path:
    path = market_dir(state_dir) / "signals" / f"{day.isoformat()}.json"
    _write_json(path, signals)
    return path


def latest_signals(state_dir: Path, max_age_days: int = 2, today: date | None = None) -> dict:
    d = market_dir(state_dir) / "signals"
    files = sorted(d.glob("*.json")) if d.is_dir() else []
    if not files:
        return {}
    newest = files[-1]
    if today and newest.stem < (today - timedelta(days=max_age_days)).isoformat():
        return {}
    return _read_json(newest, {})


def append_jsonl(path: Path, rows: Iterable[Mapping]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out


def save_whitelist(state_dir: Path, day: date, terms: Iterable[str]) -> None:
    """Effective whitelist for the day (seed + feed-derived); merged across reruns."""
    path = market_dir(state_dir) / "whitelist" / f"{day.isoformat()}.json"
    _write_json(path, sorted(set(_read_json(path, [])) | set(terms)))


def candidates_since(state_dir: Path, since: date) -> list[str]:
    rows = read_jsonl(market_dir(state_dir) / "candidates.jsonl")
    return sorted({r["repo"] for r in rows if r.get("day", "") >= since.isoformat() and r.get("repo")})
