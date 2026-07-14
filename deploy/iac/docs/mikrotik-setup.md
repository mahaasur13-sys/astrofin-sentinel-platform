# MikroTik hEX S — Initial Setup Guide

## Prerequisites
- MikroTik hEX S (RB760iGS) or equivalent RouterOS 7 device
- Ethernet cable: ether1=WAN, ether2-5=Lan trunk
- Access via WebFig, WinBox, or SSH

## Default Credentials
| Parameter | Default |
|-----------|---------|
| IP | 192.168.88.1 |
| Username | admin |
| Password | *(empty)* |

---

## Step 1 — Change Default Password
**Via CLI:**


---

## Step 2 — Configure WAN (ether1)


---

## Step 3 — Enable REST API (Required for Day 1 Scripts)

Day 1 script uses HTTPS on port 8729 by default.

---

## Step 4 — Verify API


---

## Step 5 — Save Configuration


---

## VLANs Created by Day 1 Script
| VLAN ID | Name | Subnet | MikroTik IP | Purpose |
|---------|------|--------|------------|---------|
| 10 | mgmt | 10.10.10.0/24 | 10.10.10.1 | Management |
| 20 | compute | 10.20.20.0/24 | 10.20.20.1 | GPU/CPU compute |
| 30 | storage | 10.30.30.0/24 | 10.30.30.1 | Ceph storage |
| 40 | vpn | 10.40.40.0/24 | 10.40.40.1 | WireGuard mesh |

---

## Reset to Factory Defaults

Then start from Step 1.
