#!/usr/bin/env bash
# Run the nightly batch (stage + write-notes) from this worktree. Spec §1.3 / §5.1.
# Usage: run_batch.sh <label>        run the batch; label is 02:00 or 04:00, used for the log line.
#        run_batch.sh <label> wait   wait up to WAIT_SECONDS (default 570) for that run to finish.
# The 04:00 run is the same command: the batch only processes what is still queued or staged.
#
# The writer pass can outlast the agent's 600 s Bash timeout. Claude Code then backgrounds the
# command and kills it when the session ends, so the exit line is written from an EXIT trap
# (also on HUP/INT/TERM), and `wait` lets the agent keep its turn open until the run finishes.
set -uo pipefail

label="${1:-manual}"
mode="${2:-run}"
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pipeline_dir="$(cd "$here/../.." && pwd)"
state_dir="${BLOG_PIPELINE_STATE_DIR:-$HOME/.local/state/blog-pipeline}"
mkdir -p "$state_dir"
log="$state_dir/batch.log"
running="$state_dir/batch-$label.running"
result="$state_dir/batch-$label.result"
uv_bin="${UV_BIN:-uv}"

stamp() { date '+%Y-%m-%dT%H:%M:%S%z'; }

wait_for_run() {
  local deadline=$((SECONDS + ${WAIT_SECONDS:-570})) pid
  while :; do
    if [ ! -e "$running" ] && [ -f "$result" ]; then
      local code
      code="$(cat "$result")"
      echo "batch $label exit $code"
      exit "$code"
    fi
    if [ ! -e "$running" ]; then
      echo "batch $label not started"
      exit 2
    fi
    pid="$(cat "$running" 2>/dev/null)"
    if [ -n "$pid" ] && ! kill -0 "$pid" 2>/dev/null; then
      echo "batch $label died without an exit line (pid $pid)"
      exit 1
    fi
    if [ "$SECONDS" -ge "$deadline" ]; then
      echo "batch $label still running"
      exit 75
    fi
    sleep "${WAIT_POLL_SECONDS:-5}"
  done
}

[ "$mode" = wait ] && wait_for_run

child=""
signal=""
on_exit() {
  local code=$?
  trap - EXIT HUP INT TERM
  [ -n "$child" ] && kill "$child" 2>/dev/null
  echo "$(stamp) automation $label exit $code${signal:+ ($signal)}" >>"$log"
  echo "$code" >"$result"
  rm -f "$running"
  echo "batch $label exit $code"
  exit "$code"
}
trap on_exit EXIT
trap 'signal=SIGHUP; exit 129' HUP
trap 'signal=SIGINT; exit 130' INT
trap 'signal=SIGTERM; exit 143' TERM

rm -f "$result"
echo "$$" >"$running"
echo "$(stamp) automation $label start" >>"$log"
cd "$pipeline_dir" || exit 2
# Background + wait so a signal runs the trap now instead of after the batch finishes.
"$uv_bin" run python -m batch run &
child=$!
wait "$child"
code=$?
child=""
exit "$code"
