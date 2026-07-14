#!/bin/bash
# =====================================================================
# GHCR.IO REGISTRY PUSH — First-Time Setup
# =====================================================================
# 1. Create GHCR.io PAT at: https://github.com/settings/tokens
#    Required scopes: read:packages, write:packages
#
# 2. Login:
#    echo "YOUR_GHCR_TOKEN" | docker login ghcr.io -u USERNAME --password-stdin
#
# 3. Tag + Push:
#    docker tag atom-operator:latest ghcr.io/YOUR_GHUSERNAME/atom-federation/atom-operator:7.0.0
#    docker push ghcr.io/YOUR_GHUSERNAME/atom-federation/atom-operator:7.0.0
#
# 4. Verify:
#    curl -s https://ghcr.io/v2/YOUR_GHUSERNAME/atom-federation/atom-operator/tags/list
# =====================================================================

set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io}"
ORG="${ORG:-atom-federation}"
IMAGE="${IMAGE:-atom-operator}"
TAG="${TAG:-7.0.0}"

FULL_IMAGE="${REGISTRY}/${ORG}/${IMAGE}:${TAG}"

read -rp "GHCR username: " GHCR_USER
read -sp "GHCR token (PAT): " GHCR_TOKEN
echo

echo "$GHCR_TOKEN" | docker login "${REGISTRY}" -u "$GHCR_USER" --password-stdin

docker tag "${IMAGE}:latest" "${REGISTRY}/${GHCR_USER}/${IMAGE}:${TAG}"
docker push "${REGISTRY}/${GHCR_USER}/${IMAGE}:${TAG}"

echo ""
echo "Image pushed: ${REGISTRY}/${GHCR_USER}/${IMAGE}:${TAG}"
echo "To use in manifests, update image in deployment.yaml"
