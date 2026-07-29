#!/usr/bin/env bash
# Start the AstroFin Metrics Exporter as a supervised daemon.
# Intended for: Zo managed service (mode=process) or manual background launch.
#
# Environment:
#   METRICS_PORT       — listen port (default 9191)
#   METRICS_HOST       — bind address (default 127.0.0.1)
#   METRICS_AUTH_ENABLED — set to 1/true to enable Bearer token auth
#   METRICS_API_KEY    — Bearer token value (when auth enabled)
#
# Usage:
#   METRICS_PORT=9091 bash scripts/start_metrics_exporter.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PORT="${METRICS_PORT:-9191}"
HOST="${METRICS_HOST:-127.0.0.1}"
PIDFILE="/tmp/astrofin-metrics-exporter.pid"
LOGFILE="/dev/shm/astrofin-metrics-exporter.log"

# Kill any stale instance
if [[ -f "$PIDFILE" ]]; then
    old_pid="$(cat "$PIDFILE")"
    if kill -0 "$old_pid" 2>/dev/null; then
        echo "[metrics_exporter] killing stale pid $old_pid"
        kill "$old_pid" 2>/dev/null || true
        sleep 1
    fi
    rm -f "$PIDFILE"
fi

cd "$PROJECT_ROOT"

echo "[metrics_exporter] starting on ${HOST}:${PORT}  log=${LOGFILE}"
nohup python3 scripts/metrics_exporter.py \
    --port "$PORT" \
    --host "$HOST" \
    >> "$LOGFILE" 2>&1 &

pid=$!
echo "$pid" > "$PIDFILE"
echo "[metrics_exporter] pid=$pid"

# Wait up to 5s for the server to become healthy
for i in $(seq 1 10); do
    if curl -sf "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
        echo "[metrics_exporter] healthy on http://${HOST}:${PORT}/health"
        exit 0
    fi
    sleep 0.5
done

echo "[metrics_exporter] WARNING: server did not become healthy within 5s (pid=$pid)"
exit 1
