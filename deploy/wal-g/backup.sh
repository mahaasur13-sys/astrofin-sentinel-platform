#!/usr/bin/env bash
# =============================================================================
# WAL-G Backup Script — AstroFin Sentinel V5
# =============================================================================
# Usage:
#   ./backup.sh full          — full base backup
#   ./backup.sh list          — list existing backups
#   ./backup.sh purge 30      — keep last 30 backups, delete older
#   ./backup.sh check         — check wal-g connectivity and config
#
# Called by: cron daily (see backup-cron.sh) or manually
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/wal-g.env"

# ── Load env ───────────────────────────────────────────────────────────
if [[ -f "$ENV_FILE" ]]; then
    set -a; source "$ENV_FILE"; set +a
fi

# ── Determine wal-g binary ─────────────────────────────────────────────
# In Docker: wal-g is in PATH (installed in Dockerfile or via sidecar)
# On host:   expects wal-g in /usr/local/bin
if command -v wal-g &>/dev/null; then
    WALG_BIN="wal-g"
elif [[ -f /usr/local/bin/wal-g ]]; then
    WALG_BIN="/usr/local/bin/wal-g"
else
    echo "[ERROR] wal-g not found. Install: https://github.com/wal-g/wal-g/releases"
    exit 1
fi

# ── Subcommands ────────────────────────────────────────────────────────
cmd="${1:-help}"
shift || true

case "$cmd" in
    full)
        echo "=== Starting full WAL-G backup at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
        "$WALG_BIN" backup-push "$PGDATA" 2>&1 | tee -a /var/log/wal-g-backup.log
        echo "=== Backup completed at $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="
        ;;
    list)
        "$WALG_BIN" backup-list
        ;;
    purge)
        retain="${1:-30}"
        echo "=== Purging backups older than $retain most recent ==="
        "$WALG_BIN" delete retain "$retain" --confirm
        ;;
    check)
        echo "--- wal-g binary ---"
        "$WALG_BIN" --version 2>&1 || echo "  (version check failed)"
        echo "--- Storage prefix ---"
        if [[ -n "${WALG_S3_PREFIX:-}" ]]; then
            echo "  S3: $WALG_S3_PREFIX"
        elif [[ -n "${WALG_FILE_PREFIX:-}" ]]; then
            echo "  FILE: $WALG_FILE_PREFIX"
        else
            echo "  [ERROR] Neither WALG_S3_PREFIX nor WALG_FILE_PREFIX is set."
            exit 1
        fi
        echo "--- PostgreSQL ---"
        echo "  HOST=${PGHOST:-unknown} PORT=${PGPORT:-5432} DB=${PGDATABASE:-unknown}"
        if command -v pg_isready &>/dev/null; then
            pg_isready -h "${PGHOST:-localhost}" -p "${PGPORT:-5432}" -U "${PGUSER:-postgres}" || echo "  [WARN] pg_isready failed"
        fi
        echo "--- Compression ---"
        echo "  ${WALG_COMPRESSION_METHOD:-lz4} (level ${WALG_COMPRESSION_LEVEL:-1})"
        ;;
    *)
        echo "Usage: $0 {full|list|purge <N>|check}"
        exit 1
        ;;
esac
