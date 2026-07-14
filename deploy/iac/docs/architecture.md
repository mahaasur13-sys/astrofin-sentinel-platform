# Home GPU Cluster — Architecture & Operations Guide

> **Mission:** Build a self-hosted distributed compute platform that mirrors AWS GPU cloud capabilities (g4dn-like), running on commodity hardware in a home environment.

---

## 1. Network Topology

```mermaid
graph TB
    subgraph Internet
        WAN[(WAN / ISP)]
    end

    subgraph MikroTik_hEX_S["MikroTik hEX S (L3 Router)"]
        direction TB
        WAN_IF[WAN Interface]
        BR[Bridge / VLANs]
        VLAN100[VLAN 100: mgmt]
        VLAN200[VLAN 200: gpu-nodes]
        DHCP100[DHCP: 10.66.100.0/24]
        DHCP200[DHCP: 10.66.200.0/24]
        NAT[NAT / Masquerade]
    end

    subgraph WireGuard_Mesh["AmneziaWG Mesh (wg0 · 10.66.0.0/16)"]
        WG_GPU["10.66.0.10\ngpu-node"]
        WG_EDGE["10.66.0.20\nedge-node"]
    end

    subgraph GPU_Node["gpu-node (Pop!_OS · RTX 3060)"]
        direction TB
        SLURM_CTL[slurmctld\n(primary)]
        RAY_HEAD[Ray head\n:6379]
        CEPH_OSD[ceph-osd]
        DOCKER[Docker\n+ nvidia-docker]
    end

    subgraph Edge_Node["edge-node (RK3576 · ARM)"]
        direction TB
        SLURM_WRK[slurmd]
        RAY_WRK[Ray worker]
        CEPH_OSD2[ceph-osd]
    end

    subgraph Storage["CephFS (/mnt/cephfs · 2x replica)"]
        CEPH_FS[CephFS]
        CEHP_DATA[(datasets · models · logs)]
    end

    WAN --> NAT
    NAT --> BR
    BR --> VLAN100
    BR --> VLAN200
    VLAN100 --> DHCP100
    VLAN200 --> DHCP200
    DHCP100 -.-> WG_GPU
    DHCP200 -.-> WG_GPU
    DHCP100 -.-> WG_EDGE
    DHCP200 -.-> WG_EDGE
    WG_GPU <--> WG_EDGE
    WG_GPU --> SLURM_CTL
    WG_GPU --> RAY_HEAD
    WG_GPU --> CEPH_OSD
    WG_EDGE --> SLURM_WRK
    WG_EDGE --> RAY_WRK
    WG_EDGE --> CEPH_OSD2
    CEPH_OSD <--> CEPH_OSD2
    CEPH_OSD --> CEPH_FS
    CEPH_OSD2 --> CEPH_FS
    CEPH_FS --> CEHP_DATA
```

---

## 2. Layer Architecture

| Layer | Component | Daemon/Service | Port | Notes |
|-------|-----------|----------------|------|-------|
| **L0** | Mesh VPN | AmneziaWG / wg-quick@wg0 | 51820/UDP | 10.66.0.0/16 subnet |
| **L1** | Router | RouterOS (MikroTik) | — | VLAN100/200, NAT, DHCP |
| **L2** | Distributed Storage | ceph-osd, ceph-mgr | 6800–7300 | CephFS, 2x replication |
| **L3** | GPU Batch Scheduler | slurmctld, slurmd | 6817–6818 | GPU partition (RTX 3060) |
| **L4** | Container Host | Docker + nvidia-container-runtime | 2375 | ML / AI workloads |
| **L5** | AI Runtime | Ray head + workers | 6379 / 8265 | Head on gpu-node, workers on ARM |

---

## 3. Node Inventory

| Node | Hostname | Role | IP (VLAN200) | IP (wg0) | Hardware | OS |
|------|----------|------|--------------|----------|----------|-----|
| GPU | gpu-node | Slurm primary / Ray head / Ceph OSD / Docker host | 192.168.1.10 | 10.66.0.10 | Pop!_OS 24.04, RTX 3060 12GB | Pop!_OS 24.04 NVIDIA |
| Edge | edge-node | Slurm compute / Ray worker / Ceph OSD | 192.168.1.20 | 10.66.0.20 | RK3576 ARM, 4–8 GB RAM | Custom Linux / EdgeOS |
| Router | router | MikroTik hEX S | 192.168.1.1 | — | hEX S (RB750Gr3) | RouterOS 7.x |

### GPU Partition

| Resource | gpu-node |
|----------|----------|
| GPU | NVIDIA RTX 3060 12 GB |
| CPU | ~12 threads |
| RAM | 32 GB |
| Local Disk | 1 TB NVMe |
| CUDA | 12.x |

### Edge Partition

