#!/bin/bash
# =============================================================================
# Self-Healing Watchdog: systemd services
# =============================================================================

SERVICES=("slurmctld" "slurmd" "ray-head" "ceph-mgr" "prometheus" "grafana-server")
LOG_FILE="/var/log/self_healing.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        log "OK: $svc is running"
    else
        log "WARN: $svc is DOWN, restarting..."
        systemctl restart "$svc"
        sleep 2
        if systemctl is-active --quiet "$svc"; then
            log "OK: $svc restarted successfully"
        else
            log "ERROR: $svc restart FAILED"
        fi
    fi
done
