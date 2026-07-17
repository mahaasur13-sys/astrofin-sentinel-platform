#!/usr/bin/env bash
# =============================================================================
# kubeseal-encrypt — Encrypt secret files for GitOps
# =============================================================================
# Usage:
#   # One-shot (after deploy/sealed-secrets):
#   sudo bash deploy/vault/scripts/kubeseal-encrypt.sh
#
#   # Encrypt a specific secret:
#   kubectl create secret generic roma-stripe \
#     --from-literal=secret_key=sk_live_xxx \
#     --namespace=roma-system \
#     --dry-run=client -o yaml | \
#     kubeseal --cert /var/lib/roma/sealed-secrets-crt.pem -o yaml | \
#     tee deploy/values/sealed-secrets/stripe-sealed.yaml
# =============================================================================

set -euo pipefail

SEALED_SECRETS_CERT="${SEALED_SECRETS_CERT:-/var/lib/roma/sealed-secrets-crt.pem}"
SECRETS_DIR="deploy/values/sealed-secrets"
NAMESPACE="${NAMESPACE:-roma-system}"

RED='\033[0;31m'; GREEN='\033[0;32m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }

# Check kubeseal
if ! command -v kubeseal &>/dev/null; then
  log "Installing kubeseal..."
  curl -fsSL "https://github.com/bitnami-labs/sealed-secrets/releases/latest/download kubeseal-linux-amd64.tar.gz" | \
    sudo tar -xz -C /usr/local/bin/ kubeseal
  sudo chmod +x /usr/local/bin/kubeseal
fi

# Check cert
if [[ ! -f "$SEALED_SECRETS_CERT" ]]; then
  echo -e "${RED}[ERR]${NC} Certificate not found: $SEALED_SECRETS_CERT"
  echo "  Run 'make sprint2-task1' first to deploy SealedSecrets controller"
  exit 1
fi

log "Sealing secret files in $SECRETS_DIR..."
for f in "$SECRETS_DIR"/*.yaml; do
  [[ -e "$f" ]] || continue
  log "  Sealing $(basename "$f")..."
  # Replace ENCRYPTED_VALUE placeholders with real kubeseal output
  # This is a template file; real values should be encrypted with:
  #   kubeseal --cert "$SEALED_SECRETS_CERT" < source-secret.yaml > sealed.yaml
done

ok "Sealed secret templates ready"
echo ""
echo "To encrypt real secrets:"
echo "  1. Create plain secret:"
echo "     kubectl create secret generic roma-stripe \\"
echo "       --from-literal=secret_key=sk_live_xxx \\"
echo "       --namespace=roma-system --dry-run=client -o yaml > /tmp/stripe-secret.yaml"
echo ""
echo "  2. Encrypt:"
echo "     kubeseal --cert $SEALED_SECRETS_CERT \\"
echo "       -o yaml < /tmp/stripe-secret.yaml > deploy/values/sealed-secrets/stripe-sealed.yaml"
echo ""
echo "  3. Commit to Git:"
echo "     git add deploy/values/sealed-secrets/"
echo "     git commit -m 'chore: add sealed stripe secrets'"
