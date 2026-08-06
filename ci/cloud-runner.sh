#!/usr/bin/env bash
# Run from cron/systemd on any Linux VM with Git and Docker/Podman.
set -euo pipefail

REPO_URL="${AETERNA_REPO_URL:-https://github.com/sunpotflower4460-cpu/Aeterna-Genesis.git}"
REF="${AETERNA_REF:-main}"
PROFILE="${AETERNA_CI_PROFILE:-autopilot}"
WORK_ROOT="${AETERNA_CI_WORK_ROOT:-/var/lib/aeterna-ci}"
CHECKOUT="$WORK_ROOT/repository"
LOCK="$WORK_ROOT/runner.lock"

mkdir -p "$WORK_ROOT"

run_ci() {
  if [[ ! -d "$CHECKOUT/.git" ]]; then
    git clone --filter=blob:none "$REPO_URL" "$CHECKOUT"
  fi
  git -C "$CHECKOUT" fetch --prune origin
  git -C "$CHECKOUT" checkout --force "$REF"
  git -C "$CHECKOUT" reset --hard "origin/$REF" 2>/dev/null || true
  (
    cd "$CHECKOUT"
    CI_ARTIFACTS_HOST="$WORK_ROOT/artifacts" bash ci/run-container.sh "$PROFILE"
  )
}

if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK"
  flock -n 9 || { echo "Aeterna CI is already running"; exit 0; }
  run_ci
else
  run_ci
fi
