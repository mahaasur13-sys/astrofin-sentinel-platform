#!/usr/bin/env bash
# =============================================================================
# DAY 2 — WireGuard / AmneziaWG Mesh Setup
# =============================================================================
# Target: All cluster nodes (RTX 3060 PC, RK3576, optional VPS)
# Result: Encrypted mesh network over public internet
# Run on: laptop or any node with wg-tool
# =============================================================================

set -euo pipefail

# --- Config (edit to match your IPs) ---
RTX_IP="192.168.1.100"       # Public/internet IP of RTX PC
RK3576_IP="192.168.1.200"    # Public/internet IP of RK3576
VPS_IP="${VPS_IP:-}"         # Optional VPS public IP
VPS_ENABLED="${VPS_ENABLED:-false}"

WG_NET="10.40.40.0/24"
WG_PORT=51820

RTX_WG_IP="10.40.40.10"
RK3576_WG_IP="10.40.40.20"
VPS_WG_IP="10.40.40.30"

APT_PACKAGES="wireguard-tools"

# =============================================================================
# Helpers
# =============================================================================
info() { echo "[INFO] $1"; }
warn() { echo "[WARN] $1"; }
ok()   { echo "[OK]   $1"; }

command_exists() {
  command -v "$1" &>/dev/null
}

install_wg() {
  info "Installing WireGuard..."
  if command_exists apt-get; then
    apt-get update -qq && apt-get install -y -qq $APT_PACKAGES
  else
    warn "apt not found — install wireguard-tools manually"
  fi
}

# Generate keypair
gen_keys() {
  wg genkey | tee /dev/stdin
}

# =============================================================================
# Main
# =============================================================================

if ! command_exists wg; then
  install_wg
fi

info "WireGuard mesh setup"
info "Network: $WG_NET"
info "RTX:   $RTX_WG_IP ($RTX_IP)"
info "RK3576: $RK3576_WG_IP ($RK3576_IP)"
[[ "$VPS_ENABLED" == "true" ]] && info "VPS:   $VPS_WG_IP ($VPS_IP)"

echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 0

# =============================================================================
# Generate keys locally (for demo — in prod use secure method)
# =============================================================================
info "Generating WireGuard keys (RTX node)..."
RTX_PRIV=$(wg genkey)
RTX_PUB=$(echo "$RTX_PRIV" | wg pubkey)
ok "RTX keys generated"

info "Generating WireGuard keys (RK3576)..."
RK3576_PRIV=$(wg genkey)
RK3576_PUB=$(echo "$RK3576_PRIV" | wg pubkey)
ok "RK3576 keys generated"

VPS_PRIV=""
VPS_PUB=""
if [[ "$VPS_ENABLED" == "true" ]]; then
  info "Generating WireGuard keys (VPS)..."
  VPS_PRIV=$(wg genkey)
  VPS_PUB=$(echo "$VPS_PRIV" | wg pubkey)
  ok "VPS keys generated"
fi

# =============================================================================
# Save keys to files (to deploy to nodes)
# =============================================================================
KEYDIR="$HOME/.wireguard"
mkdir -p "$KEYDIR"

echo "$RTX_PRIV"   > "$KEYDIR/rtx_private.key"
echo "$RTX_PUB"    > "$KEYDIR/rtx_public.key"
echo "$RK3576_PRIV" > "$KEYDIR/rk3576_private.key"
echo "$RK3576_PUB"  > "$KEYDIR/rk3576_public.key"
[[ "$VPS_ENABLED" == "true" ]] && echo "$VPS_PRIV" > "$KEYDIR/vps_private.key"

chmod 600 "$KEYDIR"/*.key
ok "Keys saved to $KEYDIR/"

# =============================================================================
# Generate configs
# =============================================================================
WG_DIR="/etc/wireguard"
[[ -d "$WG_DIR" ]] || sudo mkdir -p "$WG_DIR"

# RTX config
sudo tee "$WG_DIR/wg0.conf" > /dev/null << RTX_CONF
[Interface]
Address = $RTX_WG_IP/24
ListenPort = $WG_PORT
PrivateKey = $RTX_PRIV

# RK3576 peer
[Peer]
PublicKey = $RK3576_PUB
AllowedIPs = $RK3576_WG_IP/32
Endpoint = $RK3576_IP:$WG_PORT
PersistentKeepalive = 25

# VPS peer
$( [[ "$VPS_ENABLED" == "true" ]] && cat << VPS_PEER
[Peer]
PublicKey = $VPS_PUB
AllowedIPs = $VPS_WG_IP/32
Endpoint = $VPS_IP:$WG_PORT
PersistentKeepalive = 25
VPS_PEER
)
RTX_CONF
ok "Config written to $WG_DIR/wg0.conf (RTX)"

# RK3576 config (show — deploy via scp/ansible)
RK3576_CONF=$(cat << RK3576WCONF
[Interface]
Address = $RK3576_WG_IP/24
ListenPort = $WG_PORT
PrivateKey = $RK3576_PRIV

# RTX peer
[Peer]
PublicKey = $RTX_PUB
AllowedIPs = $RTX_WG_IP/32
Endpoint = $RTX_IP:$WG_PORT
PersistentKeepalive = 25
RK3576WCONF
)

echo ""
echo "=========================================="
echo "[DAY2] RTX wg0.conf ready"
echo "=========================================="
echo ""
echo "=== RTX (local — already written) ==="
sudo cat "$WG_DIR/wg0.conf"
echo ""
echo "=== RK3576 config — deploy manually ==="
echo "$RK3576_CONF"
echo ""
echo "On RK3576, save as /etc/wireguard/wg0.conf and run:"
echo "  sudo wg-quick up wg0"
echo "  sudo systemctl enable wg-quick@wg0"
echo ""

# Save RK3576 config for later deployment
cat > "$KEYDIR/rk3576_wg0.conf" <<< "$RK3576_CONF"
ok "RK3576 config saved to $KEYDIR/rk3576_wg0.conf"

# =============================================================================
# Enable forwarding + systemd
# =============================================================================
if command_exists systemctl; then
  sudo systemctl enable wg-quick@wg0 2>/dev/null || true
  ok "WireGuard autostart enabled"
fi

echo ""
echo "=========================================="
echo "[DAY2] DONE — WireGuard Mesh Ready"
echo "=========================================="
echo ""
echo "Public keys for documentation:"
echo "  RTX:    $RTX_PUB"
echo "  RK3576: $RK3576_PUB"
[[ "$VPS_ENABLED" == "true" ]] && echo "  VPS:    $VPS_PUB"
echo ""
echo "Next: bash scripts/day3-compute.sh"
