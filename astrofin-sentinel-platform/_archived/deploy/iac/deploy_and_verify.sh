#!/usr/bin/env bash
# deploy_and_verify.sh — ACOS cluster deploy + verify script
# Usage: ./deploy_and_verify.sh [--force]
#   --force  Re-run all steps even if they previously succeeded

set -euo pipefail

# ─── Paths ────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP_DIR="/tmp/acos_deploy"
LOGFILE="${SCRIPT_DIR}/deploy.log"
STATEFILE="${TMP_DIR}/.state.json"
mkdir -p "${TMP_DIR}" "${SCRIPT_DIR}/logs"

# ─── Colors ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*" >&2; }
step()    { echo -e "${CYAN}[STEP]${NC} $*"; }

# ─── Cleanup trap ─────────────────────────────────────────────────
trap 'cleanup' EXIT
cleanup() {
    local ex=$?
    if [ $ex -ne 0 ]; then
        error "Script failed. Full log: ${LOGFILE}"
    fi
}

# ─── State management ─────────────────────────────────────────────
FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

save_state() {
    local step="$1"; shift
    local val="$*"
    local timestamp
    timestamp=$(date -Iseconds)
    local tmp
    tmp=$(mktemp)
    if [ -f "${STATEFILE}" ]; then
        jq ".\"${step}\" = {status: \"${val}\", time: \"${timestamp}\"}" "${STATEFILE}" > "${tmp}" && mv "${tmp}" "${STATEFILE}"
    else
        echo "{\"${step}\": {status: \"${val}\", time: \"${timestamp}\"}}" > "${STATEFILE}"
    fi
}

get_state() {
    local step="$1"
    [ -f "${STATEFILE}" ] && jq -r ".\"${step}\".status // \"never\"" "${STATEFILE}" 2>/dev/null || echo "never"
}

mark_done()  { save_state "$1" "done"; }
mark_skip()  { save_state "$1" "skipped"; }
mark_fail()  { save_state "$1" "failed"; }
is_done()    { [ "$(get_state "$1")" == "done" ]; }

# ─── Init log ─────────────────────────────────────────────────────
log_init() {
    exec > >(tee -a "${LOGFILE}") 2>&1
    info "Log file: ${LOGFILE}"
    info "State file: ${STATEFILE}"
}

# ─── Dependency checks ────────────────────────────────────────────
check_deps() {
    step "Checking dependencies..."
    local missing=0
    local deps=(ansible terraform jq curl)
    for d in "${deps[@]}"; do
        if command -v "${d}" &>/dev/null; then
            success "${d} found"
        else
            warn "${d} NOT found — install it first"
            missing=$((missing + 1))
        fi
    done

    # Optional tools — just warn
    command -v wg &>/dev/null      && success "wg found"      || warn "wg not found (WireGuard)"
    command -v ceph &>/dev/null    && success "ceph found"    || warn "ceph not found (Ceph client)"
    command -v scontrol &>/dev/null && success "slurm found"   || warn "slurm client not found"
    command -v ray &>/dev/null     && success "ray found"     || warn "ray not found"
    command -v docker &>/dev/null  && success "docker found"  || warn "docker not found"
    command -v mikrotik_backup &>/dev/null && success "mikrotik_backup found" || warn "mikrotik_backup not found (optional)"

    if [ $missing -gt 0 ]; then
        error "${missing} required tools missing — aborting"
        error "Install: sudo apt install ansible terraform jq curl"
        exit 1
    fi

    # Ansible version
    local av
    av=$(ansible --version 2>/dev/null | head -1 | grep -oP '\d+\.\d+' | head -1)
    info "Ansible version: ${av}"

    # Terraform version
    local tv
    tv=$(terraform version -json 2>/dev/null | jq -r '.terraform_version' 2>/dev/null || terraform version 2>/dev/null | head -1)
    info "Terraform version: ${tv}"

    mark_done "deps_check"
}

# ─── File presence check ──────────────────────────────────────────
check_files() {
    step "Checking required files..."
    local required=(
        "ansible/group_vars/all.yml"
        "ansible/inventory.ini"
        "ansible/playbook.yml"
        ".env"
    )
    local optional=(
        "ansible/roles/wireguard/tasks/main.yml"
        "ansible/roles/slurm/tasks/main.yml"
        "ansible/roles/ceph/tasks/main.yml"
        "ansible/roles/ray/tasks/main.yml"
        "deploy.sh"
        "Makefile"
        "post_deploy.sh"
        "load_test/run_scenario1.sh"
    )

    for f in "${required[@]}"; do
        if [ -f "${SCRIPT_DIR}/${f}" ]; then
            success "${f}"
        else
            error "${f} MISSING — required"
            missing_required=1
        fi
    done

    for f in "${optional[@]}"; do
        if [ -f "${SCRIPT_DIR}/${f}" ]; then
            success "${f} (optional)"
        else
            warn "${f} not found — some features may be skipped"
        fi
    done

    if [ "${missing_required:-0}" -eq 1 ]; then
        error "Required files missing — cannot proceed"
        error "Ensure ansible/group_vars/all.yml and .env exist"
        exit 1
    fi

    mark_done "file_check"
}

