#!/bin/bash
# SessionStart hook for Claude Code on the web: install what tests, tools and the
# Observatory app need, so a fresh cloud container can run `pytest` and `npm run typecheck`
# immediately. Idempotent; local sessions are left untouched.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"

python3 -m pip install --quiet --disable-pip-version-check -r requirements.txt

# The app is optional for physics work; skip quietly if Node is unavailable.
if command -v npm >/dev/null 2>&1 && [ -f app/package.json ]; then
  (cd app && npm install --no-audit --no-fund --no-update-notifier --loglevel=error)
fi

# Repo packages (core, genesis, ai_lab, ...) are imported from the repo root.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  echo "export PYTHONPATH=\"${CLAUDE_PROJECT_DIR:-$PWD}\"" >> "$CLAUDE_ENV_FILE"
fi
