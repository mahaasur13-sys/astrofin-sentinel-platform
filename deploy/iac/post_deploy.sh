#!/usr/bin/env bash
# post_deploy.sh — runs after successful cluster deployment
# Usage: ./post_deploy.sh

set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASS="${GRAFANA_PASS:-${GRAFANA_PASS:-admin}}"
TELEGRAM_BOT="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"
LOGFILE="${LOGFILE:-./logs/post_deploy-$(date +%Y%m%d-%H%M%S).log}"

mkdir -p logs

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOGFILE"; }

notify() {
    local msg="$(echo "$1" | sed 's/ /%20/g')"
    [ -n "${TELEGRAM_BOT}" ] && [ -n "${CHAT_ID}" ] && \
        curl -s "https://api.telegram.org/bot${TELEGRAM_BOT}/sendMessage?chat_id=${CHAT_ID}&text=${msg}" > /dev/null
}

import_dashboards() {
    local dashboards_dir="./monitoring/dashboards"
    [ -d "$dashboards_dir" ] || { log "No dashboards dir: $dashboards_dir"; return 0; }
    for dash in "$dashboards_dir"/*.json; do
        [ -f "$dash" ] || continue
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
            --data @"$dash" \
            "${GRAFANA_URL}/api/dashboards/db" > /dev/null && \
            log "Imported: $(basename "$dash")"
    done
}

setup_alerts() {
    local alert_rules="./monitoring/prometheus/alerts.yml"
    if [ -f "${alert_rules}" ]; then
        mkdir -p /etc/prometheus/rules
        cp "${alert_rules}" /etc/prometheus/rules/acos-alerts.yml
        systemctl reload prometheus 2>/dev/null || true
        log "Alerts configured"
    else
        log "No alert rules found at $alert_rules"
    fi
}

run_loadtest() {
    if [ -x ./load_test/run_scenario1.sh ]; then
        ./load_test/run_scenario1.sh && log "Load test PASSED" || log "Load test FAILED"
    elif [ -d ./load_test ]; then
        log "Load test script not executable, skipping"
    fi
}

verify_cluster() {
    log "=== Cluster health ==="
    command -v sinfo  >/dev/null 2>&1 && sinfo -N -l || log "Slurm not available"
    command -v ceph    >/dev/null 2>&1 && ceph -s 2>/dev/null | grep -E "health|osd" | head -3 || log "Ceph not available"
    command -v ray     >/dev/null 2>&1 && ray status 2>/dev/null | head -5 || log "Ray not available"
}

main() {
    log "=== POST-DEPLOY START ==="
    import_dashboards
    setup_alerts
    verify_cluster
    run_loadtest
    notify "ACOS%20cluster%20deployed%20successfully"
    log "=== POST-DEPLOY COMPLETE ==="
}

main "$@"
