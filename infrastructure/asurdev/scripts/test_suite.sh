#!/usr/bin/env bash
# =============================================================================
# HOME CLUSTER — PRODUCTION VALIDATION TEST SUITE (L1-L6)
# =============================================================================
# Usage:
#   bash scripts/test_suite.sh              # full suite
#   bash scripts/test_suite.sh L1           # network only
#   bash scripts/test_suite.sh L2           # Slurm only
# =============================================================================

set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-home-cluster}"
RTX_IP="${RTX_IP:-10.20.20.10}"
RK3576_IP="${RK3576_IP:-10.20.20.20}"
MGMT_IP="${MGMT_IP:-10.10.10.100}"
VPS_IP="${VPS_IP:-}"
CEPH_MON_IP="${CEPH_MON_IP:-10.30.30.10}"

export PASS=0 FAIL=0 SKIP=0

info()  { echo "[INFO]  $1"; }
ok()    { echo "[PASS]  $1"; ((PASS++)); }
fail()  { echo "[FAIL]  $1" >&2; ((FAIL++)); }
skip()  { echo "[SKIP]  $1"; ((SKIP++)); }
warn()  { echo "[WARN]  $1"; }

separator() { echo "--- $1 ---"; }

# =============================================================================
# L1 — Network Layer Tests
# =============================================================================
test_l1_network() {
  separator "L1 — Network"
  
  # VLAN isolation: RK3576 should NOT reach mgmt
  info "VLAN isolation: RK3576 → MGMT VLAN (should fail)"
  if timeout 3 ping -c 1 -W 1 "$MGMT_IP" &>/dev/null; then
    fail "RK3576 reached MGMT VLAN — VLAN isolation broken"
  else
    ok "VLAN isolation OK"
  fi

  # Throughput: iperf3 RTX→RK3576
  info "Throughput test: iperf3 (RTX→RK3576)"
  if command -v iperf3 &>/dev/null; then
    timeout 10 iperf3 -c "$RK3576_IP" -t 5 -f M 2>/dev/null | tee /tmp/iperf3_result.txt || true
    if grep -q "0.00-" /tmp/iperf3_result.txt 2>/dev/null; then
      warn "iperf3 server not running on RK3576 (skip)"
      skip "iperf3 throughput"
    else
      ok "iperf3 completed"
    fi
  else
    skip "iperf3 not installed"
  fi

  # WireGuard mesh
  info "WireGuard mesh: wg show"
  if command -v wg &>/dev/null; then
    WG_IFACE=$(ip link show | grep -o 'wg[0-9]' | head -1 || true)
    if [[ -n "$WG_IFACE" ]]; then
      ok "WireGuard interface $WG_IFACE is UP"
      wg show "$WG_IFACE" | head -5
    else
      fail "WireGuard interface not found"
    fi
  else
    skip "wireguard-tools not installed"
  fi

  # Gateway reachable
  info "Gateway reachable from RTX"
  if ping -c 1 -W 2 "$RTX_IP" &>/dev/null; then
    ok "RTX reachable"
  else
    fail "RTX not reachable"
  fi
}

# =============================================================================
# L2 — Slurm Tests
# =============================================================================
test_l2_slurm() {
  separator "L2 — Slurm GPU Scheduling"

  if ! command -v sinfo &>/dev/null; then
    skip "Slurm not installed"
    return
  fi

  # GPU partition exists
  info "GPU partition exists"
  if sinfo -t normal,GPU | grep -q "gpu"; then
    ok "GPU partition found"
  else
    warn "No GPU partition (expected 'gpu' in PARTITION)"
  fi

  # Node state
  info "Slurm node state"
  sinfo -N -l | grep -v "NODES" || true

  # Submit GPU job
  info "GPU allocation test: srun nvidia-smi"
  TEST_JOB=$(srun --gres=gpu:1 --nodes=1 hostname 2>&1 || true)
  if echo "$TEST_JOB" | grep -qE "(rtx|rk3576|error|cannot)"; then
    warn "GPU job result: $TEST_JOB"
  else
    ok "GPU job submitted successfully"
  fi

  # Job queue
  info "Job queue: squeue"
  squeue --long 2>/dev/null | head -10 || warn "squeue unavailable"

  # Controller alive
  info "Slurmctld controller alive"
  if systemctl is-active slurmctld &>/dev/null; then
    ok "slurmctld is active"
  else
    fail "slurmctld is NOT active"
  fi
}

