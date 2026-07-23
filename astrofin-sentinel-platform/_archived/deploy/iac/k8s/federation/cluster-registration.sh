#!/usr/bin/env bash
# k8s/federation/cluster-registration.sh
# Register x86 and ARM clusters with KubeFed

set -euo pipefail

HOST_CONTEXT="${HOST_CONTEXT:-kubernetes-admin@cluster.local}"
ARM_CONTEXT="${ARM_CONTEXT:-kubernetes-admin@arm-cluster}"
NAMESPACE="${NAMESPACE:-kube-federation-system}"

echo "=== Registering clusters with KubeFed ==="

# Join x86 (GPU) cluster as primary
echo "[1/2] Joining x86 cluster as host..."
kubefedctl join "${HOST_CONTEXT}" \
  --cluster-context "${HOST_CONTEXT}" \
  --host-cluster-context "${HOST_CONTEXT}" \
  --namespace "${NAMESPACE}"

# Join ARM cluster as secondary (lightweight)
echo "[2/2] Joining ARM cluster (RK3576) as lightweight..."
kubefedctl join "${ARM_CONTEXT}" \
  --cluster-context "${ARM_CONTEXT}" \
  --host-cluster-context "${HOST_CONTEXT}" \
  --namespace "${NAMESPACE}" \
  --lightweight

# Verify
echo ""
echo "=== Registered clusters ==="
kubectl --context "${HOST_CONTEXT}" -n "${NAMESPACE}" get kubefedclusters

echo ""
echo "=== Cluster types ==="
kubectl --context "${HOST_CONTEXT}" -n "${NAMESPACE}" get kubefedclusters -o wide
