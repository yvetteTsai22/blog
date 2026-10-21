Nightly blog-pipeline batch ({{LABEL}} run, spec §1.3 / §5.1).

Run exactly this one command from the repository root and wait for it to finish.
Use the Bash tool with timeout 600000 and do not run it in the background; the writer pass can take 20+ minutes:

    pipeline/automations/batch/run_batch.sh {{LABEL}}

If the Bash tool reports the command "was moved to the background", do NOT end your turn: the run is killed
when the session ends. Instead run this with the Bash tool (timeout 600000), and repeat it each time it prints
`batch {{LABEL}} still running`:

    pipeline/automations/batch/run_batch.sh {{LABEL}} wait

Rules:
- Do not edit, create or delete any files. Do not run git add, commit, stash, push or switch branches.
- Do not retry, do not run other batch subcommands, and do not call Notion or any MCP tool yourself.
  The script already stages the queue and runs one writer pass.
- When it exits, reply with one line: the last line the script printed and its exit code. Then stop.
