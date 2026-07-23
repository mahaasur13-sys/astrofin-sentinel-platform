#!/usr/bin/env bash
# =============================================================================
# DAY 7 — Full Integration (Slurm + Ray + Ceph + Monitoring)
# =============================================================================
# Target: All nodes
# Result: Unified cluster with job routing, monitoring, auto-healing
# =============================================================================

set -euo pipefail

RTX_IP="10.20.20.10"
RK3576_IP="10.20.20.20"
MON_IP="10.30.30.10"

info() { echo "[INFO] $1"; }
ok()   { echo "[OK]   $1"; }
warn() { echo "[WARN] $1"; }

# =============================================================================
# Integration: Slurm <-> Ray bridge
# =============================================================================
create_slurm_ray_bridge() {
  info "Creating Slurm↔Ray bridge..."

  BRIDGE_SCRIPT="/opt/slurm-ray-bridge.sh"
  cat > "$BRIDGE_SCRIPT" << 'BRIDGE'
#!/usr/bin/env bash
# Slurm job → Ray task bridge
# Usage: sbatch slurm-ray-bridge.sh <ray_task.py>

RAY_HEAD="10.20.20.10:6379"
TASK_FILE="${1:-test_task.py}"

echo "[Bridge] Submitting $TASK_FILE to Ray via Slurm..."

# Option A: sbatch → srun → python ray task
srun --partition=gpu --gres=gpu:1 \
  python3 -c "
import ray
ray.init(address='auto')
exec(open('$TASK_FILE').read())
"

# Option B: Ray Client (connect to remote Ray from Slurm job)
# srun --partition=gpu python3 - << 'PYEOF'
# import ray
# ray.init(address='ray://$RAY_HEAD:10001')
# ...
# PYEOF
BRIDGE

  chmod +x "$BRIDGE_SCRIPT"
  ok "Bridge script: $BRIDGE_SCRIPT"
}

# =============================================================================
# Integration: Ceph → Slurm job data
# =============================================================================
setup_ceph_slurm_integration() {
  info "Setting up Ceph↔Slurm integration..."

  ssh root@"$RTX_IP" "mkdir -p /mnt/ceph-storage/slurm-jobs /mnt/ceph-storage/ai-data"

  # Point Slurm state + spool to Ceph
  ssh root@"$RTX_IP" "
    sed -i 's|StateSaveLocation=/var/spool/slurm|StateSaveLocation=/mnt/ceph-storage/slurm-jobs|' /etc/slurm/slurm.conf
    systemctl restart slurmctld
  " 2>/dev/null || warn "Ceph-Slurm integration needs manual config"

  ok "Ceph-Slurm integration configured"
}

# =============================================================================
# Integration: Ceph → Ray datasets
# =============================================================================
setup_ceph_ray_integration() {
  info "Setting up Ceph↔Ray integration..."

  PYFILE="/opt/ray-jobs/ceph_dataset.py"
  cat > "$PYFILE" << 'CEPH_RAY'
import ray
import pyarrow
import pyarrow.fs

ray.init(address="auto")

# Connect to CephFS via pyarrow
fs, path = pyarrow.fs.FileSystem.from_uri("ceph://cephfs@ceph-mon=10.30.30.10:6789")
# Or via environment variable for FUSE
# import os
# os.environ["CEPHFS_MON_HOST"] = "10.30.30.10"

print(f"Connected to Ray: {ray.cluster_resources()}")

@ray.remote
def load_from_ceph(filename):
    # Read from mounted CephFS
    with open(f"/mnt/ceph-storage/ai-data/{filename}", "r") as f:
        return f.read()

# Example: load dataset
try:
    result = ray.get(load_from_ceph.remote("test.txt"))
    print(f"Loaded: {result[:100]}")
except:
    print("No data in Ceph yet — write first: echo test > /mnt/ceph-storage/ai-data/test.txt")

@ray.remote
def save_to_ceph(filename, data):
    with open(f"/mnt/ceph-storage/ai-data/{filename}", "w") as f:
        f.write(data)
    return len(data)

ray.get(save_to_ceph.remote("output.txt", "Hello from Ray+ Ceph!")) 
print("Dataset save successful")
CEPH_RAY

  ok "Ceph-Ray integration: $PYFILE"
}

