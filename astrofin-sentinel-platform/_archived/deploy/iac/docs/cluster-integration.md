# Home Cluster Integration Guide — ACOS × AmneziaWG × Modular Monitoring

## Overview

Two-node ACOS SCL v6 cluster on Pop!_OS:

| Node | Role | IP | Components |
|------|------|-----|------------|
| **rtx3060** | Primary (server) | 192.168.1.100 | AmneziaWG server, VictoriaMetrics, Grafana, Beszel, Perses, Prometheus, Loki, AlertManager, ACOS Engine |
| **rk3576** | Secondary (client) | 192.168.1.101 | AmneziaWG client, Beszel agent, node_exporter, ACOS agent |

---

## 1. Pre-flight Checklist

Run on **each** node:

```bash
# ── System ─────────────────────────────────────────────────
uname -r                              # Kernel ≥ 5.10
id                                    # Running as root (or sudo)
cat /etc/os-release | grep -E "ID=|VERSION="

# ── Required packages ────────────────────────────────────
sudo apt-get update -qq
sudo apt-get install -y \
    build-essential \
    linux-headers-$(uname -r) \
    wireguard-tools \
    git \
    curl \
    netcat-openbsd \
    python3-pip \
    python3-venv

# ── Docker ─────────────────────────────────────────────────
docker --version
docker-compose --version || docker compose version
sudo systemctl enable --now docker

# ── Verify kernel module ─────────────────────────────────
lsmod | grep wireguard
# Expected: wireguard line (may be empty inside containers — OK)

# ── SSH access between nodes (optional) ──────────────────
# On rtx3060:
ssh-copy-id asur@192.168.1.101
```

---

## 2. Step-by-Step Deployment

### STEP 1 — Prepare both nodes

```bash
# On BOTH nodes:
sudo mkdir -p /opt/acos
git clone https://github.com/mahaasur13-sys/AsurDev.git /tmp/acos-src
sudo cp -r /tmp/acos-src/* /opt/acos/
cd /opt/acos && ls -la
```

### STEP 2 — AmneziaWG Server (rtx3060)

```bash
# On rtx3060 (192.168.1.100) as root:
cd /opt/acos
sudo bash deploy_amneziawg.sh server

# Generate keys (if not auto-generated):
sudo wg genkey | sudo tee /etc/awg/server.key
sudo wg pubkey < /etc/awg/server.key | tee /etc/awg/server.pub
# Output: SERVER_PUBLIC_KEY — SAVE THIS

# Check AmneziaWG kernel module (may not be available in containers):
lsmod | grep amnezia || lsmod | grep wireguard
# If wireguard present → works as fallback

# Create config:
sudo nano /etc/awg/awg0.conf   # See config below

# Enable IP forwarding:
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.d/99-awg.conf
sudo sysctl -p /etc/sysctl.d/99-awg.conf

# Start tunnel:
sudo awg-quick up awg0    # or: sudo wg-quick up awg0
# Verify:
ip addr show wg0
ping -c 3 10.8.0.2

# Enable at boot:
sudo systemctl enable awg-quick@awg0

# ── SERVER /etc/awg/awg0.conf ─────────────────────────────
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = <SERVER_PRIVATE_KEY>
PostUp = iptables -A FORWARD -i %i -j ACCEPT
PostUp = iptables -A FORWARD -o %i -j ACCEPT
PostUp = iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT
PostDown = iptables -D FORWARD -o %i -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

# Replace with actual client public key AFTER client setup
[Peer]
PublicKey = <CLIENT_PUBLIC_KEY>
AllowedIPs = 10.8.0.2/32
PersistentKeepalive = 25
```

### STEP 3 — AmneziaWG Client (rk3576)

