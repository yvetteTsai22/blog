"""Ranking, pool updates, message and discovery on synthetic notes."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from common import notion_schema as ns
from common.config import Config
from daily import batch_status, discovery, message, pool, ranking, runner
from daily.notes import Note, from_page, parse_body

TODAY = date(2026, 10, 20)
NOW = datetime(2026, 10, 20, 20, 0, tzinfo=timezone.utc)


def note(pid, trap=0.0, insight=0.0, pattern=0.0, topic="t1", minutes=10.0, age=1, **kw) -> Note:
    return Note(
        page_id=pid,
        title=f"title {pid}",
        session_id=f"sid-{pid}",
        created=NOW - timedelta(days=age),
        topic_of=topic,
        p={ns.P_TRAP: trap, ns.P_INSIGHT: insight, ns.P_PATTERN: pattern},
        active_minutes=minutes,
        **kw,
    )


# --- ranking ---------------------------------------------------------------

def test_percentile_midpoint_ties():
    assert ranking.percentile(5, []) == 0.0
    assert ranking.percentile(5, [5]) == 0.5
    assert ranking.percentile(10, [1, 5, 10, 20]) == pytest.approx(0.625)


def test_session_score_formula():
    n = note("a", insight=0.8, minutes=30)
    pop = [10, 20, 30, 40]
    assert ranking.session_score(n, pop) == pytest.approx(0.8 * (1 + 0.3 * 0.625))


def test_dup_penalty_only_at_confidence():
    assert ranking.dup_factor(note("a", dup_of="old-post", dup_conf=0.8)) == 0.5
    assert ranking.dup_factor(note("a", dup_of="old-post", dup_conf=0.79)) == 1.0
    assert ranking.dup_factor(note("a", dup_of="none", dup_conf=0.99)) == 1.0


@pytest.mark.parametrize(
    "kw,expected",
    [
        ({}, True),
        ({"age": 14}, True),
        ({"age": 15}, False),
        ({"pick_status": ns.PICK_PICKED}, False),
        ({"pick_status": ns.PICK_ABANDONED}, False),
        ({"pick_status": ns.PICK_LISTED, "last_listed_at": TODAY - timedelta(days=6)}, False),
        ({"pick_status": ns.PICK_LISTED, "last_listed_at": TODAY - timedelta(days=7)}, True),
    ],
)
def test_eligibility(kw, expected):
    assert ranking.is_eligible(note("a", **kw), TODAY) is expected


def test_threshold_is_on_raw_max_p():
    # 0.55 * 1.3 would clear 0.6 after weighting; the threshold is before weighting.
    topics = ranking.rank_topics([note("a", trap=0.55, minutes=100), note("b", trap=0.6, topic="t2", minutes=1)])
    assert [t.key for t in topics] == ["t2"]


def test_grouping_summed_minutes_and_top3():
    pool_ = [
        note("a1", pattern=0.7, topic="A", minutes=5),
        note("a2", pattern=0.65, topic="A", minutes=50),
        note("b", insight=0.75, topic="B", minutes=5),
        note("c", trap=0.9, topic="C", minutes=1),
        note("d", trap=0.61, topic="D", minutes=1),
        note("e", trap=0.3, topic="A", minutes=500),  # below threshold: ignored, not summed
    ]
    topics = ranking.rank_topics(pool_)
    a = next(t for t in topics if t.key == "A")
    assert a.active_minutes == 55
    assert [n.page_id for n in a.notes] and "e" not in [n.page_id for n in a.notes]
    listed, others = ranking.split(topics)
    assert len(listed) == 3 and len(others) == 1
    assert others[0].key == "D"
    assert [t.score for t in topics] == sorted((t.score for t in topics), reverse=True)


def test_new_topic_is_its_own_group():
    topics = ranking.rank_topics([note("a", trap=0.7, topic="new"), note("b", trap=0.7, topic="new")])
    assert {t.key for t in topics} == {"a", "b"}


def test_topic_score_uses_best_session_with_dup_penalty():
    t = ranking.rank_topics([note("a", trap=0.9, dup_of="p", dup_conf=0.9)])[0]
    assert t.score == pytest.approx(0.9 * 0.5 * (1 + 0.3 * 0.5))


def test_zero_topics():
    assert ranking.rank_topics([note("a", trap=0.2)]) == []


# --- pool --------------------------------------------------------------------

def test_first_listing_sets_listed_on_all_topic_notes():
    a, a_cool = note("a", trap=0.8, topic="T"), note("x", topic="T", pick_status=ns.PICK_LISTED)
    other = note("o", trap=0.1, topic="U")
    topics = ranking.rank_topics([a])
    ups = pool.plan_updates(topics, [a, a_cool, other], TODAY)
    assert {u.page_id for u in ups} == {"a", "x"}
    assert all(u.pick_status == ns.PICK_LISTED and u.listed_count == 1 and u.last_listed_at == TODAY for u in ups)


def test_second_listing_abandons():
    a = note("a", trap=0.8, topic="T", pick_status=ns.PICK_LISTED, listed_count=1)
    ups = pool.plan_updates(ranking.rank_topics([a]), [a], TODAY)
    assert ups[0].pick_status == ns.PICK_ABANDONED and ups[0].listed_count == 2


def test_picked_notes_not_touched():
    a, picked = note("a", trap=0.8, topic="T"), note("p", topic="T", pick_status=ns.PICK_PICKED)
    ups = pool.plan_updates(ranking.rank_topics([a]), [a, picked], TODAY)
    assert [u.page_id for u in ups] == ["a"]


def test_update_payload_shape():
    u = pool.PoolUpdate("a", "T", ns.PICK_LISTED, TODAY, 1)
    assert u.properties() == {
        "pick_status": {"select": {"name": "推薦過"}},
        "last_listed_at": {"date": {"start": "2026-10-20"}},
        "listed_count": {"number": 1},
    }


# --- notes parsing -------------------------------------------------------------

def test_from_page_and_body():
    page = {
        "id": "pg1",
        "created_time": "2026-10-19T10:00:00.000Z",
        "url": "https://www.notion.so/pg1",
        "properties": {
            "Title": {"type": "title", "title": [{"plain_text": "Synthetic"}]},
            "p_trap": {"type": "number", "number": 0.7},
            "p_insight": {"type": "number", "number": None},
            "pick_status": {"type": "select", "select": {"name": "推薦過"}},
            "last_listed_at": {"type": "date", "date": {"start": "2026-10-10"}},
            "privacy_flag": {"type": "checkbox", "checkbox": True},
            "reader_questions": {"type": "rich_text", "rich_text": [{"plain_text": "fix: Why X?\nunderstand: How Y?"}]},
        },
    }
    n = from_page(page)
    assert n.max_p == 0.7 and n.argmax_signal == ns.P_TRAP
    assert n.last_listed_at == date(2026, 10, 10) and n.privacy_flag
    assert n.reader_questions[0] == {"question": "Why X?", "kind": "fix"}
    body = parse_body(
        "## Learned\nFirst lesson. Second.\n## Structural features\nactive_minutes: 42.5\n"
        "see https://github.com/example/repo/pull/12"
    )
    assert body == {"active_minutes": 42.5, "lesson": "First lesson.", "link": "https://github.com/example/repo/pull/12"}
    assert parse_body("## Learned\n(none)") == {"active_minutes": 0.0, "lesson": "", "link": ""}


# --- batch status ------------------------------------------------------------

def test_batch_status_lines():
    runs = {"result": {"runs": [
        {"automationId": "x", "status": "completed", "scheduledFor": "2026-10-20T01:00:00Z"},
        {"automationId": "x", "status": "completed", "scheduledFor": "2026-10-18T01:00:00Z"},
        {"automationId": "y", "status": "completed", "scheduledFor": "2026-10-20T19:00:00Z"},
    ]}}
    autos = {"result": {"automations": [{"id": "x", "name": "Blog batch 02:00"}, {"id": "y", "name": "daily list"}]}}
    hits = batch_status.last_night(batch_status.parse_runs(runs, autos), NOW)
    assert len(hits) == 1
    lines = batch_status.status_lines(hits, 3, ZoneInfo("Europe/London"))
    assert lines == ["batch 02:00 completed", "queue: 3"]
    missing = batch_status.status_lines([], 120, ZoneInfo("Europe/London"))
    assert "did not run, 120 sessions pending" in missing[0]
    assert missing[-1].startswith("⚠ queue over 100")


# --- message -------------------------------------------------------------------

def test_message_zero_topics_and_reminders():
    text = message.render("H", ["queue: 0"], [], [], [{"title": "Old", "days": 20, "draft_path": "_drafts/x.md"},
                                                         {"title": "New", "days": 3}])
    assert "0 topics" in text and "寫作中 20 天: Old" in text and "New" not in text


def test_message_topic_lines():
    a = note("a", insight=0.8, topic="T", dup_of="old-post", dup_conf=0.5, privacy_flag=True,
             privacy_reason="client name", lesson="Do X.", link="https://github.com/e/r/commit/abcdef1",
             reader_questions=({"question": "Why?", "kind": "understand"},), market_heat=3)
    b = note("b", trap=0.7, topic="U")
    listed, others = ranking.split(ranking.rank_topics([a, b]), limit=1)
    text = message.render("H", [], listed, others, [], topic_providers=[lambda t: ["EXTRA"]],
                          global_providers=[lambda: ["GLOBAL"]])
    for expected in ("insight 0.", "1 sessions", "熱度 3 · 痛點 —", "Q (understand): Why?", "延續〈old-post〉",
                     "⚠ client name", "Do X.", "commit/abcdef1", "claude --resume sid-a", "EXTRA",
                     "其他題目: title b", "GLOBAL"):
        assert expected in text


def test_telegram_chunks():
    from daily.telegram import chunks
    parts = chunks("a" * 10 + "\n" + "b" * 5 + "\n", limit=8)
    assert "".join(parts) == "a" * 10 + "\n" + "b" * 5 + "\n" and all(len(p) <= 8 for p in parts)


# --- discovery + runner with fakes ------------------------------------------------

def test_discovery_of_steps_and_lines(tmp_path, monkeypatch):
    pkg = tmp_path / "fakeplug"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "b_step.py").write_text("ORDER = 5\ndef run(ctx): ctx.results['b'] = 1\n")
    (pkg / "a_topic.py").write_text("KIND = 'topic'\ndef lines(ctx, topic): return ['x']\n")
    (pkg / "c_global.py").write_text("KIND = 'global'\nORDER = 1\ndef lines(ctx): return ['g']\n")
    (pkg / "_private.py").write_text("def run(ctx): raise SystemExit\n")
    monkeypatch.syspath_prepend(str(tmp_path))
    import fakeplug
    assert [s.name for s in discovery.discover_steps(fakeplug)] == ["b_step"]
    found = discovery.discover_lines(fakeplug)
    assert [p.name for p in found["topic"]] == ["a_topic"] and [p.name for p in found["global"]] == ["c_global"]


class FakeNotion:
    def __init__(self, pages, bodies):
        self.pages, self.bodies, self.updated = pages, bodies, []

    def query(self, filter_):
        return [] if "property" in filter_ else list(self.pages)

    def page_text(self, pid):
        return self.bodies.get(pid, "")

    def update_page(self, pid, props):
        self.updated.append((pid, props))


def _page(pid, p_trap, topic):
    return {"id": pid, "created_time": "2026-10-19T10:00:00.000Z", "properties": {
        "Title": {"type": "title", "title": [{"plain_text": f"T {pid}"}]},
        "p_trap": {"type": "number", "number": p_trap},
        "topic_of": {"type": "rich_text", "rich_text": [{"plain_text": topic}]},
        "session id": {"type": "rich_text", "rich_text": [{"plain_text": f"sid-{pid}"}]},
    }}


@pytest.mark.parametrize("dry", [True, False])
def test_runner_end_to_end(tmp_path, monkeypatch, dry):
    fake = FakeNotion([_page("p1", 0.8, "T"), _page("p2", 0.2, "T"), _page("p3", 0.1, "U")],
                      {"p1": "## Learned\nLesson one.\nactive_minutes: 12"})
    sent = []
    monkeypatch.setattr(runner.telegram, "send", lambda cfg, text: sent.append(text) or [7])
    monkeypatch.setattr(runner, "batch_lines", lambda ctx: ["queue: 0"])
    monkeypatch.setattr(runner, "discover_steps", lambda: [discovery.Plugin("s", "step", 1, lambda c: c.results.update(s=1))])
    ctx = runner.Context(config=Config(), state_dir=tmp_path, now=NOW, dry_run=dry, notion=fake)
    out = runner.run(ctx)
    assert "Lesson one." in out["message"] and ctx.results == {"s": 1}
    if dry:
        assert fake.updated == [] and sent == [] and not (tmp_path / "daily" / "last-run.json").exists()
    else:
        assert sorted(pid for pid, _ in fake.updated) == ["p1", "p2"] and sent and out["telegram_message_ids"] == [7]
    scrubbed = runner.build_message(ctx, [], ["queue: 0"], scrub=True)
    assert "Lesson one." not in scrubbed and "T p1" not in scrubbed and "claude --resume [scrubbed]" in scrubbed
