#!/usr/bin/env bash
# =============================================================================
# DAY 1 — Network Foundation: MikroTik VLAN Setup
# =============================================================================
# Target: MikroTik hEX S (RB760iGS) — RouterOS 7
# Result: 4 VLANs (mgmt/compute/storage/vpn) + basic firewall
# Run on: laptop (management station)
# =============================================================================

set -euo pipefail

# --- Config ---
MIKROTIK_IP="10.10.10.1"
MIKROTIK_USER="admin"
MIKROTIK_PASS="${MIKROTIK_PASS:-}"   # set env var or edit
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_rsa}"

# VLAN IDs
VLAN_MGMT=10
VLAN_COMPUTE=20
VLAN_STORAGE=30
VLAN_VPN=40

# Subnets
NET_MGMT="10.10.10.0/24"
NET_COMPUTE="10.20.20.0/24"
NET_STORAGE="10.30.30.0/24"
NET_VPN="10.40.40.0/24"

# =============================================================================
# Helper: RouterOS API call
# =============================================================================
ros_api() {
  local path="$1"
  local method="${2:-GET}"
  local body="${3:-}"
  curl -s -k -X "$method" \
    "https://$MIKROTIK_IP/rest$path" \
    -u "$MIKROTIK_USER:$MIKROTIK_PASS" \
    -H "Content-Type: application/json" \
    ${body:+ -d "$body"}
}

# =============================================================================
# Check connectivity
# =============================================================================
echo "[DAY1] Checking MikroTik connectivity..."
if ! ping -c 1 -W 2 "$MIKROTIK_IP" &>/dev/null; then
  echo "[ERROR] Cannot reach MikroTik at $MIKROTIK_IP"
  echo "[INFO]  Make sure laptop is on same network or set correct IP"
  exit 1
fi
echo "[OK] MikroTik reachable"

# =============================================================================
# Check RouterOS version
# =============================================================================
echo "[DAY1] Checking RouterOS version..."
ROS_VER=$(ros_api "/system/resource" | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
echo "[INFO] RouterOS version: $ROS_VER"

# =============================================================================
# Create bridge (if not exists)
# =============================================================================
echo "[DAY1] Creating bridge br-lan..."
ros_api "/interface/bridge" "POST" '{"name":"br-lan","vlan-filtering":"yes"}' \
  2>/dev/null || echo "[INFO] Bridge may already exist"

# Add ports to bridge (ether2-ether5 as trunk)
for port in ether2 ether3 ether4 ether5; do
  ros_api "/interface/bridge/port" "POST" "{\"bridge\":\"br-lan\",\"interface\":\"$port\"}" \
    2>/dev/null && echo "[OK] Added $port to br-lan" || echo "[SKIP] $port already in bridge"
done

# =============================================================================
# Create VLANs
# =============================================================================
create_vlan() {
  local id=$1
  local name=$2
  local subnet=$3
  echo "[DAY1] Creating VLAN $id ($name)..."
  ros_api "/interface/vlan" "POST" "{\"name\":\"vlan${id}-${name}\",\"vlan-id\":${id},\"interface\":\"br-lan\"}" \
    2>/dev/null || echo "[SKIP] vlan${id}-${name} may exist"

  # Assign IP (first usable .1)
  local ip=$(echo "$subnet" | awk -F. '{print $1"."$2"."$3".1"}')
  ros_api "/ip/address" "POST" "{\"address\":\"${ip}/24\",\"interface\":\"vlan${id}-${name}\"}" \
    2>/dev/null && echo "[OK] IP $ip on vlan${id}-${name}" || echo "[SKIP] IP already assigned"
}

create_vlan $VLAN_MGMT    "mgmt"    "$NET_MGMT"
create_vlan $VLAN_COMPUTE "compute" "$NET_COMPUTE"
create_vlan $VLAN_STORAGE "storage" "$NET_STORAGE"
create_vlan $VLAN_VPN     "vpn"     "$NET_VPN"

# =============================================================================
# Basic firewall (allow established/related, drop all else on input)
# =============================================================================
echo "[DAY1] Setting up firewall..."
ros_api "/ip/firewall/filter" "POST" '{
  "chain":"input",
  "action":"accept",
  "connection-state":["established","related"]
}' 2>/dev/null || true

ros_api "/ip/firewall/filter" "POST" '{
  "chain":"input",
  "action":"drop",
  "src-address":"!10.10.10.0/24"
}' 2>/dev/null || true

# =============================================================================
# Enable SSH (if not enabled)
# =============================================================================
echo "[DAY1] Enabling SSH..."
ros_api "/ip/service" "PUT" '{"name":"ssh","port":22,"disabled":"false"}' \
  2>/dev/null || true

# =============================================================================
# DHCP server on mgmt VLAN (optional — gives IPs to new devices)
# =============================================================================
read -p "[DAY1] Setup DHCP server on mgmt VLAN? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "[DAY1] Setting up DHCP server on VLAN $VLAN_MGMT..."
  POOL_START="10.10.10.50"
  POOL_END="10.10.10.200"
  ros_api "/ip/pool" "POST" "{\"name\":\"mgmt-pool\",\"ranges\":\"${POOL_START}-${POOL_END}\"}" 2>/dev/null || true
  ros_api "/ip/dhcp-server" "POST" "{
    \"name\":\"dhcp-mgmt\",
    \"interface\":\"vlan${VLAN_MGMT}-mgmt\",
    \"address-pool\":\"mgmt-pool\",
    \"disabled\":\"false\"
  }" 2>/dev/null || echo "[INFO] DHCP server setup skipped or already exists"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo "=========================================="
echo "[DAY1] DONE — Network Foundation Ready"
echo "=========================================="
echo "VLAN $VLAN_MGMT (mgmt)    : $NET_MGMT  → MikroTik: 10.10.10.1"
echo "VLAN $VLAN_COMPUTE (compute): $NET_COMPUTE → MikroTik: 10.20.20.1"
echo "VLAN $VLAN_STORAGE (storage): $NET_STORAGE → MikroTik: 10.30.30.1"
echo "VLAN $VLAN_VPN (vpn)      : $NET_VPN  → MikroTik: 10.40.40.1"
echo ""
echo "Next: bash scripts/day2-vpn.sh"