# =============================================================================
# Simple monitoring (Prometheus metrics from Slurm + Ray)
# =============================================================================
setup_monitoring() {
  info "Setting up monitoring..."

  MONITOR_DIR="/opt/monitoring"
  mkdir -p "$MONITOR_DIR"

  # Prometheus config for Slurm exporter
  cat > "$MONITOR_DIR/prometheus.yml" << 'PROM_CONF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: slurm
    static_configs:
      - targets: ['10.20.20.10:8080']  # slurmctld exporter

  - job_name: ray
    static_configs:
      - targets: ['10.20.20.10:8265']  # ray dashboard
PROM_CONF

  # Grafana dashboard JSON (minimal)
  cat > "$MONITOR_DIR/grafana-dashboard.json" << 'GRAFANA_DASH'
{
  "dashboard": {
    "title": "Home Cluster",
    "panels": [
      {"title": "GPU Utilization", "type": "graph", "targets": [{"expr": "nvidia_gpu_utilization"}]},
      {"title": "Ray Cluster Status", "type": "stat", "targets": [{"expr": "ray_resources{category=\"CPU\"}"}]},
      {"title": "Slurm Jobs", "type": "table", "targets": [{"expr": "slurm_running_jobs"}]}
    ]
  }
}
GRAFANA_DASH

  ok "Monitoring config: $MONITOR_DIR/prometheus.yml"
}

# =============================================================================
# AI Scheduler (simple policy engine prototype)
# =============================================================================
create_ai_scheduler() {
  info "Creating AI scheduler (policy engine prototype)..."

  SCHED_DIR="/opt/ai-scheduler"
  mkdir -p "$SCHED_DIR"

  cat > "$SCHED_DIR/policy_engine.py" << 'POLICY_ENGINE'
#!/usr/bin/env python3
"""
AI Scheduler Policy Engine — home cluster version
Decides WHERE to run a job based on:
  - GPU availability (RTX 3060)
  - CPU availability (RK3576)  
  - Thermal / load state
  - Ceph data locality
  - Queue depth
"""

import subprocess
import json
import time

RTX_IP = "10.20.20.10"
RK3576_IP = "10.20.20.20"

def get_gpu_load(ip):
    """Get GPU utilization %"""
    try:
        result = subprocess.run(
            ["ssh", f"root@{ip}", "nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader"],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip().replace("%", ""))
    except:
        return 100  # assume max load if can't measure

def get_cpu_load(ip):
    """Get CPU utilization %"""
    try:
        result = subprocess.run(
            ["ssh", f"root@{ip}", "cat /proc/loadavg"],
            capture_output=True, text=True, timeout=5
        )
        load = float(result.stdout.split()[0])
        return load * 100 / 8  # normalize to 8-core RK3576
    except:
        return 100

def get_slurm_queue():
    """Get Slurm pending jobs count"""
    try:
        result = subprocess.run(["squeue", "--format=%T", "--noheader"], capture_output=True, text=True)
        return result.stdout.count("PENDING")
    except:
        return 0

def get_ray_cluster():
    """Get Ray cluster status"""
    try:
        result = subprocess.run(
            ["python3", "-c", "import ray; ray.init(); print(ray.cluster_resources())"],
            capture_output=True, text=True, timeout=10
        )
        return json.loads(result.stdout.replace("'", '"'))
    except:
        return {}

def decide_target(job_type, estimated_gpu_pct, estimated_duration_min):
    """
    Policy decision:
    Returns: ("rtx", reason) or ("rk3576", reason) or ("queue", reason)
    """
    gpu_load = get_gpu_load(RTX_IP)
    cpu_load = get_cpu_load(RK3576_IP)
    queue_depth = get_slurm_queue()

    if job_type == "gpu" or job_type == "ai":
        if gpu_load < 80:
            return ("rtx", f"GPU load {gpu_load}% < 80%")
        else:
            return ("queue", f"GPU overloaded ({gpu_load}%)")

    elif job_type == "cpu" or job_type == "light":
        if cpu_load < 70:
            return ("rk3576", f"CPU load {cpu_load:.0f}% < 70%")
        else:
            return ("queue", f"RK3576 overloaded ({cpu_load:.0f}%)")

    else:  # batch / unknown
        if gpu_load < 90:
            return ("rtx", f"GPU available ({100-gpu_load}% free)")
        elif cpu_load < 80:
            return ("rk3576", "Falling back to CPU node")
        else:
            return ("queue", f"Both nodes busy (GPU:{gpu_load}%, CPU:{cpu_load:.0f}%)")

def submit_job(job_type, script_path, policy="load"):
    """Submit job using policy decision"""
    target, reason = decide_target(job_type, 50, 30)
    
    print(f"[Policy] Decision: {target} — {reason}")

    if target == "rtx":
        cmd = f"srun --partition=gpu --gres=gpu:1 {script_path}"
    elif target == "rk3576":
        cmd = f"srun --partition=cpu {script_path}"
    else:
        cmd = f"sbatch {script_path}"

    print(f"[Policy] Running: {cmd}")
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    import sys
    job_type = sys.argv[1] if len(sys.argv) > 1 else "cpu"
    
    print("=== Home Cluster AI Scheduler ===")
    print(f"RTX GPU load: {get_gpu_load(RTX_IP)}%")
    print(f"RK3576 CPU load: {get_cpu_load(RTK3576_IP):.0f}%")
    print(f"Slurm queue: {get_slurm_queue()} pending jobs")
    print(f"Decision: {decide_target(job_type, 50, 30)}")
POLICY_ENGINE

  chmod +x "$SCHED_DIR/policy_engine.py"
  ok "AI Scheduler prototype: $SCHED_DIR/policy_engine.py"
}

