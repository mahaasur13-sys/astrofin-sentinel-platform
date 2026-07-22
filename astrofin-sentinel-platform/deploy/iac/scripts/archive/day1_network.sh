#!/usr/bin/env bash
# Day 1: Network foundation — AmneziaWG mesh + MikroTik VLAN
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

echo "=== DAY 1: Network Foundation ==="

# 1. Verify Ansible connectivity
echo "[1/5] Verifying Ansible connectivity..."
ansible all -i "$INVENTORY" -m ping

# 2. Deploy WireGuard mesh
echo "[2/5] Deploying WireGuard mesh..."
ansible-playbook -i "$INVENTORY" "$SCRIPT_DIR/../ansible/site.yml" --tags wireguard

# 3. Configure MikroTik (if API access is set up)
echo "[3/5] Configuring MikroTik router..."
ansible-playbook -i "$INVENTORY" "$SCRIPT_DIR/../ansible/site.yml" --tags mikrotik

# 4. Verify mesh connectivity
echo "[4/5] Verifying mesh tunnel..."
ansible all -i "$INVENTORY" -m shell -a "wg show wg0 | head -5"

# 5. Configure routing
echo "[5/5] Configuring routing tables..."
ansible all -i "$INVENTORY" -m sysctl -a "name=net.ipv4.ip_forward value=1"

echo "=== DAY 1 COMPLETE ==="
echo "Mesh VPN: $(grep -A1 'Address' $SCRIPT_DIR/../ansible/roles/wireguard-mesh/templates/wg0.conf.j2 2>/dev/null || echo '10.66.0.0/16')"
