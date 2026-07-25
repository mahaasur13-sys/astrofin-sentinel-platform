#!/usr/bin/env bash
# =============================================================================
# WAL-G Restore & PITR Script — AstroFin Sentinel V5
# =============================================================================
# WARNING: This script DESTROYS the current database cluster.
#          Run ONLY on a fresh or stopped PostgreSQL instance.
#
# Usage:
#   ./restore.sh latest           — restore latest base backup + replay WAL
#   ./restore.sh list             — list available backups
#   ./restore.sh pitr 2026-07-25T12:00:00Z  — PITR to exact timestamp
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/wal-g.env"

if [[ -f "$ENV_FILE" ]]; then
    set -a; source "$ENV_FILE"; set +a
fi

if command -v wal-g &>/dev/null; then
    WALG_BIN="wal-g"
elif [[ -f /usr/local/bin/wal-g ]]; then
    WALG_BIN="/usr/local/bin/wal-g"
else
    echo "[ERROR] wal-g not found."
    exit 1
fi

cmd="${1:-help}"
shift || true

case "$cmd" in
    latest)
        echo "=== Stopping PostgreSQL (required for restore) ==="
        pg_ctl stop -D "$PGDATA" 2>/dev/null || true
        echo "=== Fetching latest backup from WAL-G storage ==="
        "$WALG_BIN" backup-fetch "$PGDATA" LATEST
        echo "=== Creating recovery.signal for WAL replay ==="
        touch "${PGDATA}/recovery.signal"
        echo "=== Restarting PostgreSQL to replay WAL ==="
        pg_ctl start -D "$PGDATA" -l /var/log/postgresql/restore.log
        echo "=== PITR restore completed. Check logs: /var/log/postgresql/restore.log ==="
        ;;
    list)
        "$WALG_BIN" backup-list
        ;;
    pitr)
        target_time="${1:-}"
        if [[ -z "$target_time" ]]; then
            echo "[ERROR] PITR requires a target timestamp, e.g. 2026-07-25T12:00:00Z"
            exit 1
        fi
        echo "=== Stopping PostgreSQL ==="
        pg_ctl stop -D "$PGDATA" 2>/dev/null || true
        echo "=== Fetching backup BEFORE $target_time ==="
        "$WALG_BIN" backup-fetch "$PGDATA" LATEST
        # Configure recovery to stop at target time
        cat >> "${PGDATA}/postgresql.auto.conf" <<EOF
recovery_target_time = '$target_time'
recovery_target_action = 'promote'
EOF
        touch "${PGDATA}/recovery.signal"
        echo "=== Restarting PostgreSQL — will recover to $target_time ==="
        pg_ctl start -D "$PGDATA" -l /var/log/postgresql/pitr_restore.log
        echo "=== PITR restore initiated. Monitor: ${PGDATA}/postgresql.auto.conf ==="
        ;;
    *)
        echo "Usage: $0 {latest|list|pitr <ISO-timestamp>}"
        echo ""
        echo "WARNING: restore OVERWRITES the PostgreSQL data directory."
        echo "         Ensure the cluster is stopped before running."
        exit 1
        ;;
esac
