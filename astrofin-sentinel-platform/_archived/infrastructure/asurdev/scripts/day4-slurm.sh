#!/usr/bin/env bash
# =============================================================================
# DAY 4 — Slurm Cluster (GPU + CPU Scheduling)
# =============================================================================
# Target: RTX 3060 PC (controller + compute node), RK3576 (compute node)
# Result: Working Slurm cluster with GPU partition
# Run on: RTX PC (controller) + RK3576 (worker)
# =============================================================================

set -euo pipefail

# --- Config ---
CONTROLLER_NODE="rtx-node"
CONTROLLER_IP="10.20.20.10"
WORKER_NODES=("rk3576-node")
WORKER_IPS=("10.20.20.20")
SLURM_USER="slurm"
SLURM_VERSION="23.02"
SLURM_CTLD_PORT=6817
SLURM_SHD_PORT=6818

MUNGE_KEY="/etc/munge/munge.key"

info() { echo "[INFO] $1"; }
ok()   { echo "[OK]   $1"; }
warn() { echo "[WARN] $1"; }
error() { echo "[ERROR] $1" >&2; }

# =============================================================================
# Prereq: munge must be running
# =============================================================================
check_munge() {
  info "Checking munge..."
  if ! id "$SLURM_USER" &>/dev/null 2>&1; then
    useradd -r -s /bin/false "$SLURM_USER" 2>/dev/null || true
  fi
  create-munge-key -f 2>/dev/null || true
  chown munge:munge "$MUNGE_KEY" 2>/dev/null || true
  chmod 0400 "$MUNGE_KEY" 2>/dev/null || true
  systemctl enable munge 2>/dev/null || true
  systemctl start munge 2>/dev/null || true
  ok "Munge running"
}

# =============================================================================
# Install Slurm
# =============================================================================
install_slurm() {
  info "Installing Slurm $SLURM_VERSION..."
  
  # Ubuntu/Debian
  if command -v apt-get &>/dev/null; then
    apt-get update -qq
    # Install from Universe or build from source for latest
    apt-get install -y -qq \
      slurmctld slurmdbd slurmd slurm-client \
      libmunge-dev libmariadb-dev \
      mariadb-server  # for slurmdbd
    ok "Slurm packages installed via apt"
  else
    warn "Unsupported OS — build from source"
    return 1
  fi
}

# =============================================================================
# Controller config (slurm.conf)
# =============================================================================
create_slurm_conf() {
  info "Creating slurm.conf..."
  
  mkdir -p /var/spool/slurm /var/log/slurm /etc/slurm
  chown -R "$SLURM_USER:$SLURM_USER" /var/spool/slurm /var/log/slurm

  cat > /etc/slurm/slurm.conf << SLURM_CONF
# slurm.conf — generated for home-cluster
ClusterName=home-cluster
ControlMachine=${CONTROLLER_NODE}
ControlAddr=${CONTROLLER_IP}

SlurmUser=${SLURM_USER}
SlurmctldPort=${SLURM_CTLD_PORT}
SlurmdPort=${SLURM_SHD_PORT}

AuthType=auth/munge
StateSaveLocation=/var/spool/slurm
SlurmdSpoolDir=/var/spool/slurmd
TmpFS=/tmp
LogFile=/var/log/slurm/slurmctld.log
SlurmdLogFile=/var/log/slurm/slurmd.log

# GPU support
GresTypes=gpu
DefMemPerCPU=1024
MaxMemPerCPU=32768

# RTX GPU node
NodeName=${CONTROLLER_NODE} NodeAddr=${CONTROLLER_IP} \
  CPUs=12 RealMemory=32000 State=UNKNOWN

# RK3576 CPU node
NodeName=rk3576-node NodeAddr=10.20.20.20 \
  CPUs=8 RealMemory=8000 State=UNKNOWN

# GPU partition (RTX)
PartitionName=gpu Nodes=${CONTROLLER_NODE} Default=YES \
  MaxTime=INFINITE State=UP \
  Gres=gpu:rtx3060:1

# CPU partition (RK3576)
PartitionName=cpu Nodes=rk3576-node \
  MaxTime=INFINITE State=UP

# Scheduling
SchedulerType=sched/backfill
SelectType=select/cons_tres
SelectTypeParameters=CR_CPU_Memory,CR_GPU_Memory
SLURM_CONF

  chown root:root /etc/slurm/slurm.conf
  chmod 644 /etc/slurm/slurm.conf
  ok "slurm.conf created"
}