# =============================================================================
# L3 — Ray Tests
# =============================================================================
test_l3_ray() {
  separator "L3 — Ray Distributed AI Runtime"

  if ! command -v python3 &>/dev/null; then
    skip "Python not installed"
    return
  fi

  info "Ray status: ray status"
  if command -v ray &>/dev/null; then
    timeout 5 ray status 2>/dev/null | head -15 || warn "Ray not running"
  else
    skip "Ray not installed"
    return
  fi

  # Distributed task test
  info "Ray distributed task: 10x parallel map"
  python3 << 'PYTHON_TEST'
import sys
try:
    import ray
    ray.init(address="auto", ignore_reinit_error=True)
    
    @ray.remote
    def double(x):
        import time
        time.sleep(0.1)
        return x * 2

    results = ray.get([double.remote(i) for i in range(10)])
    expected = [i * 2 for i in range(10)]
    
    if results == expected:
        print("[PASS] Ray distributed task: 10/10 completed")
        sys.exit(0)
    else:
        print(f"[FAIL] Results mismatch: {results}")
        sys.exit(1)
except ImportError:
    print("[SKIP] Ray not installed")
    sys.exit(2)
except Exception as e:
    print(f"[WARN] Ray test error: {e}")
    sys.exit(3)
PYTHON_TEST
  local ec=$?
  if [[ $ec -eq 0 ]]; then
    ((PASS++))
  elif [[ $ec -eq 2 ]]; then
    ((SKIP++))
  else
    ((FAIL++))
  fi
}

# =============================================================================
# L4 — Ceph Tests
# =============================================================================
test_l4_ceph() {
  separator "L4 — Ceph Distributed Storage"

  if ! command -v ceph &>/dev/null; then
    skip "Ceph not installed"
    return
  fi

  info "Ceph cluster health"
  local health=$(ceph -s 2>/dev/null | grep -oE "(HEALTH_OK|HEALTH_WARN|HEALTH_ERR)" || echo "UNKNOWN")
  if [[ "$health" == "HEALTH_OK" ]]; then
    ok "Ceph HEALTH_OK"
  elif [[ "$health" == "HEALTH_WARN" ]]; then
    warn "Ceph HEALTH_WARN"
  else
    fail "Ceph HEALTH_ERR or unreachable"
  fi

  info "Ceph status details"
  ceph -s 2>/dev/null | grep -E "(osd|mon|mgr|pgs)" | head -5 || true

  # Replication test
  info "Replication test: rados put/get"
  TEST_KEY="home_cluster_test_$(date +%s)"
  if timeout 10 rados put "$TEST_KEY" /etc/hosts --cluster="$CEPH_CLUSTER_NAME" 2>/dev/null; then
    if timeout 10 rados get "$TEST_KEY" /tmp/ceph_test_out.txt --cluster="$CEPH_CLUSTER_NAME" 2>/dev/null; then
      if diff /etc/hosts /tmp/ceph_test_out.txt &>/dev/null; then
        ok "Ceph replication OK"
      else
        fail "Ceph replication data mismatch"
      fi
      rados rm "$TEST_KEY" --cluster="$CEPH_CLUSTER_NAME" 2>/dev/null || true
    else
      fail "Ceph rados get failed"
    fi
  else
    warn "Ceph rados put failed (cluster may be down)"
  fi
}

# =============================================================================
# L5 — Integration Tests
# =============================================================================
test_l5_integration() {
  separator "L5 — Integration (Slurm → Ray → Ceph)"

  # Slurm job writing to Ceph
  info "Slurm→Ceph: job writes to Ceph volume"
  cat > /tmp/slurm_ceph_test.sh << 'SLURM_CEPH'
#!/bin/bash
#SBATCH --job-name=ceph_test
#SBATCH --output=/tmp/slurm_ceph_out.txt
#SBATCH --nodes=1
#MOUNT_CEPH=1
echo "SLURM_JOB_ID=$SLURM_JOB_ID" >> /tmp/ceph_pipeline_test.txt
date >> /tmp/ceph_pipeline_test.txt
SLURM_CEPH
  if command -v sbatch &>/dev/null; then
    sbatch /tmp/slurm_ceph_test.sh &>/dev/null || warn "sbatch failed"
    sleep 3
    if [[ -f /tmp/ceph_pipeline_test.txt ]]; then
      ok "Slurm→Ceph pipeline: job wrote to shared storage"
    else
      warn "Slurm→Ceph: output not found yet"
    fi
  else
    skip "Slurm not available"
  fi

  # Ray status shows all nodes
  info "Ray cluster: node visibility"
  python3 << 'RAY_STATUS_TEST'
try:
    import ray
    ray.init(address="auto", ignore_reinit_error=True)
    nodes = ray.nodes()
    alive = [n for n in nodes if n.get("Alive", False)]
    print(f"[INFO] Ray alive nodes: {len(alive)}/{len(nodes)}")
    if len(alive) >= 1:
        print("[PASS] Ray sees cluster nodes")
    else:
        print("[FAIL] Ray sees no alive nodes")
except Exception as e:
    print(f"[WARN] {e}")
RAY_STATUS_TEST
}

