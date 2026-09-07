#!/usr/bin/env bash
# CI guard: the WAL-G restore drill must refuse to fetch into live PGDATA.
#
# Fail closed (exit 1) if the drill script:
#   - has no live-PGDATA refusal guard, or
#   - fetches directly into $PGDATA (backup-fetch "$PGDATA"), or
#   - defaults its destination to a live path (PGDATA / /var/lib/postgresql/data
#     / docker_pg_data).
#
# Deterministic: pure grep. No network, no docker, no wal-g call.

set -euo pipefail

SCRIPT="${1:-scripts/walg_restore_drill.sh}"
fail=0

# 1. The refusal guard must be present.
if ! grep -qE 'refusing to fetch into live PGDATA' "$SCRIPT"; then
  echo "::error:: $SCRIPT has no live-PGDATA refusal guard" >&2
  fail=1
fi

# 2. Must NOT fetch straight into $PGDATA.
if grep -nE 'backup-fetch[[:space:]]+"?\$?\{?PGDATA\}?"?' "$SCRIPT"; then
  echo "::error:: $SCRIPT fetches into PGDATA (live path)" >&2
  fail=1
fi

# 3. Must NOT default the destination to a live path.
if grep -nE '^(DEST|WALG_RESTORE_DIR)="?[^"]*(PGDATA|/var/lib/postgresql/data|docker_pg_data)' "$SCRIPT"; then
  echo "::error:: $SCRIPT defaults the destination to a live PGDATA path" >&2
  fail=1
fi

# 4. deploy/wal-g/restore.sh must be neutralized: no pg_ctl stop, no
#    backup-fetch into PGDATA / pg_data / pg_data_archive / docker_pg_data.
#    (Comment lines are ignored — the guard checks code, not prose.)
RESTORE_SH="${2:-deploy/wal-g/restore.sh}"
if [ -f "$RESTORE_SH" ]; then
  rlines="$(grep -vE '^[[:space:]]*#' "$RESTORE_SH")"
  if echo "$rlines" | grep -nE 'pg_ctl[[:space:]]+stop'; then
    echo "::error:: $RESTORE_SH must not call pg_ctl stop (use the drill)" >&2
    fail=1
  fi
  if echo "$rlines" | grep -nE 'backup-fetch[[:space:]]+[^[:space:]]*(PGDATA|pg_data|pg_data_archive|docker_pg_data)'; then
    echo "::error:: $RESTORE_SH must not backup-fetch into a live data path" >&2
    fail=1
  fi
fi

if [ "$fail" -ne 0 ]; then
  echo "wal-g restore guard FAILED" >&2
  exit 1
fi

echo "wal-g restore guard OK"
