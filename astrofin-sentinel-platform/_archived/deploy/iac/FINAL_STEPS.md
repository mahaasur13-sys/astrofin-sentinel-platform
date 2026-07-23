# FINAL_STEPS.md — ACOS Production Deployment Checklist

## 1. Git Push & CI/CD Setup

```bash
cd /home/workspace/home-cluster-iac
git add .
git commit -m "feat: ACOS production-ready — IaC, ML API, self-healing, CI/CD"
git push origin main
```

### GitHub Secrets (Settings → Secrets → Actions)

| Secret | Example |
|--------|---------|
| `MIKROTIK_PASS` | `your_mikrotik_password` |
| `WG_PRIVATE_KEY` | `wg_privkey_base64...` |
| `CEPH_ADMIN_KEY` | `ceph-admin-keyring-base64` |
| `GRAFANA_PASS` | `grafana_secure_password` |
| `TELEGRAM_BOT_TOKEN` | `123456:ABC-DEF...` |
| `SELF_HOSTED_RUNNER_TOKEN` | `YOUR_RUNNER_TOKEN` |

### Register Self-Hosted Runner

```bash
# On your management node:
curl -s https://raw.githubusercontent.com/mahaasur13-sys/AsurDev/main/docs/deploy-automation.md | bash
```

---

## 2. Inventory Variables (`ansible/group_vars/all.yml`)

```yaml
---
# Ansible group_vars/all.yml — ACOS cluster configuration

cluster_name: acos-home
environment: production

# Network
primary_ip: "192.168.88.2"       # RTX 3060 node
edge_ip: "192.168.88.3"           # RK3576 edge node
vps_ip: "203.0.113.5"            # Optional VPS
wireguard_port: 51820
mikrotik_ip: "192.168.88.1"
mikrotik_user: "admin"

# Storage
ceph_pool_name: "acros-storage"
ceph_replicas: 3
ceph_public_network: "192.168.88.0/24"
ceph_cluster_network: "192.168.88.0/24"

# Slurm
slurm_controller: "{{ primary_ip }}"
slurm_partitions:
  - name: gpu
    nodes: gpu-node
    tres: "gpu:1"
  - name: cpu
    nodes: cpu-node

# Ray
ray_head_ip: "{{ primary_ip }}"
ray_worker_ips:
  - "{{ edge_ip }}"

# Docker
docker_network: home-cluster-net

# Monitoring
grafana_admin_password: "{{ lookup('env', 'GRAFANA_PASS') }}"
prometheus_retention_days: 15

# Self-healing
healthcheck_interval: 60
restart_delay: 10
max_restart_attempts: 3
```

---

## 3. `post_deploy.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_USER="${GRAFANA_USER:-admin}"
GRAFANA_PASS="${GRAFANA_PASS:-$(printenv GRAFANA_PASS)}"
TELEGRAM_BOT="${TELEGRAM_BOT_TOKEN:-}"
CHAT_ID="${TELEGRAM_CHAT_ID:-}"

notify() {
    local msg="$1"
    [ -n "${TELEGRAM_BOT}" ] && [ -n "${CHAT_ID}" ] && \
        curl -s "https://api.telegram.org/bot${TELEGRAM_BOT}/sendMessage" \
            -d "chat_id=${CHAT_ID}&text=${msg}" > /dev/null
}

# Import Grafana dashboards
import_dashboards() {
    local dashboards_dir="./monitoring/dashboards"
    for dash in "${dashboards_dir}"/*.json; do
        [ -f "${dash}" ] || continue
        curl -s -X POST \
            -H "Content-Type: application/json" \
            -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
            --data @"${dash}" \
            "${GRAFANA_URL}/api/dashboards/db" > /dev/null
        echo "Imported: ${dash}"
    done
}

# Setup Prometheus alerts
setup_alerts() {
    local alert_rules="./monitoring/prometheus/alerts.yml"
    if [ -f "${alert_rules}" ]; then
        cp "${alert_rules}" /etc/prometheus/rules/acos-alerts.yml
        systemctl reload prometheus 2>/dev/null || true
        echo "Alerts configured"
    fi
}

# Run load test scenario 1
run_loadtest() {
    if [ -d ./load_test ]; then
        cd ./load_test && ./run_scenario1.sh && cd ..
        echo "Load test passed"
    fi
}

main() {
    echo "=== POST-DEPLOY RUNNING ==="
    import_dashboards
    setup_alerts
    run_loadtest
    notify "✅ ACOS cluster deployed successfully"
    echo "=== POST-DEPLOY COMPLETE ==="
}

main "$@"
```

---

## 4. `.env` for ML API

```bash
# .env — ML Inference API environment

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Model
MODEL_PATH=./models/acos_v1.pkl
MODEL_TYPE=gradient_boosting

# Storage
CEPH_RGW_HOST=192.168.88.2
CEPH_RGW_PORT=7480
CEPH_POOL=acros-storage

# Slurm
SLURMCTL_HOST=192.168.88.2
SLURMCTL_PORT=6817

# Ray
RAY_HEAD=192.168.88.2:6379

# Monitoring
PROMETHEUS_URL=http://localhost:9090
GRAFANA_URL=http://localhost:3000

# Security
API_KEY=change_me_in_production
ALLOWED_ORIGINS=https://asurdev.zo.computer

# Cache
REDIS_URL=redis://localhost:6379/0
CACHE_TTL=3600
```

---

## 5. Manual Verification Checklist (10 items)

- [ ] **Slurm**: `sinfo` — all nodes UP
- [ ] **Ceph**: `ceph -s` — HEALTH_OK, 3x replication
- [ ] **Ray**: `ray status` — head + workers connected
- [ ] **API**: `curl http://localhost:8000/health` — 200 OK
- [ ] **WireGuard**: `wg show` — peer established
- [ ] **Grafana**: Login at `http://localhost:3000` — dashboards visible
- [ ] **Self-healing**: `systemctl status acos-watchdog` — active
- [ ] **Logs**: `journalctl -u slurmctld --since "1 hour ago"` — no errors
- [ ] **Load test**: `./load_test/run_scenario1.sh` — all checks passed
- [ ] **Backups**: Ceph RGW bucket exists, daily snapshot configured

---

## 6. Roadmap (Optional Improvements)

| Priority | Feature | Benefit |
|----------|---------|---------|
| P0 | Auto model retraining (weekly CronJob) | Model stays fresh |
| P1 | Multi-site expansion (add VPS node) | True geo-distributed cluster |
| P1 | Istio + canary deployments | Zero-downtime rollouts |
| P2 | Auto-scaling based on queue depth | Cost optimization |
| P2 | Kubernetes integration (K8s workers on RK3576) | Container orchestration |
| P3 | Multi-cluster federation | Single-pane-of-glass for 2+ clusters |
| P3 | GPU time-sharing (MIG on future GPU) | Better GPU utilization |

---

*Generated: 2026-04-09 | ACOS v1.0*
