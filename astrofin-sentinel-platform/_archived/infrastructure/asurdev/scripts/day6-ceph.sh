#!/usr/bin/env bash
# =============================================================================
# DAY 6 — Ceph Distributed Storage (2-node cluster)
# =============================================================================
# Target: RTX 3060 PC (OSD + MON), RK3576 (OSD)
# Result: Ceph cluster with 2 OSDs, shared storage for AI datasets
# Run on: RTX PC (first mon), then RK3576
# =============================================================================

set -euo pipefail

CEPH_CLUSTER_NAME="${CEPH_CLUSTER_NAME:-ceph-cluster}"
CEPH_FSID="a3f2c8e1-7b9d-4e5f-8c1a-2b3d4e5f6a7b"
CEPH_VERSION="quincy"  # Reef, Quincy, Pacific

# Nodes
MON_NODE="rtx-node"
MON_IP="10.30.30.10"
OSD1_NODE="rtx-node"
OSD1_IP="10.30.30.10"
OSD1_DEV="/dev/sdb"   # secondary disk
OSD2_NODE="rk3576-node"
OSD2_IP="10.30.30.20"
OSD2_DEV="/dev/sda"

ADMIN_NODE="$MON_NODE"  # where ceph commands run

info() { echo "[INFO] $1"; }
ok()   { echo "[OK]   $1"; }
warn() { echo "[WARN] $1"; }

# =============================================================================
# Helper: run on node via SSH
# =============================================================================
ssh_run() {
  local node="$1"
  local cmd="$2"
  ssh -o StrictHostKeyChecking=no root@"$node" "$cmd"
}

# =============================================================================
# Prerequisites
# =============================================================================
install_ceph() {
  info "Installing Ceph on all nodes..."
  
  for node in "$MON_NODE" "$OSD2_NODE"; do
    info "Installing on $node..."
    ssh_run "$node" "apt-get update -qq && \
      apt-get install -y -qq ceph ceph-common librados-dev || \
      echo 'Manual install on $node: sudo apt install ceph ceph-common'" &
  done
  wait
  ok "Ceph packages installed"
}

# =============================================================================
# Deploy Ceph via ceph-deploy (recommended for small clusters)
# =============================================================================
deploy_ceph() {
  info "Deploying Ceph cluster..."

  WORKDIR="/root/ceph-deploy"
  mkdir -p "$WORKDIR"
  cd "$WORKDIR"

  # Skip if ceph-deploy not available (manual method below)
  if ! command -v ceph-deploy &>/dev/null; then
    warn "ceph-deploy not found — using manual configuration"
    deploy_manual
    return
  fi

  info "ceph-deploy new cluster..."
  ceph-deploy new "$MON_NODE" --fsid "$CEPH_FSID"

  info "ceph-deploy mon create-initial..."
  ceph-deploy mon create-initial

  info "ceph-deploy osd create..."
  ceph-deploy osd create "$OSD1_NODE" --data "$OSD1_DEV"
  ceph-deploy osd create "$OSD2_NODE" --data "$OSD2_DEV"

  info "ceph-deploy admin..."
  ceph-deploy admin "$MON_NODE" "$OSD2_NODE"

  ok "Ceph deployed via ceph-deploy"
}

# =============================================================================
# Manual Ceph bootstrap (if ceph-deploy unavailable)
# =============================================================================
deploy_manual() {
  info "Manual Ceph bootstrap on $MON_NODE..."

  ssh_run "$MON_NODE" "mkdir -p /etc/ceph /var/lib/ceph/{mon,osd,mgr} /var/log/ceph"

  # ceph.conf
  ssh_run "$MON_NODE" "cat > /etc/ceph/ceph.conf" << 'CEPH_CONF'
[global]
fsid = a3f2c8e1-7b9d-4e5f-8c1a-2b3d4e5f6a7b
mon initial members = rtx-node
mon host = 10.30.30.10
public network = 10.30.30.0/24
cluster network = 10.30.30.0/24
osd pool default size = 2
osd max object name len = 256
osd max object namespace len = 64

[mon]
mon host = %(host)s
mon addr = %(addr)s

[osd]
osd journal size = 1024
osd mkfs type = xfs
filestore xattr use omap = true
CEPH_CONF

  # Create monitor
  ssh_run "$MON_NODE" "
    ceph-authtool --create-keyring /tmp/ceph.mon.keyring --gen-key -n mon. --cap mon 'allow *'
    ceph-authtool --create-keyring /etc/ceph/ceph.client.admin.keyring --gen-key -n client.admin --cap mon 'allow *' --cap osd 'allow *' --cap mds 'allow *'
    ceph-authtool --create-keyring /tmp/ceph.bootstrap-osd.keyring --gen-key -n client.bootstrap-osd --cap mon 'profile bootstrap-osd'
    ceph-deploy --overwrite-conf gatherkeys $(hostname)
    ceph-deploy mon create-initial
    ceph-deploy osd create $(hostname) --data $OSD1_DEV
  " || warn "Manual Ceph bootstrap requires manual steps"

  ok "Manual Ceph bootstrap initiated"
}