```bash
# On rk3576 (192.168.1.101) as root:
cd /opt/acos
sudo bash deploy_amneziawg.sh client

# Generate client keys:
sudo wg genkey | sudo tee /etc/awg/client.key
sudo wg pubkey < /etc/awg/client.key | tee /etc/awg/client.pub
# Output: CLIENT_PUBLIC_KEY — COPY TO SERVER

# Server public key should be manually copied from rtx3060:
# scp asur@192.168.1.100:/etc/awg/server.pub /tmp/
# Or: cat /etc/awg/server.pub on rtx3060 and paste below

# Create client config:
sudo nano /etc/awg/awg0.conf

# ── CLIENT /etc/awg/awg0.conf ─────────────────────────────
[Interface]
Address = 10.8.0.2/24
PrivateKey = <CLIENT_PRIVATE_KEY>
DNS = 1.1.1.1

[Peer]
PublicKey = <SERVER_PUBLIC_KEY>
Endpoint = 192.168.1.100:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25

# Start:
sudo awg-quick up awg0
# Verify:
ip addr show wg0
ping -c 3 10.8.0.1

# Enable at boot:
sudo systemctl enable awg-quick@awg0
```

### STEP 4 — Key Exchange (both nodes)

```bash
# On rtx3060 — show server public key:
sudo cat /etc/awg/server.pub
# Output looks like: 4KcD...

# On rk3576 — add to client config manually:
# Paste SERVER_PUBLIC_KEY into /etc/awg/awg0.conf [Peer] PublicKey= line

# On rtx3060 — add client public key to server config:
# Paste CLIENT_PUBLIC_KEY into /etc/awg/awg0.conf [Peer] PublicKey= line

# Restart tunnel on both:
sudo awg-quick down awg0 && sudo awg-quick up awg0

# Test full connectivity:
# From rtx3060:
ping -c 3 10.8.0.2
# From rk3576:
ping -c 3 10.8.0.1
```

### STEP 5 — VictoriaMetrics (rtx3060)

```bash
# On rtx3060:
cd /opt/acos
sudo bash victoria/deploy_victoria.sh

# Verify:
curl -s http://localhost:8428/health
# Expected: {"status":"ok"}

# Add RK3576 targets:
sudo tee /etc/victoria-metrics/scrape.yml > /dev/null << 'SCRAPE'
scrape_configs:
  - job_name: 'rtx3060'
    static_configs:
      - targets: ['localhost:9100', 'localhost:8000', 'localhost:9111']
        labels:
          cluster: 'home-cluster'
          node: 'rtx3060'

  - job_name: 'rk3576'
    static_configs:
      - targets: ['192.168.1.101:9100', '192.168.1.101:8000']
        labels:
          cluster: 'home-cluster'
          node: 'rk3576'
SCRAPE

# Restart:
sudo systemctl restart victoria-metrics
curl -s http://localhost:8428/targets | python3 -m json.tool | head -20
```

### STEP 6 — Observability Stack (rtx3060)

```bash
# On rtx3060:
cd /opt/acos/observability

# Fix Loki config if missing:
cat > loki-config.yml << 'LOKI_EOF'
auth_enabled: false
server:
  http_listen_port: 3100
positions:
  filename: /tmp/positions.yaml
client:
  url: http://localhost:3100
limits:
  reject_old_samples: true
LOKI_EOF

# Start all:
docker-compose up -d

# Verify:
curl -s http://localhost:9090/-/healthy    # Prometheus
curl -s http://localhost:3000/api/health    # Grafana
curl -s http://localhost:9093/-/healthy     # AlertManager
curl -s http://localhost:3100/ready         # Loki
curl -s http://localhost:9100/metrics | head -5  # node_exporter
curl -s http://localhost:9111/metrics       # awg_exporter

# Default credentials:
# Grafana: acos / acos123
# Prometheus: no auth
# AlertManager: no auth
```

### STEP 7 — Beszel (rtx3060 + rk3576)

