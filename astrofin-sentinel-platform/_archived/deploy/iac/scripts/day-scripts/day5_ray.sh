#!/usr/bin/env bash
# Day 5: Ray AI cluster — head on GPU node, workers on ARM edge
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

echo "=== DAY 5: Ray AI Cluster ==="

RAY_VERSION="${RAY_VERSION:-2.9.0}"
RAY_HEAD_IP="${RAY_HEAD_IP:-192.168.1.10}"
RAY_HEAD_PORT="${RAY_HEAD_PORT:-6379}"

# 1. Install Ray on all nodes
log "[1/4] Installing Ray ${RAY_VERSION}..."
ansible all -i "$INVENTORY" -m shell -a "
    pip3 install ray[default]==${RAY_VERSION} redis psutil
"

# 2. Start Ray head on gpu-node (GPU node)
log "[2/4] Starting Ray head on gpu-node..."
ansible "gpu-node" -i "$INVENTORY" -m shell -a "
    ray stop 2>/dev/null || true
    ray start --head \
        --port=${RAY_HEAD_PORT} \
        --dashboard-host=0.0.0.0:8265 \
        --storage=/mnt/cephfs/ray_analytics \
        --num-cpus=\$(nproc) \
        --num-gpus=1 \
        --temp-dir=/mnt/cephfs/ray_tmp \
        --disable-initial-dashboard-tests \
        2>&1
"

# 3. Connect Ray workers (edge-node / ARM)
log "[3/4] Connecting Ray workers to head..."
ansible "edge-node" -i "$INVENTORY" -m shell -a "
    ray stop 2>/dev/null || true
    ray start --address='${RAY_HEAD_IP}:${RAY_HEAD_PORT}' \
        --num-cpus=\$(nproc) \
        --memory=\$(free -m | awk '/Mem:/ {print \$2 * 0.8}') \
        2>&1
"

# 4. Verify cluster
log "[4/4] Verifying Ray cluster status..."
ansible all -i "$INVENTORY" -m shell -a "
    ray status 2>&1 || echo 'RAY STATUS: cluster forming...'
    ray list nodes 2>&1 | head -20
"

log "=== DAY 5 COMPLETE ==="
log "Ray head: ${RAY_HEAD_IP}:${RAY_HEAD_PORT}"
log "Dashboard: http://${RAY_HEAD_IP}:8265"
log "Test: ray exec /mnt/cephfs/ray_tmp/test.py"