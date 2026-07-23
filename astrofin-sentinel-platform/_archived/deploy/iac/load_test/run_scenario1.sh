#!/usr/bin/env bash
# run_scenario1.sh — Load test scenario 1: Slurm + Ray + Ceph
set -euo pipefail

HOST="${HOST:-localhost}"
PORT="${PORT:-8081}"
LOGFILE="./logs/scenario1-$(date +%Y%m%d-%H%M%S).log"
mkdir -p logs

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOGFILE"; }

check() { "$@" && log "PASS: $*" || { log "FAIL: $*"; ERR=1; }; }
ERR=0

log "=== SCENARIO 1: ACOS Load Test ==="

# 1. API health
check curl -sf "http://${HOST}:${PORT}/health"

# 2. Slurm sinfo
command -v sinfo >/dev/null && check sinfo -N -l || log "SKIP: sinfo not available"

# 3. Ceph health
command -v ceph >/dev/null && check ceph -s 2>/dev/null | grep -q HEALTH_OK || log "SKIP: ceph not available"

# 4. Ray status
command -v ray >/dev/null && check ray status 2>/dev/null | grep -q "Ray runtime" || log "SKIP: ray not available"

# 5. API throughput (10 concurrent requests)
-throughput() {
    local start=$(date +%s%3N)
    for i in $(seq 1 10); do curl -sf "http://${HOST}:${PORT}/health" > /dev/null; done
    local end=$(date +%s%3N)
    local ms=$((end - start))
    log "10 requests: ${ms}ms"
    [ "$ms" -lt 5000 ] && log "PASS: throughput acceptable" || log "WARN: throughput slow"
}
check throughput

# 6. Docker network
command -v docker >/dev/null && check docker network inspect home-cluster-net >/dev/null 2>&1 || log "SKIP: docker not available"

# 7. Self-healing watchdog
command -v systemctl >/dev/null && check systemctl is-active acos-watchdog 2>/dev/null || log "SKIP: watchdog not available"

if [ $ERR -eq 0 ]; then
    log "=== SCENARIO 1 PASSED ==="
    exit 0
else
    log "=== SCENARIO 1 FAILED ==="
    exit 1
fi
