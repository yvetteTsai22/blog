"""Targeted sample (§1.3 step 3): R1, R5, R3, R4, clips, 18k-token cap and cut order."""
from __future__ import annotations

import json
from dataclasses import dataclass

from .features import failures
from .transcript import EDIT_TOOLS, Session, is_real_prompt

PROMPT_MAX = 1500
ANSWER_MAX = 800
# R4 tail texts are answers: spec §1.3 clips them at 800 (the TSA-44 prototype used 1200).
TAIL_MAX = ANSWER_MAX
INPUT_MAX = 300
ERR_MAX = 400
TAIL_COUNT = 3
DEFAULT_CAP = 18000

# Cut order when the cap fires: retries, middle answers, middle prompts (keep first+last),
# failures; final turns last.
CUT_ORDER = ("R3 retry", "R5 answer", "R1 prompt", "R3 fail", "R4 tail")
KEEP_ENDS = {"R1 prompt": 2}


@dataclass(frozen=True)
class Item:
    order: int
    rule: str
    text: str


def tok(s: str) -> int:
    """Rough token estimate: ASCII ~4 chars/token, other chars ~1 char/token."""
    ascii_chars = sum(1 for c in s if ord(c) < 128)
    return ascii_chars // 4 + (len(s) - ascii_chars)


def clip(s: str, n: int) -> str:
    s = s.strip()
    return s if len(s) <= n else s[: n // 2] + " …[clip]… " + s[-n // 2:]


def tool_input_brief(b: dict) -> str:
    i = b.get("input") or {}
    name = b.get("name")
    if name in EDIT_TOOLS:
        old = clip(i.get("old_string", "") or "", INPUT_MAX // 2)
        new = clip(i.get("new_string", "") or i.get("content", "") or "", INPUT_MAX // 2)
        return f"{name} {i.get('file_path')} old={old!r} new={new!r}"
    return f"{name} {clip(json.dumps(i, ensure_ascii=False), INPUT_MAX)}"


def _assistant_text(ev) -> str | None:
    if ev.role == "assistant" and ev.block.get("type") == "text":
        s = (ev.block.get("text") or "").strip()
        return s or None
    return None


def _answer_before(session: Session, idx: int) -> tuple[int, str] | None:
    """Last assistant text before event idx, not crossing an earlier real prompt."""
    for j in range(idx - 1, -1, -1):
        ev = session.events[j]
        text = _assistant_text(ev)
        if text:
            return j, text
        if is_real_prompt(ev):
            return None
    return None


def build_sample(session: Session) -> list[Item]:
    ev = session.events
    picked: list[Item] = []
    prompts = [i for i, e in enumerate(ev) if is_real_prompt(e)]
    picked += [Item(i, "R1 prompt", clip(ev[i].block["text"], PROMPT_MAX)) for i in prompts]
    for i, b, err, retry in failures(session):
        picked.append(Item(i, "R3 fail", tool_input_brief(b) + " → " + clip(err, ERR_MAX)))
        if retry:
            picked.append(Item(retry[0], "R3 retry", tool_input_brief(retry[1])))
    for p in prompts[1:]:
        hit = _answer_before(session, p)
        if hit:
            picked.append(Item(hit[0], "R5 answer", clip(hit[1], ANSWER_MAX)))
    texts = [(i, t) for i, e in enumerate(ev) if (t := _assistant_text(e))]
    picked += [Item(i, "R4 tail", clip(t, TAIL_MAX)) for i, t in texts[-TAIL_COUNT:]]
    seen, out = set(), []
    for it in sorted(picked, key=lambda x: x.order):
        key = (it.order, it.text)
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def total_tokens(items) -> int:
    return sum(tok(it.text) for it in items)


def enforce_cap(items: list[Item], cap: int = DEFAULT_CAP) -> list[Item]:
    """Drop by CUT_ORDER; within a rule drop the middle item first. Returns a new list."""
    kept = list(items)
    for rule in CUT_ORDER:
        while total_tokens(kept) > cap:
            idx = [k for k, it in enumerate(kept) if it.rule == rule]
            if len(idx) <= KEEP_ENDS.get(rule, 0):
                break
            drop = idx[len(idx) // 2]
            kept = kept[:drop] + kept[drop + 1:]
    return kept


def render(session: Session, items: list[Item]) -> str:
    lines = [f"# {session.title or session.session_id}", ""]
    lines += [f"[{it.rule}] {it.text}" for it in items]
    return "\n\n".join(lines)
