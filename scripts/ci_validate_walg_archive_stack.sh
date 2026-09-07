#!/usr/bin/env bash
# CI guard: the wal-g sidecar in the archive stack must target the archive
# cluster (postgres-archive / pg_data_archive), never the live base postgres.
#
# Fail closed (exit 1) if deploy/docker/docker-compose.wal-g.yml:
#   - sets PGHOST to the live base `postgres` (must be postgres-archive), or
#   - mounts the live `pg_data` volume (must be pg_data_archive), or
#   - has a default command of backup-push (must be backup-list).
#
# Deterministic: pure grep. No network, no docker daemon. Comments are ignored.

set -euo pipefail

SIDECAR="${1:-deploy/docker/docker-compose.wal-g.yml}"
fail=0

# Non-comment lines only.
lines="$(grep -vE '^[[:space:]]*#' "$SIDECAR")"

# 1. PGHOST must be postgres-archive, not the live base postgres.
if echo "$lines" | grep -nE 'PGHOST=postgres([^a-zA-Z0-9_-]|$)'; then
  echo "::error:: wal-g sidecar must use PGHOST=postgres-archive (not the live postgres)" >&2
  fail=1
fi
if ! echo "$lines" | grep -qE 'PGHOST=postgres-archive'; then
  echo "::error:: wal-g sidecar must set PGHOST=postgres-archive" >&2
  fail=1
fi

# 2. Volume must be pg_data_archive, not the live pg_data.
if echo "$lines" | grep -nE 'pg_data([^_a-zA-Z0-9]|$)'; then
  echo "::error:: wal-g sidecar must mount pg_data_archive (not pg_data)" >&2
  fail=1
fi
if ! echo "$lines" | grep -qE 'pg_data_archive'; then
  echo "::error:: wal-g sidecar must mount pg_data_archive" >&2
  fail=1
fi

# 3. Default command must be backup-list (never backup-push on every up).
if echo "$lines" | grep -qE 'command:[[:space:]]*\[[^]]*backup-push'; then
  echo "::error:: wal-g sidecar default command must be backup-list (not backup-push)" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "wal-g archive stack guard FAILED" >&2
  exit 1
fi

echo "wal-g archive stack guard OK"
