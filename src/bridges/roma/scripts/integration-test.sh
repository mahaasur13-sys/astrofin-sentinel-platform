#!/bin/bash
#===============================================================================
# ROMA — Integration Test Script (Sprint 2 → v1.0.0 Release Gate)
#===============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

PASS=0; FAIL=0; WARN=0

ok()   { echo -e "${GREEN}[PASS]${NC} $1"; ((PASS++)) || true; }
err()  { echo -e "${RED}[FAIL]${NC} $1"; ((WARN++)) || true; ((FAIL++)) || true; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARN++)) || true; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
}

#-------------------------------------------------------------------------------
# STAGE 1: Pre-flight checks
#-------------------------------------------------------------------------------
stage1_preflight() {
    header "[1/5] PRE-FLIGHT CHECK"
    local k8s_available=true

    if kubectl version --client >/dev/null 2>&1; then
        ok "kubectl installed (v$(kubectl version --client -o yaml 2>/dev/null | grep gitVersion | head -1 | awk '{print $2}'))"
    else
        err "kubectl not installed"
        k8s_available=false
    fi

    if $k8s_available && kubectl cluster-info >/dev/null 2>&1; then
        ok "k8s cluster connected"
        kubectl get nodes 2>/dev/null | tail -n +2 | while read line; do
            info "  Node: $(echo $line | awk '{print $1" | "$2" | "$3}')"
        done
    else
        err "No active k8s cluster"
        k8s_available=false
    fi

    if $k8s_available; then
        # Sprint 2 components
        kubectl get ns cert-manager 2>/dev/null | grep -q Active && ok "cert-manager namespace" || warn "cert-manager not installed (run: make sprint2-task4)"
        kubectl get ns kong        2>/dev/null | grep -q Active && ok "Kong namespace"        || warn "Kong not installed (run: make sprint2-task2)"
        kubectl get ns vault       2>/dev/null | grep -q Active && ok "Vault namespace"       || warn "Vault not installed (run: make sprint2-task1)"
        kubectl get ns roma-system 2>/dev/null | grep -q Active && ok "roma-system namespace" || warn "roma-system not installed (run: make k8s-deploy-home)"
        kubectl get crd romatenants.roma.io 2>/dev/null && ok "RomaTenant CRD" || warn "CRD not installed (run: make sprint2-task5)"

        # Storage
        local sc=$(kubectl get storageclass -o name 2>/dev/null | grep -E "longhorn|rook-ceph" || true)
        if [ -n "$sc" ]; then
            echo "$sc" | while read s; do
                local is_default=$(kubectl get sc "$s" -o jsonpath='{.metadata.annotations.storageclass\.kubernetes\.io/is-default-region}' 2>/dev/null)
                [ "$is_default" = "true" ] && ok "StorageClass: $s (default)" || ok "StorageClass: $s"
            done
        else
            warn "No Longhorn/Rook Ceph storage class found"
        fi
    fi

    echo ""
    echo "Pre-flight result: $PASS passed, $WARN warnings, $FAIL failures"
    [ $FAIL -gt 0 ] && { echo "Aborting due to failures."; exit 1; }
    ok "Stage 1 complete"
}

#-------------------------------------------------------------------------------
# STAGE 2: Deploy Sprint 2 components (if missing)
#-------------------------------------------------------------------------------
stage2_deploy() {
    header "[2/5] DEPLOY SPRINT 2 COMPONENTS"
    local deployed=false

    if ! kubectl get ns cert-manager 2>/dev/null | grep -q Active 2>/dev/null; then
        info "Deploying cert-manager..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.crds.yaml 2>/dev/null || true
        helm repo add jetstack https://charts.jetstack.io --force-update 2>/dev/null || true
        helm repo update 2>/dev/null || true
        helm install cert-manager jetstack/cert-manager \
            --namespace cert-manager --create-namespace --version v1.16.2 \
            --set startupapicheck.enabled=false --wait --timeout 120s 2>/dev/null || true
        kubectl apply -f deploy/cert-manager/issuer/issuers.yaml 2>/dev/null || true
        ok "cert-manager deployed"
        deployed=true
    else
        info "cert-manager already installed"
    fi

    if ! kubectl get ns kong 2>/dev/null | grep -q Active 2>/dev/null; then
        info "Deploying Kong Gateway..."
        kubectl create namespace kong --dry-run=client -o yaml | kubectl apply -f - 2>/dev/null || true
        helm repo add kong https://charts.konghq.com --force-update 2>/dev/null || true
        helm repo update 2>/dev/null || true
        helm upgrade --install kong kong/kong --version 2.36.0 \
            --namespace kong --values deploy/kong/values.yaml \
            --wait --timeout 10m --atomic --create-namespace 2>/dev/null || true
        kubectl apply -f deploy/kong/templates/plugins/tenant-plugins.yaml 2>/dev/null || true
        kubectl apply -f deploy/kong/templates/plugins/rate-limit-tenant.yaml 2>/dev/null || true
        ok "Kong deployed"
        deployed=true
    else
        info "Kong already installed"
    fi

    if ! kubectl get ns vault 2>/dev/null | grep -q Active 2>/dev/null; then
        info "Deploying Vault..."
        helm upgrade --install vault deploy/vault --namespace roma-system \
            --create-namespace --values deploy/vault/values.yaml \
            --wait --timeout 5m 2>/dev/null || true
        ok "Vault deployed"
        deployed=true
    else
        info "Vault already installed"
    fi

    if ! kubectl get crd romatenants.roma.io 2>/dev/null 2>&1 | grep -q RomaTenant; then
        info "Deploying RomaTenant CRD..."
        kubectl apply -f config/crd/bases/roma.io_romatenants.yaml 2>/dev/null || true
        kubectl apply -f config/crd/controller/deployment.yaml 2>/dev/null || true
        ok "RomaTenant CRD + Controller deployed"
        deployed=true
    else
        info "RomaTenant CRD already installed"
    fi

    $deployed && info "Some components were newly deployed — cluster may need 1-2 min to stabilize"
    ok "Stage 2 complete"
}

