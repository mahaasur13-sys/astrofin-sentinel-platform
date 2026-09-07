#!/usr/bin/env bash
# =============================================================================
# WAL-G restore — SAFE wrapper around scripts/walg_restore_drill.sh.
#
# The old restore.sh (pg_ctl stop + backup-fetch into $PGDATA) was REMOVED.
# Restore is now drill-only: fetch into an empty, absolute, NON-LIVE DEST only.
# Never fetches into /var/lib/postgresql/data, $PGDATA, pg_data, pg_data_archive,
# or docker_pg_data — the drill refuses those (exit 2).
#
# Usage:
#   ./restore.sh /tmp/pg-drill                        # LATEST
#   ./restore.sh /tmp/pg-drill base_00000001000000000000000F
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "${SCRIPT_DIR}/../../scripts/walg_restore_drill.sh" "$@"
