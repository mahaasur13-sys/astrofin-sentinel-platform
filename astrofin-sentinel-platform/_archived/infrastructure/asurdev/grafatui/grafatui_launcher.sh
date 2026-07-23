#!/bin/bash
set -euo pipefail
LOG_PREFIX="[ACOS-GRAFATUI]"

VICTORIA_URL="${VICTORIA_URL:-http://localhost:8428}"

echo "$LOG_PREFIX Starting Grafatui with VictoriaMetrics at $VICTORIA_URL..."
echo ""
echo "Controls:"
echo "  ↑↓      Navigate panels"
echo "  ←→      Switch graph"
echo "  g       Go to panel (0-9)"
echo "  d       Toggle time range (1h/6h/24h)"
echo "  q       Quit"
echo ""
echo "Panels:"
echo "  [0] ACOS Tunnel Status"
echo "  [1] Event Rate (per sec)"
echo "  [2] DAG Queue"
echo "  [3] Node CPU"
echo "  [4] Memory Available"
echo "  [5] GPU Metrics"
echo ""

if command -v grafatui &>/dev/null; then
    exec grafatui "$VICTORIA_URL"
else
    echo "$LOG_PREFIX ERROR: grafatui not installed."
    echo "$LOG_PREFIX Install with: cargo install grafatui"
    echo "$LOG_PREFIX Or use Docker:"
    echo "  docker run -it --rm ghcr.io/henrygd/grafatui:latest $VICTORIA_URL"
    exit 1
fi
