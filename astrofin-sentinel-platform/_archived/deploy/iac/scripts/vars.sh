#!/usr/bin/env bash
# vars.sh — Global variables for home-cluster-iac
# Source this: source scripts/vars.sh

# ─── Cluster nodes ────────────────────────────────────────────────
export PRIMARY_HOST="rtx3060"
export PRIMARY_IP="192.168.10.11"

export EDGE_HOST="rk3576"
export EDGE_IP="192.168.10.12"

export VPS_HOST="vps-node"
export VPS_IP="10.0.0.2"

# All compute nodes (comma-separated)
export SLURM_NODES="192.168.10.11,192.168.10.12"

# ─── Network ──────────────────────────────────────────────────────
export MIKROTIK_HOST="192.168.1.1"
export MIKROTIK_USER="admin"
export MIKROTIK_PASS="${MIKROTIK_PASS:-}"

export MANAGEMENT_VLAN_ID="10"
export MANAGEMENT_SUBNET="192.168.10.0/24"

export STORAGE_VLAN_ID="20"
export STORAGE_SUBNET="192.168.20.0/24"

export CLUSTER_VLAN_ID="30"
export CLUSTER_SUBNET="192.168.30.0/24"

# ─── AmneziaWG (WireGuard mesh) ───────────────────────────────────
export WG_PORT="51820"
export WG_NETWORK="10.10.10.0/24"
export DOCKER_NETWORK="home-cluster-net"

# ─── Slurm ────────────────────────────────────────────────────────
export SLURM_CLUSTER_NAME="home-cluster"
export SLURM_CONTROL_HOST="rtx3060"

# ─── Ray ─────────────────────────────────────────────────────────
export RAY_HEAD_IP="192.168.10.11"
export RAY_PORT="6379"
export RAY_DASHBOARD_PORT="8265"

# ─── Ceph ─────────────────────────────────────────────────────────
export CEPH_PUBLIC_NET="192.168.20.0/24"
export CEPH_CLUSTER_NET="192.168.30.0/24"
export CEPH_ADMIN_USER="admin"
export CEPH_ADMIN_PASSWORD="${CEPH_ADMIN_PASSWORD:-admin}"

# ─── SSH ─────────────────────────────────────────────────────────
export SSH_USER="root"
export SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"

# ─── Logging ──────────────────────────────────────────────────────
export LOG_DIR="${SCRIPT_DIR:-$(dirname "$0")}/../logs"
