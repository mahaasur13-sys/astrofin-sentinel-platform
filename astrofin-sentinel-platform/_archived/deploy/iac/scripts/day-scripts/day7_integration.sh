#!/usr/bin/env bash
# Day 7: Full integration — job routing + storage + monitoring
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

echo "=== DAY 7: Integration Layer ==="

# 1. Deploy Ceph
echo "[1/6] Deploying Ceph storage..."
ansible-playbook -i "$INVENTORY" "$SCRIPT_DIR/../ansible/site.yml" --tags ceph

# 2. Deploy Ray
echo "[2/6] Deploying Ray cluster..."
ansible-playbook -i "$INVENTORY" "$SCRIPT_DIR/../ansible/site.yml" --tags ray

# 3. Mount shared storage
echo "[3/6] Mounting shared CephFS..."
ansible all -i "$INVENTORY" -m mount -a "path=/mnt/cephfs src=192.168.1.10:/ fstype=ceph state=mounted"

# 4. Job routing logic
echo "[4/6] Configuring job routing..."
ansible all -i "$INVENTORY" -m lineinfile \
  -a "path=/etc/slurm/slurm.conf line='JobAcctGatherType=JobAcctGatherPlugin'"

# 5. Slurm <-> Ray bridge
echo "[5/6] Setting up Slurm-Ray bridge..."
ansible all -i "$INVENTORY" -m copy -a "content='export RAY_ADDRESS={{ ray_head_ip }}:6379' dest=/etc/profile.d/ray.sh mode=0644"

# 6. Verification
echo "[6/6] Full cluster verification..."
ansible all -i "$INVENTORY" -m shell -a "ceph -s && ray status && sinfo --partitions"

echo "=== DAY 7 COMPLETE — AWS-like system operational ==="
