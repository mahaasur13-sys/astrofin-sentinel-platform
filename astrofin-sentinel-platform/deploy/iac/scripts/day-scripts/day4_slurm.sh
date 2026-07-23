#!/usr/bin/env bash
# Day 4: Slurm GPU cluster — slurmctld + slurmd + GPU partition
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

echo "=== DAY 4: Slurm GPU Cluster ==="

# 1. Install Slurm on all nodes
echo "[1/4] Installing Slurm packages..."
ansible-playbook -i "$INVENTORY" "$SCRIPT_DIR/../ansible/site.yml" --tags slurm

# 2. Configure cluster
echo "[2/4] Configuring Slurm cluster..."
ansible all -i "$INVENTORY" -m lineinfile \
  -a "path=/etc/slurm/slurm.conf line='ClusterName=home-gpu-cluster'"

# 3. Start services
echo "[3/4] Starting Slurm services..."
ansible all -i "$INVENTORY" -m systemd -a "name=slurmctld state=started enabled=yes" \
  --limit "$(grep slurm_controller "$INVENTORY" | awk '{print $1}' | head -1)"
ansible all -i "$INVENTORY" -m systemd -a "name=slurmd state=started enabled=yes" \
  --limit "$(grep slurm_compute "$INVENTORY" | awk '{print $1}' | head -1)"

# 4. Verify
echo "[4/4] Verifying GPU scheduling..."
ansible all -i "$INVENTORY" -m shell -a "sinfo -- partitions"

echo "=== DAY 4 COMPLETE ==="
