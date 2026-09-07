#!/usr/bin/env bash
# CI guard: POSTGRES_USER must be required (${POSTGRES_USER:?...}), never a
# default superuser name (${POSTGRES_USER:-postgres}).
#
# Fail closed (exit 1) if any deploy/docker/ stack file defaults POSTGRES_USER
# (or the wal-g PGUSER) to 'postgres'.
#
# Deterministic: pure grep. No network, no docker.

set -euo pipefail

FILES=(
  deploy/docker/docker-compose.yml
  deploy/docker/docker-compose.postgres-archive.yml
  deploy/docker/docker-compose.wal-g.yml
)
fail=0

for f in "${FILES[@]}"; do
  if grep -nE 'POSTGRES_USER:-postgres' "$f"; then
    echo "::error:: $f must not default POSTGRES_USER to 'postgres' (use \${POSTGRES_USER:?})" >&2
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "postgres-user guard FAILED" >&2
  exit 1
fi

echo "postgres-user guard OK"