# ─── Load .env ────────────────────────────────────────────────────
load_env() {
    step "Loading environment from .env..."
    if [ -f "${SCRIPT_DIR}/.env" ]; then
        set -a
        source "${SCRIPT_DIR}/.env"
        set +a
        success ".env loaded"
    else
        warn ".env not found — using defaults"
    fi

    # Prompt for critical vars if missing
    if [ -z "${MIKROTIK_HOST:-}" ]; then
        read -rp "MIKROTIK_HOST (e.g. 192.168.88.1): " MIKROTIK_HOST
    fi
    if [ -z "${MIKROTIK_USER:-}" ]; then
        read -rp "MIKROTIK_USER [admin]: " MIKROTIK_USER
        MIKROTIK_USER="${MIKROTIK_USER:-admin}"
    fi
    if [ -z "${WG_PRIVATE_KEY:-}" ]; then
        read -rp "WG_PRIVATE_KEY (base64): " WG_PRIVATE_KEY
    fi

    export MIKROTIK_HOST MIKROTIK_USER WG_PRIVATE_KEY
    mark_done "env_load"
}

# ─── Terraform plan/apply ─────────────────────────────────────────
run_terraform() {
    if is_done && [ "${FORCE}" == "false" ]; then
        info "Terraform already applied — skipping (use --force to re-run)"
        return 0
    fi

    step "Running Terraform..."
    if [ ! -d "${SCRIPT_DIR}/terraform" ]; then
        warn "No terraform/ directory — skipping"
        mark_skip "terraform"
        return 0
    fi

    cd "${SCRIPT_DIR}/terraform"
    terraform init -upgrade -backend=false 2>&1 | tail -5
    terraform plan -var-file="${SCRIPT_DIR}/.tfvars" 2>&1 | tail -10

    read -rp "Apply Terraform? (y/N): " confirm
    if [[ "${confirm}" != "y" && "${confirm}" != "Y" ]]; then
        warn "Terraform apply skipped by user"
        mark_skip "terraform"
        return 0
    fi

    if terraform apply -var-file="${SCRIPT_DIR}/.tfvars" -auto-approve 2>&1 | tee -a "${LOGFILE}"; then
        success "Terraform applied"
        mark_done "terraform"
    else
        error "Terraform failed"
        mark_fail "terraform"
        exit 1
    fi
    cd "${SCRIPT_DIR}"
}

# ─── Ansible deploy ───────────────────────────────────────────────
run_ansible() {
    if is_done && [ "${FORCE}" == "false" ]; then
        info "Ansible already run — skipping (use --force to re-run)"
        return 0
    fi

    step "Running Ansible playbook..."
    if [ ! -f "${SCRIPT_DIR}/ansible/playbook.yml" ]; then
        warn "No playbook.yml — skipping"
        mark_skip "ansible"
        return 0
    fi

    cd "${SCRIPT_DIR}/ansible"
    ansible-playbook -i inventory.ini playbook.yml \
        --extra-vars="@group_vars/all.yml" \
        --vault-password-file="${SCRIPT_DIR}/.vault_pass" 2>&1 \
        | tee -a "${LOGFILE}"

    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        success "Ansible playbook completed"
        mark_done "ansible"
    else
        error "Ansible playbook failed"
        mark_fail "ansible"
        exit 1
    fi
    cd "${SCRIPT_DIR}"
}

# ─── Post-deploy ──────────────────────────────────────────────────
run_post_deploy() {
    step "Running post-deploy script..."
    if [ ! -f "${SCRIPT_DIR}/post_deploy.sh" ]; then
        warn "post_deploy.sh not found — skipping"
        mark_skip "post_deploy"
        return 0
    fi

    chmod +x "${SCRIPT_DIR}/post_deploy.sh"
    if "${SCRIPT_DIR}/post_deploy.sh" 2>&1 | tee -a "${LOGFILE}"; then
        success "Post-deploy completed"
        mark_done "post_deploy"
    else
        warn "Post-deploy had warnings — check log"
        mark_fail "post_deploy"
    fi
}

