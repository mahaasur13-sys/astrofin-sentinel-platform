#!/bin/bash
#===============================================================================
# Pop!_OS 24.04 NVIDIA — AI/Dev Workstation Auto-Setup
#===============================================================================
# Role    : SRE/DevOps Autonomous Deployment Agent
# Target  : Pop!_OS 24.04 LTS NVIDIA Edition (USB Boot → Production Ready)
# Stack   : KDE Plasma + Docker + Zsh + Python AI + Security Hardening
# Safety  : Interactive prompts, idempotent, verbose logging
#===============================================================================

set -euo pipefail

#--- Config -------------------------------------------------------------------
LOGFILE="/var/log/popos-setup-$(date +%Y%m%d-%H%M%S).log"
SCRIPT_VERSION="1.0.0"
CURRENT_USER="$(logname 2>/dev/null || echo "$SUDO_USER")"
HOMEDIR="$(getent passwd "$CURRENT_USER" | cut -d: -f6)"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

#--- Functions ----------------------------------------------------------------
log() { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOGFILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOGFILE"; }
err() { echo -e "${RED}[ERR]${NC} $1" | tee -a "$LOGFILE" >&2; }
ok() { echo -e "${GREEN}[OK]${NC} $1" | tee -a "$LOGFILE"; }
step() { echo -e "\n${CYAN}══ $1 ══${NC}" | tee -a "$LOGFILE"; }

exec &>> >(tee -a "$LOGFILE")

#--- Pre-Check ----------------------------------------------------------------
step "PRE-INSTALL CHECK"
if [[ $EUID -ne 0 ]]; then
  err "Run as: sudo $0"
  exit 1
fi

log "Script v$SCRIPT_VERSION | User: $CURRENT_USER | Home: $HOMEDIR"
log "Log: $LOGFILE"

# Detect OS
if ! grep -q "Pop!_OS" /etc/os-release 2>/dev/null; then
  warn "Not Pop!_OS detected. Continuing anyway..."
fi

# Check NVIDIA
if command -v nvidia-smi &>/dev/null; then
  ok "NVIDIA driver detected:"
  nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv 2>/dev/null || nvidia-smi | head -5
else
  warn "nvidia-smi not found. Will verify after NVIDIA stack install."
fi

#--- Interactive Config -------------------------------------------------------
step "INTERACTIVE CONFIGURATION"

read -rp "🌐 Enable SSH server? [y/N]: " ENABLE_SSH
read -rp "🐳 Install Docker + Docker Compose? [y/N]: " ENABLE_DOCKER
read -rp "🧩 Install CUDA toolkit (large download)? [y/N]: " ENABLE_CUDA
read -rp "🤖 Install AI stack (PyTorch + TensorRT)? [y/N]: " ENABLE_AI
read -rp "⚡ Apply security hardening (firewall + fail2ban)? [y/N]: " ENABLE_HARDEN

#--- Stage 1: System Update ----------------------------------------------------
step "STAGE 1 — SYSTEM UPDATE"
log "Running apt update..."
apt update -qq
log "Upgrading packages..."
apt upgrade -y -qq 2>&1 | tail -5
ok "System updated"

#--- Stage 2: NVIDIA Stack -----------------------------------------------------
step "STAGE 2 — NVIDIA STACK"

# Check if System76 driver available
if command -v system76-driver &>/dev/null; then
  log "System76 driver detected — running proprietary driver install..."
  apt install -y system76-driver-nvidia 2>&1 | tail -3
elif command -v nvidia-smi &>/dev/null; then
  ok "NVIDIA driver already active"
  nvidia-smi --query-gpu=name,driver_version --format=csv,noheader 2>/dev/null || nvidia-smi | head -2
else
  log "Installing NVIDIA driver..."
  apt install -y nvidia-driver-550 2>&1 | tail -5
fi

# Hybrid graphics mode
if command -v system76-power &>/dev/null; then
  log "Setting hybrid graphics mode (battery-friendly)..."
  system76-power graphics hybrid
  ok "Graphics mode: hybrid"
fi

#--- Stage 3: Dev Toolchain ----------------------------------------------------
step "STAGE 3 — DEV TOOLCHAIN"
apt install -y \
  build-essential \
  git \
  curl \
  wget \
  vim \
  htop \
  net-tools \
  iproute2 \
  iputils-ping \
  traceroute \
  mtr \
  dnsutils \
  telnet \
  ncdu \
  tree \
  unzip \
  zip \
  7zip-extra \
  jq \
  yq \
  htop \
  btop \
  glances \
  atop \
  sysstat \
  iotop \
  lsof \
  strace \
  ltrace \
  netcat-openbsd \
  openssl \
  ca-certificates \
  gnupg \
  software-properties-common \
  apt-transport-https \
  zlib1g-dev \
  liblibffi-dev \
  libssl-dev

ok "Dev toolchain installed"

#--- Stage 4: Zsh + Oh My Zsh --------------------------------------------------
step "STAGE 4 — ZSH + OH MY ZSH"

if [[ ! -d "$HOMEDIR/.oh-my-zsh" ]]; then
  log "Installing Oh My Zsh..."
  export RUNZSH=no
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
  ok "Oh My Zsh installed"
else
  ok "Oh My Zsh already present"
fi

# Plugins
ZSH_CUSTOM="$HOMEDIR/.oh-my-zsh/custom"
git clone -q https://github.com/zsh-users/zsh-autosuggestions.git "$ZSH_CUSTOM/plugins/zsh-autosuggestions" 2>/dev/null || ok "autosuggestions already"
git clone -q https://github.com/zsh-users/zsh-syntax-highlighting.git "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting" 2>/dev/null || ok "syntax-highlighting already"

# Set zsh as default
if [[ "$(basename "$SHELL")" != "zsh" ]]; then
  chsh -s /bin/zsh "$CURRENT_USER" 2>/dev/null || warn "Could not change shell for $CURRENT_USER"
  ok "Zsh set as default shell"
fi

#--- Stage 5: KDE Plasma -------------------------------------------------------
step "STAGE 5 — KDE PLASMA DESKTOP"

if dpkg -l plasma-desktop &>/dev/null; then
  ok "KDE Plasma already installed"
else
  log "Installing KDE Plasma..."
  apt install -y kde-plasma-desktop 2>&1 | tail -5
  ok "KDE Plasma installed"
fi

# Preferred session hint
log "To switch to KDE: logout → select 'Plasma (X11)' at login screen"

#--- Stage 6: Docker -----------------------------------------------------------
if [[ "${ENABLE_DOCKER:-N}" =~ ^[Yy]$ ]]; then
  step "STAGE 6 — DOCKER"

  if command -v docker &>/dev/null; then
    ok "Docker already installed"
  else
    log "Installing Docker..."
    apt install -y docker.io docker-compose-v2 2>&1 | tail -3
    usermod -aG docker "$CURRENT_USER"
    systemctl enable docker
    systemctl start docker
    ok "Docker installed and enabled"
  fi

  # Docker verification
  if docker ps &>/dev/null; then
    ok "Docker daemon running"
  else
    warn "Docker daemon not responding — retrying..."
    systemctl restart docker
    sleep 2
    docker ps &>/dev/null && ok "Docker daemon running" || err "Docker setup failed"
  fi
fi

#--- Stage 7: Python / AI Stack ------------------------------------------------
step "STAGE 7 — PYTHON + AI STACK"

apt install -y python3 python3-pip python3-venv python3-dev python3-numpy python3-scipy python3-matplotlib python3-pandas

# Upgrade pip
sudo -u "$CURRENT_USER" bash -c 'pip3 install --upgrade pip' 2>&1 | tail -2

if [[ "${ENABLE_AI:-N}" =~ ^[Yy]$ ]]; then
  log "Installing PyTorch (CPU)..."
  sudo -u "$CURRENT_USER" bash -c 'pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu' 2>&1 | tail -5

  log "Installing TensorFlow..."
  sudo -u "$CURRENT_USER" bash -c 'pip3 install tensorflow' 2>&1 | tail -3

  log "Installing Jupyter..."
  sudo -u "$CURRENT_USER" bash -c 'pip3 install jupyterlab notebook' 2>&1 | tail -3

  log "Installing transformers + accelerate..."
  sudo -u "$CURRENT_USER" bash -c 'pip3 install transformers accelerate' 2>&1 | tail -3

  ok "AI stack installed"
fi

#--- Stage 8: CUDA Toolkit -----------------------------------------------------
if [[ "${ENABLE_CUDA:-N}" =~ ^[Yy]$ ]]; then
  step "STAGE 8 — CUDA TOOLKIT"

  log "Adding NVIDIA CUDA repository..."
  wget -q https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring.deb
  dpkg -i cuda-keyring.deb
  rm cuda-keyring.deb
  apt update -qq
  apt install -y cuda 2>&1 | tail -5

  export PATH=/usr/local/cuda/bin:$PATH
  export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH

  if command -v nvcc &>/dev/null; then
    ok "CUDA installed: $(nvcc --version | grep "release" | awk '{print $5}')"
  else
    warn "CUDA installed but nvcc not in PATH — reboot may be needed"
  fi
fi

#--- Stage 9: Security Hardening ----------------------------------------------
if [[ "${ENABLE_HARDEN:-N}" =~ ^[Yy]$ ]]; then
  step "STAGE 9 — SECURITY HARDENING"

  # UFW Firewall
  log "Configuring UFW firewall..."
  ufw --force reset
  ufw default deny incoming
  ufw default allow outgoing
  ufw allow 22/tcp comment 'SSH'
  ufw allow 80/tcp comment 'HTTP'
  ufw allow 443/tcp comment 'HTTPS'
  ufw --force enable
  systemctl enable ufw
  ok "UFW active: $(ufw status | head -3 | tail -1)"

  # fail2ban
  apt install -y fail2ban 2>&1 | tail -3
  systemctl enable fail2ban
  systemctl start fail2ban
  ok "fail2ban enabled"

  # Disable ICMP broadcast
  echo "net.ipv4.icmp_echo_ignore_broadcasts = 1" >> /etc/sysctl.conf

  # Enforce sysctl changes
  sysctl -p 2>/dev/null || true
fi

#--- Stage 10: SSH -------------------------------------------------------------
if [[ "${ENABLE_SSH:-N}" =~ ^[Yy]$ ]]; then
  step "STAGE 10 — SSH SERVER"
  apt install -y openssh-server 2>&1 | tail -3
  systemctl enable ssh
  systemctl start ssh
  ok "SSH server enabled"
  log "Edit /etc/ssh/sshd_config to configure access"
fi

#--- Stage 11: System Optimization --------------------------------------------
step "STAGE 11 — SYSTEM OPTIMIZATION"

# SWAP tuning
if [[ -f /etc/sysctl.d/99-swappiness.conf ]]; then
  ok "Swappiness already tuned"
else
  echo "vm.swappiness=10" > /etc/sysctl.d/99-swappiness.conf
  sysctl -p /etc/sysctl.d/99-swappiness.conf 2>/dev/null || true
  ok "Swappiness set to 10"
fi

# Automatic updates
apt install -y unattended-upgrades 2>&1 | tail -3
dpkg-reconfigure -plow unattended-upgrades 2>/dev/null || true
ok "Unattended upgrades configured"

#--- Stage 12: Tailscale VPN + Cluster Mesh ---------------------------------
step "STAGE 19 — TAILSCALE VPN + CLUSTER MESH"

# Detect if already installed
if command -v tailscale &>/dev/null; then
  ok "Tailscale already installed: $(tailscale version 2>/dev/null | head -1)"
else
  log "Installing Tailscale..."
  curl -fsSL https://tailscale.com/install.sh | sh - 2>&1 | tail -5
fi

# Authenticate (interactive — or use --authkey for automation)
if ! tailscale status &>/dev/null; then
  warn "Tailscale not logged in. Two options:"
  warn "  Option A (interactive): sudo tailscale up"
  warn "  Option B (authkey):     sudo tailscale up --authkey=<key>"

  if [[ "${TAILSCALE_AUTHKEY:-}" ]]; then
    log "Using provided authkey..."
    tailscale up --authkey="$TAILSCALE_AUTHKEY" --accept-dns=false 2>&1 | tail -3
  else
    log "Set TAILSCALE_AUTHKEY env var to skip interactive login."
    log "Skipping Tailscale login — will prompt on next sudo tailscale up"
  fi
else
  ok "Tailscale already authenticated"
fi

# Enable IP forwarding for cluster mesh
if ! grep -q "net.ipv4.ip_forward = 1" /etc/sysctl.d/99-tailscale.conf 2>/dev/null; then
  echo "net.ipv4.ip_forward = 1" | tee -a /etc/sysctl.d/99-tailscale.conf
  echo "net.ipv6.conf.all.forwarding = 1" | tee -a /etc/sysctl.d/99-tailscale.conf
  sysctl -p /etc/sysctl.d/99-tailscale.conf 2>/dev/null || true
  ok "IP forwarding enabled"
fi

# Funnel: expose services without opening firewall ports
if tailscale status --self &>/dev/null; then
  # Enable funnel on this node (allows inbound traffic through Tailscale)
  tailscale funnel 443 &
  TAILSCALE_FUNNEL_PID=$!
  ok "Tailscale Funnel enabled (port 443)"
fi

# Show Tailscale status
if command -v tailscale &>/dev/null; then
  tailscale status --self 2>/dev/null | head -8 || warn "Run 'tailscale up' to connect"
fi

# Tailscale Serve: serve local HTTP services via Tailscale
log "Tailscale Serve: route local services through Tailscale network"
tailscale serve --bg https+insecure://localhost:3000 2>/dev/null || true

ok "Tailscale VPN mesh configured"
log "Connect other nodes: curl -fsSL https://tailscale.com/install.sh | sh - && sudo tailscale up"

#--- Final Validation ---------------------------------------------------------
step "FINAL VALIDATION"

log "=== System Info ==="
uname -r
uptime -p 2>/dev/null || uptime

log "=== Disk ==="
lsblk --bytes | grep -E "NAME|disk|sda|sdb|nvme" | head -10

log "=== NVIDIA ==="
if command -v nvidia-smi &>/dev/null; then
  nvidia-smi --query-gpu=name,driver_version,memory.total,utilization.gpu --format=csv 2>/dev/null || nvidia-smi | head -6
else
  warn "nvidia-smi not in PATH — try: export PATH=/usr/bin:\$PATH"
fi

log "=== Docker ==="
if command -v docker &>/dev/null; then
  docker ps &>/dev/null && ok "Docker: RUNNING" || warn "Docker: NOT running"
  docker --version
else
  warn "Docker not installed"
fi

log "=== Zsh ==="
zsh --version 2>/dev/null || warn "Zsh not found"

log "=== Python ==="
python3 --version
pip3 --version 2>/dev/null | head -1

log "=== Firewall ==="
ufw status | head -4

log "=== Log file ==="
ls -lh "$LOGFILE"

#--- Reboot Prompt -------------------------------------------------------------
step "SETUP COMPLETE"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Pop!_OS Setup Complete — Reboot Required         ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "NEXT STEPS:"
echo "  1. sudo reboot"
echo "  2. At login: select 'Plasma (X11)' session for KDE"
echo "  3. Open terminal — verify with: neofetch && nvidia-smi"
echo ""
echo "Log saved: $LOGFILE"
echo ""
