#!/bin/bash
#===============================================================================
# Pop!_OS 24.04 NVIDIA — AI/Dev Workstation Auto-Setup v1.7
#===============================================================================
# Target  : Pop!_OS 24.04 LTS NVIDIA Edition (USB Boot → Production Ready)
# Stack   : KDE + Docker + CUDA + k3s + Longhorn + Rook Ceph + MinIO + Zsh + AI Stack + Neovim
# Author  : asurdev | https://asurdev.zo.computer
# Version : 1.7 (Neovim + LazyVim Full AI/K8s)
#===============================================================================

set -euo pipefail

LOGFILE="/var/log/popos-setup-$(date +%Y%m%d-%H%M%S).log"
SCRIPT_VERSION="1.7"
CURRENT_USER="$(logname 2>/dev/null || echo "$SUDO_USER")"
HOMEDIR="$(getent passwd "$CURRENT_USER" | cut -d: -f6)"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

log()    { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOGFILE"; }
logOk()  { echo -e "${GREEN}[OK]${NC} $1" | tee -a "$LOGFILE"; }
logWarn(){ echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOGFILE"; }
logErr() { echo -e "${RED}[ERR]${NC} $1" | tee -a "$LOGFILE"; exit 1; }

check_root() {
    [[ $EUID -ne 0 ]] && logErr "Run as root: sudo bash $0"
}

gpu_check() {
    nvidia-smi &>/dev/null && nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>/dev/null
}

#===============================================================================
# STAGE 1 — Preflight Checks
#===============================================================================
stage1_preflight() {
    log "=== STAGE 1: Preflight ==="
    source /etc/os-release 2>/dev/null || true
    log "OS: $PRETTY_NAME"
    gpu_check && logOk "NVIDIA GPU: $(gpu_check)" || logWarn "GPU not detected"
    ping -c1 -W2 8.8.8.8 &>/dev/null && logOk "Network: OK" || logWarn "Network: UNREACHABLE"
    [[ -d /sys/firmware/efi ]] && log "Boot: UEFI" || log "Boot: Legacy"
    log "User: $CURRENT_USER | Home: $HOMEDIR"
}

#===============================================================================
# STAGE 2 — System Update
#===============================================================================
stage2_update() {
    log "=== STAGE 2: Update ==="
    export DEBIAN_FRONTEND=noninteractive
    apt update -qq
    apt upgrade -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" 2>&1 | tail -3
    logOk "System updated"
}

#===============================================================================
# STAGE 3 — NVIDIA Driver
#===============================================================================
stage3_nvidia() {
    log "=== STAGE 3: NVIDIA Driver ==="
    if gpu_check &>/dev/null; then
        logOk "NVIDIA driver already active"
        return 0
    fi
    if command -v system76-power &>/dev/null; then
        system76-power graphics nvidia 2>&1 | tail -2 || true
        logOk "Switched to NVIDIA mode"
    else
        apt install -y nvidia-driver-555 2>&1 | tail -3
        logOk "NVIDIA driver installed"
    fi
    logWarn "REBOOT REQUIRED"
}

#===============================================================================
# STAGE 4 — CUDA Toolkit + cuDNN (NEW v1.1)
#===============================================================================
stage4_cuda() {
    log "=== STAGE 4: CUDA Toolkit + cuDNN ==="
    if command -v nvcc &>/dev/null; then
        logOk "CUDA already: $(nvcc --version | grep release | awk '{print $5}' | tr -d ',')"
        return 0
    fi
    if apt-cache show system76-cuda-latest &>/dev/null 2>&1; then
        log "Installing system76-cuda-latest..."
        apt install -y system76-cuda-latest system76-cudnn-latest 2>&1 | tail -5
    else
        log "Installing CUDA via NVIDIA repo..."
        wget -qO /tmp/cuda-keyring.deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring.deb
        apt install -y /tmp/cuda-keyring.deb 2>&1 | tail -2
        rm -f /tmp/cuda-keyring.deb
        echo "deb [signed-by=/usr/share/keyrings/cuda-archive-keyring.gpg] http://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/ /" > /etc/apt/sources.list.d/cuda.list
        apt update -qq
        apt install -y cuda-toolkit-12-4 cuda-libraries-12-4 libcudnn9 libcudnn9-dev 2>&1 | tail -5
    fi
    if command -v nvcc &>/dev/null; then
        logOk "CUDA: $(nvcc --version | grep release | awk '{print $5}' | tr -d ',')"
    else
        logWarn "nvcc not in PATH — add to ~/.bashrc:"
        logWarn "  export PATH=/usr/local/cuda/bin:\$PATH"
    fi
}

#===============================================================================
# STAGE 5 — Docker CE + NVIDIA Container Toolkit (NEW v1.1)
#===============================================================================
stage5_docker() {
    log "=== STAGE 5: Docker + NVIDIA Container Toolkit ==="
    if ! command -v docker &>/dev/null; then
        apt install -y apt-transport-https ca-certificates gnupg lsb-release 2>&1 | tail -2
        mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg 2>/dev/null
        . /etc/os-release
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $VERSION_CODENAME stable" > /etc/apt/sources.list.d/docker.list
        apt update -qq
        apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin 2>&1 | tail -3
        systemctl enable docker --now
        logOk "Docker CE installed"
    else
        logOk "Docker already present"
    fi
    # NVIDIA Container Toolkit
    if ! command -v nvidia-ctk &>/dev/null; then
        log "Installing NVIDIA Container Toolkit..."
        curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg 2>/dev/null
        ARCH=$(dpkg --print-architecture)
        echo "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/stable/deb/$ARCH /" > /etc/apt/sources.list.d/nvidia-container-toolkit.list
        apt update -qq
        apt install -y nvidia-container-toolkit 2>&1 | tail -3
        nvidia-ctk runtime configure --runtime=containerd 2>/dev/null || true
        systemctl restart containerd
    fi
    # Test GPU passthrough
    if docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu24.04 nvidia-smi &>/dev/null; then
        logOk "Docker GPU passthrough: OK"
    else
        logWarn "Docker GPU test: FAILED (may need reboot)"
    fi
    usermod -aG docker "$CURRENT_USER" 2>/dev/null || true
}

#===============================================================================
# STAGE 6 — k3s + NVIDIA Device Plugin (NEW v1.1)
#===============================================================================
stage6_k3s() {
    log "=== STAGE 6: k3s + NVIDIA Device Plugin ==="
    if command -v k3s &>/dev/null; then
        logOk "k3s already installed"
        return 0
    fi
    log "Installing k3s..."
    curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--write-kubeconfig-mode 644 --node-label gpu=nvidia" sh - 2>&1 | tail -5
    systemctl enable k3s --now
    sleep 5
    if kubectl get nodes &>/dev/null; then
        logOk "k3s: $(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')"
    else
        logWarn "k3s installed, kubectl may need env export"
    fi
    # NVIDIA Device Plugin
    kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.5/nvidia-device-plugin.yml 2>/dev/null || logWarn "k8s-device-plugin: apply failed"
}

#===============================================================================
# STAGE 7 — Dev Toolchain
#===============================================================================
stage7_devtools() {
    log "=== STAGE 7: Dev Toolchain ==="
    apt install -y build-essential git curl wget vim htop btop tmux zsh fontconfig fonts-jetbrains-mono python3 python3-pip python3-venv python3-dev python3-numpy python3-pandas libopenblas-dev jq bat exa fzf ripgrep fd-find 2>&1 | tail -5
    if [[ ! -d "$HOMEDIR/.pyenv" ]]; then
        curl https://pyenv.run | bash 2>&1 | tail -3
    fi
    logOk "Dev tools installed"
}

#===============================================================================
# STAGE 8 — Zsh + Oh My Zsh
#===============================================================================
stage8_zsh() {
    log "=== STAGE 8: Zsh ==="
    if [[ -d "$HOMEDIR/.oh-my-zsh" ]]; then
        logOk "Oh My Zsh present"
    else
        export SHELL=/bin/zsh
        sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended 2>&1 || true
        logOk "Oh My Zsh installed"
    fi
    zsh_custom="$HOMEDIR/.oh-my-zsh/custom/plugins"
    [[ -d "$zsh_custom/plugins/zsh-autosuggestions" ]] || git clone --depth1 https://github.com/zsh-users/zsh-autosuggestions "$zsh_custom/plugins/zsh-autosuggestions" 2>/dev/null || true
    [[ -d "$zsh_custom/plugins/zsh-syntax-highlighting" ]] || git clone --depth1 https://github.com/zsh-users/zsh-syntax-highlighting "$zsh_custom/plugins/zsh-syntax-highlighting" 2>/dev/null || true
    cat >> "$HOMEDIR/.zshrc" 2>/dev/null <<'EOF'

# --- Pop!_OS AI Dev v1.1 ---
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
alias nvidia-test='docker run --rm --gpus all nvidia/cuda:12.4.0-base nvidia-smi'
alias k9s='kubectl get pods -A'
EOF
    logOk "Zsh configured"
}

#===============================================================================
# STAGE 9 — Security Hardening + Unattended Upgrades (v1.1 UPDATE)
#===============================================================================
stage9_security() {
    log "=== STAGE 9: Security ==="
    if ! command -v ufw &>/dev/null; then apt install -y ufw 2>&1 | tail -2; fi
    ufw --force disable; ufw --force enable
    ufw default deny incoming; ufw default allow outgoing
    ufw allow ssh; ufw allow 22/tcp; ufw logging off
    logOk "UFW active"
    apt install -y fail2ban 2>&1 | tail -2
    systemctl enable fail2ban --now
    logOk "Fail2ban active"
    # Unattended security upgrades
    if ! dpkg -l unattended-upgrades &>/dev/null; then
        apt install -y unattended-upgrades apt-listchanges 2>&1 | tail -2
        cat > /etc/apt/apt.conf.d/51unattended-upgrades <<'UPGRADE_EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Download-Upgradeable-Packages "1";
APT::Periodic::AutocleanInterval "7";
APT::Periodic::Unattended-Upgrade "1";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
UPGRADE_EOF
        logOk "Unattended security upgrades configured"
    fi
    # Sysctl hardening
    cat >> /etc/sysctl.d/99-security.conf <<'SYSCTL_EOF'
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.icmp_ignore_bogus_error_responses = 1
SYSCTL_EOF
    sysctl -p /etc/sysctl.d/99-security.conf 2>/dev/null || true
}

#===============================================================================
# STAGE 10 — AI Stack (PyTorch + Transformers + Gradio)
#===============================================================================
stage10_ai() {
    log "=== STAGE 10: AI Stack ==="
    pip3 install --break-system-packages jupyter numpy pandas matplotlib seaborn scikit-learn torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124 2>&1 | tail -5
    pip3 install --break-system-packages transformers datasets peft accelerate sentence-transformers gradio langchain langchain-community 2>&1 | tail -5
    logOk "AI stack installed"
}

#===============================================================================
# STAGE 11 — GPU Monitoring (NEW v1.1)
#===============================================================================
stage11_monitoring() {
    log "=== STAGE 11: GPU Monitoring ==="
    apt install -y nvtop dcgm prometheus-node-exporter 2>&1 | tail -3
    systemctl enable prometheus-node-exporter --now 2>/dev/null || true
    logOk "Monitoring: nvtop, DCGM, node-exporter ready"
}

#===============================================================================
# STAGE 12 — KDE Customization
#===============================================================================
stage12_kde() {
    log "=== STAGE 12: KDE ==="
    apt install -y ark dolphin konsole kate spectacle plasma-workspace breeze-gtk-theme kvantum latte-dock 2>&1 | tail -3
    logOk "KDE Plasma customized"
}

#===============================================================================
# STAGE 13 — Tailscale VPN (Remote Access)
#===============================================================================
stage13_tailscale() {
    log "=== STAGE 13: Tailscale VPN ==="

    # Check if already installed
    if command -v tailscale &>/dev/null; then
        logOk "Tailscale already installed: $(tailscale --version 2>/dev/null)"
        if tailscale status --self &>/dev/null; then
            logOk "Tailscale active: $(tailscale ip -4 2>/dev/null)"
        else
            logWarn "Tailscale not connected — run: tailscale up"
        fi
        return 0
    fi

    # Install Tailscale
    log "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh 2>&1 | tail -5

    # Configure with authkey if provided via env
    if [[ -n "${TAILSCALE_AUTHKEY:-}" ]]; then
        tailscale up \
            --authkey "$TAILSCALE_AUTHKEY" \
            --hostname "$(hostname)-ai-gpu" \
            --advertise-tags "tag:ai-cluster" \
            --ssh 2>&1 | tee -a "$LOGFILE"
        logOk "Tailscale connected as $(hostname)-ai-gpu"
    else
        logWarn "TAILSCALE_AUTHKEY not set"
        echo "  To connect manually:"
        echo "    tailscale up --hostname $(hostname)-ai-gpu"
        echo "  Or set env before running: export TAILSCALE_AUTHKEY=tskey-auth-..."
    fi

    # Enable and start
    systemctl enable --now tailscaled 2>/dev/null || true

    # Optional: expose k3s API via Tailscale
    if command -v k3s &>/dev/null && tailscale status --self &>/dev/null; then
        echo "  k3s kubeconfig available at: /etc/rancher/k3s/k3s.yaml"
        echo "  Tailscale IP for cluster management: $(tailscale ip -4 2>/dev/null)"
    fi

    logOk "Tailscale ready"
}

#===============================================================================
# STAGE 14 — k3s Multi-Node Support (v1.3 NEW)
#===============================================================================
stage14_k3s_multinode() {
    log "=== STAGE 14: k3s Multi-Node ==="

    local role="${K3S_ROLE:-auto}"
    local join_token_file="/var/lib/k3s/server/node-token"
    local agent_token_file="/var/lib/k3s/agent/node-token"
    local token_dest="/var/lib/k3s/join-token-$(hostname).txt"

    # Detect role
    if [[ "$role" == "auto" ]]; then
        if [[ -f "$join_token_file" ]]; then
            role="server"
            log "Role: SERVER (token found — this node is already primary)"
        elif systemctl is-active --quiet k3s; then
            role="server"
            log "Role: SERVER (k3s already running)"
        else
            role="agent"
            log "Role: AGENT (will join existing cluster)"
        fi
    fi

    log "Selected role: $role | K3S_ROLE='$role'"

    # --SERVER mode--
    if [[ "$role" == "server" ]]; then
        if systemctl is-active --quiet k3s; then
            logOk "k3s server already running"
            kubectl get nodes -o wide 2>/dev/null || logWarn "kubectl not ready yet"
        else
            log "Installing k3s as SERVER..."
            local external_ip=""
            if command -v tailscale &>/dev/null && tailscale status --self &>/dev/null; then
                external_ip=$(tailscale ip -4 2>/dev/null)
                log "Using Tailscale external IP: $external_ip"
            fi
            curl -sfL https://get.k3s.io | \
                INSTALL_K3S_EXEC="--write-kubeconfig-mode 644 --node-label node-role.kubernetes.io/server=true --node-label gpu=nvidia ${external_ip:+--node-external-ip $external_ip}" \
                sh - 2>&1 | tail -5
            systemctl enable --now k3s
            sleep 5
        fi

        # Generate join token for agents
        if [[ -f "$join_token_file" ]]; then
            local server_ip="127.0.0.1"
            if command -v tailscale &>/dev/null && tailscale status --self &>/dev/null; then
                server_ip=$(tailscale ip -4 2>/dev/null)
            fi
            local token_content="$(cat "$join_token_file")"
            echo -e "K3S_URL=https://$server_ip:6443\nK3S_TOKEN=$token_content" > "$token_dest"
            chmod 600 "$token_dest"
            logOk "Join token saved to: $token_dest"
            log "On agent nodes, run:"
            echo "  export K3S_URL=https://$server_ip:6443"
            echo "  export K3S_TOKEN=$token_content"
            echo "  curl -sfL https://get.k3s.io | sh -"
        fi

        # Label existing nodes
        kubectl label nodes --all nvidia.com/gpu=true --overwrite 2>/dev/null || true
        kubectl label nodes --all node-role.kubernetes.io/server=true --overwrite 2>/dev/null || true

    # --AGENT mode--
    elif [[ "$role" == "agent" ]]; then
        local k3s_url="${K3S_URL:-}"
        local k3s_token="${K3S_TOKEN:-}"

        if [[ -z "$k3s_url" || -z "$k3s_token" ]]; then
            logErr "AGENT mode requires K3S_URL and K3S_TOKEN env vars or $token_dest"
        fi

        if systemctl is-active --quiet k3s-agent 2>/dev/null; then
            logOk "k3s agent already running"
        else
            log "Joining cluster as AGENT..."
            local external_ip=""
            if command -v tailscale &>/dev/null && tailscale status --self &>/dev/null; then
                external_ip=$(tailscale ip -4 2>/dev/null)
                log "Using Tailscale external IP: $external_ip"
            fi
            curl -sfL https://get.k3s.io | \
                K3S_URL="$k3s_url" \
                K3S_TOKEN="$k3s_token" \
                INSTALL_K3S_EXEC="--node-label gpu=nvidia ${external_ip:+--node-external-ip $external_ip}" \
                sh - 2>&1 | tail -5
            systemctl enable --now k3s-agent
            sleep 5
        fi

        # Label this agent
        local hostname_fqdn="$(hostname)"
        kubectl label node "$hostname_fqdn" nvidia.com/gpu=true --overwrite 2>/dev/null || \
            logWarn "Could not label node (may not be ready yet)"
    fi

    # Verification
    log "=== Cluster Status ==="
    kubectl get nodes -o wide 2>/dev/null || logWarn "kubectl not ready — try again in 30s"
    kubectl get nodes -o jsonpath='{.items[*].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null && echo "" || true

    logOk "Stage 14 complete"
}

#===============================================================================
# STAGE 15 — Longhorn Storage (v1.4 NEW)
#===============================================================================
stage15_longhorn() {
    log "=== STAGE 15: Longhorn Storage ==="

    # Check prerequisites
    if ! command -v kubectl &>/dev/null; then
        logErr "kubectl not found — run stage6 first"
    fi

    # Check if Longhorn already installed
    if kubectl get pods -n longhorn-system --no-headers 2>/dev/null | grep -q .; then
        logOk "Longhorn already installed"
        kubectl get pods -n longhorn-system 2>/dev/null | tail -5
        return 0
    fi

    # Install Helm if not present
    if ! command -v helm &>/dev/null; then
        log "Installing Helm..."
        curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash 2>&1 | tail -3
        logOk "Helm installed"
    fi

    # Add Longhorn repo
    log "Adding Longhorn Helm repo..."
    helm repo add longhorn https://charts.longhorn.io 2>/dev/null || true
    helm repo update 2>&1 | tail -2

    # Count nodes for replica settings
    local node_count
    node_count=$(kubectl get nodes --no-headers 2>/dev/null | wc -l)
    local replica_count=2
    if [[ "$node_count" -ge 3 ]]; then
        replica_count=3
    fi
    log "Node count: $node_count | replicaCount: $replica_count"

    # Install Longhorn with sensible defaults for home cluster
    log "Installing Longhorn..."
    helm upgrade --install longhorn longhorn/longhorn \
        --namespace longhorn-system \
        --create-namespace \
        --set defaultClass=true \
        --set defaultClassReplicaCount=$replica_count \
        --set storageNetwork=false \
        --set ingress.enabled=false \
        --set service.ui.type=NodePort \
        --set service.ui.nodePort=30800 \
        --set persistence.defaultVolumeReconcileWaitInterval=30 \
        --set csi.attacherReplicaCount=1 \
        --set csi.provisionerReplicaCount=1 \
        --set csi.resizerReplicaCount=1 \
        --set csi.snapshotterReplicaCount=1 \
        --set topologyBasedScheduling=true \
        --set orphanPodsDeletion=true \
        --set orphanPodsDeletionWaitInterval=30 \
        --timeout 5m 2>&1 | tail -8

    # Wait for Longhorn to be ready
    log "Waiting for Longhorn to initialize (60s)..."
    sleep 60

    # Verify deployment
    local longhorn_pods
    longhorn_pods=$(kubectl get pods -n longhorn-system --no-headers 2>/dev/null | grep -v "Running\|Completed" | wc -l)
    if [[ "$longhorn_pods" -eq 0 ]]; then
        logOk "Longhorn deployed successfully"
    else
        logWarn "Longhorn may still be starting — check: kubectl get pods -n longhorn-system"
    fi

    # Show status
    kubectl get pods -n longhorn-system 2>/dev/null | tail -10

    # Set Longhorn as default StorageClass
    kubectl patch storageclass longhorn -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}' 2>/dev/null || true

    # Show StorageClass info
    log "=== StorageClass ==="
    kubectl get storageclass 2>/dev/null || true

    # Get NodePort for UI access
    local ui_port
    ui_port=$(kubectl get svc -n longhorn-system longhorn-ui -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "30800")
    local node_ip
    node_ip=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")

    logOk "Longhorn ready"
    echo ""
    echo "  UI: http://$node_ip:$ui_port"
    echo "  Default StorageClass: longhorn (replicaCount=$replica_count)"
    echo ""
    echo "  For roma-execution-bridge PVC:"
    echo "    storageClassName: longhorn"
    echo "    accessModes: [ReadWriteOnce]"
    echo "    resources: { requests: { storage: 50Gi } }"
}

#===============================================================================
# STAGE 16 — Rook Ceph Storage (v1.5 NEW)
#===============================================================================
#===============================================================================
# STAGE 16 — Rook Ceph Storage (Block + Filesystem + Object)  (v1.5 NEW)
#===============================================================================
stage16_rookceph() {
    echo "=== [16] Rook Ceph Storage (Block + FS + Object) ==="

    # 1. Уже установлен?
    if kubectl get namespace rook-ceph &>/dev/null 2>&1; then
        echo "✅ Rook Ceph уже установлен в кластере."
        kubectl get pods -n rook-ceph --no-headers 2>/dev/null | head -5
        echo "   Пропуск установки."
        return 0
    fi

    # 2. Установка Helm, если отсутствует
    if ! command -v helm &>/dev/null 2>&1; then
        echo "📦 Установка Helm..."
        curl -fsSL https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
    fi

    # 3. Добавление Rook repo
    echo "📦 Добавление Rook Helm repo..."
    helm repo add rook-release https://charts.rook.io/release 2>/dev/null || true
    helm repo update 2>&1 | tail -2

    # 4. Установка Rook Ceph Operator
    echo "🚀 Установка Rook Ceph Operator..."
    helm upgrade --install rook-ceph rook-release/rook-ceph \
        --namespace rook-ceph \
        --create-namespace \
        --version v1.14.3 \
        --set operator.logLevel=INFO \
        --wait --timeout 5m

    # 5. Создание CephCluster (оптимизировано для домашнего кластера)
    echo "📦 Создание CephCluster..."
    cat << 'CEPH_CLUSTER_EOF' | kubectl apply -f -
apiVersion: ceph.rook.io/v1
kind: CephCluster
metadata:
  name: rook-ceph
  namespace: rook-ceph
spec:
  cephVersion:
    image: quay.io/ceph/ceph:v18.2.2
  dataDirHostPath: /var/lib/rook
  mon:
    count: 3
    allowMultiplePerNode: true
  dashboard:
    enabled: true
    ssl: false
  network:
    provider: host
  crashCollector:
    disable: false
  storage:
    useAllNodes: true
    useAllDevices: false
    deviceFilter: "nvme[0-9]n[0-9]|sd[a-z]"
  resources:
    mgr:
      limits:
        cpu: "500m"
        memory: "1Gi"
CEPH_CLUSTER_EOF

    # 6. Создание StorageClass (Block + Filesystem)
    echo "📦 Создание StorageClass..."
    cat << 'SC_EOF' | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-ceph-block
provisioner: rook-ceph.rbd.csi.ceph.com
parameters:
  clusterID: rook-ceph
  pool: replicapool
  imageFormat: "2"
  imageFeatures: layering
reclaimPolicy: Retain
allowVolumeExpansion: true
---
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: rook-cephfs
provisioner: rook-ceph.cephfs.csi.ceph.com
parameters:
  clusterID: rook-ceph
  fsName: myfs
  pool: myfs-replicated
reclaimPolicy: Retain
allowVolumeExpansion: true
SC_EOF

    # 7. Ожидание и финальная проверка
    echo "⏳ Ожидание инициализации Ceph (60 секунд)..."
    sleep 60

    echo ""
    echo "=== Ceph Status ==="
    kubectl get pods -n rook-ceph -o wide
    kubectl get storageclass | grep rook-ceph

    echo ""
    echo "✅ Rook Ceph успешно установлен!"
    echo "   Block SC      : rook-ceph-block"
    echo "   Filesystem SC : rook-cephfs"
    echo "   Dashboard     : kubectl port-forward -n rook-ceph svc/rook-ceph-mgr-dashboard 7000:7000"
    echo ""
    echo "Пример PVC для roma-execution-bridge:"
    cat << 'PVC_EOF'

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: roma-checkpoints
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: rook-ceph-block
PVC_EOF

    return 0
}

#===============================================================================
# STAGE 17 — MinIO S3 Object Store (v1.6 NEW)
#===============================================================================
stage17_minio() {
    log "=== [17] MinIO S3 Object Store ==="

    local MINIO_NS="minio"
    local MINIO_TENANT="primary"
    local MINIO_UI_PORT="30901"

    # 1. Already installed?
    if kubectl get tenants.minio.io -n "$MINIO_NS" "$MINIO_TENANT" &>/dev/null 2>&1; then
        logOk "MinIO Tenant already installed"
        kubectl get tenants.minio.io -n "$MINIO_NS"
        kubectl get pods -n "$MINIO_NS" --no-headers 2>/dev/null | head -6
        echo ""
        echo "  Console: http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}' 2>/dev/null || echo 'localhost'):$MINIO_UI_PORT"
        echo "  S3:      http://$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type==\"InternalIP\")].address}' 2>/dev/null || echo 'localhost'):30900"
        echo ""
        echo "  For roma-execution-bridge S3 backup:"
        echo "    MC_HOST=myminio=http://localhost:30900"
        echo "    aws configure set --section profile --key endpoint_url --value http://localhost:30900"
        return 0
    fi

    # 2. Helm repo
    if ! helm repo list 2>/dev/null | grep -q minio; then
        log "Adding MinIO Helm repo..."
        helm repo add minio https://charts.min.io operator 2>/dev/null || true
        helm repo update 2>&1 | tail -2
    fi

    # 3. Namespace
    kubectl create namespace "$MINIO_NS" --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || true

    # 4. Pull secret (required for MinIO image)
    kubectl create secret docker-registry minio-pull-secret \
        --namespace="$MINIO_NS" \
        --docker-server=https://index.docker.io \
        --docker-username="$CURRENT_USER" \
        --docker-email="noreply@example.com" \
        --docker-password="$CURRENT_USER" \
        --dry-run=client -o yaml 2>/dev/null | kubectl apply -f - 2>/dev/null || true

    # 5. Install MinIO Tenant (tenant-based, not legacy standalone)
    #    Uses Longhorn as storage backend (PVC)
    #    Data stored at /data inside the container
    log "Deploying MinIO Tenant..."

    # Determine storage class (prefer longhorn > rook-ceph-block > standard > local-path)
    local SC
    SC=$(kubectl get storageclass -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}' 2>/dev/null | awk '{print $1}')
    [[ -z "$SC" ]] && SC=$(kubectl get storageclass -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    log "StorageClass: $SC"

    helm upgrade --install "$MINIO_TENANT" minio/tenant \
        --namespace "$MINIO_NS" \
        --create-namespace \
        --version v1.4.0 \
        \
        --set mode=standalone \
        --set replicas=1 \
        --set pools[0].name=pool1 \
        --set pools[0].servers=1 \
        --set pools[0].volumesPerServer=1 \
        --set pools[0].size=50Gi \
        --set pools[0].storageClassName="$SC" \
        \
        --set image.repository=quay.io/minio/minio \
        --set image.tag=RELEASE.2026-04-13T18-13-41Z \
        --set image.pullPolicy=IfNotPresent \
        --set imagePullSecret.name=minio-pull-secret \
        \
        --set tenants[0].accessKey=minioadmin \
        --set tenants[0].secretKey=minioadmin123 \
        \
        --set service.type=NodePort \
        --set service.consoleNodePort="$MINIO_UI_PORT" \
        --set service.minioNodePort=30900 \
        \
        --set consoleingress.enabled=false \
        --set ingress.enabled=false \
        --set monitoring.prometheus.enabled=false \
        \
        --set persistence.enabled=true \
        --set persistence.subPath="" \
        --set persistence.mountPath=/data \
        \
        --set priorityClassName=system-cluster-critical \
        --timeout 10m 2>&1 | tail -6

    # 6. Wait for MinIO to be ready
    log "Waiting for MinIO to initialize (90s)..."
    sleep 90

    # 7. Verify
    local minio_ready
    minio_ready=$(kubectl get pods -n "$MINIO_NS" --no-headers 2>/dev/null | grep -v Running | wc -l)
    if [[ "$minio_ready" -eq 0 ]]; then
        logOk "MinIO Tenant deployed successfully"
    else
        logWarn "MinIO may still be starting — check: kubectl get pods -n $MINIO_NS"
    fi

    # 8. Show status + access info
    kubectl get pods -n "$MINIO_NS" --no-headers 2>/dev/null | head -6
    echo ""

    local node_ip
    node_ip=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null || echo "localhost")

    echo "=============================================="
    echo "  ✅ MinIO S3 Object Store ready!"
    echo "=============================================="
    echo ""
    echo "  Console UI : http://$node_ip:$MINIO_UI_PORT"
    echo "    User     : minioadmin"
    echo "    Password : minioadmin123"
    echo ""
    echo "  S3 Endpoint : http://$node_ip:30900"
    echo "    User     : minioadmin"
    echo "    Password : minioadmin123"
    echo "    Region   : us-east-1"
    echo ""
    echo "=============================================="
    echo "  S3 Client (mc) setup:"
    echo "=============================================="
    cat << 'MC_EOF'
# Install mc if not present:
#   curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc -o /usr/local/bin/mc
#   chmod +x /usr/local/bin/mc

# Configure alias:
mc alias set myminio http://localhost:30900 minioadmin minioadmin123

# Verify:
mc admin info myminio

# Example: backup Longhorn snapshots to S3
mc rm -r --force myminio/longhorn-backups/ 2>/dev/null || true
mc cp -r /var/longhorn-backups/ myminio/longhorn-backups/ 2>/dev/null || true

# Example: store roma models/datasets
mc mb myminio/roma-models 2>/dev/null || true
mc cp -r /path/to/models myminio/roma-models/

# IAM policy for roma-execution-bridge:
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     { "Effect": "Allow", "Action": ["s3:*"], "Resource": ["arn:aws:s3:::roma-*"] }
#   ]
# }
MC_EOF
    echo ""
    echo "=============================================="
    echo "  PVC example for roma-execution-bridge:"
    echo "=============================================="
    cat << PVC_EOF

# Use Longhorn as backing storage for MinIO data:
# storageClassName: $SC
# resources:
#   requests:
#     storage: 100Gi
PVC_EOF
    echo ""
}

#===============================================================================
# STAGE 18 — Neovim + LazyVim Full AI/K8s
#===============================================================================
stage18_neovim() {
    log "=== STAGE 18: Neovim + LazyVim ==="
    if ! command -v nvim &>/dev/null; then
        apt install -y neovim 2>&1 | tail -3
        logOk "Neovim installed"
    else
        logOk "Neovim already present"
    fi
    # Install LazyVim
    if [[ ! -d "$HOMEDIR/.config/nvim" ]]; then
        git clone --depth 1 https://github.com/LazyVim/starter ~/.config/nvim 2>&1 | tail -3
        logOk "LazyVim installed"
    else
        logOk "LazyVim present"
    fi
    # Install plugins
    nvim --headless +Lazy! +qa 2>&1 | tail -3
    logOk "Neovim plugins installed"
}

#===============================================================================
# MAIN
#===============================================================================
main() {
    echo "=============================================="
    echo "  Pop!_OS 24.04 — AI/Dev Workstation Setup"
    echo "  Version: ${SCRIPT_VERSION:-1.6.0}  |  Stage: ${STAGE:-all}"
    echo "=============================================="

    # Run selected stage(s)
    case "${STAGE:-all}" in
        1|all)  stage01_preflight ;;
        2|all)  stage02_update    ;;
        3|all)  stage03_nvidia    ;;
        4|all)  stage04_cuda     ;;
        5|all)  stage05_docker   ;;
        6|all)  stage06_k3s      ;;
        7|all)  stage07_devtools ;;
        8|all)  stage08_zsh      ;;
        9|all)  stage09_security ;;
        10|all) stage10_ai_stack ;;
        11|all) stage11_monitoring ;;
        12|all) stage12_kde      ;;
        13|all) stage13_tailscale ;;
        14|all) stage14_k3s_multinode ;;
        15|all) stage15_longhorn ;;
        16|all) stage16_rookceph ;;
        17|all) stage17_minio ;;
        18|all) stage18_neovim ;;
        *) echo "Unknown stage: $STAGE" ;;
    esac

    echo ""
    echo "=============================================="
    echo "  ✅ Setup complete! Stage: ${STAGE:-all}"
    echo "=============================================="
}

# Parse arguments
STAGE="${1:-all}"
SCRIPT_VERSION="1.7"
main
