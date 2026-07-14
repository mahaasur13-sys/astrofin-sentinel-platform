#!/usr/bin/env bash
# Day 2: Base OS setup — Docker, Python, NTP, SSH keys, chrony, UFW
# Idempotent — safe to re-run
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY="${INVENTORY:-$SCRIPT_DIR/../ansible/inventory.ini}"

log() { echo "[$(date '+%H:%M:%S')] $*"; }

echo "=== DAY 2: Base OS Setup ==="

# 1. System packages (Docker, Python, NTP, etc.)
log "[1/6] Installing system packages..."
ansible all -i "$INVENTORY" -m apt -a "
    name=python3,python3-pip,ntp,chrony,openssh-server,ufw,curl,wget,git,htop,net-tools
    state=present
    update_cache=yes
"

# 2. SSH key propagation (passwordless ansible access)
log "[2/6] Propagating SSH public keys..."
ansible all -i "$INVENTORY" -m authorized_key -a "
    user=asur
    key='{{ lookup('file', '/home/asur/.ssh/id_rsa.pub') }}'
"

# 3. Docker installation (Pop!_OS NVIDIA Edition has nvidia-docker support)
log "[3/6] Installing Docker CE..."
ansible all -i "$INVENTORY" -m apt -a "
    name=docker-ce,docker-ce-cli,containerd.io
    state=present
    update_cache=yes
" --extra-vars="docker_ce_channel=stable" 2>/dev/null || \
ansible all -i "$INVENTORY" -m shell -a "
    curl -fsSL https://get.docker.com | sh
"

ansible all -i "$INVENTORY" -m systemd -a "name=docker state=started enabled=yes"

# 4. Python environment for ML/AI
log "[4/6] Setting up Python environment..."
ansible all -i "$INVENTORY" -m shell -a "
    pip3 install --upgrade pip setuptools wheel
    pip3 install numpy pandas torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
"

# 5. NTP / chrony sync across cluster
log "[5/6] Configuring time sync (chrony)..."
ansible all -i "$INVENTORY" -m copy -a "
    content='server 0.pool.ntp.org iburst
server 1.pool.ntp.org iburst
server 2.pool.ntp.org iburst
makestep 1 -1
'
    dest=/etc/chrony/chrony.conf
    mode=0644
    owner=root
"
ansible all -i "$INVENTORY" -m systemd -a "name=chrony state=restarted enabled=yes"

# 6. UFW firewall — permissive inside mesh, deny external
log "[6/6] Configuring UFW firewall..."
ansible all -i "$INVENTORY" -m shell -a "
    ufw --force enable
    ufw allow from 10.66.0.0/16 to any port 22,51820,2379,2380,6379,6817,6800:7300 proto=tcp
    ufw allow from 10.66.0.0/16 to any port 51820 proto=udp
    ufw default deny incoming
"

log "=== DAY 2 COMPLETE ==="
log "Docker version: $(ansible all -i "$INVENTORY" -m shell -a 'docker --version' | grep -oP 'Docker version [^,]+')"
log "Python version: $(ansible all -i "$INVENTORY" -m shell -a 'python3 --version' | grep -oP 'Python [^ ]+')"