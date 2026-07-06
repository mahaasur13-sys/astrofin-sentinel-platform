#!/usr/bin/env bash
# generate_vars.sh — Generate vars.sh for home-cluster-iac
# Usage: ./generate_vars.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_FILE="${SCRIPT_DIR}/vars.sh"

# ─── Interactive prompts ──────────────────────────────────────────
echo "=== home-cluster-iac: Variable Generator ==="
echo ""

# Node names
read -rp "Primary node name [rtx-node1]: " PRIMARY_NODE
PRIMARY_NODE="${PRIMARY_NODE:-rtx-node1}"

read -rp "Edge node name [edge-node1]: " EDGE_NODE
EDGE_NODE="${EDGE_NODE:-edge-node1}"

# Hostnames
read -rp "Primary hostname [rtx3060]: " PRIMARY_HOST
PRIMARY_HOST="${PRIMARY_HOST:-rtx3060}"

read -rp "Edge hostname [rk3576]: " EDGE_HOST
EDGE_HOST="${EDGE_HOST:-rk3576}"

# IP addresses (VLAN 10 = mgmt)
read -rp "Primary node IP (VLAN 10) [192.168.10.11]: " PRIMARY_IP
PRIMARY_IP="${PRIMARY_IP:-192.168.10.11}"

read -rp "Edge node IP (VLAN 10) [192.168.10.12]: " EDGE_IP
EDGE_IP="${EDGE_IP:-192.168.10.12}"

read -rp "Ray head IP [192.168.10.11]: " RAY_HEAD_IP
RAY_HEAD_IP="${RAY_HEAD_IP:-192.168.10.11}"

read -rp "Slurm controller IP [192.168.10.11]: " SLURM_CTLD_IP
SLURM_CTLD_IP="${SLURM_CTLD_IP:-192.168.10.11}"

# Network
read -rp "Network CIDR [192.168.10.0/24]: " NETWORK_CIDR
NETWORK_CIDR="${NETWORK_CIDR:-192.168.10.0/24}"

read -rp "VLAN ID mgmt [10]: " VLAN_MGMT
VLAN_MGMT="${VLAN_MGMT:-10}"

# AmneziaWG
read -rp "AmneziaWG port [51820]: " WG_PORT
WG_PORT="${WG_PORT:-51820}"

read -rp "AmneziaWG mesh name [home-mesh]: " WG_MESH_NAME
WG_MESH_NAME="${WG_MESH_NAME:-home-mesh}"

# Ceph
read -rp "Ceph admin key (leave empty to generate): " CEPH_FSID
CEPH_FSID="${CEPH_FSID:-$(uuidgen)}"

# Ray
read -rp "Ray dashboard port [8265]: " RAY_PORT
RAY_PORT="${RAY_PORT:-8265}"

# ─── Generate vars.sh ─────────────────────────────────────────────
cat > "${OUTPUT_FILE}" << 'VARS_EOF'
# ============================================================
# home-cluster-iac — generated variables
# Run: source scripts/vars.sh before any deployment
# ============================================================

# ─── Node Identifiers ───────────────────────────────────────────
export PRIMARY_NODE="PRIMARY_NODE__PLACEHOLDER__"
export EDGE_NODE="EDGE_NODE__PLACEHOLDER__"
export PRIMARY_HOST="PRIMARY_HOST__PLACEHOLDER__"
export EDGE_HOST="EDGE_HOST__PLACEHOLDER__"

# ─── IP Addressing (VLAN 10 = mgmt) ─────────────────────────────
export PRIMARY_IP="PRIMARY_IP__PLACEHOLDER__"
export EDGE_IP="EDGE_IP__PLACEHOLDER__"
export NETWORK_CIDR="NETWORK_CIDR__PLACEHOLDER__"
export VLAN_MGMT=VLAN_MGMT__PLACEHOLDER__
export GATEWAY_IP="GATEWAY_IP__PLACEHOLDER__"

# ─── Slurm ──────────────────────────────────────────────────────
export SLURM_CLUSTER_NAME="home-cluster"
export SLURM_CTLD_IP="SLURM_CTLD_IP__PLACEHOLDER__"
export SLURM_PARTITIONS="gpu,cpu,edge"

