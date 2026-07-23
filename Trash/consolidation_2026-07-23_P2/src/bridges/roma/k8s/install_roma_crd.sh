#!/bin/bash
# =============================================================================
# ROMA CRD + Controller Setup
# =============================================================================

set -e

NAMESPACE="roma-system"
CRD_FILE="roma-crd.yaml"

echo "=== Installing ROMA CRD + Controller ==="

echo "[1/4] Creating namespace..."
kubectl apply -f - <<< '
apiVersion: v1
kind: Namespace
metadata:
  name: roma-system
'

echo "[2/4] Applying CRD..."
kubectl apply -f "$CRD_FILE"
echo "Waiting for CRD to be established..."
sleep 3

echo "[3/4] Applying RBAC + Controller..."
kubectl apply -f "$CRD_FILE" -n roma-system

echo "[4/4] Verifying CRD..."
kubectl get crd romatasks.roma.ai 2>/dev/null && echo "✅ CRD registered" || echo "❌ CRD not found"

echo ""
echo "=== Usage ==="
echo "kubectl apply -f examples/yolov8-task.yaml -n roma-jobs"
echo "kubectl get rt -n roma-jobs"
echo "kubectl describe rt yolov8-training-001 -n roma-jobs"