#!/bin/bash
# submit.sh — Slurm job submission wrapper via AI Scheduler v2
# Usage: ./submit.sh <partition> <script> [job_id]
set -euo pipefail

PARTITION="${1:-gpu}"
SCRIPT="${2:-job.sh}"
JOB_ID="${3:-$(uuidgen 2>/dev/null | cut -d'-' -f1)}"
SCHEDULER_URL="${SCHEDULER_URL:-http://localhost:8080}"

RESPONSE=$(curl -s -X POST "${SCHEDULER_URL}/schedule" \
  -H "Content-Type: application/json" \
  -d "{\"job_type\":\"${PARTITION}\"}")

TARGET=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('target',''))" 2>/dev/null || echo "")

if [ "$TARGET" == "None" ] || [ "$TARGET" == "queue" ] || [ -z "$TARGET" ]; then
  echo "[submit] No node available, submitting to ${PARTITION} queue"
  sbatch --partition="${PARTITION}" --job-name="${JOB_ID}" "${SCRIPT}"
else
  echo "[submit] Scheduler selected node: ${TARGET} → partition: ${PARTITION}"
  sbatch --partition="${PARTITION}" --nodelist="${TARGET}" --job-name="${JOB_ID}" "${SCRIPT}"
fi
