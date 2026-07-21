#!/usr/bin/env bash
# =============================================================================
# Vault Init Script — ROMA Execution Bridge
# =============================================================================
# Usage:
#   # Home cluster (dev):
#   sudo bash deploy/vault/scripts/vault-init.sh
#
#   # Production (with AWS KMS auto-unseal):
#   VAULT_UNSEAL_TYPE=aws KMS_KEY_ID=alias/vault-unseal \
#     VAULT_AWS_REGION=us-east-1 \
#     sudo bash deploy/vault/scripts/vault-init.sh
# =============================================================================

set -euo pipefail

# --- Config -------------------------------------------------------------------
VAULT_NAMESPACE="${VAULT_NAMESPACE:-roma-system}"
VAULT_CHART="${VAULT_CHART:-deploy/vault}"
SECRET_NAME="roma-vault-sealed"
VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
TOKEN_FILE="/var/lib/roma/vault-unseal-token"

# --- Color output -------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC}  $*" >&2; }

# --- Check prerequisites ------------------------------------------------------
check_prereq() {
  log "Checking prerequisites..."
  for cmd in kubectl helm vault; do
    if ! command -v "$cmd" &>/dev/null; then
      err "$cmd not found. Install: https://developer.hashicorp.com/vault/install"
      exit 1
    fi
  done

  # Check cluster connectivity
  if ! kubectl cluster-info &>/dev/null; then
    err "Cannot reach Kubernetes cluster. Check kubeconfig."
    exit 1
  fi

  # Check namespace
  if ! kubectl get namespace "$VAULT_NAMESPACE" &>/dev/null; then
    kubectl create namespace "$VAULT_NAMESPACE"
    ok "Created namespace: $VAULT_NAMESPACE"
  fi

  ok "Prerequisites OK"
}

# --- Deploy Vault --------------------------------------------------------------
deploy_vault() {
  log "Deploying Vault via Helm..."

  # Disable injection by default for security; per-pod opt-in
  helm upgrade --install vault "$VAULT_CHART" \
    --namespace "$VAULT_NAMESPACE" \
    --create-namespace \
    --values "$VAULT_CHART/values.yaml" \
    --wait --timeout 5m \
    --debug

  ok "Vault deployed. Waiting for pod..."
  kubectl rollout status deployment/vault -n "$VAULT_NAMESPACE" --timeout=120s
  ok "Vault pod is ready"
}

