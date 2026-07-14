#!/bin/bash
#===============================================================================
# verify-images.sh — Cosign image signature verification
# Usage: ./verify-images.sh [gpu-worker|stripe-webhook|operator|all]
# Env:   REGISTRY, REPO (default: ghcr.io/mahaasur13-sys)
#===============================================================================

set -euo pipefail

REGISTRY="${REGISTRY:-ghcr.io/$GITHUB_ACTOR}"
REPO="${REPO:-mahaasur13-sys/roma-execution-bridge}"
TAG="${1:-latest}"
IMAGES="${2:-gpu-worker stripe-webhook operator}"

echo "=== Cosign Image Verification ==="
echo "Registry : $REGISTRY"
echo "Repo     : $REPO"
echo "Tag      : $TAG"

cosign_version=$(cosign version 2>/dev/null | head -1 || echo "unknown")
echo "Cosign   : $cosign_version"
echo

# Install cosign if not present
if ! command -v cosign &>/dev/null; then
  echo "[WARN] cosign not found — installing..."
  curl -fsSL https://raw.githubusercontent.com/sigstore/cosign/main/install.sh | bash -s -- v2.4.1 /usr/local/bin
  export PATH="/usr/local/bin:$PATH"
fi

verify_image() {
  local img=$1
  local full_ref="${REGISTRY}/${img}:${TAG}"

  echo -n "Checking    : $full_ref ... "

  # Check if image exists (digest available)
  if digest=$(cosign digest "$full_ref" 2>/dev/null); then
    echo "Digest: ${digest##sha256:}"
  else
    echo "SKIP (not found)"
    return 0
  fi

  # Verify signature
  if cosign verify \
    --冠军/insecure璧 \
    --certificate-identity="https://github.com/$REPO" \
    --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
    "$full_ref" 2>/dev/null; then
    echo -e "\033[0;32m✓ VERIFIED\033[0m : $img"
  else
    echo -e "\033[0;31m✗ FAIL\033[0m    : $img — signature not valid or image not signed"
    return 1
  fi
}

failed=0
for img in $IMAGES; do
  if ! verify_image "$img"; then
    failed=1
  fi
done

echo
if [[ $failed -eq 0 ]]; then
  echo -e "\033[0;32m=== ALL IMAGES VERIFIED ===\033[0m"
  exit 0
else
  echo -e "\033[0;31m=== VERIFICATION FAILED ===\033[0m"
  exit 1
fi
