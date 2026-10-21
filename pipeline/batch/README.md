# batch — 02:00 / 04:00 nightly batch (spec §1.3)

Two phases, so Python never talks to Notion:

1. **Stage** (`uv run python -m batch stage`): drains `<state>/pending-queue.txt` in order.
   Per session: empty check → structural features → targeted sample (all from `sampler/`) →
   one `claude -p` summary + scoring call (`summarize/`) → per-session steps → staged note at
   `<state>/outbox/<sessionId>.json` (properties + markdown body, built by `notes/`).
   Then nightly steps run once. Status goes to `<state>/batch-status.json`, log to `<state>/batch.log`.
2. **Write** (`uv run python -m batch write-notes`): ONE headless agent pass per batch, using the
   instructions in `write_notes_prompt.md` and the notion-personal MCP. For each staged note it
   queries the Slip box by `session id`, creates the page only if missing, then runs
   `uv run python -m batch commit <sid> --page-id <id>`, which records the write in
   `<state>/written.jsonl`, deletes the outbox file and removes the id from the queue.
   An Orca automation can paste the same prompt file to its own agent instead.

`uv run python -m batch run` does both. `uv run python -m batch pending` prints what is staged.

## Idempotency and queue rules

| Queue entry state | Action |
|---|---|
| in `written.jsonl` | dropped from queue, nothing written |
| already staged in outbox | skipped (no new LLM call), waits for the write pass |
| transcript missing | dropped, logged |
| empty (0 tool calls, ≤1 real prompt) | dropped, nothing written |
| LLM or parse error | left in queue for the 04:00 rerun, logged |
| over the per-night cap | left in queue (`deferred_by_cap`) |

The Notion query by `session id` is the second guard: a rerun after a lost `commit` finds the
existing page and commits its id instead of creating a duplicate.

## Limits

- At most 60 notes per cycle (02:00 → 02:00), counting written plus staged.
- `queue_length` and `queue_warning` (> 100) are written to `batch-status.json` for the 21:00 run.

## Config (`pipeline.local.yml`, gitignored)

```yaml
batch:
  model: haiku               # summary + scoring model for claude -p
  writer_model: haiku        # model for the write-notes agent pass
  max_notes_per_night: 60
  client_projects: []        # substrings of ~/.claude/projects/<slug>; match => origin=client
  denylist: []               # extra never-mention terms, scrubbed from model output
```

The summary call runs from an empty temp dir with `--setting-sources project
--no-session-persistence --strict-mcp-config --tools ""`, so the user `SessionEnd` hook does not
re-queue it and the model has no tools.

## Step interface (`batch/steps/`)

Any module `batch/steps/<name>.py` (not starting with `_`) is auto-discovered. No runner edits.

```python
NAME = "jev_shadow"   # optional, defaults to the module name
KIND = "session"      # "session" (per staged note) or "nightly" (once after the loop)
ORDER = 50            # optional, default 100; lower runs first

def run(ctx, session, record):   # KIND == "session"
    """Return a new record dict (or None to keep it). Do not mutate `record`."""
    return {
        **record,
        "extra_properties": {**record["extra_properties"], "jev_p_trap": 0.4},
        "extra_body": [*record["extra_body"], "## Jev shadow\n..."],
    }

def run(ctx, status):            # KIND == "nightly"
    """status: this run's batch-status dict (cycle, staged ids, queue_length, ...)."""
```

- `ctx` is `batch.runner.Context`: `state_dir`, `config` (`ctx.config.get("a.b")`), `now`,
  `cycle`, `model`, `log(msg)`.
- `session` is `sampler.Session` (raw events, for steps that need the sample, e.g. Jev).
- `record` keys: `session_id`, `cycle`, `origin`, `topic_of`, `summary` (all §1.3 step-4 fields),
  `features`, `extra_properties` (merged into Notion properties — use names from
  `common/notion_schema.py`), `extra_body` (markdown sections appended to the note body).
- A step that raises is logged and skipped; the note is still staged. A nightly step failure
  never fails the batch.