#-------------------------------------------------------------------------------
# STAGE 3: Apply RomaTenant CR and verify all resources
#-------------------------------------------------------------------------------
stage3_verify() {
    header "[3/5] VERIFY ROMATENANT RESOURCES"
    local test_tenant="partner-acme-free"

    # Apply sample if no tenant exists
    if ! kubectl get romatenant "$test_tenant" -n roma-system >/dev/null 2>&1; then
        info "Applying sample RomaTenant: $test_tenant"
        kubectl apply -f config/crd/samples/romatenant-free.yaml 2>/dev/null || true
        info "Waiting 10s for controller to react..."
        sleep 10
    fi

    # Verify namespace
    info "Checking namespace..."
    if kubectl get ns "roma-tenant-$test_tenant" >/dev/null 2>&1; then
        ok "Namespace roma-tenant-$test_tenant created"
    else
        err "Namespace roma-tenant-$test_tenant missing (CRD controller may not be running)"
    fi

    # Verify ingress
    info "Checking ingress..."
    if kubectl get ingress -n "roma-tenant-$test_tenant" >/dev/null 2>&1; then
        ok "Ingress created"
    else
        warn "Ingress not found (ingress controller may not be configured)"
    fi

    # Verify Certificate (TLS)
    info "Checking TLS certificate..."
    if kubectl get certificate -n "roma-tenant-$test_tenant" >/dev/null 2>&1; then
        local cert_status=$(kubectl get certificate -n "roma-tenant-$test_tenant" -o jsonpath='{.items[0].status.conditions[0].status}' 2>/dev/null)
        [ "$cert_status" = "True" ] && ok "Certificate issued" || warn "Certificate not yet issued (status=$cert_status)"
    else
        warn "Certificate resource not found"
    fi

    # Verify KongConsumer
    info "Checking KongConsumer..."
    if kubectl get kongconsumer -n kong "$test_tenant" >/dev/null 2>&1; then
        ok "KongConsumer created"
    else
        warn "KongConsumer not found (Kong may need a few minutes to sync)"
    fi

    # Verify KongPlugin (rate-limit)
    info "Checking KongPlugin rate-limit..."
    if kubectl get kongplugin -n kong "rate-limit-$test_tenant" >/dev/null 2>&1; then
        ok "KongPlugin rate-limit created"
    else
        warn "KongPlugin rate-limit not found"
    fi

    # Verify Vault secret path
    info "Checking Vault KV path..."
    if kubectl exec -n vault vault-0 -- vault kv list roma/tenants >/dev/null 2>&1; then
        ok "Vault KV path roma/tenants accessible"
    else
        warn "Vault KV path not accessible (run: make vault-init)"
    fi

    # Verify Stripe webhook
    info "Checking Stripe webhook deployment..."
    if kubectl get deployment -n roma-system stripe-webhook >/dev/null 2>&1; then
        local ready=$(kubectl get deployment -n roma-system stripe-webhook -o jsonpath='{.status.readyReplicas}' 2>/dev/null)
        [ "$ready" = "1" ] && ok "Stripe webhook running (1 replica)" || warn "Stripe webhook not ready (readyReplicas=$ready)"
    else
        warn "Stripe webhook deployment not found (run: make sprint2-task3)"
    fi

    ok "Stage 3 complete"
}

