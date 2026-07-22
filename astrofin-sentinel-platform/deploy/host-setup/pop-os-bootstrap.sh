#!/usr/bin/env bash
# =============================================================================
# AstroFin Sentinel Platform — Pop!_OS bootstrap
#
# Run as REGULAR user with sudo rights:
#   chmod +x pop-os-bootstrap.sh && ./pop-os-bootstrap.sh
#
# What this does:
#   1. apt update + install: docker.io, docker-compose-v2, git, curl, jq,
#      python3-pip, python3-venv, pipx, build-essential, libpq-dev
#   2. Add current user to 'docker' group
#   3. If GPU: install nvidia-container-toolkit + configure docker runtime
#   4. Generate SSH key for GitHub (if missing) and print public key
#   5. Clone astrofin-sentinel-platform into ~/astrofin-sentinel-platform
#   6. (optional) Create .env from .env.example
#   7. Print next-step summary
#
# Safe to re-run: every step is idempotent.
# =============================================================================
set -uo pipefail

RED=$'\e[31m'; GRN=$'\e[32m'; YEL=$'\e[33m'; BLU=$'\e[34m'; RST=$'\e[0m'
log()  { printf "${BLU}[bootstrap]${RST} %s\n" "$*"; }
ok()   { printf "${GRN}[ok]${RST} %s\n" "$*"; }
warn() { printf "${YEL}[warn]${RST} %s\n" "$*"; }
err()  { printf "${RED}[err]${RST} %s\n" "$*"; }

# Must NOT be root (we need to add current user to docker group, not root)
if [[ $EUID -eq 0 ]]; then
  err "Не запускайте от root. Используйте обычного пользователя с sudo."
  exit 1
fi

# Sudo available?
if ! command -v sudo >/dev/null 2>&1; then
  err "sudo не найден. Установите: apt install sudo"
  exit 1
fi

REPO_DIR="$HOME/astrofin-sentinel-platform"
REPO_URL="git@github.com:mahaasur13-sys/astrofin-sentinel-platform.git"

# ── 1. apt + packages ──────────────────────────────────────────────────────
log "1/7 apt update + install packages"
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
  ca-certificates curl gnupg lsb-release jq make \
  git python3 python3-pip python3-venv pipx build-essential libpq-dev \
  docker.io docker-compose-v2

# Enable + start docker
if ! systemctl is-active --quiet docker; then
  sudo systemctl enable --now docker
fi
ok "docker installed: $(docker --version 2>/dev/null)"

# ── 2. Add user to docker group ────────────────────────────────────────────
log "2/7 user '$USER' → docker group"
if groups "$USER" | grep -qw docker; then
  ok "user уже в группе docker"
else
  sudo usermod -aG docker "$USER"
  warn "добавлены в группу docker — нужно перелогиниться (или newgrp docker)"
fi

# ── 3. NVIDIA Container Toolkit (если есть GPU) ────────────────────────────
log "3/7 NVIDIA Container Toolkit (если GPU)"
if command -v nvidia-smi >/dev/null 2>&1; then
  if ! command -v nvidia-ctk >/dev/null 2>&1; then
    log "устанавливаю nvidia-container-toolkit..."
    # Official NVIDIA repo for Pop!_OS / Ubuntu
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
      | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
      | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
      | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
  fi
  sudo nvidia-ctk runtime configure --runtime=docker
  sudo systemctl restart docker
  ok "NVIDIA Container Toolkit настроен"
  # Test
  if docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
    ok "docker --gpus работает (nvidia-smi из контейнера OK)"
  else
    warn "docker --gpus не работает из контейнера — перелогиньтесь и проверьте"
  fi
else
  ok "GPU не обнаружен — пропускаю NVIDIA toolkit"
fi

# ── 4. SSH key for GitHub ──────────────────────────────────────────────────
log "4/7 SSH key для GitHub"
if [[ -f "$HOME/.ssh/id_ed25519.pub" ]]; then
  ok "SSH ключ уже есть"
elif [[ -f "$HOME/.ssh/id_rsa.pub" ]]; then
  ok "RSA SSH ключ уже есть"
else
  read -r -p "Введите email для SSH-ключа (или Enter для ${USER}@$(hostname)): " email
  email=${email:-${USER}@$(hostname)}
  ssh-keygen -t ed25519 -C "$email" -f "$HOME/.ssh/id_ed25519" -N ""
  (ssh-agent -s >/dev/null 2>&1 &)
  ssh-add "$HOME/.ssh/id_ed25519" 2>/dev/null || true
  ok "ключ создан"
fi

echo ""
echo "${YEL}Добавьте публичный ключ в GitHub:${RST}"
cat "$HOME/.ssh/id_ed25519.pub" 2>/dev/null || cat "$HOME/.ssh/id_rsa.pub"
echo ""
echo "GitHub → Settings → SSH and GPG keys → New SSH key"
echo "(затем нажмите Enter для продолжения)"
read -r -p "[Enter когда добавите] " _
ok "SSH готов"

# ── 5. Test GitHub SSH + clone repo ────────────────────────────────────────
log "5/7 проверяю GitHub SSH..."
if ! ssh -T -o StrictHostKeyChecking=no -o ConnectTimeout=10 git@github.com 2>&1 | grep -q "successfully authenticated"; then
  err "GitHub SSH auth не прошёл. Проверьте, что ключ добавлен в GitHub."
  exit 1
fi
ok "GitHub SSH OK"

log "6/7 клонирую репозиторий"
if [[ -d "$REPO_DIR" ]]; then
  warn "$REPO_DIR уже существует — пропускаю clone"
else
  git clone --recurse-submodules "$REPO_URL" "$REPO_DIR"
  ok "cloned → $REPO_DIR"
fi

# ── 6. .env (если есть .env.example) ───────────────────────────────────────
log "7/7 .env из .env.example"
cd "$REPO_DIR"
if [[ -f .env.example ]] && [[ ! -f .env ]]; then
  cp .env.example .env
  warn "создан .env — откройте и заполните пароли/токены перед docker compose up"
  ok ".env создан"
else
  ok ".env не требуется или уже есть"
fi

# ── Final summary ──────────────────────────────────────────────────────────
echo ""
echo "${GRN}══════════════════════════════════════════════════${RST}"
echo "${GRN} Bootstrap завершён${RST}"
echo "${GRN}══════════════════════════════════════════════════${RST}"
echo ""
echo "Следующие шаги:"
echo "  1. cd $REPO_DIR"
echo "  2. nano .env                  # заполните пароли"
echo "  3. docker compose config --quiet   # валидация"
echo "  4. docker compose up -d            # запуск 7 сервисов"
echo "  5. docker compose ps               # проверить статус"
echo "  6. curl -s http://localhost:8050/health   # app"
echo "  7. curl -s http://localhost:8081/health   # ml-engine"
echo ""
echo "Если что-то не работает — см. docs/docker-live-run.md"