# --- Init Vault (dev mode tokens) --------------------------------------------
init_vault_dev() {
  log "Initializing Vault (dev mode)..."

  # Dev mode auto-unseals; we just need the root token
  local pod
  pod=$(kubectl get pods -n "$VAULT_NAMESPACE" -l app.kubernetes.io/name=vault \
    -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

  if [[ -z "$pod" ]]; then
    err "Vault pod not found"
    exit 1
  fi

  # Get dev root token from pod logs
  local token
  token=$(kubectl exec -n "$VAULT_NAMESPACE" "$pod" -- vault print token 2>/dev/null || \
          kubectl logs -n "$VAULT_NAMESPACE" "$pod" | grep 'Root Token' | awk '{print $NF}' | head -1)

  if [[ -z "$token" ]]; then
    # Fallback: read from file inside container
    token=$(kubectl exec -n "$VAULT_NAMESPACE" "$pod" -- cat /vault/file/.vault-unseal-token 2>/dev/null || \
            kubectl exec -n "$VAULT_NAMESPACE" "$pod" -- cat /tmp/vault-token 2>/dev/null)
  fi

  if [[ -z "$token" ]]; then
    err "Could not retrieve Vault token. Check pod logs: kubectl -n $VAULT_NAMESPACE logs $pod"
    exit 1
  fi

  # Verify connectivity
  export VAULT_TOKEN="$token"
  local tries=10
  while ! vault status &>/dev/null; do
    sleep 2
    ((tries--)) || break
  done

  if vault status &>/dev/null; then
    ok "Vault is initialized and unsealed"
  else
    warn "Vault may still be initializing. Trying direct pod exec..."
    kubectl exec -n "$VAULT_NAMESPACE" "$pod" -- vault status
  fi

  echo ""
  log "Root token: ${token:0:8}... (truncated for safety)"
  echo "$token" > "$TOKEN_FILE"
  chmod 600 "$TOKEN_FILE"
  ok "Token saved to $TOKEN_FILE"

  # Configure env var for subsequent commands
  echo "export VAULT_TOKEN='$token'" > /etc/profile.d/roma-vault.sh
  chmod +x /etc/profile.d/roma-vault.sh
  ok "Added VAULT_TOKEN to /etc/profile.d/roma-vault.sh"
}

# --- Create ROMA secrets engine -----------------------------------------------
create_secrets_engine() {
  log "Configuring ROMA secrets engine..."

  export VAULT_TOKEN
  VAULT_TOKEN=$(cat "$TOKEN_FILE" 2>/dev/null || echo "")

  # KV secrets engine v2
  vault secrets enable -path=roma -version=2 kv 2>/dev/null || \
    log "KV engine already enabled"

  # Enable Kubernetes auth (for k8s service account JWT)
  vault auth enable kubernetes 2>/dev/null || \
    log "Kubernetes auth already enabled"

  # Configure k8s auth
  vault write auth/kubernetes/config \
    token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt \
    2>/dev/null || warn "K8s auth config failed (expected in dev mode)"

  ok "Secrets engine configured"
}

# --- Create static secrets (Stripe, DB, API keys) ----------------------------
create_static_secrets() {
  log "Creating ROMA static secrets..."

  export VAULT_TOKEN
  VAULT_TOKEN=$(cat "$TOKEN_FILE")

  # Stripe API keys
  vault kv put roma/stripe \
    secret_key="PLACEHOLDER_STRIPE_SECRET" \
    webhook_secret="whsec_XXXXXXXXXXXXXXXXXXXXXXXX" \
    2>/dev/null || warn "Stripe secrets already exist"

  # PostgreSQL connection string
  vault kv put roma/database \
    host="roma-postgres.roma-system.svc.cluster.local" \
    port="5432" \
    username="roma" \
    password="CHANGE_ME" \
    database="roma" \
    2>/dev/null || warn "DB secrets already exist"

  # ROMA API keys
  vault kv put roma/api \
    roma_api_key="roma_PLACEHOLDER_STRIPE_SECRET" \
    roma_webhook_secret="whsec_roma_XXXXXXXXXXXXXXXX" \
    2>/dev/null || warn "API secrets already exist"

  # Redis
  vault kv put roma/redis \
    host="roma-redis.roma-system.svc.cluster.local" \
    port="6379" \
    password="CHANGE_ME" \
    2>/dev/null || warn "Redis secrets already exist"

  ok "Static secrets created"
  echo ""
  log "⚠️  NEXT: Run 'make vault-seal' to seal the vault after initial setup"
  echo "         In production, enable AWS/GCP/Azure auto-unseal instead"
}

# --- Apply SealedSecrets CRD --------------------------------------------------
deploy_sealed_secrets() {
  log "Deploying SealedSecrets controller..."

  # Install SealedSecrets via Helm (bitnami chart)
  helm upgrade --install sealed-secrets sealed-secrets \
    --repo https://charts.bitnami.com/bitnami \
    --namespace kube-system \
    --create-namespace \
    --set-string controller.resources.requests.memory="64Mi" \
    --set-string controller.resources.requests.cpu="50m" \
    --wait --timeout 3m

  ok "SealedSecrets controller installed in kube-system"
  kubectl rollout status deployment/sealed-secrets -n kube-system --timeout=60s

  # Save unsealed master key for emergency recovery
  local key
  key=$(kubectl get secret -n kube-system -l sealedsecrets.bitnami.com/key-v1-null \
    -o jsonpath='{.items[0].data.tls\.crt}' 2>/dev/null || echo "")

  if [[ -n "$key" ]]; then
    echo "$key" | base64 -d > /var/lib/roma/sealed-secrets-crt.pem
    chmod 600 /var/lib/roma/sealed-secrets-crt.pem
    ok "SealedSecrets certificate saved to /var/lib/roma/sealed-secrets-crt.pem"
  fi
}

# --- Apply SealedSecrets templates ---------------------------------------------
apply_sealed_secret_templates() {
  log "Applying SealedSecret templates..."
  local ts_dir="deploy/values/sealed-secrets"
  for f in "$ts_dir"/*.yaml; do
    [[ -e "$f" ]] || continue
    log "  Applying $(basename "$f")..."
    kubectl apply -f "$f"
  done
  ok "SealedSecret templates applied"
}

# --- Usage --------------------------------------------------------------------
usage() {
  cat <<EOF
Usage: $0 <command>

Commands:
  all          Deploy Vault + SealedSecrets + init secrets
  vault        Deploy Vault Helm chart only
  vault-init   Initialize Vault (dev mode, get tokens)
  vault-seal   Seal Vault (stop using, lock down)
  sealed       Deploy SealedSecrets controller
  secrets      Create ROMA static secrets in Vault
  help         Show this help

Environment:
  VAULT_NAMESPACE    Kubernetes namespace (default: roma-system)
  VAULT_ADDR         Vault address (default: http://vault:8200)

Examples:
  # Full install (home cluster):
  sudo bash deploy/vault/scripts/vault-init.sh all

  # Production (AWS auto-unseal):
  VAULT_UNSEAL_TYPE=aws KMS_KEY_ID=alias/vault-unseal \\
    VAULT_AWS_REGION=us-east-1 \\
    sudo bash deploy/vault/scripts/vault-init.sh all

  # Just sealed secrets:
  sudo bash deploy/vault/scripts/vault-init.sh sealed
EOF
}

# --- Main ---------------------------------------------------------------------
main() {
  local cmd="${1:-all}"

  case "$cmd" in
    all)
      check_prereq
      deploy_vault
      init_vault_dev
      create_secrets_engine
      create_static_secrets
      deploy_sealed_secrets
      apply_sealed_secret_templates
      echo ""
      ok "=== Vault + SealedSecrets fully initialized ==="
      echo ""
      echo "Next steps:"
      echo "  kubectl -n $VAULT_NAMESPACE get pods  # verify Vault running"
      echo "  kubectl -n kube-system get pods        # verify SealedSecrets running"
      echo "  make vault-status                      # check Vault health"
      ;;
    vault)        check_prereq; deploy_vault ;;
    vault-init)   check_prereq; deploy_vault; init_vault_dev ;;
    vault-seal)   check_prereq; kubectl exec -n "$VAULT_NAMESPACE" \
                      "$(kubectl get pods -n "$VAULT_NAMESPACE" -l app.kubernetes.io/name=vault \
                      -o jsonpath='{.items[0].metadata.name}')" -- vault operator seal ;;
    sealed)       check_prereq; deploy_sealed_secrets; apply_sealed_secret_templates ;;
    secrets)      check_prereq; create_static_secrets ;;
    help)         usage ;;
    *)            usage; exit 1 ;;
  esac
}

main "$@"
