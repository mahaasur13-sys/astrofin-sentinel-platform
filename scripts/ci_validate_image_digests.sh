#!/usr/bin/env bash
# CI guard: base stack images must be pinned tag@sha256, no floating :latest.
#
# Fail closed (exit 1) if:
#   - postgres/redis/python (base compose + Dockerfile FROM) has a tag without
#     @sha256:, or
#   - any image:/FROM line in the tracked stack files uses :latest.
#
# Scans only the explicit stack files (not the whole repo — docs/notes may
# mention "latest" in prose). Deterministic: pure grep. No network, no docker.

set -euo pipefail

BASE_FILES=(deploy/docker/docker-compose.yml deploy/docker/Dockerfile)
ALL_FILES=(
  deploy/docker/docker-compose.yml
  deploy/docker/Dockerfile
  deploy/docker/docker-compose.grafana-edge.yml
  deploy/docker/docker-compose.grafana-edge-public.yml
  deploy/docker/docker-compose.grafana-oauth2-proxy.yml
  deploy/docker/docker-compose.dex.yml
)
fail=0

# 1. MUST images (postgres/redis/python) must be tag@sha256: in base files.
for f in "${BASE_FILES[@]}"; do
  if grep -nE '(image:|FROM)[[:space:]]+(postgres|redis|python):[^@[:space:]]+' "$f" \
      | grep -v '@sha256:'; then
    echo "::error:: $f has an unpinned postgres/redis/python image (needs tag@sha256:)" >&2
    fail=1
  fi
done

# 2. No :latest on any image/FROM line in the stack files.
for f in "${ALL_FILES[@]}"; do
  if grep -nE '(image:|FROM)[[:space:]]+[^[:space:]]+:latest([@[:space:]]|$)' "$f"; then
    echo "::error:: $f has a floating :latest image" >&2
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "image digests guard FAILED" >&2
  exit 1
fi

echo "image digests guard OK"
