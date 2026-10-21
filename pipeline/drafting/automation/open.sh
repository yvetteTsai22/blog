#!/usr/bin/env bash
# 21:00 drafting run (spec §1.4 steps 4–6). Run from the draft-blog worktree root.
# Usage: open.sh [--dry-run [--scrub]]
# The pipeline code is found next to this script, so the automation prompt names one path.
set -uo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pipeline_dir="$(cd "$here/../.." && pwd)"
repo="${DRAFT_BLOG_WORKTREE:-$PWD}"
uv_bin="${UV_BIN:-uv}"

cd "$pipeline_dir" || exit 2
exec "$uv_bin" run python -m drafting open --repo "$repo" "$@"
