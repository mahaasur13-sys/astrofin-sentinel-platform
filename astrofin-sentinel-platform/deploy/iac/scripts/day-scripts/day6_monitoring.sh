#!/usr/bin/env bash
# Day 6: Monitoring stack — Prometheus + Grafana + exporters
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

echo "=== DAY 6: Monitoring Stack ==="

GRAFANA_ADMIN_PASSWORD="${GRAFANA_ADMIN_PASSWORD:-admin123}"
PROMETHEUS_RETENTION_DAYS="${PROMETHEUS_RETENTION_DAYS:-15}"

# 1. Create monitoring namespace / directories
log "[1/7] Preparing monitoring directories..."
ansible all -i "$INVENTORY" -m file -a "path=/opt/monitoring state=directory mode=0755"
ansible all -i "$INVENTORY" -m file -a "path=/opt/monitoring/prometheus state=directory mode=0755"
ansible all -i "$INVENTORY" -m file -a "path=/opt/monitoring/grafana/state mode=0755"
ansible all -i "$INVENTORY" -m file -a "path=/opt/monitoring/alertmanager state=directory mode=0755"

# 2. Install Prometheus via Docker
log "[2/7] Starting Prometheus container..."
ansible "gpu-node" -i "$INVENTORY" -m docker_container -a "
    name=prometheus
    image=prom/prometheus:v2.48.0
    restart_policy=always
    network_mode=host
    volumes=/opt/monitoring/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml,r,/opt/monitoring/prometheus/data:/prometheus
    command='--config.file=/etc/prometheus/prometheus.yml --storage.tsdb.retention.time=${PROMETHEUS_RETENTION_DAYS}d --storage.tsdb.path=/prometheus --web.console.libraries=/usr/share/prometheus/console_libraries --web.console.templates=/usr/share/prometheus/consoles'
    env=PROMETHEUS_RETENTION=${PROMETHEUS_RETENTION_DAYS}
"

# 3. Install node-exporter on all nodes
log "[3/7] Starting node-exporter on all nodes..."
ansible all -i "$INVENTORY" -m docker_container -a "
    name=node_exporter
    image=prom/node-exporter:v1.7.0
    restart_policy=always
    network_mode=host
    args='--path.procfs=/host/proc --path.sysfs=/host/sys --path.rootfs=/rootfs --collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    published_ports=9100:9100
"

# 4. Slurm exporter (on controller node)
log "[4/7] Starting Slurm exporter..."
ansible "gpu-node" -i "$INVENTORY" -m docker_container -a "
    name=slurm_exporter
    image=ghcr.io/jahidulp/slurm-exporter:latest
    restart_policy=always
    network_mode=host
    env=SLURMCTLD_HOST=192.168.1.10,SLURMCTLD_PORT=6817
    published_ports=8080:8080
"

# 5. Install Grafana via Docker
log "[5/7] Starting Grafana container..."
ansible "gpu-node" -i "$INVENTORY" -m docker_container -a "
    name=grafana
    image=grafana/grafana:10.2.2
    restart_policy=always
    network_mode=host
    volumes=/opt/monitoring/grafana/state:/var/lib/grafana,/opt/monitoring/grafana/provisioning:/etc/grafana/provisioning
    env=GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD},GF_USERS_ALLOW_SIGN_UP=false,GF_SERVER_ROOT_URL=http://192.168.1.10:3000
    published_ports=3000:3000
"

# 6. Provision Grafana datasources and dashboards
log "[6/7] Provisioning Grafana datasources and dashboards..."
ansible "gpu-node" -i "$INVENTORY" -m copy -a "
    content='apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    url: http://localhost:9090
    isDefault: true
    editable: false
    jsonData:
      timeInterval: 15s
'
    dest=/opt/monitoring/grafana/provisioning/datasources/prometheus.yml
    mode=0644
"

ansible "gpu-node" -i "$INVENTORY" -m copy -a "
    content='apiVersion: 1
providers:
  - name: HomeCluster Dashboards
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /etc/grafana/provisioning/dashboards
'
    dest=/opt/monitoring/grafana/provisioning/dashboards/dashboard.yml
    mode=0644
"

# Dashboard JSON imports (Slurm ID 14061, Ceph ID 3662, Node ID 1860)
ansible "gpu-node" -i "$INVENTORY" -m file -a "path=/opt/monitoring/grafana/provisioning/dashboards/dashboards state=directory mode=0755"

# 7. Prometheus scrape config
log "[7/7] Configuring Prometheus scrape targets..."
ansible "gpu-node" -i "$INVENTORY" -m copy -a "
    content='global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: home-gpu-cluster

scrape_configs:
  - job_name: prometheus
    static_configs:
      - targets: [localhost:9090]

  - job_name: node
    static_configs:
      - targets:
          - 192.168.1.10:9100
          - 192.168.1.20:9100

  - job_name: slurm
    static_configs:
      - targets: [192.168.1.10:8080]

  - job_name: ceph
    static_configs:
      - targets: [192.168.1.10:9283]
'
    dest=/opt/monitoring/prometheus/prometheus.yml
    mode=0644
"

log "=== DAY 6 COMPLETE ==="
log "Prometheus: http://192.168.1.10:9090"
log "Grafana:    http://192.168.1.10:3000 (admin/${GRAFANA_ADMIN_PASSWORD})"
log "Node exporter: http://192.168.1.10:9100 / http://192.168.1.20:9100"
log "Slurm exporter: http://192.168.1.10:8080/metrics"