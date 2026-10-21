"""Synthetic tests for Jev shadow scoring and the "Jev 另外推" line. No network."""
from __future__ import annotations

import io
import json
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import pytest

from common import notion_schema as ns
from common.config import Config
from jev import JevClient, JevError, MODEL, build_request, jev_enabled, parse_answers, scorer_for
from jev.routing import config_warnings
from jev.topline import jev_top_topics, render
from summarize.posts import PostOption

POSTS = [PostOption("slow-reviewer", "Slow reviewer", "desc", "opening text")]


def answers(trap=0.7, insight=0.2, pattern=0.4, dup="none", conf=0.9):
    return {
        "model": MODEL,
        "answers": {
            "p_trap": {"type": "noul", "noul": trap},
            "p_insight": {"type": "noul", "noul": insight},
            "p_pattern": {"type": "noul", "noul": pattern},
            "dup_of": {"type": "choice", "choice": dup, "confidence": conf, "probabilities": {}},
        },
        "usage": {"input_tokens": 1234},
    }


# --- request shape -------------------------------------------------------

def test_request_is_pinned_and_asks_exactly_four_questions_on_raw_sample():
    body = build_request("RAW SAMPLE", POSTS)
    assert body["model"] == "jev-1.14.0"
    assert body["state"] == {"session_sample": "RAW SAMPLE"}
    q = body["questions"]
    assert set(q) == {"p_trap", "p_insight", "p_pattern", "dup_of"}
    assert all(q[k]["type"] == "noul" for k in ns.P_SIGNALS)
    assert all("Generality rule" in q[k]["instructions"]["rule"] for k in ns.P_SIGNALS)
    assert q["dup_of"]["type"] == "choice"
    assert set(q["dup_of"]["criteria"]) == {"slow-reviewer", "none"}


# --- parsing -------------------------------------------------------------

def test_parse_maps_to_jev_properties():
    r = parse_answers(answers(dup="slow-reviewer", conf=0.85), ["slow-reviewer"])
    assert r.properties() == {
        ns.JEV_P_TRAP: 0.7, ns.JEV_P_INSIGHT: 0.2, ns.JEV_P_PATTERN: 0.4, ns.JEV_DUP_OF: "slow-reviewer",
    }
    assert "confidence 0.85" in r.body_section()
    assert r.input_tokens == 1234


def test_parse_unknown_slug_becomes_none():
    assert parse_answers(answers(dup="ghost"), ["slow-reviewer"]).dup_of == "none"


def test_parse_rejects_out_of_range():
    with pytest.raises(ValueError):
        parse_answers(answers(trap=1.5), [])


# --- routing -------------------------------------------------------------

def cfg(**batch):
    return Config(local={"batch": batch})


def test_client_never_goes_to_jev():
    assert not jev_enabled(cfg(client_scorer="jev"), ns.ORIGIN_CLIENT)
    assert jev_enabled(cfg(), ns.ORIGIN_PERSONAL)
    assert scorer_for(cfg(client_scorer="jev"), ns.ORIGIN_CLIENT) == "haiku"
    assert any("ignored" in w for w in config_warnings(cfg(client_scorer="jev")))


def test_personal_scorer_default_and_switch():
    assert scorer_for(cfg(), ns.ORIGIN_PERSONAL) == "haiku"
    assert scorer_for(cfg(personal_scorer="jev"), ns.ORIGIN_PERSONAL) == "jev"
    assert scorer_for(cfg(personal_scorer="gpt"), ns.ORIGIN_PERSONAL) == "haiku"


# --- client --------------------------------------------------------------

class FakeResp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_client_retries_429_then_succeeds_and_sends_bearer():
    calls = []

    def opener(req, timeout):
        calls.append(req)
        if len(calls) == 1:
            raise urllib.error.HTTPError(req.full_url, 429, "busy", {}, io.BytesIO(b"{}"))
        return FakeResp(json.dumps(answers()).encode())

    c = JevClient("secret-key", sleep=lambda s: None, opener=opener)
    assert c.system_one({"x": 1})["model"] == MODEL
    assert len(calls) == 2
    assert calls[0].get_header("Authorization") == "Bearer secret-key"


