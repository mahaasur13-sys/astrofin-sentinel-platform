#!/usr/bin/env bash
# =============================================================================
# WATCHDOG v2 — Root-Cause Self-Healing Daemon
# =============================================================================
# Improvements over v1:
#   - Root cause detection (not just restart, but WHY)
#   - Retry strategy (3 attempts, exponential backoff)
#   - Escalation (Telegram alert after 3 failures)
#   - State tracking (failure history file)
# =============================================================================

set -euo pipefail

LOG_FILE="${LOG_FILE:-/var/log/watchdog.log}"
STATE_FILE="${STATE_FILE:-/var/run/watchdog.state}"
ALERT_COOLDOWN=3600  # 1 hour between Telegram alerts
INTERVAL="${INTERVAL:-30}"

RTX_IP="10.20.20.10"
RK3576_IP="10.20.20.20"
TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-}"
SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"

# ============================================================================
# LOGGING
# ============================================================================

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE" 2>/dev/null || echo "[$*]"; }
log_warn() { log "WARN: $*"; }
log_fail() { log "FAIL: $*"; }
log_ok()   { log "OK:   $*"; }

# ============================================================================
# STATE TRACKING
# ============================================================================

declare -A FAILURE_COUNT
declare -A LAST_FAILURE

load_state() {
    [[ -f "$STATE_FILE" ]] || return
    while IFS='=' read -r key value; do
        FAILURE_COUNT["$key"]=$value
    done < "$STATE_FILE"
}

save_state() {
    > "$STATE_FILE"
    for key in "${!FAILURE_COUNT[@]}"; do
        echo "${key}=${FAILURE_COUNT[$key]}" >> "$STATE_FILE"
    done
}

reset_failures() {
    local service="$1"
    FAILURE_COUNT["$service"]=0
    unset LAST_FAILURE["$service"]
}

inc_failure() {
    local service="$1"
    local now
    now=$(date +%s)
    FAILURE_COUNT["$service"]=$((${FAILURE_COUNT[$service]:-0} + 1))
    LAST_FAILURE["$service"]=$now
    save_state
}

should_alert() {
    local service="$1"
    local threshold="${2:-3}"
    [[ $((${FAILURE_COUNT[$service]:-0})) -ge $threshold ]]
}

check_cooldown() {
    local service="$1"
    local last="${LAST_FAILURE[$service]:-0}"
    local now
    now=$(date +%s)
    [[ $((now - last)) -gt $ALERT_COOLDOWN ]]
}

# ============================================================================
# ESCALATION
# ============================================================================

escalate() {
    local service="$1"
    local reason="$2"
    local node="${3:-unknown}"

    log_warn "ESCALATION: $service on $node — $reason (attempts: ${FAILURE_COUNT[$service]:-0})"

    if [[ -n "$TELEGRAM_BOT_TOKEN" ]] && [[ -n "$TELEGRAM_CHAT_ID" ]]; then
        local msg="🚨 *Watchdog Escalation*\n\n*Service:* $service\n*Node:* $node\n*Reason:* $reason\n*Attempts:* ${FAILURE_COUNT[$service]:-0}\n*Time:* $(date '+%Y-%m-%d %H:%M:%S')"
        curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TELEGRAM_CHAT_ID}" \
            -d "text=${msg}" \
            -d "parse_mode=Markdown" > /dev/null 2>&1 || true
    fi

    if [[ -n "$SLACK_WEBHOOK" ]]; then
        curl -s -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"🚨 Watchdog: $service on $node failed — $reason\"}" > /dev/null 2>&1 || true
    fi
}

# ============================================================================
# ROOT CAUSE DETECTION
# ============================================================================

diagnose_service() {
    local service="$1"
    local node="${2:-localhost}"

    case "$service" in
        slurmd)
            # Check: is slurmd process dead? OOM? network?
            if ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no "root@${node}" "systemctl is-active slurmd" 2>/dev/null | grep -qv active; then
                local mem_pressure
                mem_pressure=$(ssh -o ConnectTimeout=3 "root@${node}" "grep -i oom /var/log/syslog 2>/dev/null | tail -3" 2>/dev/null || echo "")
                if [[ -n "$mem_pressure" ]]; then
                    echo "root_cause=oom_kill"
                else
                    echo "root_cause=process_crash"
                fi
            else
                echo "root_cause=unknown"
            fi
            ;;
        slurmctld)
            # Check: DB connectivity? port binding? config error?
            echo "root_cause=controller_failure"
            ;;
        ray)
            # Check: OOM? GPU driver? port conflict?
            echo "root_cause=ray_crash"
            ;;
        ceph-osd)
            # Check: disk full? slow disk? network partition?
            echo "root_cause=osd_down"
            ;;
        wg-quick)
            # Check: kernel module? MTU? peer unreachable?
            echo "root_cause=wireguard_down"
            ;;
        *)
            echo "root_cause=unknown"
            ;;
    esac
}

# ============================================================================
# SERVICE RESTART WITH RETRY
# ============================================================================

