"""Run the shadow call and turn its answers into note properties."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from common import notion_schema as ns
from summarize.posts import PostOption

from .questions import JEV_QUESTION_IDS, build_request


@dataclass(frozen=True)
class JevResult:
    model: str
    p: dict[str, float]          # keyed by Haiku names: p_trap, p_insight, p_pattern
    dup_of: str
    dup_confidence: float
    input_tokens: int = 0

    def properties(self) -> dict:
        props = {JEV_QUESTION_IDS[k]: round(v, 4) for k, v in self.p.items()}
        props[ns.JEV_DUP_OF] = self.dup_of
        return props

    def body_section(self) -> str:
        ps = " · ".join(f"{k} {v:.2f}" for k, v in self.p.items())
        return (
            "## Jev shadow\n"
            f"- model: {self.model}\n"
            f"- {ps}\n"
            f"- dup_of: {self.dup_of} (confidence {self.dup_confidence:.2f})\n"
            "- shadow only: stored, never ranked"
        )


def _num(value) -> float:
    x = float(value)
    if not 0.0 <= x <= 1.0:
        raise ValueError("probability out of range")
    return x


def parse_answers(resp: dict, valid_slugs: Iterable[str]) -> JevResult:
    answers = resp["answers"]
    p = {k: _num(answers[k]["noul"]) for k in ns.P_SIGNALS}
    dup = answers[ns.DUP_OF]
    choice = str(dup.get("choice") or ns.DUP_OF_NONE)
    if choice not in set(valid_slugs) | {ns.DUP_OF_NONE}:
        choice = ns.DUP_OF_NONE
    conf = dup.get("confidence")
    return JevResult(
        model=str(resp.get("model") or ""),
        p=p,
        dup_of=choice,
        dup_confidence=_num(conf) if conf is not None else 0.0,
        input_tokens=int((resp.get("usage") or {}).get("input_tokens") or 0),
    )


def score_sample(client, sample: str, posts: list[PostOption]) -> JevResult:
    """Exactly one Jev call for one session."""
    resp = client.system_one(build_request(sample, posts))
    return parse_answers(resp, [p.slug for p in posts])
