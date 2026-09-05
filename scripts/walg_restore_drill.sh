#!/usr/bin/env bash
# =============================================================================
# WAL-G restore DRILL — fetch a backup into a SAFE, empty directory only.
#
# This is the safe restore-drill entrypoint. It NEVER targets the live
# Postgres data directory, never runs `pg_ctl`, and never stops a running
# cluster. After fetch you start postgres yourself on THIS destination only.
#
# Usage:
#   ./scripts/walg_restore_drill.sh /tmp/pg-drill            # LATEST
#   ./scripts/walg_restore_drill.sh /tmp/pg-drill base_0000.. # named backup
#   WALG_RESTORE_DIR=/tmp/pg-drill ./scripts/walg_restore_drill.sh
#
# Refuses (exit 2) if the destination is a live PGDATA mount:
#   /var/lib/postgresql/data, $PGDATA, or any path named docker_pg_data.
# =============================================================================
set -euo pipefail

DEST="${1:-${WALG_RESTORE_DIR:-}}"
BACKUP_NAME="${2:-LATEST}"

# ── Guard: destination must be an absolute path ────────────────────────
if [[ -z "$DEST" ]]; then
  echo "Usage: $0 <absolute-restore-dir> [backup-name|LATEST]" >&2
  echo "   or: WALG_RESTORE_DIR=<absolute-dir> $0" >&2
  exit 2
fi
case "$DEST" in
  /*) ;;
  *)
    echo "[ERROR] restore dir must be an absolute path: $DEST" >&2
    exit 2
    ;;
esac

# ── Guard: refuse to fetch into live PGDATA ────────────────────────────
realpath_or_self() {
  python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$1" 2>/dev/null || echo "$1"
}

refuse_live() {
  echo "refusing to fetch into live PGDATA: $DEST" >&2
  exit 2
}

resolved_dest="$(realpath_or_self "$DEST")"

# Explicit forbidden live paths.
for live in "/var/lib/postgresql/data" "${PGDATA:-}"; do
  [[ -n "$live" ]] || continue
  if [[ "$resolved_dest" == "$(realpath_or_self "$live")" ]]; then
    refuse_live
  fi
done

# Any path that contains a docker_pg_data segment (the local live volume).
if [[ "$resolved_dest" == *"/docker_pg_data"* ]]; then
  refuse_live
fi

# ── Guard: destination must be empty or non-existent ───────────────────
if [[ -e "$DEST" ]]; then
  if [[ -n "$(ls -A "$DEST" 2>/dev/null)" ]]; then
    echo "[ERROR] target directory is not empty: $DEST" >&2
    exit 2
  fi
else
  mkdir -p "$DEST"
fi

# ── Locate wal-g and env (gitignored live env, if present) ─────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../deploy/wal-g/wal-g.env"
if [[ -f "$ENV_FILE" ]]; then
  set -a; source "$ENV_FILE"; set +a
fi

if command -v wal-g &>/dev/null; then
  WALG_BIN="wal-g"
elif [[ -f /usr/local/bin/wal-g ]]; then
  WALG_BIN="/usr/local/bin/wal-g"
else
  echo "[ERROR] wal-g not found." >&2
  exit 1
fi

echo "=== Fetching backup '$BACKUP_NAME' into $DEST ==="
"$WALG_BIN" backup-fetch "$DEST" "$BACKUP_NAME"

echo "files restored to $DEST; start postgres separately on THIS dest only"
