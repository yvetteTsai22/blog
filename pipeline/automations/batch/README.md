# automations/batch — 02:00 / 04:00 Orca automations (spec §5.1, TSA-64)

Two Orca automations run the TSA-63 batch (`uv run python -m batch run`) in this worktree.

| Automation | Trigger | Grace | Precheck |
|---|---|---|---|
| `blog-pipeline batch 02:00` | `--trigger daily --time 02:00` | 60 | none, so the 21:00 run always sees a real run |
| `blog-pipeline batch 04:00 rerun` | `--trigger daily --time 04:00` | 60 | inline `precheck.inline`: skipped only when queue and outbox are verified empty (fails open) |

Timezone: `Europe/London`. Spec §5.1 says `Asia/Taipei`; the user overrode it on 2026-10-20
because they now live in London, and "no daytime run" means the user's local day.
Never use the default grace (720): a missed 02:00 would catch up mid-morning.

## Files

- `run_batch.sh <label>` — `cd pipeline && uv run python -m batch run`; logs start/exit to
  `<state>/batch.log`, prints `batch <label> exit <code>`, returns the batch exit code.
  The exit line comes from an EXIT/HUP/INT/TERM trap, so a killed run logs `exit 143 (SIGTERM)`.
  `run_batch.sh <label> wait` waits up to 570 s for that run (`<state>/batch-<label>.running|.result`)
  and prints `batch <label> exit N`, `still running` (exit 75) or `died without an exit line`.
  The 04:00 run is the same command: the batch only processes what is still queued or staged,
  so it finishes what 02:00 left (LLM errors, an unfinished writer pass).
- `precheck.inline` — the 04:00 `--precheck` string. Orca runs it with `spawn(cmd, {shell: true})`
  (`/bin/sh -c`) in the run's repo path, so it must not reference a worktree path. Any non-zero exit
  is recorded as `skipped_precheck`, so it fails open: exit 1 only when the queue has no non-blank line
  AND `outbox/` is empty (a missing queue file counts as empty); any error exits 0.
- `has_work.sh` — same logic as `precheck.inline` as a script, for local use; tests run both.
- `prompt.md` — agent prompt; `{{LABEL}}` becomes `02:00` or `04:00` at create time.

## Create commands (run from the worktree root)

```sh
orca automations create --name "blog-pipeline batch 02:00" --trigger daily --time 02:00 \
  --timezone Europe/London --missed-run-grace-minutes 60 --provider claude \
  --extra-agent-args="--model haiku" --workspace "path:$PWD" --workspace-mode existing \
  --fresh-session --enabled --prompt "$(sed 's/{{LABEL}}/02:00/g' pipeline/automations/batch/prompt.md)" --json

orca automations create --name "blog-pipeline batch 04:00 rerun" --trigger daily --time 04:00 \
  --timezone Europe/London --missed-run-grace-minutes 60 --provider claude \
  --extra-agent-args="--model haiku" --workspace "path:$PWD" --workspace-mode existing \
  --fresh-session --enabled --precheck "$(cat pipeline/automations/batch/precheck.inline)" \
  --prompt "$(sed 's/{{LABEL}}/04:00/g' pipeline/automations/batch/prompt.md)" --json
```

Check: `orca automations list --json`. Manual run: `orca automations run <uuid>`.

## Tests

`cd pipeline && uv run pytest automations/batch -q` (fake `uv` via `UV_BIN`, temp state dir).

## Unattended-run requirements

- The run agent needs `Bash(pipeline/automations/batch/run_batch.sh:*)` allowed, or it stops at a
  permission prompt. It lives in the worktree's gitignored `.claude/settings.local.json`.
- The writer pass can take 20+ minutes, longer than the 600000 ms Bash cap. Claude Code then backgrounds
  the script and kills it when the agent ends its turn (02:00 run 77eb18fc on 2026-10-21: no `exit` line).
  The prompt tells the agent to keep its turn open with `run_batch.sh <label> wait` until it finishes.
- Prompts are copied into the automation at create time. After editing `prompt.md`, run
  `orca automations edit <id> --prompt "$(sed 's/{{LABEL}}/02:00/g' pipeline/automations/batch/prompt.md)"`
  (and the same with `04:00`).
