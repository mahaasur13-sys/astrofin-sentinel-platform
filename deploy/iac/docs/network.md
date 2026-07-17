# Network Design

## VLAN Architecture

```
MikroTik hEX S (L3 Core)
│
├── VLAN 10 — Management
│   ├── Subnet:  10.10.10.0/24
│   ├── Gateway: 10.10.10.1
│   ├── DHCP pool: 10.10.10.100–200
│   └── Used for: SSH, Ansible, monitoring
│
├── VLAN 20 — GPU / Slurm
│   ├── Subnet:  10.20.20.0/24
│   ├── Gateway: 10.20.20.1
│   ├── Static:  10.20.20.10 (rtx-node)
│   ├── Static:  10.20.20.20 (rk3576-edge)
│   └── Used for: Slurm, Ray, GPU jobs
│
├── VLAN 30 — Ceph Storage
│   ├── Subnet:  10.30.30.0/24
│   ├── Gateway: 10.30.30.1
│   └── Used for: Ceph OSD, CephFS, RBD
│
└── VLAN 40 — Kubernetes (future)
    ├── Subnet:  10.40.40.0/24
    └── Used for: K8s pods, services
```

## WireGuard Mesh Overlay

| Node | WG IP | Physical IP | Role |
|------|-------|-------------|------|
| rtx-node | 10.99.99.10 | 10.20.20.10 | GPU head |
| rk3576-edge | 10.99.99.20 | 10.20.20.20 | Edge worker |

## Firewall Rules

```
/ip firewall filter add chain=forward action=accept src-address=10.0.0.0/8 dst-address=10.0.0.0/8 comment="Allow LAN"
/ip firewall filter add chain=forward action=drop src-address=0.0.0.0/0 comment="Drop all other forward"
```

## DNS Records

| Hostname | IP | Type |
|----------|-----|------|
| rtx-node.home.local | 10.20.20.10 | A |
| rk3576-edge.home.local | 10.20.20.20 | A |
