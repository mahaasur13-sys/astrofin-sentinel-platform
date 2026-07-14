#!/bin/bash
# start-dashboard.sh — ATOM-META-RL-008: Private Dashboard Launcher
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'

cleanup() {
  echo -e "\n${YELLOW}🛑 Graceful shutdown...${NC}"
  pkill -f "gunicorn.*web.wsgi" 2>/dev/null && echo -e "${GREEN}✅ Gunicorn stopped${NC}"
  pkill -f "vite" 2>/dev/null && echo -e "${GREEN}✅ Vite stopped${NC}"
  exit 0
}
trap cleanup SIGINT SIGTERM

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  AstroFin Meta-RL — PRIVATE Dashboard${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

# ── P0.1: Kill old processes ──────────────────────────────────
echo -e "\n${YELLOW}🧹 Cleaning up old processes...${NC}"
pkill -f "gunicorn.*web.wsgi" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "node.*astrofin-meta" 2>/dev/null || true
sleep 1
echo -e "${GREEN}✅ Old processes killed${NC}"

# ── P0.2: Start Gunicorn backend ──────────────────────────────
echo -e "\n${YELLOW}🚀 Starting Gunicorn backend on 127.0.0.1:8050...${NC}"
cd /home/workspace/AstroFinSentinelV5
gunicorn -w 2 -b 127.0.0.1:8050 --timeout 120 web.wsgi:app \
  --access-logfile /tmp/astrofin-access.log \
  --error-logfile /tmp/astrofin-error.log \
  --daemon
sleep 3

# Verify backend
if curl -sf http://127.0.0.1:8050/api/health > /dev/null 2>&1; then
  HEALTH=$(curl -s http://127.0.0.1:8050/api/health)
  echo -e "${GREEN}✅ Gunicorn backend UP${NC}"
else
  echo -e "${RED}❌ Gunicorn failed to start — check /tmp/astrofin-error.log${NC}"
  tail -5 /tmp/astrofin-error.log 2>/dev/null
  exit 1
fi

# ── P0.3: Start React frontend ─────────────────────────────────
echo -e "\n${YELLOW}⚛️  Starting React frontend on http://localhost:5173...${NC}"
cd /home/workspace/astrofin-meta-rl
bun run dev --host 0.0.0.0 &
BUN_PID=$!
sleep 5

if kill -0 $BUN_PID 2>/dev/null; then
  echo -e "${GREEN}✅ React frontend UP${NC}"
else
  echo -e "${RED}❌ React failed to start${NC}"
  exit 1
fi

# ── Summary ────────────────────────────────────────────────────
GUNICORN_PID=$(pgrep -f "gunicorn.*web.wsgi" | head -1)
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ ALL SERVICES STARTED SUCCESSFULLY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${GREEN}Frontend${NC}:  http://localhost:5173"
echo -e "  ${GREEN}Backend${NC}:   http://localhost:8050"
echo -e "  ${GREEN}Health${NC}:    http://localhost:8050/api/health"
echo ""
echo -e "${YELLOW}🔒 PRIVATE ACCESS ONLY — no public URL${NC}"
echo ""
echo -e "  SSH tunnel for remote access:"
echo -e "    ${BLUE}ssh -L 5173:localhost:5173 -L 8050:localhost:8050 \\${NC}"
echo -e "       user@your-zo-server${NC}"
echo ""
echo -e "  Then open: http://localhost:5173"
echo ""
echo -e "${YELLOW}PIDs:${NC} gunicorn=$GUNICORN_PID bun=$BUN_PID"
echo ""
echo -e "Press ${RED}Ctrl+C${NC} to stop all services"
echo ""
wait
