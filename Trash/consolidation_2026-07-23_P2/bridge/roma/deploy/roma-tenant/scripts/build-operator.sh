#!/bin/bash
#===============================================================================
# ROMA Tenant Operator — Build & Push Script
# Build: config/crd/Dockerfile.operator
# Registry: ghcr.io/mahaasur13-sys/roma-tenant-operator
#===============================================================================

set -euo pipefail

REGISTRY="ghcr.io/mahaasur13-sys"
IMAGE="roma-tenant-operator"
VERSION="${1:-latest}"
TAG="${REGISTRY}/${IMAGE}:${VERSION}"

cd "$(dirname "$0")/../.."

echo "[INFO] Building operator image: ${TAG}"
docker build \
  -t "${TAG}" \
  -f config/crd/Dockerfile.operator \
  .

echo "[INFO] Pushing to GHCR..."
docker push "${TAG}"

echo ""
echo "✅ Operator image pushed: ${TAG}"
echo ""
echo "Next steps:"
echo "  1. Update image tag in config/crd/controller/deployment.yaml if needed"
echo "  2. Apply CRD + operator to cluster:"
echo "     kubectl apply -f config/crd/bases/roma.io_romatenants.yaml"
echo "     kubectl apply -f config/crd/controller/deployment.yaml"
echo "  3. Create a sample tenant:"
echo "     kubectl apply -f config/crd/samples/romatenant-free.yaml"
echo "  4. Verify:"
echo "     kubectl get romatenants"
echo "     kubectl get ns -l roma.io/tenant"
echo "     kubectl get ingress -n roma-partner-acme"