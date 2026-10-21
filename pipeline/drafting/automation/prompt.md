Blog drafting session, 21:00 (spec §1.4 steps 4–6, §1.6).

Step 1. From this worktree's root, run exactly this command once and wait for it:

    {{PIPELINE_DIR}}/drafting/automation/open.sh

It runs tonight's topic list (and sends the Telegram message), closes the previous drafting
session only if it is idle, and prints this session's opening context.

Step 2. If it exits non-zero, reply with its last 5 lines and stop. Do not retry.

Step 3. Otherwise the printed text is your opening context and your instructions for this
session. Show Yvette sections 1–6 as printed, then wait for her to pick a topic or an
unfinished article. Follow "How this session works" from then on.

Rules: never push, never stash, never switch branches, never commit unless Yvette says so.
Read literature-note bodies through Notion MCP only after she picks.