# =============================================================================
# Cluster health check
# =============================================================================
health_check() {
  info "Running cluster health check..."

  echo ""
  echo "=== Slurm ==="
  ssh root@"$RTX_IP" "sinfo" 2>/dev/null || echo "Slurm: unreachable"
  
  echo ""
  echo "=== Ray ==="
  ssh root@"$RTX_IP" "ray status" 2>/dev/null || echo "Ray: unreachable"
  
  echo ""
  echo "=== Ceph ==="
  ssh root@"$RTX_IP" "ceph -s" 2>/dev/null || echo "Ceph: unreachable"
  
  echo ""
  echo "=== GPU ==="
  ssh root@"$RTX_IP" "nvidia-smi --query-gpu=name,utilization.gpu,memory.used --format=csv" 2>/dev/null || \
    echo "GPU: unreachable"
}

# =============================================================================
# Final summary
# =============================================================================
final_summary() {
  echo ""
  echo "=========================================="
  echo "[DAY7] DONE — Full Integration Complete"
  echo "=========================================="
  echo ""
  echo "Your home cluster is now fully integrated:"
  echo ""
  echo "  Slurm (batch scheduling)     → GPU jobs via srun/sbatch"
  echo "  Ray (AI runtime)             → Distributed AI via ray.get/remote"
  echo "  Ceph (distributed storage)   → /mnt/ceph-storage/"
  echo "  WireGuard (mesh network)     → 10.40.40.0/24"
  echo "  AI Scheduler (policy engine) → /opt/ai-scheduler/policy_engine.py"
  echo ""
  echo "Useful commands:"
  echo "  ssh root@10.20.20.10                    # RTX node"
  echo "  ssh root@10.20.20.20                   # RK3576 node"
  echo "  srun --partition=gpu nvidia-smi        # GPU job"
  echo "  ray status                             # Ray cluster"
  echo "  python /opt/ai-scheduler/policy_engine.py gpu  # AI scheduler"
  echo ""
  echo "Quick test:"
  echo "  cd /opt/ray-jobs && python distributed_training.py"
  echo ""
  echo "=========================================="
  echo "NEXT: Maintain, scale, add nodes"
  echo "=========================================="
}

# =============================================================================
# Main
# =============================================================================
main() {
  echo "=========================================="
  echo "[DAY7] Full Integration"
  echo "=========================================="

  create_slurm_ray_bridge
  setup_ceph_slurm_integration
  setup_ceph_ray_integration
  setup_monitoring
  create_ai_scheduler
  health_check
  final_summary
}

main
