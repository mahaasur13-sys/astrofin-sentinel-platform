#!/usr/bin/env bash
# CI guard: volume snapshot must be grafana/redis-only and refuse pg_data/live paths.
#
# Fail closed (exit 1) if the snapshot script:
#   - allows postgres/pg/wal-g, or
#   - has no pg_data / docker volumes dir refusal, or
#   - defaults its destination to a live volume path.
#
# Deterministic: pure grep. No docker run, no network.

set -euo pipefail

SCRIPT="${1:-scripts/volume_snapshot.sh}"
fail=0

# 1. Must refuse postgres (WAL-G only).
if ! grep -qE 'refusing to snapshot (postgres|pg|wal-g)|WAL-G only' "$SCRIPT"; then
  echo "::error:: $SCRIPT does not refuse postgres/pg (must be WAL-G only)" >&2
  fail=1
fi

# 2. Must refuse pg_data / docker_pg_data destinations.
if ! grep -qE 'pg_data|docker_pg_data' "$SCRIPT"; then
  echo "::error:: $SCRIPT has no pg_data destination refusal" >&2
  fail=1
fi

# 3. Must refuse the docker volumes dir.
if ! grep -qE '/var/lib/docker/volumes' "$SCRIPT"; then
  echo "::error:: $SCRIPT has no docker-volumes-dir refusal" >&2
  fail=1
fi

# 4. Destination must not default to a live volume path.
if grep -nE '^(DEST|OUT)="?[^"]*(/var/lib/docker/volumes|pg_data|docker_pg_data)' "$SCRIPT"; then
  echo "::error:: $SCRIPT defaults its destination to a live volume path" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "volume snapshot guard FAILED" >&2
  exit 1
fi

echo "volume snapshot guard OK"