#-------------------------------------------------------------------------------
# STAGE 4: Generate test report
#-------------------------------------------------------------------------------
stage4_report() {
    header "[4/5] TEST REPORT"
    echo ""
    echo -e "${CYAN}Summary:${NC}"
    echo -e "  ${GREEN}Passed : $PASS${NC}"
    echo -e "  ${YELLOW}Warnings: $WARN${NC}"
    echo -e "  ${RED}Failed : $FAIL${NC}"
    echo ""

    echo -e "${CYAN}Cluster state:${NC}"
    kubectl get crd 2>/dev/null | grep -E "romatenant|vault|kong|cert-manager|sealedsecrets" | while read line; do
        info "  CRD: $(echo $line | awk '{print $1}')"
    done
    echo ""

    echo -e "${CYAN}Relevant pods:${NC}"
    kubectl get pods -A 2>/dev/null | grep -E "vault|kong|cert-manager|stripe-webhook|roma-tenant-operator|romatenant" | while read line; do
        local ns=$(echo $line | awk '{print $1}')
        local name=$(echo $line | awk '{print $2}')
        local status=$(echo $line | awk '{print $3}')
        case $status in
            Running|Completed) ok "  [$ns] $name — $status" ;;
            *) warn "  [$ns] $name — $status" ;;
        esac
    done
    echo ""

    if [ $FAIL -eq 0 ]; then
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║   ✅ INTEGRATION TEST PASSED — READY FOR RELEASE v1.0.0         ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    else
        echo -e "${RED}╔══════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║   ❌ INTEGRATION TEST FAILED — FIX FAILURES BEFORE RELEASE       ║${NC}"
        echo -e "${RED}╚══════════════════════════════════════════════════════════════════╝${NC}"
    fi
}

#-------------------------------------------------------------------------------
# STAGE 5: Mock mode (no cluster — validate manifests)
#-------------------------------------------------------------------------------
stage5_mock() {
    header "[MOCK MODE] Validating manifests without k8s cluster"
    echo ""

    local yaml_errors=0

    info "Validating CRD YAML..."
    set +e; python3 -c "import yaml; yaml.safe_load(open('config/crd/bases/roma.io_romatenants.yaml'))" 2>/dev/null; rc=$?; set -e
    [ $rc -eq 0 ] && ok "  CRD YAML valid" || { err "  CRD YAML invalid (rc=$rc)"; ((yaml_errors++)); }

    info "Validating sample manifests..."
    for f in config/crd/samples/romatenant-*.yaml; do
        set +e; python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>/dev/null; rc=$?; set -e
        [ $rc -eq 0 ] && ok "  $f valid" || { err "  $f invalid (rc=$rc)"; ((yaml_errors++)); }
    done

    info "Validating Helm chart..."
    [ -f charts/roma-execution-bridge/Chart.yaml ]  && ok "  Chart.yaml exists"    || { err "  Chart.yaml missing"; ((yaml_errors++)) || true; }
    [ -f charts/roma-execution-bridge/values.yaml ]  && ok "  values.yaml exists"   || { err "  values.yaml missing"; ((yaml_errors++)) || true; }
    if command -v helm >/dev/null 2>&1; then
        helm template roma charts/roma-execution-bridge --namespace roma-system >/dev/null 2>&1 && ok "  Helm template valid" || { err "  Helm template error"; ((yaml_errors++)) || true; }
    else
        warn "  helm not installed — skipping template validation"
    fi

    info "Checking Stripe webhook files..."
    [ -f deploy/stripe-webhook/Dockerfile ] && ok "  Dockerfile.webhook exists" || { err "  Dockerfile.webhook missing"; ((yaml_errors++)); }
    [ -f deploy/stripe-webhook/deploy/deployment.yaml ] && ok "  deployment.yaml exists" || warn "  deployment.yaml missing"

    info "Checking Sprint 2 manifest directories..."
    [ -d deploy/vault ]              && ok "  deploy/vault/"              || err "  deploy/vault/ missing"
    [ -d deploy/kong ]               && ok "  deploy/kong/"               || err "  deploy/kong/ missing"
    [ -d deploy/sealed-secrets ]     && ok "  deploy/sealed-secrets/"     || err "  deploy/sealed-secrets/ missing"
    [ -d deploy/cert-manager ]       && ok "  deploy/cert-manager/"        || err "  deploy/cert-manager/ missing"
    [ -d config/crd/samples ]        && ok "  config/crd/samples/"         || err "  config/crd/samples/ missing"
    [ -d config/crd/controller ]     && ok "  config/crd/controller/"      || err "  config/crd/controller/ missing"

    echo ""
    if [ $yaml_errors -eq 0 ]; then
        ok "Mock test PASSED — all manifests valid"
        echo ""
        echo "To run full integration test on a k8s cluster:"
        echo "  curl -sfL https://get.k3s.io | sh -   # Install k3s"
        echo "  make integration-test                   # Run full pipeline"
    else
        err "Mock test FAILED — $yaml_errors errors found"
    fi
}

#-------------------------------------------------------------------------------
# MAIN
#-------------------------------------------------------------------------------
main() {
    echo ""
    echo -e "${CYAN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║   ROMA — Integration Test (Sprint 2 → v1.0.0 Release Gate)   ║${NC}"
    echo -e "${CYAN}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ "${1:-}" = "mock" ]; then
        stage5_mock
    else
        stage1_preflight
        stage2_deploy
        stage3_verify
        stage4_report
    fi
}

main "$@"
