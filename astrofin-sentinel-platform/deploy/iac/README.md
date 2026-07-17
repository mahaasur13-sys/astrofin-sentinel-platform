# home-cluster-iac
## Distributed mini-AWS cluster: Ceph + Slurm + Ray + Kubernetes + AmneziaWG

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CONTROL PLANE                             │
│  MikroTik hEX S (L3 router) — VLAN + Firewall + NAT          │
│  AmneziaWG Mesh (WireGuard) — encrypted overlay network     │
└────────────────┬────────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────────┐
│                 COMPUTE FABRIC                               │
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  RTX 3060    │         │   RK3576     │                  │
│  │  (GPU node)  │◄──────►│  (edge +     │                  │
│  │              │         │   lightweight│                  │
│  │  Slurm head  │         │   Ray worker │                  │
│  │  Ray head    │         │  AmneziaWG   │                  │
│  │  K8s worker  │         │  endpoint    │                  │
│  └──────┬───────┘         └──────┬───────┘                  │
│         │                         │                         │
│  ┌──────▼─────────────────────────▼───────┐                │
│  │         Ceph 2-node cluster            │                │
│  │  (distributed storage, 3x replication) │                │
│  └─────────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Components

| Layer | Component | Role |
|-------|-----------|------|
| **Network** | MikroTik hEX S | L3 routing, VLAN, DHCP, firewall |
| **Mesh VPN** | AmneziaWG (WireGuard) | Encrypted overlay, site-to-site |
| **GPU Compute** | RTX 3060 + Slurm | Batch GPU job scheduling |
| **AI Runtime** | Ray (head + workers) | Distributed AI tasks |
| **Storage** | Ceph FS (2-node) | Distributed block + FS storage |
| **Container** | Kubernetes (K8s) | Service orchestration |
| **IaC** | Terraform + Ansible | Infrastructure provisioning |

## 🗓️ Day 0–7 Deployment

| Day | Focus | Playbook | Output |
|-----|-------|----------|--------|
| **Day 0** | Bootstrap | `day0-bootstrap.yml` | Base OS, user, SSH |
| **Day 1** | Network | `day1-network.yml` | VLAN, DHCP, routing |
| **Day 2** | Mesh VPN | `day2-vpn.yml` | AmneziaWG mesh |
| **Day 3** | Compute | `day3-compute.yml` | GPU/Docker/Python env |
| **Day 4** | Slurm | `day4-slurm.yml` | GPU partition, batch scheduling |
| **Day 5** | Ray | `day5-ray.yml` | AI runtime layer |
| **Day 6** | Ceph | `day6-ceph.yml` | Distributed storage |
| **Day 7** | Integration | `day7-integration.yml` | Unified system |

## 🛠️ Quick Start

```bash
# Clone and enter
git clone https://github.com/mahasur13-sis/home-cluster-iac.git
cd home-cluster-iac

# Day 0 bootstrap
make bootstrap

# Or run specific day
ansible-playbook ansible/playbooks/day1-network.yml

# Terraform plan
make plan

# Validate Terraform
make validate
```

## 🔧 Terraform Modules

```
terraform/
├── main.tf                 # Root configuration
├── variables.tf            # Input variables
├── outputs.tf              # Output values
└── modules/
    ├── mikrotik/           # MikroTik router config
    ├── ceph/               # Ceph storage cluster
    ├── slurm/              # Slurm HA (3-controller)
    ├── k8s/                # Kubernetes cluster
    ├── wireguard/          # WireGuard mesh
    ├── compute/            # Compute nodes
    ├── network/            # Network/VLAN
    └── monitoring/         # Prometheus + Grafana
```

## 📋 Ansible Roles

```
ansible/
├── playbooks/
│   ├── day0-bootstrap.yml
│   ├── day1-network.yml
│   ├── day2-vpn.yml
│   ├── day3-compute.yml
│   ├── day4-slurm.yml
│   ├── day5-ray.yml
│   ├── day6-ceph.yml
│   └── day7-integration.yml
└── roles/
    ├── common/             # Base setup, users, SSH
    ├── mikrotik-config/    # Router configuration
    ├── slurm/              # Slurm installation
    ├── slurm_ha/           # Slurm HA setup
    ├── ceph/               # Ceph installation
    ├── ray/                # Ray cluster
    ├── kubernetes/         # K8s worker setup
    ├── edge-node/          # RK3576 edge node
    └── monitoring/         # Prometheus/Grafana
```

## 🔒 SDLC OS Phase 3 — Validation

This repo uses **SDLC OS Phase 3** for patch validation:

```python
from sdlc_os.phase3 import Kernel, GateEngine

# Validate before execution
kernel = Kernel(repo_path="/path/to/home-cluster-iac")
result = kernel.run(plan=repair_plan, snapshot=current_state)

# Hard contract: executor only runs if validation passes
```

### Gates
| Gate | Blocks |
|------|--------|
| `graph_gate` | Cycles, orphan edges |
| `policy_gate` | Layer violations, forbidden imports |
| `diff_gate` | >10 file patches, unclassified changes |
| `determinism_gate` | Non-deterministic patches |
| `safety_gate` | `risk > 0.5`, unproven dangerous actions |

## 📊 Monitoring

- **Prometheus**: `http://10.20.20.10:9090`
- **Grafana**: `http://10.20.20.10:3000`
- **Grafana dashboards**: Cluster, Ceph, Slurm, Ray metrics

## 🌐 Network Topology

```
Internet
    │
    ▼
┌─────────────┐
│ MikroTik    │  VLAN10 (mgmt):    10.10.10.0/24
│ hEX S       │  VLAN20 (compute): 10.20.20.0/24
│ (L3 router) │  VLAN30 (storage): 10.30.30.0/24
└──────┬──────┘  VLAN40 (edge):   10.40.40.0/24
       │
       │  WireGuard (AmneziaWG)
       ▼
┌──────────────┐   ┌──────────────┐
│   RTX 3060   │◄──│   RK3576     │
│ 10.20.20.10  │   │ 10.20.20.11  │
└──────────────┘   └──────────────┘
```

## 🔑 Key Ports

| Service | Port | Node |
|---------|------|------|
| SSH | 22 | all |
| WireGuard | 51820/udp | all |
| Slurmctld | 6817 | RTX 3060 |
| Slurmdbd | 6819 | RTX 3060 |
| Ray head | 6379 | RTX 3060 |
| Ceph MON | 6789 | ceph-* |
| Ceph OSD | 6800+ | ceph-* |
| K8s API | 6443 | RTX 3060 |
| Prometheus | 9090 | RTX 3060 |
| Grafana | 3000 | RTX 3060 |

## 📁 Repository Structure

```
home-cluster-iac/
├── Makefile                    # One-command targets
├── README.md                   # This file
├── RELEASE_NOTES.md            # Version history
├── SECURITY.md                 # Security policy
├── CI_CD_SETUP.md              # CI/CD pipeline
├── FINAL_ENHANCEMENTS.md       # Last enhancements
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── terraform.tfvars.example
│   └── modules/               # Terraform modules
├── ansible/
│   ├── playbooks/             # Day 0-7 playbooks
│   └── roles/                 # Ansible roles
├── k8s/
│   └── overlays/              # K8s manifests
├── scripts/                   # Utility scripts
└── docs/                      # Documentation
```

## ✅ Requirements

- Ansible >= 2.10
- Terraform >= 1.5
- kubectl >= 1.27
- Python >= 3.10

## 📜 License

MIT

## 👤 Author

**asurdev** — `github.com/mahasur13-sis`

---

*Last updated: 2026-04-09*