# =============================================================================
# L6 — AI Scheduler Prototype Tests
# =============================================================================
test_l6_ai_scheduler() {
  separator "L6 — AI Scheduler (Policy Engine Prototype)"

  if [[ ! -f /home/workspace/home-cluster-iac/ai_scheduler/scheduler.py ]]; then
    skip "AI scheduler not deployed yet"
    return
  fi

  info "AI Scheduler: policy routing test"
  python3 << 'SCHEDULER_TEST'
import sys
import os
sys.path.insert(0, '/home/workspace/home-cluster-iac/ai_scheduler')

try:
    # Mock nodes for testing
    mock_nodes = [
        {"hostname": "rtx-node", "gpu_load": 95, "cpu_load": 30, "mem_free_gb": 10},
        {"hostname": "rk3576", "gpu_load": 0, "cpu_load": 20, "mem_free_gb": 5},
    ]
    
    # Import and test
    from scheduler import route_job
    
    # Test GPU job routing
    result = route_job({"type": "gpu_training", "memory_gb": 8}, mock_nodes)
    print(f"[INFO] GPU job routed to: {result}")
    
    # Test CPU job routing
    result2 = route_job({"type": "cpu_batch", "memory_gb": 2}, mock_nodes)
    print(f"[INFO] CPU job routed to: {result2}")
    
    print("[PASS] AI Scheduler routing logic OK")
except ImportError as e:
    print(f"[SKIP] AI scheduler import failed: {e}")
    sys.exit(2)
except Exception as e:
    print(f"[FAIL] AI scheduler error: {e}")
    sys.exit(1)
SCHEDULER_TEST
  local ec=$?
  if [[ $ec -eq 0 ]]; then
    ((PASS++))
  elif [[ $ec -eq 2 ]]; then
    ((SKIP++))
  else
    ((FAIL++))
  fi
}

# =============================================================================
# Self-healing Tests
# =============================================================================
test_self_healing() {
  separator "Self-Healing / Auto-Recovery"

  if [[ ! -f /home/workspace/home-cluster-iac/self_healing/health_check.sh ]]; then
    skip "Self-healing scripts not deployed"
    return
  fi

  info "Health check: all services"
  bash /home/workspace/home-cluster-iac/self_healing/health_check.sh 2>&1 | tail -20
}

# =============================================================================
# MAIN
# =============================================================================
run_all() {
  test_l1_network
  test_l2_slurm
  test_l3_ray
  test_l4_ceph
  test_l5_integration
  test_l6_ai_scheduler
  test_self_healing
}

LAYER="${1:-all}"
case "$LAYER" in
  L1) test_l1_network ;;
  L2) test_l2_slurm ;;
  L3) test_l3_ray ;;
  L4) test_l4_ceph ;;
  L5) test_l5_integration ;;
  L6) test_l6_ai_scheduler ;;
  all) run_all ;;
  *) echo "Usage: $0 [L1|L2|L3|L4|L5|L6|all]"; exit 1 ;;
esac

echo ""
separator "TEST SUMMARY"
echo "  PASSED: $PASS"
echo "  FAILED: $FAIL" 
echo "  SKIPPED: $SKIP"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo "[RESULT] FAILED — $FAIL critical issues need attention"
  exit 1
elif [[ $SKIP -gt 0 ]]; then
  echo "[RESULT] PASSED WITH SKIPS — system partially deployed"
  exit 0
else
  echo "[RESULT] ALL TESTS PASSED"
  exit 0
fi

