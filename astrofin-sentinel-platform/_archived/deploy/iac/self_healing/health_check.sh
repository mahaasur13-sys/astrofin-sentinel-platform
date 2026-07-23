#!/usr/bin/env bash
# =============================================================================
# SELF-HEALING — Health Check Script (runs via cron or systemd timer)
# =============================================================================
# Checks: Slurm, Ray, Ceph, WireGuard, node reachability
# Auto-restarts failed services
# Logs to /var/log/health_check.log
# =============================================================================

set -euo pipefail

LOG_FILE="${LOG_FILE:-/var/log/health_check.log}"
RTX_IP="${RTX_IP:-10.20.20.10}"
RK3576_IP="${RK3576_IP:-10.20.20.20}"
VPS_IP="${VPS_IP:-}"
ALERT_EMAIL="${ALERT_EMAIL:-}"
RAY_HEAD="10.20.20.10"
CEPH_CLUSTER="${CEPH_CLUSTER:-ceph-cluster}"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"; }

# --- Service checks ---
check_slurm() {
  if systemctl is-active slurmctld &>/dev/null; then
    log "OK slurmctld is running"
  else
    log "WARN slurmctld DOWN — restarting"
    systemctl restart slurmctld || log "ERROR restart failed"
  fi

  if systemctl is-active munge &>/dev/null; then
    log "OK munge is running"
  else
    log "WARN munge DOWN — restarting"
    systemctl restart munge || log "ERROR restart failed"
  fi
}

check_ray() {
  if pgrep -x ray &>/dev/null; then
    log "OK Ray is running"
  else
    log "WARN Ray DOWN — restarting"
    sudo -u $USER ray start --head --port=6379 --dashboard-host=0.0.0.0 &
    sleep 5
  fi
}

check_ceph() {
  local health=$(ceph -s 2>/dev/null | grep -oE "(HEALTH_OK|HEALTH_WARN|HEALTH_ERR)" || echo "UNKNOWN")
  log "Ceph health: $health"
  
  if [[ "$health" == "HEALTH_ERR" ]]; then
    log "CRITICAL Ceph HEALTH_ERR — alerting"
    [[ -n "$ALERT_EMAIL" ]] && echo "Ceph HEALTH_ERR on $(hostname)" | mail -s "[CRITICAL] Ceph DOWN" "$ALERT_EMAIL"
  fi
}

check_nodes() {
  for ip in "$RTX_IP" "$RK3576_IP"; do
    if ping -c 2 -W 3 "$ip" &>/dev/null; then
      log "OK node $ip reachable"
    else
      log "WARN node $ip UNREACHABLE"
    fi
  done
}

check_wireguard() {
  local wg_iface=$(ip link show | grep -o 'wg[0-9]' | head -1 || true)
  if [[ -n "$wg_iface" ]]; then
    log "OK WireGuard interface $wg_iface is UP"
  else
    log "WARN WireGuard interface DOWN — restarting"
    systemctl restart wg-quick@wg0 || log "ERROR wg restart failed"
  fi
}

# --- Main ---
log "=== Health check started ==="
check_nodes
check_wireguard
check_slurm
check_ray
check_ceph
log "=== Health check completed ==="
