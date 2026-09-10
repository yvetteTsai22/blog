#!/bin/bash
# Worktree setup: install all dependencies for the hybrid Jekyll + Vite blog.
# Safe to re-run. Run from the repo root (any worktree).

set -euo pipefail
cd "$(dirname "$0")"

echo "==> bundle install (Jekyll, Ruby 3.2)"
bundle install

echo "==> npm install (root gulp pipeline, Node 18)"
npm install

for pkg in _tool-recommends/*/package.json; do
  dir=$(dirname "$pkg")
  echo "==> npm install --legacy-peer-deps ($dir)"
  (cd "$dir" && npm install --legacy-peer-deps)
done

echo "==> npm install --legacy-peer-deps (fire-calculator)"
(cd fire-calculator && npm install --legacy-peer-deps)

echo "==> setup complete"
