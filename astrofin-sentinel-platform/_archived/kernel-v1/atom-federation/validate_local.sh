#!/bin/bash
# =====================================================================
# STEP 5c — LOCAL K8S VALIDATION (KIND)
# Atom Federation OS — Kind Cluster Validation Runbook
# =====================================================================
set -euo pipefail

CLUSTER_NAME="${CLUSTER_NAME:-atom-os}"
OPERATOR_NS="${OPERATOR_NS:-atom-system}"
SAMPLE_NS="${SAMPLE_NS:-default}"

info()  { echo "[INFO]  $*" ; }
warn()  { echo "[WARN]  $*" ; }
fail()  { echo "[FAIL]  $*" ; exit 1 ; }

# ── Pre-flight ──────────────────────────────────────────────────────
for cmd in kind kubectl docker; do
    command -v $cmd >/dev/null 2>&1 || fail "$cmd not found. Install: https://kind.sigs.k8s.io/"
done

# ── Bootstrap ───────────────────────────────────────────────────────
info "Creating Kind cluster: $CLUSTER_NAME"
kind create cluster --name "$CLUSTER_NAME" --wait 5m

info "Setting context"
kubectl cluster-info --context "kind-$CLUSTER_NAME"
kubectl config set-context "kind-$CLUSTER_NAME"

# ── Install CRD + RBAC + Operator ────────────────────────────────────
info "Installing ATOM Operator..."
kubectl apply -f kubernetes/manifests/install.yaml

info "Installing sample ATOMCluster..."
kubectl apply -f kubernetes/manifests/sample.yaml

# Wait for operator to start
info "Waiting for operator to be Ready..."
kubectl wait --namespace "$OPERATOR_NS" \
    --for=condition=Ready \
    --selector=app=atom-operator \
    --timeout=120s

# ── Phase 1: CRD Validation ──────────────────────────────────────────
info "=== PHASE 1: CRD Installation ==="
kubectl get crd atomclusters.atom.io 2>/dev/null \
    && info "✓ CRD installed" \
    || fail "CRD not installed"

info "CRD schema..."
kubectl explain atomclusters 2>/dev/null | head -3 || fail "Cannot explain CRD"
kubectl explain atomclusters.status.nodes 2>/dev/null | head -3 || fail "Cannot explain CRD status"

