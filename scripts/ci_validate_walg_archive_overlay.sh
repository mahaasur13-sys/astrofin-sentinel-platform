#!/usr/bin/env bash
# CI guard: the optional Postgres archive overlay must be safe.
#
# Fail closed (exit 1) if deploy/docker/docker-compose.postgres-archive.yml:
#   - references the live pg_data / docker_pg_data volume (must use the separate
#     pg_data_archive), or
#   - does not declare/use pg_data_archive, or
#   - does not enable archive_mode, or
#   - publishes ports (5432 must stay internal).
#
# Deterministic: pure grep. No network, no docker daemon. Comments are ignored.

set -euo pipefail

OVERLAY="${1:-deploy/docker/docker-compose.postgres-archive.yml}"
fail=0

# Non-comment lines only (so a doc comment mentioning pg_data is not flagged).
lines="$(grep -vE '^[[:space:]]*#' "$OVERLAY")"

# 1a. Must not reference the old/legacy docker_pg_data volume.
if echo "$lines" | grep -nE 'docker_pg_data'; then
  echo "::error:: archive overlay must not use docker_pg_data (use pg_data_archive)" >&2
  fail=1
fi

# 1b. Must not reference the live base `pg_data` volume (pg_data_archive is OK).
if echo "$lines" | grep -nE 'pg_data([^_a-zA-Z0-9]|$)'; then
  echo "::error:: archive overlay must not use the live pg_data volume (use pg_data_archive)" >&2
  fail=1
fi

# 1c. Must actually use the separate pg_data_archive volume.
if ! echo "$lines" | grep -qE 'pg_data_archive'; then
  echo "::error:: archive overlay must declare/use pg_data_archive" >&2
  fail=1
fi

# 2. Must enable archive_mode.
if ! echo "$lines" | grep -qE 'archive_mode[[:space:]]*=[[:space:]]*on'; then
  echo "::error:: archive overlay must enable archive_mode=on" >&2
  fail=1
fi

# 3. Must not publish any host port (5432 stays internal).
if echo "$lines" | grep -nE 'ports:'; then
  echo "::error:: archive overlay must not publish ports (5432 internal-only)" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "wal-g archive overlay guard FAILED" >&2
  exit 1
fi

echo "wal-g archive overlay guard OK"
