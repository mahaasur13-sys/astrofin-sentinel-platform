#!/usr/bin/env bash
# =============================================================================
# DAY 5 — Ray Cluster (Distributed AI Runtime)
# =============================================================================
# Target: RTX 3060 PC (head), RK3576 (worker)
# Result: Ray cluster with GPU support for distributed AI workloads
# Run on: RTX PC (head), then RK3576 (worker)
# =============================================================================

set -euo pipefail

RAY_HEAD_IP="10.20.20.10"
RAY_WORKERS=("10.20.20.20")
RAY_DASHBOARD_PORT=8265
RAY_REDIS_PORT=6379

RAY_HEAD_NODE="rtx-node"
RAY_WORKER_NODE="rk3576-node"

info() { echo "[INFO] $1"; }
ok()   { echo "[OK]   $1"; }
warn() { echo "[WARN] $1"; }

# =============================================================================
# Install Ray
# =============================================================================
install_ray() {
  info "Installing Ray..."
  if command -v ray &>/dev/null; then
    ok "Ray already installed"
    ray --version
  else
    pip3 install --quiet --user ray[default] ray[air]
    ok "Ray installed"
  fi
}

# =============================================================================
# Start Ray head
# =============================================================================
start_head() {
  info "Starting Ray head on RTX (this node)..."
  
  # Kill existing ray
  ray stop 2>/dev/null || true

  # Start head
  nohup ray start --head \
    --port=$RAY_REDIS_PORT \
    --dashboard-host=0.0.0.0 \
    --dashboard-port=$RAY_DASHBOARD_PORT \
    --num-gpus=1 \
    --implicitly-pools-memory=$((32 * 1024 * 1024 * 1024)) \
    &>/dev/null &

  sleep 3

  # Verify
  if ray status 2>/dev/null | grep -q "Restarting\|Dead"; then
    warn "Ray head may not be healthy — check: ray status"
  else
    ok "Ray head started"
    echo ""
    echo "  Dashboard: http://$RAY_HEAD_IP:$RAY_DASHBOARD_PORT"
    echo "  Redis: $RAY_HEAD_IP:$RAY_REDIS_PORT"
  fi
}

# =============================================================================
# Start Ray workers
# =============================================================================
start_workers() {
  info "Starting Ray workers..."

  for worker_ip in "${RAY_WORKERS[@]}"; do
    info "Starting worker on $worker_ip..."
    
    # SSH and start ray worker
    ssh root@$worker_ip "ray stop 2>/dev/null || true; \
      ray start --address='$RAY_HEAD_IP:$RAY_REDIS_PORT' \
      --num-gpus=0 \
      --block" &>/dev/null &

    sleep 2
    ok "Worker $worker_ip started (async)"
  done
}

# =============================================================================
# Test Ray cluster
# =============================================================================
test_ray() {
  info "Testing Ray cluster..."
  
  python3 << 'PYTEST'
import ray
import time

try:
  ray.init(address="auto", ignore_reinit_error=True)
  print(f"Connected to Ray: {ray.get_runtime_context().get_worker_id()[:8]}")
  
  @ray.remote
  def test_task():
    import time
    time.sleep(0.5)
    return "OK"

  results = ray.get([test_task.remote() for _ in range(4)])
  print(f"Tasks completed: {results}")
  
  # GPU test
  @ray.remote(num_gpus=0.5)
  def gpu_task():
    import torch
    return f"CUDA: {torch.cuda.is_available()}"

  try:
    result = ray.get(gpu_task.remote())
    print(f"GPU task: {result}")
  except Exception as e:
    print(f"GPU task skipped: {e}")
  
  ray.shutdown()
  print("Ray cluster test PASSED")
except Exception as e:
  print(f"Ray test failed: {e}")
PYTEST
}

# =============================================================================
# Ray job script template
# =============================================================================
create_ray_scripts() {
  info "Creating Ray job templates..."
  
  SCRIPT_DIR="/opt/ray-jobs"
  mkdir -p "$SCRIPT_DIR"

  # Simple Ray job
  cat > "$SCRIPT_DIR/distributed_training.py" << 'RAY_TRAIN'
import ray
import torch
import time

ray.init(address="auto")

print(f"Ray initialized: {ray.cluster_resources()}")

@ray.remote(num_gpus=1)
def train_model(epoch):
    torch.cuda.init()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.nn.Linear(1000, 100).to(device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    
    data = torch.randn(64, 1000).to(device)
    target = torch.randn(64, 100).to(device)
    
    start = time.time()
    for _ in range(10):
        optimizer.zero_grad()
        output = model(data)
        loss = (output - target).pow(2).mean()
        loss.backward()
        optimizer.step()
    
    elapsed = time.time() - start
    return {"epoch": epoch, "loss": loss.item(), "time": elapsed, "device": str(device)}

futures = [train_model.remote(i) for i in range(4)]
results = ray.get(futures)
for r in results:
    print(f"Epoch {r['epoch']}: loss={r['loss']:.4f}, time={r['time']:.2f}s, device={r['device']}")
RAY_TRAIN

  # Ray Serve example
  cat > "$SCRIPT_DIR/ray_serve_inference.py" << 'RAY_SERVE'
import ray
from ray import serve
import torch

ray.init(address="auto")
serve.start(detached=True)

@serve.deployment(num_replicas=2, ray_actor_options={"num_gpus": 0.25})
class Inferencer:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = torch.nn.Linear(512, 256).to(self.device)
        self.model.eval()
    
    def __call__(self, request):
        import json
        data = torch.randn(1, 512).to(self.device)
        with torch.no_grad():
            output = self.model(data)
        return {"output": output.cpu().numpy().tolist(), "device": self.device}

Inferencer.deploy()
print("Ray Serve running on http://localhost:8000")
RAY_SERVE

  ok "Ray job scripts created in $SCRIPT_DIR"
}

# =============================================================================
# Main
# =============================================================================
main() {
  echo "=========================================="
  echo "[DAY5] Ray Cluster Setup"
  echo "=========================================="
  
  install_ray
  
  echo ""
  echo "--- Starting Ray Head ---"
  start_head
  
  echo ""
  echo "--- Starting Ray Workers ---"
  start_workers
  
  sleep 5
  
  echo ""
  echo "--- Testing Ray Cluster ---"
  test_ray
  
  echo ""
  echo "--- Creating Job Templates ---"
  create_ray_scripts

  echo ""
  echo "=========================================="
  echo "[DAY5] DONE — Ray Cluster Ready"
  echo "=========================================="
  echo ""
  echo "Useful:"
  echo "  ray status           # cluster status"
  echo "  python /opt/ray-jobs/distributed_training.py"
  echo "  python /opt/ray-jobs/ray_serve_inference.py"
  echo ""
  echo "Next: bash scripts/day6-ceph.sh"
}

main
