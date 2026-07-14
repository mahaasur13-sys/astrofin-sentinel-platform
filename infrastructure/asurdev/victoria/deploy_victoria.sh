#!/bin/bash
set -euo pipefail
LOG_PREFIX="[ACOS-VICTORIA]"

echo "$LOG_PREFIX === VictoriaMetrics Deploy ==="

# Detect platform
ARCH=$(uname -m)
case "$ARCH" in
  x86_64) VICTORIA_ARCH="amd64" ;;
  aarch64) VICTORIA_ARCH="arm64" ;;
  armv7l) VICTORIA_ARCH="armhf" ;;
  *) echo "$LOG_PREFIX Unsupported arch: $ARCH"; exit 1 ;;
esac

VICTORIA_VERSION="${VICTORIA_VERSION:-v1.99.0}"
VICTORIA_URL="https://github.com/VictoriaMetrics/VictoriaMetrics/releases/download/${VICTORIA_VERSION}/victoria-metrics-linux-${VICTORIA_ARCH}.tar.gz"

echo "$LOG_PREFIX Installing VictoriaMetrics ${VICTORIA_VERSION} for ${VICTORIA_ARCH}..."

# Download
TMP=$(mktemp -d)
curl -fsSL "$VICTORIA_URL" -o "$TMP/victoria.tar.gz"
tar -xzf "$TMP/victoria.tar.gz" -C "$TMP"
sudo mv "$TMP/victoria-metrics-prod" /usr/local/bin/victoria-metrics
sudo mv "$tmp/victoria-metrics-import" /usr/local/bin/ 2>/dev/null || true
rm -rf "$TMP"

# Create user
id -u victoria &>/dev/null || sudo useradd -rs /bin/false victoria

# Directories
sudo mkdir -p /var/lib/victoria-metrics /var/log/victoria-metrics /etc/victoria-metrics
sudo chown victoria:victoria /var/lib/victoria-metrics /var/log/victoria-metrics

# Scrape config
sudo tee /etc/victoria-metrics/scrape.yml > /dev/null << 'SCRAPE'
# Auto-discovered targets for ACOS cluster
# RTX3060: primary node
- targets: ['localhost:9100', 'localhost:8000', 'localhost:9111']
  labels:
    cluster: 'home-cluster'
    node: 'rtx3060'

# RK3576: secondary node (configured via agent)
# Remote scrape — configure in VictoriaMetrics as:
# - targets: ['192.168.1.101:9100', '192.168.1.101:8000']
#   labels:
#     cluster: 'home-cluster'
#     node: 'rk3576'
SCRAPE

# systemd unit
sudo tee /etc/systemd/system/victoria-metrics.service > /dev/null << 'SYSTEMD'
[Unit]
Description=VictoriaMetrics Time Series Database
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=victoria
Group=victoria
WorkingDirectory=/var/lib/victoria-metrics
ExecStart=/usr/local/bin/victoria-metrics \
    -promscrape.config=/etc/victoria-metrics/scrape.yml \
    -retentionPeriod=30d \
    -graphiteListenAddr=:2003 \
    -opentsdbListenAddr=:4242 \
    -influxListenAddr=:8086 \
    -httpListenAddr=:8428 \
    -storageDataPath=/var/lib/victoria-metrics \
    -loggerLevel=INFO
Restart=on-failure
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SYSTEMD

# Enable
sudo systemctl daemon-reload
sudo systemctl enable victoria-metrics
sudo systemctl start victoria-metrics

echo ""
echo "$LOG_PREFIX === VictoriaMetrics Deployed ==="
echo "$LOG_PREFIX Web UI:     http://localhost:8428"
echo "$LOG_PREFIX Metrics:    http://localhost:8428/api/v1/write"
echo "$LOG_PREFIX Prometheus: http://localhost:8428/api/v1/query"
echo ""
echo "$LOG_PREFIX Add RK3576 targets to /etc/victoria-metrics/scrape.yml:"
echo "$LOG_PREFIX   - targets: ['192.168.1.101:9100', '192.168.1.101:8000']"
