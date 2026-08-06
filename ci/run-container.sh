#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-autopilot}"
IMAGE="${AETERNA_CI_IMAGE:-aeterna-genesis-ci:local}"
ARTIFACTS="${CI_ARTIFACTS_HOST:-$(pwd)/ci-artifacts}"
CPUS="${CI_CPUS:-2}"
MEMORY="${CI_MEMORY:-4g}"

if command -v docker >/dev/null 2>&1; then
  ENGINE=docker
elif command -v podman >/dev/null 2>&1; then
  ENGINE=podman
else
  echo "Docker or Podman is required." >&2
  exit 2
fi

mkdir -p "$ARTIFACTS"
"$ENGINE" build --file ci/Dockerfile --tag "$IMAGE" .
"$ENGINE" run --rm \
  --cpus "$CPUS" \
  --memory "$MEMORY" \
  --volume "$ARTIFACTS:/artifacts" \
  "$IMAGE" "$PROFILE"

echo "CI artifacts: $ARTIFACTS"
