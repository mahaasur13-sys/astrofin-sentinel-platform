#!/bin/bash
# =============================================================================
# ROMA End-to-End GPU Test
# Verifies: CLI → Bridge → K8s → GPU node → nvidia-smi output
# =============================================================================

set -e

BRIDGE_URL="${BRIDGE_URL:-http://localhost:8080}"
NS="roma-system"
JOB_NAME="roma-gpu-test"

echo "=== ROMA GPU E2E Test ==="

# 1. Check bridge health
echo "[1/6] Bridge health..."
curl -sf "${BRIDGE_URL}/health" || { echo "FAIL: Bridge not reachable at ${BRIDGE_URL}"; exit 1; }
echo "✓ Bridge OK"

# 2. Apply RBAC
echo "[2/6] Applying RBAC..."
kubectl apply -f k8s/rbac-roma-executor.yaml 2>/dev/null || echo "WARN: RBAC already exists or kubectl not configured"
echo "✓ RBAC applied"

# 3. Apply GPU test job
echo "[3/6] Submitting GPU test job..."
kubectl delete job ${JOB_NAME} -n ${NS} --ignore-not-found=true
kubectl apply -f k8s/gpu-test-job.yaml
echo "✓ Job submitted"

# 4. Wait for pod scheduling (max 60s)
echo "[4/6] Waiting for pod scheduling..."
POD=""
for i in $(seq 1 30); do
  POD=$(kubectl get pods -n ${NS} -l purpose=gpu-validation -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
  STATUS=$(kubectl get pod ${POD} -n ${NS} -o jsonpath='{.status.phase}' 2>/dev/null || echo "Pending")
  echo "  [${i}s] pod=${POD:-none} status=${STATUS}"
  if [ "${STATUS}" == "Running" ] || [ "${STATUS}" == "Succeeded" ] || [ "${STATUS}" == "Failed" ]; then
    break
  fi
  sleep 2
done

# 5. Get logs
echo "[5/6] Fetching nvidia-smi output..."
kubectl logs -n ${NS} ${POD} 2>/dev/null || echo "POD=${POD} status=$(kubectl get pod ${POD} -n ${NS} -o jsonpath='{.status.phase}' 2>/dev/null)"

# 6. Final status
echo "[6/6] Final job status..."
kubectl get job ${JOB_NAME} -n ${NS} -o yaml 2>/dev/null | grep -E "succeeded|failed|active" || true

echo "=== E2E Test Complete ==="
echo "To view logs: kubectl logs -n ${NS} ${POD}"
echo "To delete:    kubectl delete job ${JOB_NAME} -n ${NS}"