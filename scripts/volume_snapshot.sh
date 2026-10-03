#!/usr/bin/env bash
# =============================================================================
# volume_snapshot.sh — optional snapshot of grafana_data / redis_data / prom_data.
#
# Usage: ./scripts/volume_snapshot.sh grafana    /abs/backup-dir
#        ./scripts/volume_snapshot.sh redis      /abs/backup-dir
#        ./scripts/volume_snapshot.sh prometheus /abs/backup-dir
#
# Fail-closed: grafana, redis, prometheus are snapshot-able (tar). postgres is
# WAL-G-only (never a tar). Refuses to write into docker volumes dir or any
# pg_data path.
# =============================================================================
set -euo pipefail

SERVICE="${1:-}"
DEST="${2:-}"

# ── Service allowlist ──────────────────────────────────────────────────
case "$SERVICE" in
  grafana)
    VOL="grafana_data"
    ;;
  redis)
    VOL="redis_data"
    ;;
  prometheus)
    VOL="prom_data"
    ;;
  postgres|pg|pg_data|pg_data_archive|wal-g|docker_pg_data)
    echo "refusing to snapshot $SERVICE: postgres is WAL-G only (never tar)" >&2
    exit 2
    ;;
  "")
    echo "Usage: $0 grafana|redis|prometheus <absolute-dest-dir>" >&2
    exit 2
    ;;
  *)
    echo "unknown service: $SERVICE (only grafana, redis, prometheus are snapshot-able)" >&2
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

# ── Guard: refuse if the target container is running (busy volume) ─────
case "$SERVICE" in
  grafana)    CNAME="astrofinsentinel_grafana" ;;
  redis)      CNAME="astrofinsentinel_redis" ;;
  prometheus) CNAME="astrofinsentinel_prom" ;;
esac
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CNAME}$"; then
  echo "[ERROR] $SERVICE container is running; stop $SERVICE manually before snapshot" >&2
  exit 3
fi

mkdir -p "$DEST"

TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${DEST}/${SERVICE}-${TS}.tar.gz"

echo "=== snapshotting ${VOL} -> ${OUT} ==="
docker run --rm \
  -v "${VOL}:/source:ro" \
  -v "${DEST}:/dest" \
  alpine tar czf "/dest/$(basename "$OUT")" -C /source .

echo "snapshot written to ${OUT}"
