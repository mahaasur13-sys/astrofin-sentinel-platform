#!/usr/bin/env bash
#
# deploy.sh — ACOS Cluster Deployment
# Usage:
#   ./deploy.sh [--dry-run] [--skip-days=N,N] [--only=COMPONENT]
#   ./deploy.sh day1|day2|...|day7|all
#   ./deploy.sh verify|monitor|ml-api|loadtest|troubleshoot
#
set -euo pipefail

# ── Colours ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'
INFO="${BLUE}[INFO]${RESET}"; SUCCESS="${GREEN}[OK]${RESET}"
WARN="${YELLOW}[WARN]${RESET}"; ERROR="${RED}[ERROR]${RESET}"

# ── Config ────────────────────────────────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_ROOT"
SKIP_DAYS="${SKIP_DAYS:-}"; ONLY="${ONLY:-}"; DRY_RUN=false
LOGFILE="${REPO_ROOT}/deploy-$(date +%Y%m%d-%H%M%S).log"

# Parse args
for arg in "$@"; do
  case $arg in
    --dry-run)        DRY_RUN=true; log "DRY-RUN mode (no changes will be made)" ;;
    --skip-days=*)    SKIP_DAYS="${arg#*=}"; log "Will skip days: $SKIP_DAYS" ;;
    --only=*)         ONLY="${arg#*=}";       log "Will deploy only: $ONLY" ;;
    --*)              log "Unknown option: $arg" && exit 1 ;;
  esac
done

# ── Helpers ─────────────────────────────────────────────────────────────────
log()  { echo -e "${INFO} $*"; }
warn() { echo -e "${WARN} $*" >&2; }
err()  { echo -e "${ERROR} $*" >&2; exit 1; }
cmd()  { log "Running: $*"; $DRY_RUN || "$@"; }
cmd_sudo() { local c="$*"; $DRY_RUN || sudo bash -c "$c"; }

is_skipped() {
  [[ " $SKIP_DAYS " =~ " $1 " ]] && return 0
  [[ -n "$ONLY" && " $ONLY " != " all " && " $ONLY " != " $1 " ]] && return 1
  return 0
}

check_reqs() {
  for bin in ansible ansible-playbook terraform docker git curl; do
    command -v $bin &>/dev/null || err "Required binary missing: $bin"
  done
  # Check ansible/group_vars/all.yml exists
  [[ -f ansible/group_vars/all.yml ]] || err "ansible/group_vars/all.yml not found — copy from all.yml.example and fill in REQUIRED values"
}

log_step() {
  log "${BOLD}${CYAN}═══ STEP $1: $2 ═══${RESET}"
}

wait_ssh() {
  local host=$1; local maxwait=${2:-60}
  log "Waiting for SSH on $host (max ${maxwait}s)..."
  for i in $(seq 1 $maxwait); do
    timeout 2 ssh -o ConnectTimeout=1 -o StrictHostKeyChecking=no "$host" echo ok &>/dev/null && log "SSH OK: $host" && return 0
    sleep 1
  done
  warn "SSH timeout on $host — continuing anyway"
}

# ── Verify ──────────────────────────────────────────────────────────────────
verify() {
  log_step "VERIFY" "Cluster Status"
  echo -e "\n${BOLD}=== Slurm ===${RESET}"
  cmd sinfo || warn "sinfo failed (slurmctld not running?)"
  echo -e "\n${BOLD}=== Ceph ===${RESET}"
  cmd ceph -s 2>/dev/null || warn "ceph not available"
  echo -e "\n${BOLD}=== Ray ===${RESET}"
  cmd ray status 2>/dev/null || warn "ray not available"
  echo -e "\n${BOLD}=== ML API Health ===${RESET}"
  curl -sf http://localhost:8081/health 2>/dev/null | python3 -m json.tool || warn "ML API not responding"
  echo -e "\n${BOLD}=== WireGuard Peers ===${RESET}"
  cmd_sudo wg show 2>/dev/null || warn "WireGuard not active"
  echo -e "\n${BOLD}=== Docker containers ===${RESET}"
  cmd docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || warn "docker not available"
}

# ── Components (Ansible tags) ───────────────────────────────────────────────
deploy_component() {
  local tag=$1; local desc=$2
  log_step "COMPONENT" "$desc"
  ansible-playbook -i ansible/inventory.ini ansible/site.yml \
    --tags "$tag" --diff ${DRY_RUN:+--check}
}

# ── Day steps ───────────────────────────────────────────────────────────────
day1() {
  deploy_component "mikrotik" "MikroTik Router Config (VLAN, DHCP, Firewall)"
}
day2() {
  deploy_component "wireguard-mesh" "WireGuard/AmneziaWG Mesh VPN"
}
day3() {
  deploy_component "compute-nodes" "GPU Drivers, Docker, Python env (RTX 3060)"
}
day4() {
  deploy_component "slurm-cluster" "Slurm Cluster (GPU scheduling, partitions)"
}
day5() {
  deploy_component "ray-cluster" "Ray Head + Workers (distributed AI)"
}
day6() {
  deploy_component "ceph-storage" "Ceph FS (2-node replication)"
}
day7() {
  log_step "DAY 7" "Integration Layer"
  deploy_component "integration" "Job routing, Slurm↔Ray bridge, CephFS mount"
  deploy_component "monitoring" "Prometheus + Grafana"
  deploy_component "self-healing" "Watchdog + Cron"
}