```bash
# On rtx3060:
cd /opt/acos/beszel

# Edit agent key BEFORE starting:
# Replace REPLACE_WITH_RTX_AGENT_KEY with a secure random string:
KEY=$(openssl rand -hex 32)
sed -i "s/REPLACE_WITH_RTX_AGENT_KEY/$KEY/" docker-compose.yml
echo "Beszel Agent Key: $KEY"  # SAVE THIS — needed for Beszel web UI

docker-compose up -d

# On rk3576 — add second agent:
# Edit docker-compose on rk3576:
# REPLACE_WITH_RK3576_AGENT_KEY with another key

# Access Beszel Web UI: http://192.168.1.100:8090
# Add agents using the keys generated above
```

### STEP 8 — Perses (rtx3060)

```bash
# On rtx3060:
cd /opt/acos/perses
docker-compose up -d

# Access: http://192.168.1.100:8080
# Import dashboard: copy contents of dashboards/acos.json into Perses UI
```

### STEP 9 — Grafatui (rtx3060, optional terminal client)

```bash
# Install:
cargo install grafatui

# Or via Docker:
docker run -it --rm \
    -e TERM=xterm-256color \
    ghcr.io/henrygd/grafatui:latest \
    http://localhost:8428

# Or use the launcher:
cd /opt/acos/grafatui
./grafatui_launcher.sh
```

### STEP 10 — ACOS Python modules + systemd services (both nodes)

```bash
# On BOTH nodes:
cd /opt/acos

# Install Python modules:
sudo mkdir -p /opt/acos/{events,state,projection,storage,validator,network,incidents,recorder}
sudo cp -r acos/*.py /opt/acos/
sudo cp -r acos/*/*.py /opt/acos/*/

# Copy systemd services:
sudo cp systemd/acos-tunnel-monitor.service /etc/systemd/system/
sudo cp systemd/tunnel_monitor.py /opt/acos/network/
sudo chmod +x /opt/acos/network/tunnel_monitor.py

# Reload systemd:
sudo systemctl daemon-reload

# Enable services:
sudo systemctl enable acos-tunnel-monitor
sudo systemctl start acos-tunnel-monitor

# Verify:
sudo systemctl status acos-tunnel-monitor --no-pager
journalctl -u acos-tunnel-monitor -n 20 --no-pager
```

### STEP 11 — Install ACOS Monitor CLI (both nodes)

```bash
# On BOTH nodes:
sudo cp /opt/acos/acos/cli/monitor.py /usr/local/bin/acos-monitor
sudo chmod +x /usr/local/bin/acos-monitor

# Create wrapper:
sudo tee /usr/local/bin/acos << 'ACOS_WRAPPER'
#!/bin/bash
exec /usr/local/bin/acos-monitor monitor "$@"
ACOS_WRAPPER
sudo chmod +x /usr/local/bin/acos

# Test:
acos monitor list
acos monitor status
```

---

## 3. Verification Commands

```bash
# ── Tunnel ─────────────────────────────────────────────────
sudo awg show                          # WireGuard status
ip addr show wg0                      # Interface UP?
ping -c 3 10.8.0.1                    # Server reachable?
ping -c 3 10.8.0.2                    # Client reachable?

# ── ACOS ──────────────────────────────────────────────────
cd /opt/acos
python3 tests/test_amneziawg_integration.py

# ── Monitoring ────────────────────────────────────────────
curl -s http://localhost:8428/health
curl -s http://localhost:9090/api/v1/query?query=up
curl -s http://localhost:9111/metrics | grep awg_
curl -s http://localhost:9100/metrics | grep node_cpu

# ── Cluster Status ────────────────────────────────────────
sudo /opt/acos/cluster_status.sh
acos monitor status
```

---

## 4. Switching Monitoring Backends

```bash
# List backends:
acos monitor list

# Switch active backend:
acos monitor switch beszel    # → Beszel web UI
acos monitor switch perses     # → Perses web UI
acos monitor switch grafana    # → Grafana web UI
acos monitor switch grafatui   # → Terminal client

# Verify switch:
acos monitor status
cat /etc/acos/monitoring.json
```

---

## 5. Troubleshooting

### Tunnel won't come up

