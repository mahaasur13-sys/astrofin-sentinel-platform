#!/bin/bash
# H-02: Load test 100 RPS — breaking point determination.
# Run on staging with Docker. Sandbox: script only (no Docker).

set -euo pipefail

HOST="${1:-http://localhost:8000}"
USER_COUNT="${2:-100}"
RAMP_RATE="${3:-10}"
DURATION="${4:-15m}"
OUTPUT_HTML="${5:-docs/performance/stress-test-100rps.html}"
LOCUST_FILE="tests/load/locustfile_sprint_e.py"

echo "============================================"
echo "  LOAD TEST — Breaking Point"
echo "  Host:     $HOST"
echo "  Users:    $USER_COUNT"
echo "  Ramp:     $RAMP_RATE/sec"
echo "  Duration: $DURATION"
echo "  Output:   $OUTPUT_HTML"
echo "============================================"
echo ""

# Step 1: Start staging
echo "[1/4] Starting staging..."
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d --wait 2>/dev/null || true
sleep 15

# Step 2: Health check
echo "[2/4] Health check..."
curl -s "$HOST/health" | python3 -m json.tool 2>/dev/null || echo "  ⚠️ Health endpoint not reachable"

# Step 3: Warmup
echo "[3/4] Warmup (10 users × 30s)..."
locust -f "$LOCUST_FILE" \
  --host "$HOST" \
  -u 10 -r 2 --run-time 30s \
  --headless --only-summary 2>/dev/null || true

# Step 4: Full load
echo "[4/4] Stress test ($USER_COUNT users × $DURATION)..."
locust -f "$LOCUST_FILE" \
  --host "$HOST" \
  -u "$USER_COUNT" -r "$RAMP_RATE" \
  --run-time "$DURATION" \
  --html "$OUTPUT_HTML" \
  --csv "docs/performance/stress-test-100rps" \
  --csv-full-history

echo ""
echo "============================================"
echo "  Done. Report: $OUTPUT_HTML"
echo "============================================"