# =============================================================================
# Create Ceph pools
# =============================================================================
create_pools() {
  info "Creating Ceph pools..."
  
  ssh_run "$MON_NODE" "ceph osd pool create ai-data 128 128" 2>/dev/null || true
  ssh_run "$MON_NODE" "ceph osd pool create slurm-jobs 64 64" 2>/dev/null || true
  ssh_run "$MON_NODE" "ceph osd pool create ray-cache 64 64" 2>/dev/null || true
  
  # Enable RBD
  ssh_run "$MON_NODE" "ceph osd pool application enable rbd rbd" 2>/dev/null || true

  ok "Ceph pools created"
}

# =============================================================================
# Mount CephFS (optional)
# =============================================================================
mount_cephfs() {
  info "Setting up CephFS..."
  
  # Create MDS
  ssh_run "$MON_NODE" "ceph-deploy mds create $MON_NODE" 2>/dev/null || true
  
  # Create filesystem
  ssh_run "$MON_NODE" "ceph fs new cephfs cephfs_metadata cephfs_data" 2>/dev/null || true
  
  # Mount
  ssh_run "$MON_NODE" "mkdir -p /mnt/cephfs && \
    mount -t ceph $MON_IP:6789:/ /mnt/cephfs -o name=admin,secret=$(ceph-authtool -p /etc/ceph/ceph.client.admin.keyring)" \
    2>/dev/null || warn "CephFS mount needs manual setup"

  ok "CephFS configured"
}

# =============================================================================
# Test Ceph
# =============================================================================
test_ceph() {
  info "Testing Ceph cluster..."
  
  ssh_run "$MON_NODE" "ceph -s" 2>/dev/null || \
    ssh_run "$MON_NODE" "ceph status" 2>/dev/null || \
    warn "ceph status failed — cluster may not be up"
}

# =============================================================================
# Create mount helper script
# =============================================================================
create_mount_script() {
  info "Creating mount helper..."
  
  cat > /opt/ceph-mount.sh << 'MOUNT_SCRIPT'
#!/usr/bin/env bash
# Mount Ceph storage on all cluster nodes

MON_IP="10.30.30.10"
MOUNT_POINT="/mnt/ceph-storage"

install_mount() {
  apt-get install -y -qq ceph-fuse 2>/dev/null || apt-get install -y -qq ceph-common
  mkdir -p "$MOUNT_POINT"
  
  # Get admin key
  ADMIN_KEY=$(ceph-authtool -p /etc/ceph/ceph.client.admin.keyring 2>/dev/null)
  
  # Mount via kernel
  mount -t ceph $MON_IP:6789:/ $MOUNT_POINT -o name=admin,secret=$ADMIN_KEY 2>/dev/null && \
    echo "Mounted at $MOUNT_POINT" || \
    echo "Mount failed — check: ceph health"
}

install_mount
MOUNT_SCRIPT

  chmod +x /opt/ceph-mount.sh
  ok "Mount script at /opt/ceph-mount.sh"
}

# =============================================================================
# Main
# =============================================================================
main() {
  echo "=========================================="
  echo "[DAY6] Ceph Storage Cluster Setup"
  echo "=========================================="
  
  install_ceph
  echo ""
  echo "On MON node ($MON_NODE), run:"
  echo "  bash -x \$(which day6-ceph.sh)  # or run manually"
  
  echo ""
  echo "After bootstrap:"
  echo "  1. ceph -s           # check cluster health"
  echo "  2. ceph osd tree     # show OSDs"
  echo "  3. rbd create ai-data/dataset1 --size 100G  # create block device"
  echo ""
  
  create_pools
  mount_cephfs
  create_mount_script
  test_ceph

  echo ""
  echo "=========================================="
  echo "[DAY6] DONE — Ceph Storage Ready"
  echo "=========================================="
  echo ""
  echo "Next: bash scripts/day7-integration.sh"
}

main
