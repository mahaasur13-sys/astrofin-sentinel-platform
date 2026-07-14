#!/usr/bin/env bash
# encrypt-secret.sh — Encrypt a secret using kubeseal for SealedSecrets
set -euo pipefail

NAMESPACE="${NAMESPACE:-roma-system}"
SECRET_NAME="${SECRET_NAME:-stripe-webhook-secret}"
SEALED_OUTPUT="${SEALED_OUTPUT:-deploy/stripe-webhook/deploy/sealed-secret.yaml}"

if ! command -v kubeseal &>/dev/null; then
    echo "[WARN] kubeseal not found — install: https://github.com/bitnami-labs/sealed-secrets"
    echo "[INFO] Creating plain secret YAML instead (NOT for Git commit!)"
    kubectl create secret generic "${SECRET_NAME}" \
        --namespace "${NAMESPACE}" \
        --from-literal=STRIPE_WEBHOOK_SECRET="whsec-REDACTED-xxx" \
        --dry-run=o yaml > "${SEALED_OUTPUT}"
    echo "[WARN] Plain secret written to ${SEALED_OUTPUT} — DO NOT COMMIT TO GIT"
    exit 0
fi

echo "[INFO] Encrypting secret via kubeseal..."
kubeseal --scope namespace-wide \
         --namespace "${NAMESPACE}" \
         --format yaml \
         --secret-name "${SECRET_NAME}" \
         --file - > "${SEALED_OUTPUT}" <<'EOF'
apiVersion: v1
kind: Secret
metadata:
  name: stripe-webhook-secret
  namespace: roma-system
type: Opaque
stringData:
  STRIPE_WEBHOOK_SECRET: "REPLACE_WITH_WHSEC_xxx"
EOF

echo "[OK] SealedSecret written to ${SEALED_OUTPUT}"
echo "[INFO] Commit encrypted file to Git safely."