# ─── Ray ─────────────────────────────────────────────────────────
export RAY_HEAD_IP="RAY_HEAD_IP__PLACEHOLDER__"
export RAY_PORT=RAY_PORT__PLACEHOLDER__
export RAY_DASHBOARD_PORT=8265

# ─── Ceph ────────────────────────────────────────────────────────
export CEPH_CLUSTER_NAME="ceph-cluster"
export CEPH_FSID="CEPH_FSID__PLACEHOLDER__"
export CEPH_MON_HOST="${PRIMARY_IP},${EDGE_IP}"
export CEPH_OSD_DATA="/var/lib/ceph/osd/ceph-osd"

# ─── AmneziaWG Mesh ──────────────────────────────────────────────
export WG_MESH_NAME="WG_MESH_NAME__PLACEHOLDER__"
export WG_PORT=WG_PORT__PLACEHOLDER__
export WG_ENDPOINT="WG_ENDPOINT__PLACEHOLDER__:${WG_PORT}"

# ─── Docker ──────────────────────────────────────────────────────
export DOCKER_NETWORK="home-cluster-net"
export DOCKER_SUBNET="172.30.0.0/16"

# ─── Monitoring ──────────────────────────────────────────────────
export GRAFANA_PORT="3000"
export PROMETHEUS_PORT="9090"
export LOKI_PORT="3100"

# ─── Paths ───────────────────────────────────────────────────────
export CLUSTER_ROOT="/opt/cluster"
export SCRIPTS_DIR="${CLUSTER_ROOT}/scripts"
VARS_EOF

# Replace placeholders using sed
sed -i "s/PRIMARY_NODE__PLACEHOLDER__/${PRIMARY_NODE}/g" "${OUTPUT_FILE}"
sed -i "s/EDGE_NODE__PLACEHOLDER__/${EDGE_NODE}/g" "${OUTPUT_FILE}"
sed -i "s/PRIMARY_HOST__PLACEHOLDER__/${PRIMARY_HOST}/g" "${OUTPUT_FILE}"
sed -i "s/EDGE_HOST__PLACEHOLDER__/${EDGE_HOST}/g" "${OUTPUT_FILE}"
sed -i "s/PRIMARY_IP__PLACEHOLDER__/${PRIMARY_IP}/g" "${OUTPUT_FILE}"
sed -i "s/EDGE_IP__PLACEHOLDER__/${EDGE_IP}/g" "${OUTPUT_FILE}"
sed -i "s/NETWORK_CIDR__PLACEHOLDER__/${NETWORK_CIDR}/g" "${OUTPUT_FILE}"
sed -i "s/VLAN_MGMT__PLACEHOLDER__/${VLAN_MGMT}/g" "${OUTPUT_FILE}"

# Gateway = first usable IP in CIDR
GW_IP=$(echo "${NETWORK_CIDR}" | awk -F'.' '{print $1"."$2"."$3".1"}')
sed -i "s|GATEWAY_IP__PLACEHOLDER__|${GW_IP}|g" "${OUTPUT_FILE}"

sed -i "s/SLURM_CTLD_IP__PLACEHOLDER__/${SLURM_CTLD_IP}/g" "${OUTPUT_FILE}"
sed -i "s/RAY_HEAD_IP__PLACEHOLDER__/${RAY_HEAD_IP}/g" "${OUTPUT_FILE}"
sed -i "s/RAY_PORT__PLACEHOLDER__/${RAY_PORT}/g" "${OUTPUT_FILE}"
sed -i "s/CEPH_FSID__PLACEHOLDER__/${CEPH_FSID}/g" "${OUTPUT_FILE}"
sed -i "s/WG_MESH_NAME__PLACEHOLDER__/${WG_MESH_NAME}/g" "${OUTPUT_FILE}"
sed -i "s/WG_PORT__PLACEHOLDER__/${WG_PORT}/g" "${OUTPUT_FILE}"
sed -i "s|WG_ENDPOINT__PLACEHOLDER__|${PRIMARY_IP}|g" "${OUTPUT_FILE}"

# Make executable
chmod +x "${OUTPUT_FILE}"

echo ""
echo "✓ Generated: ${OUTPUT_FILE}"
echo ""
echo "Next steps:"
echo "  1. Edit any values manually if needed"
echo "  2. Run: source scripts/vars.sh"
echo "  3. Run: make day1   # MikroTik VLAN"