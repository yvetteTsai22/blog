#!/bin/sh
# Precheck for the 04:00 rerun. Orca skips the run (skipped_precheck) on ANY non-zero exit,
# so this fails open: exit 1 only after positively verifying that the queue has no non-blank
# line AND outbox/ is empty. Any error (missing or unreadable state dir, unreadable queue,
# outbox not a directory) exits 0 and the run happens; the batch is a no-op when empty.
# The live automation uses precheck.inline (same logic, no worktree path); keep both in sync.
d="${BLOG_PIPELINE_STATE_DIR:-$HOME/.local/state/blog-pipeline}"
q="$d/pending-queue.txt"
o="$d/outbox"

[ -d "$d" ] && [ -r "$d" ] || exit 0
if [ -e "$q" ]; then
  [ -f "$q" ] && [ -r "$q" ] || exit 0
  grep -q '[^[:space:]]' "$q"
  [ $? -eq 1 ] || exit 0 # 0 = work queued, 2 = read error
fi
if [ -e "$o" ]; then
  [ -d "$o" ] && [ -r "$o" ] || exit 0
  n=$(ls -A "$o") || exit 0
  [ -z "$n" ] || exit 0
fi
exit 1
