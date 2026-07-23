#!/usr/bin/env bash
# =============================================================================
# DAY 3 — Compute Nodes Setup (RTX 3060 + RK3576)
# =============================================================================
# Target: RTX 3060 PC, RK3576 edge node
# Result: GPU drivers, Docker, Python env, basic cluster tools
# Run on: each compute node directly (or via ansible from laptop)
# =============================================================================

set -euo pipefail

NODE="${1:-local}"   # pass "rtx", "rk3576", or "local"
CLUSTER_NAME="${CLUSTER_NAME:-home-cluster}"

NVIDIA_DRIVER="550"
CUDA_VERSION="12-4"

info() { echo "[INFO] $1"; }
ok()   { echo "[OK]   $1"; }
warn() { echo "[WARN] $1"; }

# =============================================================================
# Detect OS
# =============================================================================
detect_os() {
  if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    OS="$ID"
    VER="$VERSION_ID"
  else
    OS="unknown"
    VER="unknown"
  fi
  echo "Detected: $OS $VER"
}

# =============================================================================
# Install common packages
# =============================================================================
install_common() {
  info "Installing common packages..."
  apt-get update -qq
  apt-get install -y -qq \
    curl wget git vim tmux htop net-tools \
    apt-transport-https ca-certificates gnupg2 \
    python3 python3-pip python3-venv \
    build-essential  # for compiling python packages
  ok "Common packages installed"
}

# =============================================================================
# NVIDIA drivers (RTX node only)
# =============================================================================
install_nvidia() {
  if ! command -v nvidia-smi &>/dev/null; then
    info "Installing NVIDIA driver $NVIDIA_DRIVER..."
    apt-get install -y -qq \
      nvidia-driver-${NVIDIA_DRIVER} \
      nvidia-dkms-${NVIDIA_DRIVER} \
      nvidia-settings \
      nvidia-utils-${NVIDIA_DRIVER}
    ok "NVIDIA driver installed"
    info "Reboot required: sudo reboot"
  else
    nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1 | \
      xargs -I{} info "NVIDIA already installed: {}"
  fi

  # CUDA toolkit
  info "Installing CUDA toolkit..."
  apt-get install -y -qq nvidia-cuda-toolkit || \
    warn "CUDA toolkit installation skipped (or use Pop!_OS pre-installed)"
}

# =============================================================================
# Docker
# =============================================================================
install_docker() {
  if command -v docker &>/dev/null; then
    ok "Docker already installed"
    return
  fi

  info "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl --user enable docker 2>/dev/null || true
  usermod -aG docker "$USER" || true
  ok "Docker installed"
}

# =============================================================================
# NVIDIA container toolkit (for Docker + GPU)
# =============================================================================
install_nvidia_container_toolkit() {
  if command -v nvidia-ctk &>/dev/null; then
    ok "NVIDIA container toolkit already installed"
    return
  fi

  info "Installing NVIDIA container toolkit..."
  curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia.gpg
  echo "deb [signed-by=/usr/share/keyrings/nvidia.gpg] https://nvidia.github.io/libnvidia-container/stable/debian/\$(. /etc/os-release && echo \$ID\$VERSION_ID)/amd64 /" \
    | tee /etc/apt/sources.list.d/nvidia.list > /dev/null
  apt-get update -qq
  apt-get install -y -qq nvidia-container-toolkit
  nvidia-ctk runtime configure --runtime=docker
  ok "NVIDIA container toolkit installed"
}

# =============================================================================
# Python ML environment
# =============================================================================
install_python_ml() {
  info "Setting up Python ML environment..."
  
  PYTHON_DIR="$HOME/pyenv"
  [[ "$NODE" == "root" ]] && PYTHON_DIR="/opt/ml"
  
  mkdir -p "$PYTHON_DIR"
  
  # Minimal ML requirements
  pip3 install --quiet --user \
    numpy pandas scikit-learn torch torchvision \
    transformers accelerate \
    ray \
    jupyterlab 2>/dev/null || \
    warn "Some ML packages skipped (check pip)"
  
  ok "Python ML environment ready at $PYTHON_DIR"
}

# =============================================================================
# Cluster hosts file
# =============================================================================
update_hosts() {
  info "Updating /etc/hosts with cluster entries..."
  grep -q "rtx-node" /etc/hosts 2>/dev/null || \
    tee -a /etc/hosts > /dev/null << EOF

# Home cluster entries
10.20.20.10  rtx-node
10.20.20.20  rk3576-node
10.30.30.10  rtx-node  # Ceph OSD
10.40.40.10  rtx-node  # WireGuard
EOF
  ok "/etc/hosts updated"
}

# =============================================================================
# Munge (for Slurm)
# =============================================================================
install_munge() {
  info "Installing munge (Slurm authentication)..."
  apt-get install -y -qq munge
  create-munge-key 2>/dev/null || true
  chown -R munge:munge /etc/munge /var/lib/munge /var/log/munge 2>/dev/null || true
  ok "Munge installed"
}

# =============================================================================
# Main
# =============================================================================
main() {
  echo "=========================================="
  echo "[DAY3] Compute Nodes Setup"
  echo "=========================================="
  echo "Node target: $NODE"
  detect_os
  install_common
  install_munge

  if [[ "$NODE" == "rtx" ]] || [[ "$NODE" == "local" ]]; then
    echo ""
    echo "--- RTX GPU Node Setup ---"
    install_nvidia
    install_docker
    install_nvidia_container_toolkit
  fi

  if [[ "$NODE" == "rk3576" ]] || [[ "$NODE" == "local" ]]; then
    echo ""
    echo "--- RK3576 Edge Node Setup ---"
    # ARM-optimized packages (no GPU)
    apt-get install -y -qq libopenblas-dev liblapack-dev gfortran || true
  fi

  install_python_ml
  update_hosts

  echo ""
  echo "=========================================="
  echo "[DAY3] DONE — Compute Nodes Ready"
  echo "=========================================="
  echo ""
  echo "IMPORTANT: Reboot RTX node after NVIDIA driver install:"
  echo "  sudo reboot"
  echo ""
  echo "Next: bash scripts/day4-slurm.sh"
}

main
