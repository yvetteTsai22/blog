# daily — 21:00 ranking, pool updates and Telegram message (spec §1.4, §1.5, §3)

Zero LLM calls. Python talks to Notion REST and the Telegram Bot API directly.

```sh
uv run python -m daily run                       # rank, write pool updates, run steps, send
uv run python -m daily run --dry-run             # print the message; no Telegram, no Notion writes
uv run python -m daily run --dry-run --scrub     # same, session content replaced by [scrubbed]
uv run python -m daily run --dry-run --json      # also print the run summary (topics, planned updates)
```

## What a run does

1. Queries the Slip box (by data source id, never by search) for `source = agent-session`
   notes created in the last 15 days.
2. **Eligibility** (§3): `pick_status` in 未推薦/推薦過, at most 14 days old, and at least 7 days
   since `last_listed_at`.
3. Reads the body of each eligible note once (cached in `<state>/daily/body-cache.json`):
   `active_minutes` from the structural features, the lesson (first sentence of `## Learned`),
   and the first GitHub PR or commit link.
4. **Ranking** (`ranking.py`):
   - a session counts only if max(p_trap, p_insight, p_pattern) ≥ 0.6 (before weighting);
   - session score = max p × (1 + 0.3 × active-minutes percentile among eligible notes) ×
     (0.5 if `dup_of` ≠ none at confidence ≥ 0.8);
   - sessions group by `topic_of` (`new` or empty = its own topic); topic score = best session's
     max p × its dup factor × (1 + 0.3 × percentile of the topic's summed minutes among topics);
   - top 3 are listed; the rest over the threshold go on the "other topics" line.
5. **Pool updates** (`pool.py`): every 未推薦/推薦過 note sharing a listed `topic_of` gets
   `last_listed_at = today`, `listed_count = topic max + 1`, and `pick_status = 推薦過`, or
   `放棄` when that count reaches 2 (it is still listed that night).
6. Runs extra steps from `daily/steps/`.
7. Builds and sends the message (every night, 0 topics included). Long messages split at 4096
   chars. The run summary goes to `<state>/daily/last-run.json`, logs to `<state>/daily/daily.log`.

Message sections, in order: batch status (`orca automations runs --json`, last 24 h, plus queue
length; "did not run" line; ⚠ when the queue is over 100) → per topic: title, reason line
`<signal> <score> · <n> sessions · <min> min`, `熱度 · 痛點` (only when market values exist),
primary reader question, `延續〈post〉`, `⚠ <privacy reason>`, topic line providers, then per
session the lesson, PR/commit link and `claude --resume <id>` → other topics → global line
providers → `寫作中` reminders over 14 days.

## Config (`pipeline.local.yml`, gitignored)

```yaml
notion:
  token: ...                      # internal integration shared with the Slip box
telegram:
  bot_token: ...
  chat_id: ...
daily:
  timezone: Europe/London         # default; "today", ages and cooldown use this zone
  batch_automation_names: [batch] # case-insensitive substrings of the batch automation names
```

Secrets are read only from this file and never printed.

## Extension: `daily/steps/` (extra 21:00 steps)

Any module `daily/steps/<name>.py` not starting with `_` that defines `run` is discovered. Steps run
after the pool updates and before the message is built (e.g. TSA-68 reconciliation).

```python
NAME = "reconcile"   # optional, defaults to the module name
ORDER = 50           # optional, default 100; lower runs first

def run(ctx):
    """ctx is daily.runner.Context. Respect ctx.dry_run: no external writes when it is True."""
    ctx.results["reconcile"] = {"published": 1}
```

`ctx` fields: `config` (`ctx.config.get("a.b")`), `state_dir`, `now`, `tz`, `today`, `dry_run`,
`notion` (`daily.notion.Notion`: `query`, `page_text`, `update_page`), `notes` (all recent notes),
`pool` (eligible notes), `topics`, `listed`, `others`, `updates`, `results` (a dict steps fill for
line providers), `log(msg)`. A step that raises is logged and skipped.

## Extension: `daily/lines/` (message line providers)

Any module `daily/lines/<name>.py` with `KIND` and `lines` is discovered.

```python
KIND = "global"      # once per message, after the "other topics" line (Jev, reconciliation result)
ORDER = 50

def lines(ctx):
    return ["Jev 另外推: ..."]
```

```python
KIND = "topic"       # once per listed topic, after its built-in lines, before its sessions

def lines(ctx, topic):
    """topic: daily.ranking.Topic (key, notes, score, best, active_minutes, signal)."""
    return [f"market: {topic.best.props.get('market_status')}"]
```

`lines/resume_drafting.py` (ORDER 1000) prints the `claude --continue` line for the drafting
worktree (`daily.drafting_dir`, default `~/orca/workspaces/blog/draft-blog`).

`Note.props` holds every Slip box property as a plain value, so providers can read properties this
module does not model (e.g. `jev_p_trap`). A provider that raises is logged and contributes nothing.

## Tests

`uv run pytest daily` — synthetic notes only.
