#!/usr/bin/env bash
# Day 6: Ceph storage — 2-node replicated storage cluster
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

echo "=== DAY 6: Ceph Distributed Storage ==="

CEPH_VERSION="${CEPH_VERSION:-quincy}"
CEPH_FS_NAME="${CEPH_FS_NAME:-cephfs}"
CEPH_POOL_REPLICAS="${CEPH_POOL_REPLICAS:-2}"

# 1. Install Ceph on all nodes
log "[1/6] Installing Ceph packages..."
ansible all -i "$INVENTORY" -m apt -a "
    name=ceph-base,ceph-common,ceph-osd,ceph-mgr,ceph-mon,python3-ceph-argparse,cephadm
    state=present
    update_cache=yes
"

# 2. Bootstrap Ceph monitor on gpu-node (primary)
log "[2/6] Bootstrapping Ceph monitor..."
ansible "gpu-node" -i "$INVENTORY" -m shell -a "
    cd /etc/ceph
    cephadm bootstrap --mon-ip=192.168.1.10 \
        --initial-dashboard-user=admin \
        --initial-dashboard-password='{{ ceph_admin_password }}' \
        --no-minimize-cluster-size \
        2>&1 | tail -10
"

# 3. Add edge-node as mon
log "[3/6] Adding edge-node as monitor..."
ansible "gpu-node" -i "$INVENTORY" -m shell -a "
    ceph orch host add edge-node 192.168.1.20
    sleep 5
    ceph -s
"

# 4. Deploy OSDs (use unused data disk)
log "[4/6] Deploying Ceph OSDs..."
ansible all -i "$INVENTORY" -m shell -a "
    cephadm shell -- ceph volume raw list 2>/dev/null | grep -q available || \
    cephadm shell -- ceph osd create 2>&1 || true
    ceph orch device ls --hostname=gpu-node
"
ansible "gpu-node" -i "$INVENTORY" -m shell -a "
    ceph orch osd create gpu-node:/dev/sdb 2>&1 || true
"

# 5. Create CephFS
log "[5/6] Creating CephFS..."
ansible "gpu-node" -i "$INVENTORY" -m shell -a "
    ceph osd pool create cephfs_data 128
    ceph osd pool create cephfs_metadata 64
    ceph fs new ${CEPH_FS_NAME} cephfs_metadata cephfs_data
    ceph fs ls
"

# 6. Mount on all nodes
log "[6/6] Mounting CephFS on all nodes..."
ansible all -i "$INVENTORY" -m shell -a "
    mkdir -p /mnt/cephfs
    mount -t ceph 192.168.1.10:6789:/ /mnt/cephfs \
        -o name=admin,secret=\$(ceph auth get-key client.admin),_netdev
    echo '192.168.1.10:6789:/ /mnt/cephfs ceph _netdev,name=admin,secretfile=/etc/ceph/cephfs_secret 0 0' >> /etc/fstab
"
ansible all -i "$INVENTORY" -m shell -a "df -h /mnt/cephfs"

log "=== DAY 6 COMPLETE ==="
ansible "gpu-node" -i "$INVENTORY" -m shell -a "ceph -s | head -10"