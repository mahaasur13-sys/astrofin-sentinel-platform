#!/usr/bin/env bash
# CI guard: the archive+wal-g stack must resolve MinIO via host.docker.internal
# (extra_hosts host-gateway), never a hardcoded gateway IP (172.19.0.1 etc.).
#
# Fail closed (exit 1) if either overlay lacks host.docker.internal:host-gateway
# or hardcodes a 172.x gateway IP.
#
# Deterministic: pure grep. No network, no docker daemon.

set -euo pipefail

ARCHIVE="${1:-deploy/docker/docker-compose.postgres-archive.yml}"
SIDECAR="${2:-deploy/docker/docker-compose.wal-g.yml}"
fail=0

for f in "$ARCHIVE" "$SIDECAR"; do
  # Must declare host.docker.internal:host-gateway.
  if ! grep -qE 'host\.docker\.internal:host-gateway' "$f"; then
    echo "::error:: $f must declare extra_hosts host.docker.internal:host-gateway" >&2
    fail=1
  fi
  # Must not hardcode a 172.x gateway IP.
  if grep -nE '172\.[0-9]+\.[0-9]+\.[0-9]+' "$f"; then
    echo "::error:: $f must not hardcode a gateway IP (use host.docker.internal)" >&2
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "wal-g archive extra-hosts guard FAILED" >&2
  exit 1
fi

echo "wal-g archive extra-hosts guard OK"
