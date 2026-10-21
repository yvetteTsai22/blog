"""Parse and normalise the model's JSON reply into a Summary (spec §1.3 step 4)."""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Iterable

from common import notion_schema as ns

from .prompt import GENERALITY_CAP
from .scrub import basename, scrub

SUMMARY_FIELDS = ("request", "investigated", "learned", "completed", "next_steps", "notes")
FILE_FIELDS = ("files_read", "files_edited")
MAX_QUESTIONS = 3
MIN_PHRASES, MAX_PHRASES = 2, 3
TITLE_MAX = 80


class ParseError(ValueError):
    """The model reply is not a usable JSON object."""


@dataclass(frozen=True)
class Summary:
    title: str
    request: str
    investigated: str
    learned: str
    completed: str
    next_steps: str
    notes: str
    files_read: list[str]
    files_edited: list[str]
    generality: str
    p_trap: float
    p_insight: float
    p_pattern: float
    dup_of: str
    dup_of_confidence: float
    topic_of: str
    privacy_flag: bool
    privacy_reason: str
    reader_questions: list[dict]
    phrases: list[str]
    domain_repo: str
    origin: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ParseError("no JSON object in reply")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ParseError(f"invalid JSON: {exc.msg}") from None
    if not isinstance(data, dict):
        raise ParseError("reply is not a JSON object")
    return data


def prob(value) -> float:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return 0.0
    return round(min(max(x, 0.0), 1.0), 3)


def as_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in ("true", "yes", "1")
    return bool(value)


def text(value) -> str:
    if isinstance(value, list):
        return "\n".join(f"- {v}" for v in value if str(v).strip())
    return "" if value is None else str(value).strip()


def files(value) -> list[str]:
    items = value if isinstance(value, list) else []
    return sorted({basename(str(v)) for v in items if str(v).strip()})


def questions(value) -> list[dict]:
    out = []
    for q in value if isinstance(value, list) else []:
        if isinstance(q, str):
            q = {"question": q, "kind": "none"}
        if not isinstance(q, dict) or not str(q.get("question", "")).strip():
            continue
        kind = str(q.get("kind", "none")).strip().lower()
        out.append({
            "question": str(q["question"]).strip(),
            "kind": kind if kind in ns.READER_QUESTION_KINDS else "none",
        })
    return out[:MAX_QUESTIONS]


def choice(value, options: Iterable[str], default: str) -> str:
    v = str(value or "").strip()
    return v if v in set(options) else default


def parse_output(
    reply: str,
    post_slugs: Iterable[str] = (),
    topic_ids: Iterable[str] = (),
    deny: Iterable[str] = (),
) -> Summary:
    raw = scrub(extract_json(reply), deny)
    warnings = []

    generality = choice(raw.get("generality"), ("general", "project_only"), "general")
    p = {k: prob(raw.get(k)) for k in ns.P_SIGNALS}
    if generality == "project_only" and any(v > GENERALITY_CAP for v in p.values()):
        warnings.append("project_only scores capped")
        p = {k: min(v, GENERALITY_CAP) for k, v in p.items()}

    dup_of = choice(raw.get("dup_of"), post_slugs, ns.DUP_OF_NONE)
    if str(raw.get("dup_of") or "").strip() not in (dup_of, ""):
        warnings.append("unknown dup_of slug replaced by none")
    dup_conf = prob(raw.get("dup_of_confidence")) if dup_of != ns.DUP_OF_NONE else 0.0

    topic = str(raw.get("topic_of") or "").strip()
    topic_of = topic if topic in set(topic_ids) else ns.TOPIC_NEW

    phrases = [str(x).strip() for x in raw.get("phrases") or [] if str(x).strip()][:MAX_PHRASES]
    if len(phrases) < MIN_PHRASES:
        warnings.append(f"only {len(phrases)} phrases")

    domain_repo = str(raw.get("domain_repo") or "none").strip()
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", domain_repo):
        domain_repo = "none"

    title = text(raw.get("title")) or text(raw.get("request"))[:TITLE_MAX] or "Untitled session"

    return Summary(
        title=title[:TITLE_MAX],
        **{k: text(raw.get(k)) for k in SUMMARY_FIELDS},
        **{k: files(raw.get(k)) for k in FILE_FIELDS},
        generality=generality,
        **p,
        dup_of=dup_of,
        dup_of_confidence=dup_conf,
        topic_of=topic_of,
        privacy_flag=as_bool(raw.get("privacy_flag")),
        privacy_reason=text(raw.get("privacy_reason")),
        reader_questions=questions(raw.get("reader_questions")),
        phrases=phrases,
        domain_repo=domain_repo,
        origin=choice(raw.get("origin"), ns.ORIGIN_OPTIONS, ns.ORIGIN_PERSONAL),
        warnings=warnings,
    )
