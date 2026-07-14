#!/bin/bash
#===============================================================================
# Sprint 2 Task 4 — cert-manager + TLS Setup
# Installs cert-manager via Helm and configures Let's Encrypt issuers
#===============================================================================
set -euo pipefail

LOGFILE="/var/log/cert-manager-setup-$(date +%Y%m%d-%H%M%S).log"
EMAIL="admin@${DOMAIN:-roma.internal}"
STAGING_EMAIL="staging@${DOMAIN:-roma.internal}"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

log()  { echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOGFILE"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOGFILE"; }
err()  { echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOGFILE"; exit 1; }

#--- Validate prerequisites ---
validate() {
  command -v kubectl >/dev/null 2>&1 || err "kubectl not found"
  command -v helm >/dev/null 2>&1 || err "helm not found"
  kubectl cluster-info >/dev/null 2>&1 || err "No cluster connection"
  log "Prerequisites OK"
}

#--- Install cert-manager via Helm ---
install_cert_manager() {
  log "Installing cert-manager v1.16.2 via Helm..."
  
  # Check if already installed
  if helm list -n cert-manager 2>/dev/null | grep -q cert-manager; then
    warn "cert-manager already installed, skipping Helm install"
    return 0
  fi

  # Install Jetstack Helm repo
  helm repo add jetstack https://charts.jetstack.io --force-update 2>>"$LOGFILE"
  helm repo update 2>>"$LOGFILE"

  # Install cert-manager CRDs first (required before Helm install)
  log "Installing CRDs..."
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.crds.yaml \
    2>>"$LOGFILE"

  # Helm install with ownership fix
  helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --create-namespace \
    --version v1.16.2 \
    --set startupapicheck.enabled=false \
    --set global.leaderElection.namespace=cert-manager \
    2>>"$LOGFILE"

  log "Waiting for cert-manager pod..."
  kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=cert-manager \
    -n cert-manager --timeout=120s 2>>"$LOGFILE" || warn "Timeout waiting — will continue"

  log "✅ cert-manager installed"
}

#--- Create ClusterIssuers (staging + production) ---
create_issuers() {
  log "Creating ClusterIssuer resources..."

  # Staging Issuer (Let's Encrypt staging — for testing)
  cat <<'STAGINGEOF' | kubectl apply -f - 2>>"$LOGFILE"
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
  annotations:
    description: "Let's Encrypt STAGING issuer for initial TLS testing"
spec:
  acme:
    server: https://acme-staging-v02.api.letsencrypt.org/directory
    email: STAGING_EMAIL_PLACEHOLDER
    privateKeySecretRef:
      name: letsencrypt-staging-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
STAGINGEOF

  # Production Issuer (Let's Encrypt production)
  cat <<'PRODEOF' | kubectl apply -f - 2>>"$LOGFILE"
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
  annotations:
    description: "Let's Encrypt PRODUCTION issuer — rate limited, use staging first"
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: PROD_EMAIL_PLACEHOLDER
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
      - http01:
          ingress:
            class: nginx
PRODEOF

  log "✅ ClusterIssuers created"
}

#--- Patch existing Kong ingress with TLS ---
patch_kong_tls() {
  log "Patching Kong ingress for TLS..."

  local ingress_file="deploy/k8s/ingresses/gateway-tls.yaml"

  cat <<'KONGEOF' > "$ingress_file"
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: kong-gateway-tls
  namespace: kong
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-staging
    kubernetes.io/tls-acme: "true"
    acme.cert-manager.io/http01-edit-in-place: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - kong.roma.internal
      secretName: kong-tls
  rules:
    - host: kong.roma.internal
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: proxy-kong
                port:
                  number: 80
KONGEOF

  kubectl apply -f "$ingress_file" 2>>"$LOGFILE"
  log "✅ Kong TLS ingress applied"
}

#--- Main ---
main() {
  echo "=============================================="
  echo "  cert-manager + TLS Setup — Sprint 2 Task 4"
  echo "=============================================="
  
  validate
  install_cert_manager
  create_issuers
  
  echo ""
  log "✅ Setup complete!"
  log "Next: patch your ingresses with cert-manager annotations"
  log "Example annotation: cert-manager.io/cluster-issuer: letsencrypt-staging"
  echo "Run 'kubectl get clusterissuer' to verify issuers"
  echo "Run 'kubectl get certificates' to see issued certs"
}

main "$@"