```bash
# Check kernel module:
lsmod | grep -E "wireguard|amnezia"

# Check config syntax:
sudo awg showconfig wg0

# Check logs:
journalctl -u acos-tunnel-monitor -f
dmesg | grep -i wireguard

# Verify keys match:
# On server: sudo wg show wg0
# On client: ping server's 10.8.0.1
```

### Metrics not scraping

```bash
# Test individual exporters:
curl -s http://localhost:9100/metrics | grep up
curl -s http://localhost:9111/metrics | grep awg

# Check Prometheus targets:
curl -s http://localhost:9090/api/v1/targets | python3 -c "
import sys,json
data=json.load(sys.stdin)
for t in data['data']['activeTargets']:
    print(f\"{t['labels']['job']}: {t['health']} — {t['lastError'][:80] if t.get('lastError') else 'OK'}\"
"

# Firewall check:
sudo iptables -L -n | grep -E "9100|8428|9111"
```

### VictoriaMetrics not receiving data

```bash
# Check storage:
curl -s http://localhost:8428/api/v1/query?query=up

# Check retention:
curl -s http://localhost:8428/internal/rollup?match[]=up | head -5

# Restart:
sudo systemctl restart victoria-metrics
journalctl -u victoria-metrics -n 20 --no-pager
```

### Ports already in use

```bash
# Find what's using a port:
sudo ss -tlnp | grep ':3000\|:8428\|:9090\|:9111\|:8090'
# Kill if needed:
sudo fuser -k 3000/tcp
```

### Podman instead of Docker (Pop!_OS quirk)

```bash
# If docker-compose fails, try:
docker compose up -d    # Docker v2 syntax
# OR
podman-compose up -d    # If podman installed
```

---

## 6. All Services Reference

| Service | Port | URL | Auth |
|---------|------|-----|------|
| VictoriaMetrics | 8428 | http://localhost:8428 | None |
| Prometheus | 9090 | http://localhost:9090 | None |
| Grafana | 3000 | http://localhost:3000 | acos / acos123 |
| Beszel | 8090 | http://localhost:8090 | Set on first login |
| Perses | 8080 | http://localhost:8080 | None |
| Loki | 3100 | http://localhost:3100 | None |
| AlertManager | 9093 | http://localhost:9093 | None |
| node_exporter | 9100 | http://localhost:9100/metrics | None |
| awg_exporter | 9111 | http://localhost:9111/metrics | None |
| ACOS Metrics | 8000 | http://localhost:8000/metrics | None |
| AmneziaWG | 51820 | UDP | Keys only |

### AmneziaWG Network

| Node | LAN IP | VPN IP | Role |
|------|--------|--------|------|
| rtx3060 | 192.168.1.100 | 10.8.0.1 | Server |
| rk3576 | 192.168.1.101 | 10.8.0.2 | Client |

---

## 7. Quick Reference

```bash
# Full cluster deploy (rtx3060):
cd /opt/acos && sudo bash deploy_all.sh

# Per-node deploy:
# rtx3060:
sudo bash deploy_all.sh --skip-wg server
# rk3576:
sudo bash deploy_all.sh --skip-wg client

# Check everything:
sudo /opt/acos/cluster_status.sh

# Run tests:
cd /opt/acos && python3 tests/test_amneziawg_integration.py

# Watch tunnel:
journalctl -u acos-tunnel-monitor -f

# Send metrics to VM:
curl -d "awg_tunnel_up{node=\"rtx3060\"} 1" http://localhost:8428/api/v1/import/prometheus

# Rebuild ACOS state from events:
cd /opt/acos && python3 -c "
import sys; sys.path.insert(0, '/opt/acos')
from acos.events.event_log import EventLog
from acos.state.reducer import StateReducer
log = EventLog()
reducer = StateReducer(log)
for trace_id in set(e.trace_id for e in log.get_all() if e.trace_id):
    state = reducer.rebuild(trace_id)
    print(f\"{trace_id}: {state['status']}\")
"
```