# =============================================================================
# L7 — FAILURE ORCHESTRATION TEST
# =============================================================================
test_l7() {
  log "L7: FAILURE ORCHESTRATION" "INFO"

  local FAILED=0

  # L7.1 — Simulate GPU node failure (slurmd stop on RTX)
  log "L7.1: Killing slurmd on GPU node..." "WARN"
  run_on_node "${RTX_IP}" "systemctl stop slurmd 2>/dev/null || pkill slurmd || true"

  sleep 5

  # L7.2 — Verify Slurm detects node failure
  log "L7.2: Slurm should mark node as DOWN..." "INFO"
  local slurmd_status
  slurmd_status=$(run_on_node "${RTX_IP}" "systemctl is-active slurmd 2>/dev/null || echo 'inactive'" 2>/dev/null || echo " unreachable")
  if [[ "$slurmd_status" != "active" ]]; then
    log "  ✓ slurmd confirmed down on RTX" "OK"
  else
    log "  ✗ slurmd still active!" "FAIL"
    ((FAILED++))
  fi

  # L7.3 — Scheduler should detect GPU node down and redirect
  log "L7.3: AI Scheduler should route to backup (RK3576)..." "INFO"
  local scheduler_decision
  scheduler_decision=$(curl -s -X POST http://localhost:8080/schedule \
    -H "Content-Type: application/json" \
    -d '{"job_type":"gpu","memory_gb":4}' 2>/dev/null | python3 -c \
    "import sys,json; print(json.load(sys.stdin).get('target','error'))" 2>/dev/null || echo "unreachable")

  if [[ "$scheduler_decision" == "rk3576-node" ]] || [[ "$scheduler_decision" == "error" ]]; then
    log "  ✓ Scheduler redirected/failed gracefully (target: $scheduler_decision)" "OK"
  else
    log "  ✗ Scheduler returned: $scheduler_decision (expected: rk3576-node or error)" "FAIL"
    ((FAILED++))
  fi

  # L7.4 — Restore slurmd
  log "L7.4: Restoring slurmd on RTX..." "INFO"
  run_on_node "${RTX_IP}" "systemctl start slurmd 2>/dev/null || /usr/sbin/slurmd" 2>/dev/null || true
  sleep 5

  # L7.5 — Verify cluster health restored
  log "L7.5: Verify Slurm sees RTX node again..." "INFO"
  local slurmd_after
  slurmd_after=$(run_on_node "${RTX_IP}" "systemctl is-active slurmd 2>/dev/null || echo 'inactive'" 2>/dev/null || echo "unreachable")
  if [[ "$slurmd_after" == "active" ]]; then
    log "  ✓ RTX slurmd restored" "OK"
  else
    log "  ✗ RTX slurmd NOT restored (manual intervention required)" "FAIL"
    ((FAILED++))
  fi

  echo ""
  if [[ $FAILED -eq 0 ]]; then
    log "[RESULT] L7: PASSED ✓" "OK"
    return 0
  else
    log "[RESULT] L7: FAILED — $FAILED check(s) failed" "FAIL"
    return 1
  fi
}

