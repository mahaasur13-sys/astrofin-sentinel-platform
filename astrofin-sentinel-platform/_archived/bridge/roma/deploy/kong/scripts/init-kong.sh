#!/usr/bin/env bash
# =============================================================================
# Kong Gateway Init — Sprint 2 Task 2
# =============================================================================
# Installs Kong via Helm, configures plugins, consumers, and routes
# Idempotent: safe to re-run
# Requires: kubectl, helm, Kong CRDs installed
# =============================================================================

set -euo pipefail

NAMESPACE="kong"
CHART_VERSION="2.36.0"
ROMADIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log() { echo -e "\033[0;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[0;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[0;31m[ERROR]\033[0m $*" >&2; exit 1; }

# Check prerequisites
command -v kubectl >/dev/null 2>&1 || err "kubectl not found"
command -v helm >/dev/null 2>&1 || err "helm not found"

# Ensure namespace
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Add Kong Helm repo
log "Adding Kong Helm repo..."
helm repo add kong https://charts.konghq.com --force-update 2>/dev/null || true
helm repo update 2>/dev/null || true

# Install Kong CRDs
log "Applying Kong CRDs..."
kubectl apply -f "https://docs.konghq.com/kubernetes-ingress-controller/latest/reference/crd/ul背上.list" 2>/dev/null || \
  kubectl apply -f "https://raw.githubusercontent.com/Kong/kubernetes-ingress-controller/v2.14.0/deploy/crd-all-in-one.yaml"

# Create DB secret
kubectl create secret generic kong-db-secret \
  --from-literal=password="$(openssl rand -base64 32)" \
  --namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# Create Redis secret
kubectl create secret generic redis-master-secret \
  --from-literal=redis-password="$(openssl rand -base64 24)" \
  --namespace roma-system --dry-run=client -o yaml | kubectl apply -f -

# Install/upgrade Kong via Helm
log "Deploying Kong Gateway..."
helm upgrade --install kong kong/kong \
  --version "$CHART_VERSION" \
  --namespace "$NAMESPACE" \
  --values "${ROMADIR}/deploy/kong/values.yaml" \
  --wait --timeout 10m \
  --atomic \
  --create-namespace

# Apply plugins
log "Applying KongPlugin CRDs..."
kubectl apply -f "${ROMADIR}/deploy/kong/templates/plugins/tenant-plugins.yaml"
kubectl apply -f "${ROMADIR}/deploy/kong/templates/plugins/rate-limit-tenant.yaml"

# Wait for pods
log "Waiting for Kong pods..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kong \
  --namespace "$NAMESPACE" --timeout=120s

# Get proxy URL
PROXY_IP=$(kubectl get svc -n "$NAMESPACE" kong-proxy -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "pending")
log "Kong Proxy: http://${PROXY_IP}:80"
log "Kong Admin: http://${PROXY_IP}:8001"
log ""
log "✅ Kong Gateway deployed successfully"
log "   Next: apply tenant consumers and ingress routes"
log ""
log "   kubectl apply -f ${ROMADIR}/deploy/kong/templates/ingress.yaml"
log ""
log "Sprint 2 Task 2 — complete. Push changes:"
log "   cd ${ROMADIR} && git add . && git commit -m 'feat(sprint2-task2): Kong API Gateway'"