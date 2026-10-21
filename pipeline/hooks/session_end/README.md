# SessionEnd queue hook (spec §1.2)

`queue_session.py` is a user-level Claude Code `SessionEnd` hook. It reads the hook
JSON on stdin and appends the `session_id` as one line to
`${BLOG_PIPELINE_STATE_DIR:-~/.local/state/blog-pipeline}/pending-queue.txt`.

- Stdlib only, no LLM call, no judgement.
- Subagent sessions are skipped (v1 exclusion): any `transcript_path` containing `/subagents/`.
- Append is atomic: `O_APPEND` + `flock` + one `write`. Missing dirs are created.
- Always exits 0. Errors go to `<state>/hooks.log` (stderr if the log is unwritable),
  so a failing hook never blocks session end.

## Install

Add one entry to the `hooks.SessionEnd` array in `~/.claude/settings.json`, keeping
any existing entries. Use the absolute path of your checkout:

```json
{
  "hooks": [
    {
      "type": "command",
      "command": "/usr/bin/python3 /ABSOLUTE/PATH/TO/blog/pipeline/hooks/session_end/queue_session.py",
      "timeout": 5
    }
  ]
}
```

## Test

```sh
uv run --no-project --with pytest pytest -q pipeline/hooks/session_end/tests
```