| Resource | edge-node |
|----------|----------|
| CPU | Rockchip RK3576 (4×A72 + 4×A53) |
| RAM | 4–8 GB |
| Storage | eMMC / microSD |
| Role | Lightweight compute + Ray worker |

---

## 4. Day-by-Day Build Guide

| Day | Focus | What Gets Deployed |
|-----|-------|-------------------|
| **Day 1** | Network | AmneziaWG mesh + MikroTik VLAN + routing |
| **Day 2** | Base OS | Docker, Python, NTP, SSH, chrony, UFW firewall |
| **Day 3** | Compute | CUDA drivers, nvidia-container-runtime, ML Python env |
| **Day 4** | Slurm | slurmctld (RTX) + slurmd (ARM) + GPU partition |
| **Day 5** | Ray | Ray head (GPU) + Ray workers (ARM) + distributed tasks |
| **Day 6** | Storage + Monitoring | CephFS 2-node replication + Prometheus + Grafana |
| **Day 7** | Integration | Job routing, Slurm↔Ray bridge, full cluster verification |

---

## 5. Quick Start

### Prerequisites

- Clone the repo:
  ```bash
  git clone https://github.com/mahaasur13-sys/AsurDev.git
  cd AsurDev/home-cluster-iac
  ```

- Configure secrets in `ansible/group_vars/all.yml`:
  ```yaml
  ceph_admin_password: "your-secret"
  grafana_admin_password: "admin123"
  ```

- Copy MikroTik Terraform secrets (or set as GitHub Actions secrets):
  ```bash
  export TF_VAR_mikrotik_host="192.168.1.1"
  export TF_VAR_mikrotik_user="admin"
  export TF_VAR_mikrotik_password="your-password"
  ```

### Deploy (Day-by-Day)

```bash
cd scripts/
make day1    # Network foundation
make day2    # Base OS
make day3    # Compute / GPU drivers
make day4    # Slurm cluster
make day5    # Ray AI cluster
make day6    # Ceph + Monitoring
make day7    # Integration

# Or deploy everything at once:
make all
```

### Verify

```bash
make verify              # All cluster services
make verify-docker       # Docker status
make verify-gpu          # GPU info via nvidia-smi
```

---

## 6. Variables Reference (`group_vars/all.yml`)

| Variable | Default | Description |
|----------|---------|-------------|
| `mesh_vpn_subnet` | `10.66.0.0/16` | WireGuard mesh subnet |
| `wireguard_port` | `51820` | WireGuard UDP port |
| `ceph_cluster_network` | `192.168.1.0/24` | Ceph cluster network |
| `ceph_osd_pool_size` | `2` | Ceph OSD replication factor |
| `ray_head_ip` | `192.168.1.10` | Ray head node IP |
| `ray_version` | `2.9.0` | Ray version |
| `slurm_partitions` | gpu / compute | Slurm partition definitions |

---

## 7. Monitoring

| Service | URL | Default Credentials |
|---------|-----|-------------------|
| Prometheus | http://192.168.1.10:9090 | — |
| Grafana | http://192.168.1.10:3000 | admin / admin123 |
| Ray Dashboard | http://192.168.1.10:8265 | — |
| Node Exporter | http://192.168.1.10:9100 | — |

### Grafana Dashboards

| ID | Dashboard |
|----|-----------|
| 14061 | Slurm |
| 3662 | Ceph |
| 1860 | Node Exporter (System Monitoring) |

---

## 8. Slurm HA

Slurm supports native HA via multiple `SlurmctldHost` entries in `slurm.conf`. The failover script (`slurm_ha_failover.sh`) monitors the primary controller and promotes a backup using CephFS as a distributed lock.

```
SlurmctldHost=gpu-node,edge-node   # primary, backup
```

If the primary goes down, Slurm automatically connects to the next listed controller.

---

## 9. Terraform (MikroTik)

```bash
cd terraform/mikrotik/
terraform init
terraform plan   # validates the plan only, no changes applied
terraform apply  # applies VLAN, DHCP, NAT configs to MikroTik
```

Required secrets (set via environment or GitHub Actions):
- `TF_VAR_mikrotik_host`
- `TF_VAR_mikrotik_user`
- `TF_VAR_mikrotik_password`

---

## 10. CI/CD Checks

Every push to `home-cluster-iac/**` triggers `.github/workflows/infra-ci.yml`:

| Check | Tool | Purpose |
|-------|------|---------|
| Terraform validate + plan | `terraform validate` / `terraform plan` | Syntax and drift check for MikroTik configs |
| Ansible lint | `ansible-lint` | Role and playbook quality |
| YAML lint | `yamllint` | YAML file correctness |
| ShellCheck | `shellcheck` | Bash script safety |

---

*Architecture maintained in `mahaasur13-sys/AsurDev` → `home-cluster-iac/`*