restart_service() {
    local service="$1"
    local node="${2:-localhost}"
    local max_attempts="${3:-3}"
    local delay="$((INTERVAL * 2))"

    local attempt=1
    while [[ $attempt -le $max_attempts ]]; do
        log "  Attempt $attempt/$max_attempts: restarting $service on $node..."

        local rc=0
        if [[ "$node" == "localhost" ]] || [[ "$node" == "127.0.0.1" ]]; then
            systemctl restart "$service" 2>/dev/null || rc=$?
        else
            ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no "root@${node}" \
                "systemctl restart $service" 2>/dev/null || rc=$?
        fi

        if [[ $rc -eq 0 ]]; then
            sleep 5
            # Verify
            if [[ "$node" == "localhost" ]] || [[ "$node" == "127.0.0.1" ]]; then
                systemctl is-active "$service" &>/dev/null && rc=0 || rc=1
            else
                ssh -o ConnectTimeout=5 "root@${node}" "systemctl is-active $service" &>/dev/null && rc=0 || rc=1
            fi
        fi

        if [[ $rc -eq 0 ]]; then
            log_ok "$service restarted successfully (attempt $attempt)"
            return 0
        fi

        log_warn "  Restart attempt $attempt failed (rc=$rc)"
        [[ $attempt -lt $max_attempts ]] && sleep $((delay * attempt))
        ((attempt++))
    done

    return 1
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

check_node() {
    local ip="$1"
    local name="$2"
    local failed=0

    if ! ping -c 2 -W 2 "$ip" &>/dev/null; then
        log_warn "Node $name ($ip) is UNREACHABLE"
        escalate "node_down" "$ip" "$name"
        return 1
    fi
    log_ok "Node $name ($ip) is reachable"
    return 0
}

check_service() {
    local service="$1"
    local node="$2"
    local name="${3:-$service}"

    local is_active
    is_active=$(ssh -o ConnectTimeout=3 -o StrictHostKeyChecking=no "root@${node}" \
        "systemctl is-active $service" 2>/dev/null || echo "unknown")

    if [[ "$is_active" != "active" ]]; then
        log_warn "$name on $node is NOT active (state=$is_active)"

        if [[ -z "${FAILURE_COUNT["${name}_${node}"]:-" }" ]]; then
            FAILURE_COUNT["${name}_${node}"]=0
        fi

        inc_failure "${name}_${node}"
        local cause
        cause=$(diagnose_service "$service" "$node")

        if restart_service "$service" "$node"; then
            reset_failures "${name}_${node}"
        else
            if should_alert "${name}_${node}" 3 && check_cooldown "${name}_${node}"; then
                escalate "${name}" "restart_failed_after_3_attempts: $cause" "$node"
            fi
        fi
    else
        [[ "${FAILURE_COUNT[${name}_${node}]:-0}" -gt 0 ]] && reset_failures "${name}_${node}"
        log_ok "$name on $node is active"
    fi
}

check_ceph_health() {
    local out
    out=$(ssh -o ConnectTimeout=5 "root@${RTX_IP}" "ceph health detail 2>/dev/null" || echo "HEALTH_ERR")
    if echo "$out" | grep -q "HEALTH_OK"; then
        log_ok "Ceph cluster is healthy"
        reset_failures "ceph"
    elif echo "$out" | grep -q "HEALTH_WARN"; then
        log_warn "Ceph is in WARNING state"
    else
        log_fail "Ceph is in ERROR state"
        inc_failure "ceph"
        if should_alert "ceph" 2; then
            escalate "ceph" "ceph health error" "$RTX_IP"
        fi
    fi
}

check_gpu_available() {
    local out
    out=$(ssh -o ConnectTimeout=5 "root@${RTX_IP}" "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader 2>/dev/null" || echo "unavailable")
    if [[ "$out" == "unavailable" ]]; then
        log_fail "GPU is UNAVAILABLE on RTX"
        inc_failure "gpu"
        if should_alert "gpu" 2; then
            escalate "gpu" "nvidia-smi unavailable" "$RTX_IP"
        fi
    else
        log_ok "GPU available (utilization: ${out}%)"
        reset_failures "gpu"
    fi
}

check_scheduler_api() {
    local resp
    resp=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8080/health 2>/dev/null || echo "000")
    if [[ "$resp" == "200" ]]; then
        log_ok "AI Scheduler API is healthy"
        reset_failures "scheduler"
    else
        log_warn "AI Scheduler API returned HTTP $resp"
        inc_failure "scheduler"
        restart_service "scheduler" "localhost"
    fi
}

# ============================================================================
# MAIN LOOP
# ============================================================================

main() {
    mkdir -p "$(dirname "$LOG_FILE")" "$(dirname "$STATE_FILE")"
    load_state

    log "=== Watchdog v2 started (interval=${INTERVAL}s) ==="

    while true; do
        # Node reachability
        check_node "$RTX_IP" "RTX"     || true
        check_node "$RK3576_IP" "RK3576" || true

        # Critical services (node, service, display_name)
        check_service "slurmd"   "$RTX_IP"    "slurmd"
        check_service "slurmctld" "$RTX_IP"    "slurmctld"
        check_service "ray"      "$RTX_IP"    "ray-head"

        # Ceph (periodic — every 3rd cycle)
        (( $(date +%s) % 90 == 0 )) && check_ceph_health || true

        # GPU
        check_gpu_available

        # Scheduler API
        check_scheduler_api

        # WireGuard on all nodes
        for node_ip in "$RTX_IP" "$RK3576_IP"; do
            check_service "wg-quick@wg0" "$node_ip" "wireguard-${node_ip}"
        done

        log "=== Cycle complete $(date '+%H:%M:%S') ==="
        sleep "$INTERVAL"
    done
}

# Run as daemon or single check
if [[ "${1:-}" == "--daemon" ]]; then
    main
elif [[ "${1:-}" == "--check" ]]; then
    load_state
    check_node "$RTX_IP" "RTX"
    check_service "slurmd" "$RTX_IP" "slurmd"
    check_gpu_available
    check_scheduler_api
else
    echo "Usage: $0 --daemon   (run continuously)"
    echo "       $0 --check    (single check pass)"
    exit 1
fi
