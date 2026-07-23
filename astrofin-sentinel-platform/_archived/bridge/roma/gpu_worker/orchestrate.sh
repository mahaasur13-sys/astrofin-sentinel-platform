#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")/.." 
PID_DIR=".pids"; LOG_DIR=".logs"
mkdir -p "$PID_DIR" "$LOG_DIR"
export PYTHONPATH=.

NAMES=("worker-registry" "gpu-lock-manager" "retry-system" "gpu-observability")
MODULES=("gpu_worker.worker_registry_fast:app" "gpu_worker.gpu_lock_manager_fast:app" "gpu_worker.retry_system_fast:app" "gpu_worker.observability_fast:app")
PORTS=(8000 8001 8002 8003)

start() {
    for i in 0 1 2 3; do
        NAME="${NAMES[$i]}"; MOD="${MODULES[$i]}"; PORT="${PORTS[$i]}"; PIDFILE="$PID_DIR/${NAME}.pid"
        [ -f "$PIDFILE" ] && kill "$(cat $PIDFILE)" 2>/dev/null || true
        nohup python3 -m uvicorn "$MOD" --host 0.0.0.0 --port "$PORT" > "$LOG_DIR/${NAME}.log" 2>&1 &
        echo $! > "$PIDFILE"; echo "[START] $NAME :$PORT PID $!"
    done; echo "[OK] All started"
}
stop() {
    for NAME in "${NAMES[@]}"; do
        PIDFILE="$PID_DIR/${NAME}.pid"
        [ -f "$PIDFILE" ] && kill "$(cat $PIDFILE)" 2>/dev/null; rm -f "$PIDFILE"
    done; echo "[OK] All stopped"
}
status() {
    for i in 0 1 2 3; do
        NAME="${NAMES[$i]}"; PORT="${PORTS[$i]}"; PIDFILE="$PID_DIR/${NAMES[$i]}.pid"
        if [ -f "$PIDFILE" ] && kill -0 "$(cat $PIDFILE)" 2>/dev/null; then
            echo "✓ $NAME (:$PORT) PID $(cat $PIDFILE)"
        else echo "✗ $NAME (:$PORT) STOPPED"; fi
    done
}
"$@"
