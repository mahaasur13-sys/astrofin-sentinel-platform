#!/usr/bin/env bash
# =============================================================================
# WAL-G Backup Cron — AstroFin Sentinel V5
# =============================================================================
# Install:  cp deploy/wal-g/backup-cron.sh /etc/cron.daily/wal-g-backup
#           chmod +x /etc/cron.daily/wal-g-backup
#
# Or via docker-compose (recommended):
#   wal-g-backup:
#     image: ghcr.io/wal-g/wal-g:latest
#     entrypoint: ["/bin/sh", "-c", "while true; do sleep 86400; /wal-g-scripts/backup.sh full; done"]
# =============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="/var/log/wal-g-backup.log"

echo "=== Cron backup started $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOGFILE"

# 1. Full daily backup
"${SCRIPT_DIR}/backup.sh" full

# 2. Purge: keep last 30 backups (30 days rolling)
"${SCRIPT_DIR}/backup.sh" purge 30

# 3. Purge old WAL segments (kept alongside base backups)
if command -v wal-g &>/dev/null; then
    echo "--- Deleting WAL segments older than 31 days ---" | tee -a "$LOGFILE"
    wal-g delete before FIND_FULL "$(date -d '31 days ago' +%Y-%m-%dT%H:%M:%SZ)" --confirm 2>&1 | tee -a "$LOGFILE"
fi

echo "=== Cron backup finished $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee -a "$LOGFILE"
