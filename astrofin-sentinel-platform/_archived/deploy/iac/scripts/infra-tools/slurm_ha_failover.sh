#!/usr/bin/env bash
# Slurm HA failover script — monitors primary controller, promotes backup on failure
# Usage: ./slurm_ha_failover.sh [primary_host] [backup_host] [vip_interface] [vip_ip]
set -euo pipefail

PRIMARY="${1:-192.168.1.10}"
BACKUP="${2:-192.168.1.20}"
VIP_IFACE="${3:-wg0}"
VIP_IP="${4:-10.66.0.100}"

LOG="/var/log/slurm_ha.log"
LOCK_FILE="/mnt/cephfs/.slurm_ha_lock"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG"
}

is_primary_alive() {
    # Check if primary slurmctld is responding
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no asur@"$PRIMARY" "scontrol ping" 2>/dev/null | grep -q "ping ok"; then
        return 0
    fi
    return 1
}

acquire_lock() {
    # Use CephFS as distributed lock mechanism
    if ssh "$BACKUP" "mkdir '$LOCK_FILE' 2>/dev/null"; then
        log "Lock acquired on $BACKUP"
        return 0
    fi
    # Another node already holds the lock
    existing_holder=$(ssh "$BACKUP" "cat '$LOCK_FILE/holder' 2>/dev/null" || echo "unknown")
    log "Lock held by: $existing_holder"
    return 1
}

promote_backup() {
    log "Promoting $BACKUP to primary slurmctld..."
    
    # Stop slurmd on backup first
    ssh asur@"$BACKUP" "sudo systemctl stop slurmd" 2>/dev/null || true
    
    # Start slurmctld on backup
    ssh asur@"$BACKUP" "sudo systemctl start slurmctld"
    
    # Verify
    if ssh asur@"$BACKUP" "systemctl is-active slurmctld" | grep -q "active"; then
        log "Backup promoted successfully"
        
        # Configure slurm.conf to point to new primary
        ssh asur@"$BACKUP" "sudo sed -i 's/SlurmctldHost=.*/SlurmctldHost=$BACKUP/' /etc/slurm/slurm.conf"
        ssh asur@"$BACKUP" "sudo systemctl restart slurmctld"
        
        # Bring up VIP
        ssh asur@"$BACKUP" "sudo ip addr add $VIP_IP/24 dev $VIP_IFACE label $VIP_IFACE:0" 2>/dev/null || true
        return 0
    else
        log "ERROR: Backup promotion failed"
        return 1
    fi
}

main() {
    log "=== Slurm HA Monitor Starting ==="
    log "Primary: $PRIMARY | Backup: $BACKUP | VIP: $VIP_IP"
    
    while true; do
        if ! is_primary_alive; then
            log "PRIMARY DEAD — attempting failover..."
            
            if acquire_lock; then
                if promote_backup; then
                    log "F failover complete. New primary: $BACKUP"
                fi
            else
                log "Could not acquire lock — another node handling failover"
            fi
        else
            log "Primary alive — monitoring..."
        fi
        
        sleep 30
    done
}

main "$@"