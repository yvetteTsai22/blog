"""Prompt for the per-session summary + scoring call (spec §1.3 step 4, §2)."""
from __future__ import annotations

import json
from typing import Iterable, Mapping

from common import notion_schema as ns

from .posts import PostOption

GENERALITY_CAP = 0.3

OUTPUT_SCHEMA = {
    "title": "short public title for the lesson (≤ 80 chars)",
    "request": "what the user asked for",
    "investigated": "what was looked into",
    "learned": "what was learned",
    "completed": "what got done",
    "next_steps": "what is left",
    "files_read": ["file names only, no directories"],
    "files_edited": ["file names only, no directories"],
    "notes": "anything else worth keeping",
    "generality": "general | project_only",
    "p_trap": "0..1",
    "p_insight": "0..1",
    "p_pattern": "0..1",
    "dup_of": "an option slug or none",
    "dup_of_confidence": "0..1",
    "topic_of": "an existing topic id or new",
    "privacy_flag": "true | false",
    "privacy_reason": "why, or empty",
    "reader_questions": [{"question": "…", "kind": "|".join(ns.READER_QUESTION_KINDS)}],
    "phrases": ["2-3 concrete public search phrases"],
    "domain_repo": "owner/repo of the main public tool involved, or none",
    "origin": "personal | client",
}

INSTRUCTIONS = f"""You summarise and score one Claude Code session for a public tech blog's topic pipeline.
Reply with ONE JSON object only, no prose, no code fence. Write every value in English.

De-contextualise. The blog is public. Never write client or company names, private repo names,
internal codenames, people's names, hostnames, URLs of private systems, absolute paths or directories.
Describe the work generically ("a client's web app", "an internal service"). File lists hold bare file names.
Words listed under NEVER MENTION must not appear anywhere in your output.

Scores are probabilities that this session is worth a blog post of that kind:
- p_trap: a non-obvious trap, bug or failure mode others will hit.
- p_insight: an insight about how tools/agents/LLMs really behave.
- p_pattern: a reusable workflow, design or code pattern.
Generality rule: only lessons reusable outside this project count. If the lesson is a fix that only
matters inside this project, set generality=project_only and keep every p_* at or below {GENERALITY_CAP}.
Routine work with nothing new scores low (under 0.2).

dup_of: the slug of the existing post this lesson repeats, or "none"; dup_of_confidence 0..1.
topic_of: reuse an existing topic id below if this session continues it, otherwise "new".
privacy_flag: true if the lesson can't be told without revealing private or client details.
reader_questions: REQUIRED, 1-3 questions a reader would search for, primary first, kind one of
{", ".join(ns.READER_QUESTION_KINDS)}. Always fill this, even when scores are low.
phrases: REQUIRED, 2-3 concrete public phrases (tool + problem) a developer would search for.
Always fill this, even when scores are low.
origin: "client" only if the code belongs to a client's or employer's product. The user's own
blog, tools, dotfiles, side projects and agent setup are "personal". When unsure, "client".

Output keys and shapes:
{json.dumps(OUTPUT_SCHEMA, ensure_ascii=False, indent=1)}
"""


def _post_block(posts: Iterable[PostOption]) -> str:
    rows = [
        {"slug": p.slug, "title": p.title, "description": p.description, "opening": p.opening}
        for p in posts
    ]
    return json.dumps(rows, ensure_ascii=False, indent=1) if rows else "[]"


def build_prompt(
    sample: str,
    features: Mapping,
    posts: Iterable[PostOption] = (),
    topics: Iterable[str] = (),
    never_mention: Iterable[str] = (),
) -> str:
    topic_list = sorted(set(topics))
    deny = sorted({t for t in never_mention if t})
    return "\n\n".join([
        INSTRUCTIONS,
        "## NEVER MENTION\n" + (", ".join(deny) if deny else "(none)"),
        "## Existing posts (dup_of options)\n" + _post_block(posts),
        "## Existing topic ids (topic_of options)\n" + (json.dumps(topic_list, ensure_ascii=False) if topic_list else "[]"),
        "## Structural features\n" + json.dumps(dict(features), ensure_ascii=False),
        "## Session sample\n" + sample,
    ])
