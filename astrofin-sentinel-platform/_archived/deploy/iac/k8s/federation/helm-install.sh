#!/usr/bin/env bash
# k8s/federation/helm-install.sh
# Install KubeFed (Kubernetes Federation v2) via Helm

set -euo pipefail

KUBEFED_VERSION="${KUBEFED_VERSION:-0.10.0}"
KUBEFED_NAMESPACE="${KUBEFED_NAMESPACE:-kube-federation-system}"
KUBEFED_CHART="https://github.com/kubernetes-sigs/kubefed/releases/download/v${KUBEFED_VERSION}/kubefed-${KUBEFED_VERSION}.tgz"

# ── Detect cluster contexts ───────────────────────────────────────────────────
CONTEXT_X86="${CONTEXT_X86:-kubernetes-admin@cluster.local}"
CONTEXT_ARM="${CONTEXT_ARM:-kubernetes-admin@arm-cluster}"
KUBECONFIG="${KUBECONFIG:-/etc/kubernetes/admin.conf}"

echo "=== KubeFed Installer ==="
echo "Version: ${KUBEFED_VERSION}"
echo "Namespace: ${KUBEFED_NAMESPACE}"

# ── Install kubefedctl ──────────────────────────────────────────────────────
echo "[1/4] Downloading kubefedctl..."
curl -sLO "https://github.com/kubernetes-sigs/kubefed/releases/download/v${KUBEFED_VERSION}/kubefedctl-linux-amd64.tgz"
tar -xzf kubefedctl-linux-amd64.tgz
mv kubefedctl /usr/local/bin/kubefedctl
chmod +x /usr/local/bin/kubefedctl
rm -f kubefedctl-linux-amd64.tgz

# ── Install KubeFed Helm chart on x86 cluster ─────────────────────────────────
echo "[2/4] Installing KubeFed on x86 cluster (${CONTEXT_X86})..."
helm repo add kubefed https://kubernetes-sigs.github.io/kubefed/charts
helm repo update

helm upgrade -i kubefed "${KUBEFED_CHART}" \
  --namespace "${KUBEFED_NAMESPACE}" \
  --create-namespace \
  --set controllermanager.replicaCount=2 \
  --kubecontext "${CONTEXT_X86}"

# ── Register clusters ─────────────────────────────────────────────────────────
echo "[3/4] Registering clusters with KubeFed..."

# Register x86 cluster
kubefedctl join "${CONTEXT_X86}" \
  --cluster-context "${CONTEXT_X86}" \
  --host-cluster-context "${CONTEXT_X86}" \
  --namespace "${KUBEFED_NAMESPACE}"

# Register ARM cluster
kubefedctl join "${CONTEXT_ARM}" \
  --cluster-context "${CONTEXT_ARM}" \
  --host-cluster-context "${CONTEXT_X86}" \
  --namespace "${KUBEFED_NAMESPACE}" \
  --lightweight

# ── Verify ───────────────────────────────────────────────────────────────────
echo "[4/4] Verifying KubeFed installation..."
kubectl --context "${CONTEXT_X86}" -n "${KUBEFED_NAMESPACE}" get pods

echo "=== KubeFed installed ==="
echo "Next: kubectl --context ${CONTEXT_X86} apply -f k8s/federation/federated-deployment.yaml"
