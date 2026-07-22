#!/usr/bin/env bash
# =============================================================================
# AstroFin Sentinel Platform — pre-flight audit for Pop!_OS host
#
# Run this on the TARGET MACHINE (your desktop), not on the Zo container.
#   chmod +x audit-popos.sh && ./audit-popos.sh
#
# Exit codes:
#   0  all checks green
#   1  at least one critical check failed (blocker)
#   2  warnings only (works, but suboptimal)
# =============================================================================
set -uo pipefail

RED=$'\e[31m'; GRN=$'\e[32m'; YEL=$'\e[33m'; BLU=$'\e[34m'; RST=$'\e[0m'
PASS=0; WARN=0; FAIL=0
declare -a RESULTS=()

check_pass() { PASS=$((PASS+1)); RESULTS+=("PASS  $1"); printf "  ${GRN}✓${RST} %s\n" "$1"; }
check_warn() { WARN=$((WARN+1)); RESULTS+=("WARN  $1 — $2"); printf "  ${YEL}!${RST} %s — %s\n" "$1" "$2"; }
check_fail() { FAIL=$((FAIL+1)); RESULTS+=("FAIL  $1 — $2"); printf "  ${RED}✗${RST} %s — %s\n" "$1" "$2"; }

section() { printf "\n${BLU}▶ %s${RST}\n" "$1"; }

# ── 1. OS ────────────────────────────────────────────────────────────────────
section "1. Operating system"
if [[ -f /etc/os-release ]]; then
  . /etc/os-release
  if [[ "$ID" == "pop" ]]; then
    check_pass "Pop!_OS $VERSION_ID detected"
  elif [[ "$ID" == "ubuntu" ]]; then
    check_warn "Ubuntu $VERSION_ID (not Pop!_OS, but should still work)" "Pop!_OS Ubuntu-based — proceed"
  else
    check_warn "Detected $ID $VERSION_ID (not Pop!_OS)" "Procede solo si basato su Ubuntu/Debian"
  fi
else
  check_fail "OS detection" "/etc/os-release missing — not a Linux distro"
fi

# Kernel version (need 5.x+ for cgroups v2 / docker)
kernel_major=$(uname -r | cut -d. -f1)
if (( kernel_major >= 5 )); then
  check_pass "Kernel $(uname -r)"
else
  check_warn "Kernel $(uname -r)" "older than 5.x — upgrade recommended"
fi

# ── 2. Resources ────────────────────────────────────────────────────────────
section "2. Hardware resources"

# RAM (GB)
ram_gb=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo)
if (( ram_gb >= 16 )); then
  check_pass "RAM: ${ram_gb} GB"
elif (( ram_gb >= 8 )); then
  check_warn "RAM: ${ram_gb} GB" "рекомендуется 16+ GB для полного стека (7 сервисов + БД + Prometheus)"
else
  check_fail "RAM: ${ram_gb} GB" "минимум 8 GB, рекомендуется 16+"
fi

# Disk free on /
disk_free_gb=$(df -BG / | awk 'NR==2 {gsub("G",""); print $4}')
if (( disk_free_gb >= 100 )); then
  check_pass "Disk free: ${disk_free_gb} GB on /"
elif (( disk_free_gb >= 50 )); then
  check_warn "Disk free: ${disk_free_gb} GB" "50 GB — Docker images + Postgres WAL могут съесть быстро"
else
  check_fail "Disk free: ${disk_free_gb} GB" "минимум 50 GB, рекомендуется 100+"
fi

# CPU cores
cpu_cores=$(nproc)
if (( cpu_cores >= 4 )); then
  check_pass "CPU: ${cpu_cores} cores"
else
  check_warn "CPU: ${cpu_cores} cores" "4+ cores рекомендуется"
fi

# ── 3. GPU ──────────────────────────────────────────────────────────────────
section "3. GPU (optional — only for gpu-worker service)"

if command -v nvidia-smi >/dev/null 2>&1; then
  gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
  if [[ -n "$gpu_name" ]]; then
    check_pass "NVIDIA GPU detected: $gpu_name"
    # Driver version
    driver=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader 2>/dev/null | head -1)
    check_pass "NVIDIA driver: $driver"
  else
    check_warn "nvidia-smi present but no GPU enumerated" "проверьте подключение"
  fi
else
  check_warn "No NVIDIA GPU / nvidia-smi missing" "gpu-worker service не запустится — это OK, остальные 6 сервисов работают"
fi

# ── 4. Required tools ───────────────────────────────────────────────────────
section "4. Required command-line tools"

for tool in git curl jq make; do
  if command -v "$tool" >/dev/null 2>&1; then
    check_pass "$tool: $(command -v "$tool")"
  else
    check_fail "$tool missing" "sudo apt install -y $tool"
  fi
done

# ── 5. Docker ───────────────────────────────────────────────────────────────
section "5. Docker Engine + Compose"

