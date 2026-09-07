#!/usr/bin/env bash
# CI guard: the archive+wal-g stack must be wired correctly.
#
# Sidecar (docker-compose.wal-g.yml) must target postgres-archive / pg_data_archive
# and default to backup-list.
# Archive overlay (docker-compose.postgres-archive.yml) must carry the WAL-G
# storage env (WALG_S3_PREFIX, AWS_ENDPOINT) + libsodium key path so that
# archive_command `wal-g wal-push %p` can reach storage, and must keep using
# pg_data_archive (never the live pg_data).
#
# Fail closed (exit 1) on any violation. Deterministic: pure grep, comments ignored.

set -euo pipefail

SIDECAR="${1:-deploy/docker/docker-compose.wal-g.yml}"
OVERLAY="${2:-deploy/docker/docker-compose.postgres-archive.yml}"
fail=0

# --- Sidecar checks ---------------------------------------------------------
lines="$(grep -vE '^[[:space:]]*#' "$SIDECAR")"

# PGHOST must be postgres-archive, not the live base postgres.
if echo "$lines" | grep -nE 'PGHOST=postgres([^a-zA-Z0-9_-]|$)'; then
  echo "::error:: wal-g sidecar must use PGHOST=postgres-archive (not the live postgres)" >&2
  fail=1
fi
if ! echo "$lines" | grep -qE 'PGHOST=postgres-archive'; then
  echo "::error:: wal-g sidecar must set PGHOST=postgres-archive" >&2
  fail=1
fi

# Volume must be pg_data_archive, not the live pg_data.
if echo "$lines" | grep -nE 'pg_data([^_a-zA-Z0-9]|$)'; then
  echo "::error:: wal-g sidecar must mount pg_data_archive (not pg_data)" >&2
  fail=1
fi
if ! echo "$lines" | grep -qE 'pg_data_archive'; then
  echo "::error:: wal-g sidecar must mount pg_data_archive" >&2
  fail=1
fi

# Default command must be backup-list (never backup-push on every up).
if echo "$lines" | grep -qE 'command:[[:space:]]*\[[^]]*backup-push'; then
  echo "::error:: wal-g sidecar default command must be backup-list (not backup-push)" >&2
  fail=1
fi

# --- Archive overlay checks -------------------------------------------------
olines="$(grep -vE '^[[:space:]]*#' "$OVERLAY")"

# Must carry WALG_S3_PREFIX (fail-closed ${VAR:?}) — else wal-push has no storage.
if ! echo "$olines" | grep -qE 'WALG_S3_PREFIX=\$\{'; then
  echo "::error:: postgres-archive must set WALG_S3_PREFIX=\${...} (archive_command wal-push needs it)" >&2
  fail=1
fi

# Must carry AWS_ENDPOINT (fail-closed ${VAR:?}).
if ! echo "$olines" | grep -qE 'AWS_ENDPOINT=\$\{'; then
  echo "::error:: postgres-archive must set AWS_ENDPOINT=\${...} (archive_command wal-push needs it)" >&2
  fail=1
fi

# Must carry the libsodium key path (file, not literal).
if ! echo "$olines" | grep -qE 'WALG_LIBSODIUM_KEY_PATH=/run/secrets/walg_libsodium_key'; then
  echo "::error:: postgres-archive must set WALG_LIBSODIUM_KEY_PATH=/run/secrets/walg_libsodium_key" >&2
  fail=1
fi

# Volume must still be pg_data_archive, never the live pg_data.
if echo "$olines" | grep -nE 'pg_data([^_a-zA-Z0-9]|$)'; then
  echo "::error:: postgres-archive must use pg_data_archive (not pg_data)" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "wal-g archive stack guard FAILED" >&2
  exit 1
fi

echo "wal-g archive stack guard OK"
