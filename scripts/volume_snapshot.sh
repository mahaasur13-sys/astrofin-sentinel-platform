#!/usr/bin/env bash
# =============================================================================
# volume_snapshot.sh — optional snapshot of the grafana_data volume only.
#
# Usage: ./scripts/volume_snapshot.sh grafana /abs/backup-dir
#
# Fail-closed: only grafana is snapshot-able. postgres is WAL-G-only (never a
# tar); redis_data and prom_data are NOT backed up. Refuses to write into
# docker volumes dir or any pg_data path.
# =============================================================================
set -euo pipefail

SERVICE="${1:-}"
DEST="${2:-}"

# ── Service allowlist ──────────────────────────────────────────────────
case "$SERVICE" in
  grafana)
    VOL="grafana_data"
    ;;
  postgres|pg|wal-g)
    echo "refusing to snapshot $SERVICE: postgres is WAL-G only (never tar)" >&2
    exit 2
    ;;
  redis|prometheus)
    echo "refusing to snapshot $SERVICE: $SERVICE data is not backed up" >&2
    exit 2
    ;;
  "")
    echo "Usage: $0 grafana <absolute-dest-dir>" >&2
    exit 2
    ;;
  *)
    echo "unknown service: $SERVICE (only grafana is snapshot-able)" >&2
    exit 2
    ;;
esac

# ── Guard: destination must be absolute ────────────────────────────────
case "$DEST" in
  /*) ;;
  *)
    echo "[ERROR] dest must be an absolute path: $DEST" >&2
    exit 2
    ;;
esac

# ── Guard: refuse live docker volumes dir ──────────────────────────────
case "$DEST" in
  /var/lib/docker/volumes|/var/lib/docker/volumes/*)
    echo "refusing to write into docker volumes dir: $DEST" >&2
    exit 2
    ;;
esac

# ── Guard: refuse any pg_data / docker_pg_data path ────────────────────
case "$DEST" in
  *pg_data*|*docker_pg_data*)
    echo "refusing to write into pg_data: $DEST" >&2
    exit 2
    ;;
esac

# ── Guard: refuse if grafana is running (busy volume) ──────────────────
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^astrofinsentinel_grafana$'; then
  echo "[ERROR] grafana container is running; stop grafana manually before snapshot" >&2
  exit 3
fi

mkdir -p "$DEST"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${DEST}/grafana-${TS}.tar.gz"

echo "=== snapshotting ${VOL} -> ${OUT} ==="
docker run --rm \
  -v "${VOL}:/source:ro" \
  -v "${DEST}:/dest" \
  alpine tar czf "/dest/$(basename "$OUT")" -C /source .

echo "snapshot written to ${OUT}"