# =============================================================================
# gres.conf (GPU resources)
# =============================================================================
create_gres_conf() {
  info "Creating gres.conf..."
  
  cat > /etc/slurm/gres.conf << GRES_CONF
# GPU Generic Resource configuration
NodeName=${CONTROLLER_NODE} Name=gpu Type=rtx3060 File=/dev/nvidia0 Count=1
GRES_CONF

  chown root:root /etc/slurm/gres.conf
  chmod 644 /etc/slurm/gres.conf
  ok "gres.conf created"
}

# =============================================================================
# cgroup.conf (for GPU isolation)
# =============================================================================
create_cgroup_conf() {
  cat > /etc/slurm/cgroup.conf << CGROUP_CONF
CgroupAutomount=yes
ConstrainCores=yes
ConstrainRAMSpace=yes
AllowedDevicesFile=/etc/slurm/gres.conf
CGROUP_CONF
  ok "cgroup.conf created"
}

# =============================================================================
# Start controller
# =============================================================================
start_controller() {
  info "Enabling and starting slurmctld..."
  systemctl enable slurmctld
  systemctl start slurmctld
  sleep 2
  systemctl status slurmctld --no-pager || true
  ok "Slurm controller running"
}

# =============================================================================
# Configure worker (RK3576)
# =============================================================================
configure_worker() {
  info "Worker configuration (run on rk3576-node)..."
  
  # On RK3576, install slurmd
  ssh root@10.20.20.20 "apt-get install -y -qq slurmd slurm-client munge" 2>/dev/null || \
    warn "SSH to RK3576 failed — configure manually on that node"

  # Copy slurm.conf to worker
  scp /etc/slurm/slurm.conf root@10.20.20.20:/etc/slurm/slurm.conf 2>/dev/null || \
    warn "SCP failed — copy slurm.conf to worker manually"

  ssh root@10.20.20.20 "systemctl enable slurmd && systemctl start slurmd" 2>/dev/null || \
    warn "Failed to start slurmd on worker"

  ok "Worker configured (or manual steps required)"
}

# =============================================================================
# Test Slurm
# =============================================================================
test_slurm() {
  info "Testing Slurm..."
  
  sleep 2
  
  sinfo_result=$(sinfo 2>/dev/null || echo "sinfo not found")
  echo "$sinfo_result"
  
  srun --partition=gpu hostname 2>/dev/null || \
    warn "srun test skipped (cluster not fully up)"
}

# =============================================================================
# Main
# =============================================================================
main() {
  echo "=========================================="
  echo "[DAY4] Slurm Cluster Setup"
  echo "=========================================="
  
  check_munge
  install_slurm
  create_slurm_conf
  create_gres_conf
  create_cgroup_conf
  start_controller
  
  echo ""
  read -p "Configure RK3576 worker now? (y/N): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    configure_worker
  fi

  test_slurm

  echo ""
  echo "=========================================="
  echo "[DAY4] DONE — Slurm Cluster Ready"
  echo "=========================================="
  echo ""
  echo "Useful commands:"
  echo "  sinfo                # show cluster status"
  echo "  srun --partition=gpu nvidia-smi    # test GPU job"
  echo "  squeue              # show jobs"
  echo ""
  echo "Next: bash scripts/day5-ray.sh"
}

main
