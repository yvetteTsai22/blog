---
description: Start a daytime drafting session (dry run, no Telegram, no list counters)
argument-hint: "[Notion literature-note URL | topic]"
---

Start a drafting session now, the same way the 21:00 automation does, but read-only until I pick.

1. Read `pipeline/drafting/session.md` and follow it for the rest of this session.
2. If `$ARGUMENTS` is empty: from the repo root run
   `cd pipeline && uv run python -m drafting open --repo .. --dry-run`
   and show me its output (unfinished articles, today's list, Notion links). Then wait for my pick.
   If `$ARGUMENTS` is not empty, treat it as my pick (a Notion literature-note URL or a topic
   from the list) and skip the opener.
3. After the pick, follow `session.md` from "After Yvette picks a topic".

Never run the opener without `--dry-run`: a real run sends Telegram and advances the
`推薦過` / cooldown counters. Do not push, stash, or switch branches.