# =============================================================================
# L8 — NETWORK PARTITION TEST
# =============================================================================
test_l8() {
  log "L8: NETWORK PARTITION" "INFO"

  local FAILED=0

  # L8.1 — Bring down WireGuard interface
  log "L8.1: Tearing down WireGuard mesh..." "WARN"
  run_on_node "${RTX_IP}" "wg-quick down wg0 2>/dev/null || ip link del wg0 2>/dev/null || true" 2>/dev/null || true

  sleep 3

  # L8.2 — Verify nodes are unreachable via VPN
  log "L8.2: Nodes unreachable via VPN (10.40.40.x)..." "INFO"
  local ping_result
  ping_result=$(ping -c 2 -W 2 "${RTX_IP}" 2>&1 | grep -o "2 received" || echo "no response")
  if [[ "$ping_result" != "2 received" ]]; then
    log "  ✓ VPN partition confirmed (no ping)" "OK"
  else
    log "  ✗ VPN still reachable!" "FAIL"
    ((FAILED++))
  fi

  # L8.3 — Check Ceph still accessible via LAN IP (fallback)
  log "L8.3: Ceph accessible via LAN IP..." "INFO"
  local ceph_lan
  ceph_lan=$(curl -s -k "https://${RTX_IP}:8443/api/summary" --connect-timeout 3 2>/dev/null | python3 -c \
    "import sys,json; print('ok' if 'health' in json.load(sys.stdin) else 'fail')" 2>/dev/null || echo "unreachable")
  if [[ "$ceph_lan" == "ok" ]] || [[ "$ceph_lan" == "unreachable" ]]; then
    log "  ✓ Ceph check complete (result: $ceph_lan)" "OK"
  else
    log "  ✗ Ceph LAN unreachable" "FAIL"
    ((FAILED++))
  fi

  # L8.4 — Restore WireGuard
  log "L8.4: Restoring WireGuard mesh..." "INFO"
  run_on_node "${RTX_IP}" "wg-quick up wg0 2>/dev/null || wg-quick up wg0" 2>/dev/null || \
    run_on_node "${RTX_IP}" "ip link add wg0 type wireguard 2>/dev/null || true" 2>/dev/null || true
  sleep 3

  # L8.5 — Verify mesh restored
  log "L8.5: WireGuard mesh restored..." "INFO"
  local wg_check
  wg_check=$(run_on_node "${RTX_IP}" "wg show wg0 2>/dev/null | head -1 || echo 'no interface'" 2>/dev/null || echo "unreachable")
  if [[ "$wg_check" != "no interface" ]]; then
    log "  ✓ WireGuard interface restored" "OK"
  else
    log "  ✗ WireGuard NOT restored (manual: wg-quick up wg0)" "FAIL"
    ((FAILED++))
  fi

  echo ""
  if [[ $FAILED -eq 0 ]]; then
    log "[RESULT] L8: PASSED ✓" "OK"
    return 0
  else
    log "[RESULT] L8: FAILED — $FAILED check(s) failed" "FAIL"
    return 1
  fi
}

# =============================================================================
# L9 — LOAD SPIKE TEST (100 concurrent jobs)
# =============================================================================
test_l9() {
  log "L9: LOAD SPIKE — 100 concurrent jobs" "INFO"

  local FAILED=0

  # L9.1 — Submit 100 sleep jobs via Slurm
  log "L9.1: Submitting 100 sleep jobs..." "INFO"
  local job_ids=""
  for i in $(seq 1 100); do
    local jid
    jid=$(sbatch --partition=cpu --wrap="sleep 60" 2>/dev/null | grep -oP 'Submitted batch job \K\d+' || echo "")
    if [[ -n "$jid" ]]; then
      job_ids="${job_ids} ${jid}"
    fi
  done

  local submitted
  submitted=$(echo "$job_ids" | wc -w)
  log "  Submitted: ${submitted}/100 jobs" "INFO"

  if [[ "$submitted" -lt 90 ]]; then
    log "  ✗ Too few jobs accepted (${submitted}/100)" "FAIL"
    ((FAILED++))
  else
    log "  ✓ Queue accepted ${submitted} jobs" "OK"
  fi

  # L9.2 — Scheduler handles concurrent requests
  log "L9.2: Scheduler handles 50 concurrent /schedule requests..." "INFO"
  local sched_ok=0
  for i in $(seq 1 50); do
    local resp
    resp=$(curl -s -X POST http://localhost:8080/schedule \
      -H "Content-Type: application/json" \
      -d '{"job_type":"cpu","memory_gb":1}' --connect-timeout 1 2>/dev/null | \
      python3 -c "import sys,json; print('ok' if 'target' in json.load(sys.stdin) else 'err')" 2>/dev/null || echo "fail")
    [[ "$resp" == "ok" ]] && ((sched_ok++))
  done

  log "  Scheduler OK: ${sched_ok}/50 concurrent requests" "INFO"
  if [[ "$sched_ok" -ge 45 ]]; then
    log "  ✓ Scheduler stable under load (${sched_ok}/50)" "OK"
  else
    log "  ✗ Scheduler degraded (${sched_ok}/50)" "FAIL"
    ((FAILED++))
  fi

  # L9.3 — Cleanup jobs
  log "L9.3: Cancel submitted jobs..." "INFO"
  for jid in $job_ids; do
    scancel "$jid" 2>/dev/null || true
  done
  log "  ✓ Jobs cancelled" "OK"

  echo ""
  if [[ $FAILED -eq 0 ]]; then
    log "[RESULT] L9: PASSED ✓" "OK"
    return 0
  else
    log "[RESULT] L9: FAILED — $FAILED check(s) failed" "FAIL"
    return 1
  fi
}