# ─── Load test ────────────────────────────────────────────────────
run_load_test() {
    step "Running load test (scenario 1)..."
    if [ ! -f "${SCRIPT_DIR}/load_test/run_scenario1.sh" ]; then
        warn "run_scenario1.sh not found — skipping"
        mark_skip "load_test"
        return 0
    fi

    chmod +x "${SCRIPT_DIR}/load_test/run_scenario1.sh"
    if "${SCRIPT_DIR}/load_test/run_scenario1.sh" 2>&1 | tee -a "${LOGFILE}"; then
        success "Load test PASSED"
        mark_done "load_test"
        return 0
    else
        warn "Load test FAILED — check components individually"
        mark_fail "load_test"
        return 1
    fi
}

# ─── Telegram notification ────────────────────────────────────────
send_telegram() {
    local token="${TELEGRAM_BOT_TOKEN:-}"
    local chat="${TELEGRAM_CHAT_ID:-}"
    local status="$1"
    local duration="$2"

    if [ -z "${token}" ] || [ -z "${chat}" ]; then
        info "Telegram not configured — skipping notification"
        return 0
    fi

    local msg
    msg="*ACOS Deploy ${status}*\n"
    msg+="Duration: ${duration}\n"
    msg+="Log: ${LOGFILE}\n"
    msg+="State: ${STATEFILE}"

    curl -sf -X POST "https://api.telegram.org/bot${token}/sendMessage" \
        -d "chat_id=${chat}" \
        -d "text=${msg}" \
        -d "parse_mode=Markdown" > /dev/null 2>&1 \
        && success "Telegram notified" \
        || warn "Telegram notification failed"
}

# ─── Generate report ──────────────────────────────────────────────
generate_report() {
    local duration="$1"
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║           DEPLOY REPORT  —  ACOS Cluster            ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    printf "%-20s %-12s %s\n" "STEP" "STATUS" "TIME"
    echo "────────────────────────────────────────────────────"

    if [ -f "${STATEFILE}" ]; then
        jq -r 'to_entries[] | "\(.key)\t\(.value.status)\t\(.value.time // "-")"' "${STATEFILE}" 2>/dev/null \
            | while IFS=$'\t' read -r step status time; do
                local color
                case "${status}" in
                    done)   color="${GREEN}" ;;
                    failed) color="${RED}" ;;
                    skipped) color="${YELLOW}" ;;
                    *)      color="${NC}" ;;
                esac
                printf "%-20s ${color}%-12s${NC} %s\n" "${step}" "${status}" "${time}"
            done
    fi

    echo ""
    echo "Duration: ${duration}"
    echo "Log file: ${LOGFILE}"
    echo "State:    ${STATEFILE}"
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║               VERIFICATION CHECKLIST                 ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "  Run manually:"
    echo "  make verify-full          # Full verification"
    echo "  make verify-components    # Component check"
    echo "  make logs                # View all logs"
    echo "  ./load_test/run_scenario1.sh  # Load test"
    echo ""
    echo "  Check Grafana dashboards:"
    echo "  http://localhost:3001 (or configured HOST:PORT)"
    echo ""
    echo "  Check Prometheus targets:"
    echo "  http://localhost:9090/targets"
    echo ""
}

# ─── Main ─────────────────────────────────────────────────────────
main() {
    local start_time
    start_time=$(date +%s)

    log_init

    echo "╔══════════════════════════════════════════════════════╗"
    echo "║       ACOS Cluster — Deploy & Verify Script          ║"
    echo "║       Force: ${FORCE}                                    ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""

    check_deps
    check_files
    load_env

    step "=== DEPLOY PHASE ==="
    run_terraform || true
    run_ansible   || { error "Ansible failed — aborting"; exit 1; }

    step "=== POST-DEPLOY PHASE ==="
    run_post_deploy
    run_load_test

    local end_time
    end_time=$(date +%s)
    local duration
    duration=$(printf '%02d:%02d:%02d' $(( (end_time - start_time)/3600 )) $(( (end_time - start_time)%3600/60 )) $(( (end_time - start_time)%60 )))

    generate_report "${duration}"

    local final_status="SUCCESS"
    [ -f "${STATEFILE}" ] && jq -e 'to_entries[] | .value.status == "failed"' "${STATEFILE}" > /dev/null 2>&1 && final_status="PARTIAL"

    send_telegram "${final_status}" "${duration}"

    if [ "${final_status}" == "SUCCESS" ]; then
        success "All done! Cluster deployed and verified."
    else
        warn "Deploy completed with some failures — check the report above."
    fi
}

main "$@"
