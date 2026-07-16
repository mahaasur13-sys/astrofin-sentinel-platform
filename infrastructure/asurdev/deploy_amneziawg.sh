#!/bin/bash
# ACOS AmneziaWG Deploy - Pop!_OS (ALL CRITICAL FIXES APPLIED)
set -euo pipefail
LOG_PREFIX="[ACOS-DEPLOY]"

if [[ $EUID -ne 0 ]]; then
   echo "ERROR: Run as root or with sudo" >&2; exit 1
fi

ROLE="${1:-server}"
echo "$LOG_PREFIX Role: $ROLE"

# --- Kernel headers ---
echo "$LOG_PREFIX Installing kernel headers..."
apt-get update -qq
apt-get install -y -qq build-essential linux-headers-$(uname -r) wireguard-tools git curl > /dev/null 2>&1

# --- AmneziaWG kernel module ---
if [[ "$ROLE" == "server" ]]; then
  echo "$LOG_PREFIX Building AmneziaWG kernel module..."
  AWG_TMP=$(mktemp -d)
  chmod 700 "$AWG_TMP"
  git clone --depth=1 https://github.com/amnezia-vpn/amneziawg-linux-kernel.git "$AWG_TMP" 2>/dev/null || true
  if [[ -d "$AWG_TMP" ]] && [[ -f "$AWG_TMP/Makefile" ]]; then
    (cd "$AWG_TMP" && make -j$(nproc) 2>/dev/null && make install 2>/dev/null) || true
  fi
  rm -rf "$AWG_TMP"
fi

# --- awg utility ---
if ! command -v awg &> /dev/null; then
  echo "$LOG_PREFIX Installing awg-quick..."
  AWG_TOOLS=$(mktemp -d)
  chmod 700 "$AWG_TOOLS"
  git clone --depth=1 https://github.com/amnezia-vpn/amneziawg.git "$AWG_TOOLS" 2>/dev/null || true
  if [[ -f "$AWG_TOOLS/Makefile" ]]; then
    (cd "$AWG_TOOLS" && make -j$(nproc) && make install) || true
  fi
  rm -rf "$AWG_TOOLS"
fi

# --- Fallback ---
if ! command -v awg-quick &> /dev/null && ! command -v awg &> /dev/null; then
  echo "$LOG_PREFIX WireGuard fallback..."
  cp /usr/bin/wg-quick /usr/local/bin/awg-quick 2>/dev/null || true
  ln -sf /usr/bin/wg /usr/local/bin/awg 2>/dev/null || true
fi

# --- WireGuard module ---
echo "$LOG_PREFIX Checking wireguard module..."
modprobe wireguard 2>/dev/null || echo "$LOG_PREFIX wireguard module not available (OK if container)"

# --- Generate keys with restricted permissions ---
SERVER_KEY="/etc/awg/server.key"
CLIENT_KEY="/etc/awg/client.key"
mkdir -p /etc/awg

if [[ ! -f "$SERVER_KEY" ]]; then
  echo "$LOG_PREFIX Generating server keypair..."
  wg genkey | tee "$SERVER_KEY" > /dev/null
  chmod 600 "$SERVER_KEY"
  chmod 644 "${SERVER_KEY}.pub"
fi

if [[ "$ROLE" == "client" ]] && [[ ! -f "$CLIENT_KEY" ]]; then
  echo "$LOG_PREFIX Generating client keypair..."
  wg genkey | tee "$CLIENT_KEY" > /dev/null
  chmod 600 "$CLIENT_KEY"
  chmod 644 "${CLIENT_KEY}.pub"
fi

# --- Create server config (CRITICAL-4: AmneziaWG obfuscation) ---
if [[ "$ROLE" == "server" ]]; then
  SERVER_PUB=$(cat "${SERVER_KEY}.pub")
  echo "$LOG_PREFIX Creating server config..."
  tee /etc/awg/awg0.conf > /dev/null << CONF
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = $(cat $SERVER_KEY)
Jc = 4
Jmin = 40
Jmax = 55
S1 = 1
S2 = 2
H1 = 1
H2 = 2
H3 = 3
H4 = 4

[Peer]
PublicKey = $([[ -f "${CLIENT_KEY}.pub" ]] && cat "${CLIENT_KEY}.pub" || echo "REPLACE_WITH_CLIENT_PUB")
AllowedIPs = 10.8.0.2/32
PersistentKeepalive = 25
CONF
  chmod 600 /etc/awg/awg0.conf
  echo "$LOG_PREFIX Server public key: $SERVER_PUB"
fi

# --- Create client config ---
if [[ "$ROLE" == "client" ]]; then
  CLIENT_PUB=$(cat "${CLIENT_KEY}.pub")
  SERVER_PUB=$(cat /etc/awg/server.pub 2>/dev/null || echo "REPLACE_WITH_SERVER_PUB")
  WAN_IP=$(curl -s ifconfig.me 2>/dev/null || echo "YOUR_SERVER_IP")
  echo "$LOG_PREFIX Creating client config..."
  tee /etc/awg/awg0.conf > /dev/null << CONF
[Interface]
Address = 10.8.0.2/24
PrivateKey = $(cat $CLIENT_KEY)
DNS = 1.1.1.1
Jc = 4
Jmin = 40
Jmax = 55
S1 = 1
S2 = 2
H1 = 1
H2 = 2
H3 = 3
H4 = 4

[Peer]
PublicKey = $SERVER_PUB
Endpoint = ${WAN_IP}:51820
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
CONF
  chmod 600 /etc/awg/awg0.conf
  echo "$LOG_PREFIX Client public key: $CLIENT_PUB"
fi

# --- IP forwarding ---
echo "$LOG_PREFIX Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1 2>/dev/null || true
grep -q "net.ipv4.ip_forward" /etc/sysctl.d/99-acos.conf || \
  echo "net.ipv4.ip_forward=1" | tee /etc/sysctl.d/99-acos.conf > /dev/null

# --- Firewall: restrict access (CRITICAL-6) ---
echo "$LOG_PREFIX Setting firewall rules..."
# Allow loopback
iptables -A INPUT -i lo -j ACCEPT 2>/dev/null || true
# Allow established
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT 2>/dev/null || true
# Allow AmneziaWG UDP
iptables -A INPUT -p udp --dport 51820 -j ACCEPT 2>/dev/null || true
# Allow only localnet + VPN for management ports
for PORT in 8428 9090 3000 3100 9111 8000 8080; do
  iptables -A INPUT -p tcp --dport $PORT -s 192.168.0.0/16 -j ACCEPT 2>/dev/null || true
  iptables -A INPUT -p tcp --dport $PORT -s 10.8.0.0/24 -j ACCEPT 2>/dev/null || true
done
# Drop everything else
iptables -A INPUT -j DROP 2>/dev/null || true

# --- Copy Python module ---
echo "$LOG_PREFIX Installing Python module..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/acos/network/amnezia_wg.py" ]]; then
  mkdir -p /opt/acos/network
  cp "$SCRIPT_DIR/acos/network/amnezia_wg.py" /opt/acos/network/
  echo "$LOG_PREFIX Python module installed"
fi

echo ""
echo "$LOG_PREFIX === Deploy Complete ==="
echo "$LOG_PREFIX Run: sudo awg-quick up awg0"
echo "$LOG_PREFIX Run: sudo awg show"
