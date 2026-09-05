#!/usr/bin/env bash
# CI guard: base compose must NOT enable WAL archiving.
#
# Fail closed (exit 1) if deploy/docker/docker-compose.yml (the BASE stack)
# contains archive_mode=on or archive_command=. The example file
# (deploy/wal-g/postgresql-archive.conf.example) is intentionally NOT scanned —
# it is documentation, not prod config.
#
# Deterministic: pure grep. No network, no docker.

set -euo pipefail

BASE="${1:-deploy/docker/docker-compose.yml}"
fail=0

if grep -nE 'archive_mode[[:space:]]*=[[:space:]]*on|archive_command[[:space:]]*=' "$BASE"; then
  echo "::error:: base compose must not enable WAL archive (archive_mode=on / archive_command=)" >&2
  fail=1
fi

if [ "$fail" -ne 0 ]; then
  echo "wal-g archive-off guard FAILED" >&2
  exit 1
fi

echo "wal-g archive-off guard OK"
