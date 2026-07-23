#!/bin/bash
set -euo pipefail
# ============================================================
# ACOS Cluster Status — all-in-one diagnostic
# ============================================================
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

echo "═══════════════════════════════════════════════════════════"
echo "  ACOS Home Cluster — Status Report"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ── Pre-flight checks ──────────────────────────────────────
check_port() { nc -z -w2 "$1" "$2" 2>/dev/null && echo "UP" || echo "DOWN"; }

# ── AmneziaWG Tunnel ───────────────────────────────────────
echo -n "  [TUNNEL] AmneziaWG (wg0): "
if ip link show wg0 &>/dev/null && ip addr show wg0 | grep -q "inet "; then
    echo -e "${GREEN}UP${NC}"
    ip -br addr show wg0 | awk '{print "           " $0}'
else
    echo -e "${RED}DOWN${NC}"
fi

# ── VictoriaMetrics ─────────────────────────────────────────
echo -n "  [VM]    VictoriaMetrics (:8428): "
VM_STATUS=$(check_port localhost 8428)
echo -e "${GREEN}${VM_STATUS}${NC}"

# ── Prometheus ─────────────────────────────────────────────
echo -n "  [VM]    Prometheus (:9090): "
PROM_STATUS=$(check_port localhost 9090)
echo -e "${GREEN}${PROM_STATUS}${NC}"

# ── Grafana ────────────────────────────────────────────────
echo -n "  [UI]    Grafana (:3000): "
GRAFANA_STATUS=$(check_port localhost 3000)
echo -e "${GREEN}${GRAFANA_STATUS}${NC}"

# ── Beszel ─────────────────────────────────────────────────
echo -n "  [UI]    Beszel (:8090): "
BESZEL_STATUS=$(check_port localhost 8090)
echo -e "${GREEN}${BESZEL_STATUS}${NC}"

# ── Perses ────────────────────────────────────────────────
echo -n "  [UI]    Perses (:8080): "
PERSES_STATUS=$(check_port localhost 8080)
echo -e "${GREEN}${PERSES_STATUS}${NC}"

# ── node_exporter ─────────────────────────────────────────
echo -n "  [EXP]   node_exporter (:9100): "
NE_STATUS=$(check_port localhost 9100)
echo -e "${GREEN}${NE_STATUS}${NC}"

# ── awg_exporter ──────────────────────────────────────────
echo -n "  [EXP]   awg_exporter (:9111): "
AWG_STATUS=$(check_port localhost 9111)
echo -e "${GREEN}${AWG_STATUS}${NC}"

# ── ACOS Metrics Exporter ────────────────────────────────
echo -n "  [EXP]   acos_exporter (:8000): "
ACOS_STATUS=$(check_port localhost 8000)
echo -e "${GREEN}${ACOS_STATUS}${NC}"

# ── AlertManager ──────────────────────────────────────────
echo -n "  [ALERT] AlertManager (:9093): "
AM_STATUS=$(check_port localhost 9093)
echo -e "${GREEN}${AM_STATUS}${NC}"

# ── Loki ──────────────────────────────────────────────────
echo -n "  [LOG]   Loki (:3100): "
LOKI_STATUS=$(check_port localhost 3100)
echo -e "${GREEN}${LOKI_STATUS}${NC}"

echo ""
echo "───────────────────────────────────────────────────────────"
echo "  Active monitoring backend:"
if [[ -f /etc/acos/monitoring.json ]]; then
    BACKEND=$(python3 -c "import json; print(json.load(open('/etc/acos/monitoring.json')).get('active_backend','grafana'))" 2>/dev/null || echo "unknown")
    echo "  ▶ $BACKEND"
else
    echo "  ▶ grafana (default)"
fi
echo ""
echo "───────────────────────────────────────────────────────────"
echo "  Services:"
systemctl is-active acos-tunnel-monitor 2>/dev/null | xargs -I{} echo "    acos-tunnel-monitor: {}"
systemctl is-active victoria-metrics 2>/dev/null | xargs -I{} echo "    victoria-metrics: {}"
echo ""

# ── Docker containers ─────────────────────────────────────
if command -v docker &>/dev/null; then
    echo "  Docker containers:"
    docker ps --format "    {{.Names}}: {{.Status}}" 2>/dev/null | grep acos | head -10 || echo "    (none running)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Quick commands:"
echo "    acos monitor status           # Full ACOS status"
echo "    acos monitor switch beszel    # Switch to Beszel"
echo "    journalctl -u acos-tunnel-monitor -f  # Watch tunnel"
echo "    curl -s localhost:8428/health        # VictoriaMetrics health"