# ── Phase 2: Operator Lifecycle ─────────────────────────────────────
info "=== PHASE 2: Operator Lifecycle ==="
OPERATOR_POD=$(kubectl get pods -n "$OPERATOR_NS" -l app=atom-operator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
[[ -z "$OPERATOR_POD" ]] && kubectl get pods -A | grep atom && fail "No operator pod found"

info "Operator pod: $OPERATOR_POD"
kubectl wait --namespace "$OPERATOR_NS" \
    --for=condition=Ready \
    pod/"$OPERATOR_POD" \
    --timeout=60s

info "Operator logs (first 50 lines)..."
kubectl logs -n "$OPERATOR_NS" "$OPERATOR_POD" --tail=50

# ── Phase 3: ATOMCluster Reconciliation ─────────────────────────────
info "=== PHASE 3: ATOMCluster Creation ==="
kubectl get atomclusters -n "$SAMPLE_NS"
kubectl get atomclusters -n "$SAMPLE_NS" -o wide

info "Waiting for ATOMCluster phase != Failed (90s)..."
timeout 90 bash -c '
    while true; do
        phase=$(kubectl get atomclusters sample -n $SAMPLE_NS -o jsonpath="{.status.phase}" 2>/dev/null)
        echo "  Phase: $phase"
        [[ "$phase" == "Running" ]] && exit 0
        [[ "$phase" == "Failed" ]]  && exit 2
        sleep 5
    done
' && info "✓ Cluster Running" || { fail "Cluster went to Failed or timeout"; }

info "Cluster full status:"
kubectl describe atomclusters sample -n "$SAMPLE_NS" | grep -A 40 "Status:"

# ── Phase 4: StatefulSet Lifecycle ───────────────────────────────────
info "=== PHASE 4: StatefulSet + Pods ==="
kubectl get sts -n "$SAMPLE_NS" -l app=atom-node
kubectl get pods -n "$SAMPLE_NS" -l app=atom-node -o wide

STS_REPLICAS=$(kubectl get sts -n "$SAMPLE_NS" -l app=atom-node -o jsonpath='{.items[0].spec.replicas}' 2>/dev/null || echo "0")
info "StatefulSet desired replicas: $STS_REPLICAS"

info "Waiting for all pods Running & Ready (180s)..."
kubectl wait --namespace "$SAMPLE_NS" \
    --for=condition=Ready \
    --selector=app=atom-node \
    --timeout=180s \
    && info "✓ All pods Ready" \
    || warn "Timeout waiting for pods — may still be starting"

# ── Phase 5: SBS Violation / Scale Drift ─────────────────────────────
info "=== PHASE 5: Scale Drift Reaction ==="
INITIAL_REPLICAS=$(kubectl get sts atom-node -n "$SAMPLE_NS" -o jsonpath='{.spec.replicas}')

info "Injecting scale drift (1 replica)..."
kubectl scale sts atom-node -n "$SAMPLE_NS" --replicas=1

info "Operator should restore desired replicas ($INITIAL_REPLICAS)..."
timeout 90 bash -c '
    while true; do
        replicas=$(kubectl get sts atom-node -n $SAMPLE_NS -o jsonpath="{.spec.replicas}" 2>/dev/null)
        echo "  STS replicas: $replicas"
        [[ "$replicas" == "$INITIAL_REPLICAS" ]] && exit 0
        sleep 5
    done
' && info "✓ PASS: Operator restored replicas" \
  || warn "TIMEOUT: Operator did not restore replicas in 90s"

# ── Phase 6: Pod Kill Recovery ───────────────────────────────────────
info "=== PHASE 6: Pod Kill / Restart Recovery ==="
TARGET_POD=$(kubectl get pods -n "$SAMPLE_NS" -l app=atom-node -o jsonpath='{.items[0].metadata.name}')
[[ -z "$TARGET_POD" ]] && warn "No atom-node pod found" || {
    info "Deleting pod: $TARGET_POD"
    kubectl delete pod "$TARGET_POD" -n "$SAMPLE_NS" --wait=false

    info "Waiting for replacement pod Ready (120s)..."
    kubectl wait --namespace "$SAMPLE_NS" \
        --for=condition=Ready \
        --selector=app=atom-node \
        --timeout=120s \
        && info "✓ PASS: Pod recreated and Ready" \
        || warn "TIMEOUT: Pod not recreated in 120s"

    info "Verifying cluster phase still Running..."
    kubectl get atomclusters sample -n "$SAMPLE_NS" -o jsonpath='{.status.phase}'
    echo ""
}

# ── Phase 7: Annotation Throttle ─────────────────────────────────────
info "=== PHASE 7: Annotation-Based Throttle ==="
kubectl patch atomclusters sample -n "$SAMPLE_NS" \
    --type=merge \
    -p '{"metadata":{"annotations":{"coherence_drift":"0.95"}}}'

sleep 10
THROTTLED=$(kubectl get atomclusters sample -n "$SAMPLE_NS" \
    -o jsonpath='{.metadata.annotations.throttled}' 2>/dev/null || echo "not-set")
info "Throttle annotation: throttled=$THROTTLED"

# Clean up
kubectl patch atomclusters sample -n "$SAMPLE_NS" \
    --type=merge \
    -p '{"metadata":{"annotations":{"coherence_drift":"0.0","throttled":"false"}}}'

# ── Final Report ─────────────────────────────────────────────────────
info ""
info "=============================================="
info "  STEP 5c — VALIDATION REPORT"
info "=============================================="
kubectl get crd atomclusters.atom.io 2>/dev/null && info "✓ CRD installed" || info "✗ CRD missing"
kubectl get pods -n "$OPERATOR_NS" -l app=atom-operator 2>/dev/null | grep -q Running && info "✓ Operator Running" || info "✗ Operator not Running"
kubectl get sts -n "$SAMPLE_NS" -l app=atom-node 2>/dev/null | grep -q "atom-node" && info "✓ StatefulSet exists" || info "✗ StatefulSet missing"
kubectl get atomclusters sample -n "$SAMPLE_NS" -o jsonpath='{.status.phase}' | grep -q "Running" && info "✓ Cluster Running" || info "✗ Cluster not Running"
kubectl get pods -n "$SAMPLE_NS" -l app=atom-node 2>/dev/null | grep -q "Running" && info "✓ Nodes Running" || info "✗ Nodes not Running"

info ""
info "Operator logs:"
kubectl logs -n "$OPERATOR_NS" "$OPERATOR_POD" --tail=20

info ""
info "To clean up: kind delete cluster --name $CLUSTER_NAME"
info "To re-run:   bash validate_local.sh"
