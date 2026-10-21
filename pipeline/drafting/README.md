# drafting — 21:00 drafting session (spec §1.4 steps 5–6, §1.6, §5.1 21:00 row; TSA-67)

One Orca automation at 21:00 runs in the `draft-blog` worktree. Its agent runs
`drafting/automation/open.sh`, which:

1. runs the TSA-65 daily run in-process (`daily.runner.run`: rank, pool updates, extra steps,
   Telegram message);
2. closes the previous drafting session **only if idle**: every agent pane Orca tracks in the
   worktree whose state is `done` and that is not this session gets `orca terminal close`.
   Any other state is kept. No git command is run; nothing is committed or stashed;
3. prints the opening context, in order:
   1. unfinished articles (`blog status=寫作中` or `note pending`): title, days, draft path;
   2. today's list, the same text as the Telegram message;
   3. Notion links (not bodies) to the listed topics' literature notes;
   4. blog `.claude/CLAUDE.md`, the `article-writing` skill, the 2 most recent `_posts/`;
   5. uncommitted changes (`git status`, plus gitignored `_drafts/` files), one line each with
      the article slug;
   6. client-origin literature notes, highlighted;

   followed by the session instructions in `session.md` (pick flow and publish flow).

The agent shows that to Yvette and waits for a pick. The run completes when the agent goes idle;
the session stays open for writing.

```sh
uv run python -m drafting open --repo ~/orca/workspaces/blog/draft-blog                     # real run
uv run python -m drafting open --repo ~/orca/workspaces/blog/draft-blog --dry-run --scrub   # preview
uv run python -m drafting close-previous --repo ~/orca/workspaces/blog/draft-blog --dry-run
```

A real run also saves the opening context to `<state>/drafting/opening-<date>.md`.
`--dry-run` makes no Telegram send, no Notion writes and closes nothing.

## Pipeline location

`pipeline/` is not on `master` yet, so the automation calls it in the `blog-pipeline` worktree.
That path is one value, `{{PIPELINE_DIR}}` in `automation/prompt.md`, substituted at create time.
Once `pipeline/` is merged to `master` (and so into `draft-blog`), edit the automation's prompt
to use the `draft-blog` copy.

## Create command (run once; timezone is Europe/London by user decision)

```sh
PIPELINE_DIR=~/orca/workspaces/blog/blog-pipeline/pipeline
orca automations create --name "blog-pipeline 21:00 list + drafting" --trigger daily --time 21:00 \
  --timezone Europe/London --missed-run-grace-minutes 180 --provider claude \
  --workspace "path:$HOME/orca/workspaces/blog/draft-blog" --workspace-mode existing \
  --fresh-session --enabled \
  --prompt "$(sed "s#{{PIPELINE_DIR}}#$PIPELINE_DIR#g" "$PIPELINE_DIR/drafting/automation/prompt.md")" --json
```

Manual run: `orca automations run <id>` (a real run: it sends Telegram and writes Notion).

## Drafts and git

`_drafts/` is gitignored on `master`, so the session commits a draft with
`git add -f _drafts/<slug>.md`, one article per commit, only when Yvette says so.
`draft-blog` is never pushed.

## Tests

`uv run pytest drafting -q` — synthetic notes, a fake `orca`, and a temp git repo.