if command -v docker >/dev/null 2>&1; then
  docker_ver=$(docker --version 2>/dev/null | awk '{print $3}' | tr -d ',')
  check_pass "docker: $docker_ver"
  # daemon reachable?
  if docker info >/dev/null 2>&1; then
    check_pass "docker daemon reachable"
  else
    check_fail "docker daemon not reachable" "sudo systemctl enable --now docker, затем перелогиниться"
  fi
else
  check_fail "docker missing" "sudo apt install -y docker.io (или см. https://docs.docker.com/engine/install/ubuntu/)"
fi

# Compose (v2 plugin or v1 binary)
if docker compose version >/dev/null 2>&1; then
  compose_ver=$(docker compose version --short 2>/dev/null)
  check_pass "docker compose (v2 plugin): $compose_ver"
elif command -v docker-compose >/dev/null 2>&1; then
  compose_ver=$(docker-compose --version 2>/dev/null | awk '{print $3}' | tr -d ',')
  check_warn "docker-compose v1: $compose_ver" "рекомендуется v2 plugin (sudo apt install docker-compose-v2)"
else
  check_fail "docker compose missing" "sudo apt install docker-compose-v2 (или apt install docker-compose)"
fi

# User in docker group?
if groups "$USER" 2>/dev/null | grep -qw docker; then
  check_pass "user '$USER' in 'docker' group"
else
  check_warn "user '$USER' not in 'docker' group" "sudo usermod -aG docker \$USER && newgrp docker"
fi

# ── 6. NVIDIA Container Toolkit (if GPU present) ────────────────────────────
section "6. NVIDIA Container Toolkit"

if command -v nvidia-smi >/dev/null 2>&1; then
  if command -v nvidia-ctk >/dev/null 2>&1; then
    check_pass "nvidia-ctk: $(nvidia-ctk --version 2>/dev/null | tail -1)"
  else
    check_warn "nvidia-ctk missing" "sudo apt install -y nvidia-container-toolkit && sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker"
  fi
else
  echo "  (skipped — no NVIDIA GPU detected)"
fi

# ── 7. GitHub access ────────────────────────────────────────────────────────
section "7. GitHub access (SSH key)"

if [[ -f "$HOME/.ssh/id_ed25519.pub" ]] || [[ -f "$HOME/.ssh/id_rsa.pub" ]]; then
  if [[ -f "$HOME/.ssh/id_ed25519.pub" ]]; then
    pub="$HOME/.ssh/id_ed25519.pub"
  else
    pub="$HOME/.ssh/id_rsa.pub"
  fi
  fingerprint=$(ssh-keygen -lf "$pub" 2>/dev/null | awk '{print $2}')
  check_pass "SSH public key: $pub (fingerprint $fingerprint)"

  # Test GitHub SSH auth
  if ssh -T -o StrictHostKeyChecking=no -o ConnectTimeout=5 git@github.com 2>&1 | grep -q "successfully authenticated"; then
    check_pass "GitHub SSH auth works"
  else
    check_warn "GitHub SSH auth did not respond 'authenticated'" "проверьте, что ключ добавлен в GitHub → Settings → SSH and GPG keys"
  fi
else
  check_warn "No SSH key found in ~/.ssh" "ssh-keygen -t ed25519 -C 'your@email' (затем добавьте в GitHub)"
fi

# ── 8. Network / DNS ────────────────────────────────────────────────────────
section "8. Network reachability"

if curl -fsS -o /dev/null -m 5 https://github.com 2>/dev/null; then
  check_pass "github.com reachable"
else
  check_fail "github.com unreachable" "проверьте интернет / firewall / proxy"
fi

if curl -fsS -o /dev/null -m 5 https://registry-1.docker.io 2>/dev/null; then
  check_pass "Docker Hub registry reachable"
else
  check_warn "Docker Hub registry unreachable" "docker pull может не работать — нужен mirror или VPN"
fi

# ── 9. Summary ──────────────────────────────────────────────────────────────
section "Summary"
printf "  ${GRN}PASS: %d${RST}  ${YEL}WARN: %d${RST}  ${RED}FAIL: %d${RST}\n\n" "$PASS" "$WARN" "$FAIL"

if (( FAIL > 0 )); then
  echo "Blockers (must fix):"
  printf "  ${RED}✗${RST} %s\n" "${RESULTS[@]}" | grep '^  ✗ FAIL'
  echo ""
  echo "Next: исправьте FAIL-пункты и перезапустите audit."
  exit 1
elif (( WARN > 0 )); then
  echo "Warnings (можно продолжить, но рекомендуется исправить):"
  printf "  ${YEL}!${RST} %s\n" "${RESULTS[@]}" | grep '^  ! WARN'
  echo ""
  echo "Next: можно запускать bootstrap, но учтите WARN-предупреждения."
  exit 2
else
  echo "All green. Можно запускать pop-os-bootstrap.sh."
  exit 0
fi
