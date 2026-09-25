#!/usr/bin/env bash
# CI guard: WAL-G sidecar overlay must be optional, port-free, and never use an
# untrusted third-party wal-g image. TODO / missing @sha256 is a failure.
#
# Deterministic: pure grep. No network, no docker pull.

set -euo pipefail

OVERLAY="${1:-deploy/docker/docker-compose.wal-g.yml}"
fail=0

# 1. Overlay must exist.
if [[ ! -f "$OVERLAY" ]]; then
  echo "::error:: $OVERLAY missing" >&2
  exit 1
fi

# 2. Overlay must not publish ports (wal-g is a run-once CLI).
if grep -nE '^[[:space:]]+ports:' "$OVERLAY"; then
  echo "::error:: $OVERLAY must not publish ports" >&2
  fail=1
fi

# 3. No floating :latest on a real repository.
if grep -nE 'image:[[:space:]]+[^[:space:]]+:latest([@[:space:]]|$)' "$OVERLAY"; then
  echo "::error:: $OVERLAY must not use :latest" >&2
  fail=1
fi

# 4. Untrusted third-party wal-g images are forbidden.
if grep -nE 'image:[[:space:]]+[^[:space:]]*(chekkan|healthsamurai|euank|tmarkunin|koehn)/' "$OVERLAY"; then
  echo "::error:: $OVERLAY must not use an untrusted third-party wal-g image" >&2
  fail=1
fi

# 5. The image may be a TODO placeholder / unpinned — WARNING only (no public
#    official wal-g image to pin yet). Pinned (@sha256:) is also fine.
if grep -qE 'image:[[:space:]]+.*TODO' "$OVERLAY" || ! grep -qE 'image:[[:space:]]+[^[:space:]]+@sha256:' "$OVERLAY"; then
  echo "::error::$OVERLAY wal-g image is TODO or missing @sha256" >&2
  exit 1
fi

if [ "$fail" -ne 0 ]; then
  echo "wal-g sidecar guard FAILED" >&2
  exit 1
fi

echo "wal-g sidecar guard OK"
