"""The four shadow questions: three Nouls p_* with the generality rule, one Choice dup_of."""
from __future__ import annotations

from typing import Iterable

from common import notion_schema as ns
from summarize.posts import PostOption

MODEL = "jev-1.14.0"  # pinned (spec §1.3 step 5); bump only with the TSA-57 decision

GENERALITY = (
    "Generality rule: only a lesson that another developer could reuse outside this project counts. "
    "A fix that only matters inside this one project is a no."
)

NOULS = {
    ns.P_TRAP: (
        "Is this Claude Code session worth a public blog post about a non-obvious trap, bug or failure mode "
        "that other developers will also hit?",
        "The `session_sample` shows a surprising failure, pitfall or bug whose cause and lesson apply beyond this project",
        "Routine work, an obvious mistake, or a fix that only matters inside this project",
    ),
    ns.P_INSIGHT: (
        "Is this Claude Code session worth a public blog post about an insight into how tools, agents or LLMs really behave?",
        "The `session_sample` reveals tool, agent or model behaviour that other developers would find new and useful",
        "Nothing new about how tools, agents or models behave, or the observation only matters inside this project",
    ),
    ns.P_PATTERN: (
        "Is this Claude Code session worth a public blog post about a reusable workflow, design or code pattern?",
        "The `session_sample` shows a workflow, design or code pattern other developers could copy into their own projects",
        "Routine work with no reusable pattern, or a pattern tied to this one project",
    ),
}

JEV_QUESTION_IDS = dict(zip(ns.P_SIGNALS, ns.JEV_P_SIGNALS))


def _noul(instructions: str, yes: str, no: str) -> dict:
    return {
        "type": "noul",
        "instructions": {"question": instructions, "rule": GENERALITY},
        "criteria": {"true": yes, "false": no},
    }


def _dup_choice(posts: Iterable[PostOption]) -> dict:
    criteria = {
        p.slug: {"title": p.title, "description": p.description, "opening": p.opening}
        for p in posts
    }
    criteria[ns.DUP_OF_NONE] = "The lesson is not already covered by any of the existing posts"
    return {
        "type": "choice",
        "instructions": (
            "Which existing blog post does the main lesson of the session in `session_sample` repeat? "
            f"Pick {ns.DUP_OF_NONE} unless a post already tells the same lesson."
        ),
        "criteria": criteria,
    }


def build_questions(posts: Iterable[PostOption]) -> dict:
    questions = {qid: _noul(*NOULS[qid]) for qid in ns.P_SIGNALS}
    questions[ns.DUP_OF] = _dup_choice(posts)
    return questions


def build_request(sample: str, posts: Iterable[PostOption], model: str = MODEL) -> dict:
    """State is the raw targeted sample, never the Haiku summary."""
    return {"model": model, "state": {"session_sample": sample}, "questions": build_questions(posts)}
