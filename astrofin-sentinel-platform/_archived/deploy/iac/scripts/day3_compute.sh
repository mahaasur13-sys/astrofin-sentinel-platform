#!/usr/bin/env bash
# Day 3: Compute node preparation — CUDA + Docker + Python env
# Run on all GPU-capable nodes (gpu-node with RTX 3060)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

echo "=== DAY 3: Compute Setup (GPU Node) ==="

TARGET_NODE="gpu-node"

# 1. NVIDIA driver verification
log "[1/5] Verifying NVIDIA driver..."
ansible "$TARGET_NODE" -i "$INVENTORY" -m shell -a "
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
"

# 2. CUDA toolkit installation (if not present)
log "[2/5] Installing CUDA 12.x..."
ansible "$TARGET_NODE" -i "$INVENTORY" -m apt -a "
    name=cuda-toolkit-12-4
    state=present
    update_cache=yes
" 2>/dev/null || log "CUDA toolkit already installed or not available via apt"

# 3. nvidia-container-toolkit for Docker GPU passthrough
log "[3/5] Configuring nvidia-container-runtime..."
ansible "$TARGET_NODE" -i "$INVENTORY" -m shell -a "
    distribution=\"\$(. /etc/os-release;echo \$ID\$VERSION_ID)\"
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/\$distribution/nvidia.list | sed 's#deb https:#deb [signed-by=/usr/share/keyrings/nvidia.gpg] https:#g' | tee /etc/apt/sources.list.d/nvidia.list
    apt-get update
    apt-get install -y nvidia-container-toolkit
    systemctl restart docker
"

# 4. ML Python packages
log "[4/5] Installing ML Python packages..."
ansible "$TARGET_NODE" -i "$INVENTORY" -m shell -a "
    pip3 install \
        jupyterlab notebook \
        scikit-learn scipy pandas matplotlib seaborn \
        transformers datasets accelerate \
        ray[default]==2.9.0 \
        dask distributed \
        kubernetes mlflow wandb \
        2>&1 | tail -5
"

# 5. Create working directories on CephFS
log "[5/5] Creating working directories..."
ansible all -i "$INVENTORY" -m file -a "
    path=/home/asur/workspace
    state=directory
    mode=0755
    owner=asur
"
ansible all -i "$INVENTORY" -m shell -a "
    mkdir -p /mnt/cephfs/{datasets,models,logs,checkpoints}
    chown -R asur:asur /mnt/cephfs/{datasets,models,logs,checkpoints}
"

log "=== DAY 3 COMPLETE ==="
log "GPU: $(ansible "$TARGET_NODE" -i "$INVENTORY" -m shell -a 'nvidia-smi --query-gpu=name --format=csv,noheader' | grep -v CHANGED | grep -v SUCCESS | tr -d '\n')"
log "CUDA: $(ansible "$TARGET_NODE" -i "$INVENTORY" -m shell -a 'nvcc --version' 2>/dev/null | grep -oP 'V[0-9]+\.[0-9]+' | tail -1)"