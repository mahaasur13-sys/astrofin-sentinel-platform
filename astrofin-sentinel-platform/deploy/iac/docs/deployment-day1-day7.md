# Deployment Guide: Day 1 → Day 7

## Overview

Full step-by-step deployment of the distributed home cloud platform.

---

## 🔴 DAY 1 — Network Foundation

### Goal
MikroTik hEX S configured with 4 VLANs for cluster isolation.

### Steps

```bash
# Connect management laptop to MikroTik ether1
# Default MikroTik IP: 192.168.1.1

# Run Day 1 script
cd home-cluster-iac
MIKROTIK_PASS=your_password MIKROTIK_HOST=10.10.10.1 make day1-network

# Or manually via API
curl -s -k -X POST "https://10.10.10.1/rest/interface/bridge" \
  -u "admin:your_password" -H "Content-Type: application/json" \
  -d '{"name":"br-cluster","vlan-filtering":"yes"}'
```

### Expected Output
```
[DAY1] Checking MikroTik connectivity...
[OK] MikroTik reachable
[DAY1] Creating bridge br-lan...
[OK] Added ether2 to br-lan
...
[DAY1] DONE — Network Foundation Ready
  VLAN 10 (mgmt)    : 10.10.10.0/24  → MikroTik: 10.10.10.1
  VLAN 20 (compute) : 10.20.20.0/24  → MikroTik: 10.20.20.1
  VLAN 30 (storage) : 10.30.30.0/24  → MikroTik: 10.30.30.1
  VLAN 40 (vpn)     : 10.40.40.0/24  → MikroTik: 10.40.40.1
```

---

## 🟠 DAY 2 — WireGuard Mesh Encryption

### Goal
Encrypted point-to-point mesh between RTX and RK3576.

### Steps

```bash
# Generate WireGuard keys on RTX node
wg genkey | tee privatekey | wg pubkey > publickey

# Setup AmneziaWG (optional — better obfuscation)
curl -fsSL https://raw.githubusercontent.com/amnezia-vpn/amnezia-client/master/deploy/ags.sh | bash

# Copy wg0.conf template
cp configs/wireguard/wg0.conf /etc/wireguard/wg0.conf
vim /etc/wireguard/wg0.conf  # add private key

# Enable wireguard
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0
```

### Expected Output
```
[DAY2] WireGuard mesh active
  Endpoint: 10.200.0.10 (RTX) <-> 10.200.0.11 (RK3576)
  Protocol: AmneziaWG / WireGuard
```

---

## 🔵 DAY 3 — Compute Nodes

### Goal
RTX 3060 ready for GPU workloads.

### Steps

```bash
# Run Day 3 script on RTX node
bash scripts/day3-compute.sh

# Or manually:
# 1. Install NVIDIA driver
sudo apt install nvidia-driver-535 nvidia-dkms-535

# 2. Verify CUDA
nvidia-smi  # should show RTX 3060

# 3. Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 4. Install Python ML env
python3 -m venv ~/.venv/ml
source ~/.venv/ml/bin/activate
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Expected Output
```
[DAY3] NVIDIA driver: 535.104.05
[DAY3] CUDA version: 11.8
[DAY3] Docker: 24.0.5
[DAY3] PyTorch: 2.1.0+cu118
[OK] GPU node ready
```

---

## 🟢 DAY 4 — Slurm Cluster

### Goal
Slurm GPU scheduler with RTX 3060 partition.

### Steps

```bash
# Run Day 4 script on RTX node (as root)
bash scripts/day4-slurm.sh

# Verify GPU scheduling
sinfo -Nel  # show all nodes
srun --partition=gpu --gres=gpu:rtx3060:1 nvidia-smi
```

### Expected Output
```
PARTITION AVAIL TIMECUT LIMIT NODES STATE   NODELIST
gpu*         up   infinite  72:0     1 drain* home-rtx3060
edge         up   infinite 168:0     1 drain* edge-rk3576
debug        up       1:0     0  2 drain* home-rtx3060,edge-rk3576

[DAY4] Slurm cluster: 2 nodes, 1 GPU
[OK] GPU job submitted
```

---

## 🟣 DAY 5 — Ray AI Runtime

### Goal
Distributed Ray cluster for AI workloads.

### Steps

```bash
# Run Day 5 script
bash scripts/day5-ray.sh

# Test Ray cluster
ray status
python -c "import ray; ray.init(); print(ray.cluster_resources())"
```

### Expected Output
```
[DAY5] Ray head started on 10.20.20.10:6379
[DAY5] Ray worker started on 10.20.20.11:6379
[OK] Ray cluster: 2 nodes, 12 CPU, 1 GPU
```

---

## 🟤 DAY 6 — Ceph Storage

### Goal
Distributed storage with 2-node replication.

### Steps

```bash
# Run Day 6 script
bash scripts/day6-ceph.sh

# Verify Ceph health
ceph status
ceph osd tree
```

### Expected Output
```
[DAY6] Ceph cluster initialized
[DAY6] OSDs: 2 (home-rtx3060 + edge-rk3576)
[OK] Ceph health: HEALTH_OK
[OK] 2x replication active
```

---

## ⚫ DAY 7 — Integration

### Goal
Full system integration with job routing and monitoring.

### Steps

```bash
# Run Day 7 script
bash scripts/day7-integration.sh

# Verify all components
make status
curl http://localhost:9090/api/v1/status  # Prometheus
```

### Expected Output
```
[DAY7] Prometheus scraping: slurm, ray, ceph, node
[DAY7] Grafana: http://10.20.20.10:3000
[DAY7] Slurm ↔ Ray bridge: ACTIVE
[OK] Mini-AWS fully operational
```

---

## 🔄 Rollback

If any day fails:

```bash
# Check logs
journalctl -u slurmd -n 50
cat /var/log/slurmctld.log

# Reset and retry
make day4-slurm  # re-run specific day
```
