# 🏗️ Home Cluster Architecture — Unified System Design

## Overview

```
Layer          Technology              Purpose
─────────────────────────────────────────────────────────────
L0 (Mesh)      AmneziaWG / WireGuard   Encrypted overlay VPN
L1 (Network)   MikroTik VLANs           Layer 3 routing + isolation
L2 (Storage)   Ceph 2-node             Distributed replicated storage
L3 (Compute)   Slurm GPU scheduling     Batch GPU job orchestration
L4 (AI)        Ray distributed          Distributed AI runtime
L5 (Optional)  Kubernetes federation    Container orchestration layer
```

## Node Roles

### Primary Node (RTX 3060 PC)
- Slurm controller (with HA backup)
- Slurm compute node (GPU partition)
- Ray head node
- Ceph MON + OSD
- Docker host (ML workloads)

### Edge Node (RK3576)
- Slurm compute node (CPU partition)
- Ray worker (lightweight)
- Ceph OSD
- AmneziaWG endpoint
- Optional: K8s worker (NOT control plane)

### Optional VPS Node
- WireGuard relay
- Potential Ceph OSD (cold storage)
- Ray worker (inference offload)

## Network Design

### VLAN Segmentation
```
VLAN 10 (mgmt)    10.10.10.0/24    — SSH, Ansible, monitoring
VLAN 20 (compute) 10.20.20.0/24   — Slurm, Ray internode
VLAN 30 (storage) 10.30.30.0/24   — Ceph public + cluster network
VLAN 40 (vpn)     10.40.40.0/24   — WireGuard mesh overlay
```

### AmneziaWG Mesh
- Each node has a WireGuard public key
- Mesh topology: all nodes connect to all others
- Used for: Ceph replication traffic, Ray internode, cross-node jobs

## Storage Design (Ceph)

### 2-Node Configuration
```
OSD.1: RTX PC  → /dev/sdb (secondary disk)
OSD.2: RK3576  → /dev/sda (primary disk)

pg_num = 128 (min), replication factor = 3
Min size = 2 (allows 1 node failure)
```

### Use Cases
- `/mnt/cephfs/datasets/` — AI training data
- `/mnt/cephfs/models/` — model checkpoints
- RBD volumes for Docker/K8s

## Compute Design (Slurm)

### Partitions
```
Partition  Nodes       CPUs   GPUs   MaxTime
──────────────────────────────────────────────
gpu        rtx-node     12     1      24:00
cpu        rk3576-node   8     0      24:00
debug      all          all   all    01:00
```

### HA Configuration
- 1 primary controller (RTX PC)
- 1 secondary controller (RK3576 or VPS)
- VIP on WireGuard interface
- CephFS as distributed lock for failover

## AI Runtime Design (Ray)

### Cluster Topology
```
Ray Head:  rtx-node:6379 (dashboard :8265)
Ray Worker CPU: rk3576-node
```

### Job Types
- Ray AIR tasks (distributed Python)
- Ray Serve (HTTP inference API)
- Ray Batch inference
- Ray Datasets (shared storage via Ceph)

## Day 0–7 Deployment Lifecycle

```
Day 0  — Bootstrap: SSH keys, base packages, users
Day 1  — Network: MikroTik VLAN config, Ansible bootstrap
Day 2  — VPN mesh: AmneziaWG install + verification
Day 3  — Compute: NVIDIA drivers, Docker, Python env
Day 4  — Slurm: Controller + compute nodes, GPU partition
Day 5  — Ray: Head + worker, distributed task test
Day 6  — Ceph: MON + OSD deployment, replication test
Day 7  — Integration: job routing, Slurm↔Ray bridge, monitoring
```

## Directory Structure

```
home-cluster-iac/
├── scripts/               ← Canonical day-scripts (AsurDev baseline)
│   ├── day1-network.sh
│   ├── day2-vpn.sh
│   ├── day3-compute.sh
│   ├── day4-slurm.sh
│   ├── day5-ray.sh
│   ├── day6-ceph.sh
│   ├── day7-integration.sh
│   ├── test_suite.sh      ← L1-L6 validation suite
│   └── infra-tools/       ← Operational utilities
│       ├── validate.sh
│       ├── generate_vars.sh
│       ├── vars.sh
│       ├── slurm_ha_failover.sh
│       └── day6_monitoring.sh
├── terraform/             ← IaC modules
│   ├── main.tf
│   └── modules/
│       ├── network/
│       ├── compute/
│       ├── storage/
│       ├── slurm/
│       ├── ray/
│       └── vpn_mesh/
├── ansible/               ← Configuration management
│   ├── inventory.ini
│   ├── playbook.yml
│   ├── site.yml
│   └── roles/
├── k8s/                   ← Kubernetes manifests
│   ├── manifests/
│   └── federation/
├── monitoring/            ← Prometheus + Grafana
│   ├── prometheus.yml
│   ├── grafana-datasources.yml
│   └── alerts/
├── self_healing/          ← Watchdog + HA
│   ├── watchdog.sh
│   ├── health_check.sh
│   ├── cluster-watchdog.service
│   └── k8s_watchdog.yaml
└── docs/
    └── ARCHITECTURE.md
```

## Key Integration Points

### Slurm ↔ Ray Bridge
```bash
# Submit Ray task via Slurm
sbatch --partition=gpu --gres=gpu:1 \
  /opt/slurm-ray-bridge.sh my_ray_task.py
```

### Ceph ↔ Docker/K8s
```bash
# Mount CephFS in container
docker run -v /mnt/cephfs/datasets:/data my-image
```

### Monitoring Stack
- Prometheus: metrics collection (node-exporter, slurm-exporter, ceph-exporter)
- Grafana: dashboards (cluster_overview.json)
- Alertmanager: PagerDuty/Telegram notifications

## Security Considerations

- WireGuard mesh is encrypted (no plain-text cross-node traffic)
- Ceph replication over WireGuard tunnel
- Slurm munge key shared across all nodes
- No exposed services on public internet (VLAN isolation)
