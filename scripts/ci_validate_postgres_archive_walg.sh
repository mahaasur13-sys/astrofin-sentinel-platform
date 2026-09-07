#!/usr/bin/env bash
# CI guard: the postgres-archive image must be Debian/glibc + pinned wal-g.
#
# Fail closed (exit 1) if:
#   - deploy/docker/Dockerfile.postgres-archive has a FROM on alpine, or
#   - its wal-g COPY --from does NOT pin the signed wal-g-pg digest
#     @sha256:8de34314…, or
#   - the archive overlay uses an alpine postgres image, or does not use the
#     ghcr.io/mahaasur13-sys/astrofin-postgres-archive image, or still references
#     the live pg_data / docker_pg_data volume.
#
# Deterministic: pure grep. No network, no docker daemon. Comments are ignored.

set -euo pipefail

DOCKERFILE="${1:-deploy/docker/Dockerfile.postgres-archive}"
OVERLAY="${2:-deploy/docker/docker-compose.postgres-archive.yml}"
fail=0

# 1. Dockerfile FROM must not be alpine (glibc wal-g needs Debian/Ubuntu).
if grep -nE '^FROM[[:space:]]+.*alpine' "$DOCKERFILE"; then
  echo "::error:: postgres-archive Dockerfile FROM must not be alpine" >&2
  fail=1
fi

# 2. wal-g COPY --from must pin the signed wal-g-pg digest @sha256:8de34314…
if ! grep -nE 'COPY[[:space:]]+--from=ghcr\.io/mahaasur13-sys/wal-g-pg.*@sha256:8de34314' "$DOCKERFILE"; then
  echo "::error:: postgres-archive Dockerfile must COPY wal-g from the pinned signed wal-g-pg digest (@sha256:8de34314…)" >&2
  fail=1
fi

# Overlay checks on non-comment lines only.
lines="$(grep -vE '^[[:space:]]*#' "$OVERLAY")"

# 3. Overlay image must not be alpine postgres.
if echo "$lines" | grep -nE 'image:[[:space:]]*[^[:space:]]*postgres[^[:space:]]*alpine'; then
  echo "::error:: postgres-archive overlay must not use an alpine postgres image" >&2
  fail=1
fi

# 4. Overlay image must be the astrofin-postgres-archive image.
if ! echo "$lines" | grep -nE 'image:[[:space:]]*ghcr\.io/mahaasur13-sys/astrofin-postgres-archive'; then
  echo "::error:: postgres-archive overlay must use ghcr.io/mahaasur13-sys/astrofin-postgres-archive" >&2
  fail=1
fi

# 5. Overlay volume must still be pg_data_archive (never pg_data / docker_pg_data).
if echo "$lines" | grep -nE 'docker_pg_data|pg_data([^_a-zA-Z0-9]|$)'; then
  echo "::error:: postgres-archive overlay must not use pg_data / docker_pg_data" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "postgres-archive wal-g guard FAILED" >&2
  exit 1
fi

echo "postgres-archive wal-g guard OK"