def test_client_error_never_leaks_key():
    def opener(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 401, "no", {}, io.BytesIO(b'{"detail":"bad key"}'))

    c = JevClient("secret-key", opener=opener)
    with pytest.raises(JevError) as exc:
        c.system_one({})
    assert "secret-key" not in str(exc.value) and "secret-key" not in repr(c)


def test_missing_key_fails_fast():
    with pytest.raises(JevError):
        JevClient.from_config(Config())


# --- batch step ----------------------------------------------------------

@dataclass
class Ctx:
    config: Config
    posts_dir: Path
    logs: list = field(default_factory=list)

    def log(self, m):
        self.logs.append(m)


def record(origin):
    return {"session_id": "s1", "origin": origin, "extra_properties": {"x": 1}, "extra_body": ["b"]}


def test_step_scores_personal_and_skips_client(monkeypatch, tmp_path):
    from batch.steps import jev_shadow
    from sampler import load_session

    sent = []

    class Fake:
        def system_one(self, body):
            sent.append(body)
            return answers()

    monkeypatch.setattr(jev_shadow, "client_factory", lambda config: Fake())
    transcript = tmp_path / "s1.jsonl"
    transcript.write_text("\n".join(json.dumps(e) for e in [
        {"type": "user", "timestamp": "2026-10-20T10:00:00Z", "message": {"role": "user", "content": "fix the flaky hook"}},
        {"type": "assistant", "timestamp": "2026-10-20T10:01:00Z", "message": {"role": "assistant", "content": [{"type": "text", "text": "Found a race."}]}},
    ]), encoding="utf-8")
    session = load_session(transcript)
    ctx = Ctx(Config(), tmp_path / "no-posts")

    assert jev_shadow.run(ctx, session, record(ns.ORIGIN_CLIENT)) is None
    assert sent == []

    rec = record(ns.ORIGIN_PERSONAL)
    out = jev_shadow.run(ctx, session, rec)
    assert len(sent) == 1
    assert "fix the flaky hook" in sent[0]["state"]["session_sample"]
    assert out["extra_properties"][ns.JEV_P_TRAP] == 0.7 and out["extra_properties"]["x"] == 1
    assert out["extra_body"][-1].startswith("## Jev shadow")
    assert rec["extra_properties"] == {"x": 1}  # input not mutated


# --- daily line ----------------------------------------------------------

@dataclass(frozen=True)
class N:
    title: str
    topic_key: str
    props: dict
    url: str = ""
    origin: str = ns.ORIGIN_PERSONAL


def jp(t, i=0.0, p=0.0):
    return {ns.JEV_P_TRAP: t, ns.JEV_P_INSIGHT: i, ns.JEV_P_PATTERN: p}


def test_top3_excludes_haiku_listed_client_and_unscored():
    pool = [
        N("A", "a", jp(0.9), "https://n/a"),
        N("A2", "a", jp(0.95), "https://n/a2"),
        N("B listed", "b", jp(0.99)),
        N("C", "c", jp(0.1, 0.8)),
        N("D", "d", jp(0.3)),
        N("E", "e", jp(0.2)),
        N("Client", "f", jp(1.0), origin=ns.ORIGIN_CLIENT),
        N("Unscored", "g", {}),
    ]
    picks = jev_top_topics(pool, {"b"})
    assert [(k, n.title) for k, n, _ in picks] == [("a", "A2"), ("c", "C"), ("d", "D")]
    out = render(picks)
    assert out[0] == "Jev 另外推:" and out[1] == "• A2 0.95 https://n/a2"


def test_empty_line():
    assert render([]) == ["Jev 另外推: (none)"]


def test_line_provider_uses_ctx():
    from daily.lines import jev_extra

    @dataclass
    class T:
        key: str

    @dataclass
    class C:
        pool: list
        listed: list

    out = jev_extra.lines(C([N("X", "x", jp(0.5), "u")], [T("y")]))
    assert out == ["Jev 另外推:", "• X 0.50 u"]