# ── ML API ──────────────────────────────────────────────────────────────────
ml_api() {
  log_step "ML_API" "FastAPI Inference Service"
  cmd "make ml-api-docker-build || true"
  if systemctl is-active --quiet ml-inference 2>/dev/null; then
    log "ML API already running — restarting"
    cmd_sudo "systemctl restart ml-inference"
  else
    cmd_sudo "cp ml_engine/inference/ml-inference.service /etc/systemd/system/ \
      && systemctl daemon-reload && systemctl enable ml-inference \
      && systemctl start ml-inference"
  fi
  sleep 3
  curl -sf http://localhost:8081/health | python3 -m json.tool || warn "ML API health check failed"
}

# ── Monitoring ──────────────────────────────────────────────────────────────
monitor() {
  log_step "MONITORING" "Prometheus + Grafana stack"
  deploy_component "monitoring" "Monitoring Stack"
  log "Grafana: http://localhost:3000  (admin / password from all.yml)"
}

# ── Load tests ────────────────────────────────────────────────────────────────
loadtest() {
  log_step "LOADTEST" "Running stress scenarios"
  if [[ ! -d "load_tests" ]]; then
    warn "load_tests/ directory not found — skipping load tests"
    return
  fi
  cmd "pytest load_tests/ -v --tb=short" || warn "Some load tests failed"
}

# ── Self-healing ────────────────────────────────────────────────────────────
self_healing() {
  log_step "SELF_HEALING" "Watchdog + Cron setup"
  deploy_component "self-healing" "Self-healing watchdog"
}

# ── Integration test ─────────────────────────────────────────────────────────
integration_test() {
  log_step "INTEGRATION" "Slurm + ML API end-to-end"
  if command -v squeue &>/dev/null && curl -sf http://localhost:8081/health &>/dev/null; then
    log "Submitting test job..."
    echo "#!/bin/bash\n#SBATCH --gres=gpu:1\n#SBATCH --partition=gpu\necho hello" > /tmp/test_job.sh
    cmd "sbatch /tmp/test_job.sh"
    sleep 5
    log "Checking job history..."
    cmd "sacct --format=JobID,JobName,State,ExitCode -j $(squeue -h -o %id | head -1) 2>/dev/null || true"
  else
    warn "Slurm or ML API not ready — skipping integration test"
  fi
}

# ── Troubleshooting ──────────────────────────────────────────────────────────
troubleshoot() {
  log_step "TROUBLESHOOT" "Diagnostic commands"
  echo -e "\n${BOLD}--- WireGuard ─--${RESET}"
  cmd_sudo "wg show; ip link show | grep wg"
  echo -e "\n${BOLD}--- Slurm logs ─--${RESET}"
  cmd "sudo journalctl -u slurmctld --no-pager -n 30 2>/dev/null || true"
  echo -e "\n${BOLD}--- Ceph health ─--${RESET}"
  cmd "ceph health detail 2>/dev/null || true"
  echo -e "\n${BOLD}--- Ray logs ─--${RESET}"
  cmd "ray logs 2>/dev/null | tail -20 || true"
  echo -e "\n${BOLD}--- ML API logs ─--${RESET}"
  cmd "sudo journalctl -u ml-inference --no-pager -n 30 2>/dev/null || true"
}

# ── Main ──────────────────────────────────────────────────────────────────────
usage() {
  echo -e "${BOLD}Usage:${RESET} $0 [day1|day2|...|day7|all|verify|ml-api|monitor|loadtest|self-healing|integration|troubleshoot] [OPTIONS]"
  echo ""
  echo "Options:"
  echo "  --dry-run         Show what would be done (Ansible --check)"
  echo "  --skip-days=N,N   Skip specific days"
  echo "  --only=COMPONENT  Deploy only named component"
  echo ""
  echo "Examples:"
  echo "  $0 all                      # Full 7-day deployment"
  echo "  $0 day4                     # Only Slurm"
  echo "  $0 verify                   # Check cluster status"
  echo "  $0 ml-api                   # Deploy ML inference API"
  echo "  $0 --dry-run day5           # Preview Ray deployment"
}

main() {
  check_reqs

  [[ $# -eq 0 ]] && { usage; exit 0; }

  case $1 in
    day1)      day1 ;;
    day2)      day2 ;;
    day3)      day3 ;;
    day4)      day4 ;;
    day5)      day5 ;;
    day6)      day6 ;;
    day7)      day7 ;;
    all)       day1; day2; day3; day4; day5; day6; day7; verify ;;
    verify)    verify ;;
    ml-api)    ml_api ;;
    monitor)   monitor ;;
    loadtest)  loadtest ;;
    self-healing) self_healing ;;
    integration)  integration_test ;;
    troubleshoot)  troubleshoot ;;
    help|--help|-h) usage ;;
    *)          err "Unknown command: $1 — try: day1-day7, all, verify, ml-api, monitor, loadtest, self-healing, integration, troubleshoot" ;;
  esac
}

main "$@"