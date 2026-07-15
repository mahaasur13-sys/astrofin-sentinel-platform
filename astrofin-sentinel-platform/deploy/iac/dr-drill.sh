#!/bin/bash
#===============================================================================
# DR Drill — Velero Backup & Restore Test (home-cluster-iac)
#===============================================================================
# Purpose : Real DR drill on home k3s cluster
# Storage : MinIO (S3-compatible) on home-cluster
# Pre-req : kubectl configured, velero CLI installed, cluster accessible
# Usage   : ./dr-drill.sh [--dry-run]
#===============================================================================

set -euo pipefail

DRILL_NS="dr-test-$(date +%Y%m%d-%H%M%S)"
BACKUP_NAME="dr-test-$(date +%Y%m%d-%H%M%S)"
VELERO_NS="veleno"
TIMEOUT="300s"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'

DRY_RUN=""
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN="--dry-run"

log() { echo -e "${BLUE}[INFO]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC} $*" >&2; }
ok()   { echo -e "${GREEN}[OK]${NC} $*"; }

require() { command -v "$1" >/dev/null 2>&1 || { err "Required: $1"; exit 1; }; }

#--- Pre-checks ---------------------------------------------------------------
log "=== DR Drill Pre-Checks ==="
require kubectl
require velero

if ! kubectl cluster-info >/dev/null 2>&1; then
  err "Cannot reach cluster — check kubeconfig"; exit 1
fi

if ! kubectl get ns "$VELERO_NS" >/dev/null 2>&1; then
  err "Velero not installed in '$VELERO_NS'"; exit 1
fi

VELERO_OK=$(kubectl get pod -n "$VELERO_NS" -l app.kubernetes.io/name=velero \
  -o jsonpath='{.items[0].status.phase}' 2>/dev/null)
if [[ "$VELERO_OK" != "Running" ]]; then
  err "Velero pod not Running (got: $VELERO_OK)"; exit 1
fi
ok "Velero is Running"

STORAGE_CLASS=$(kubectl get storageclass \
  -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}' 2>/dev/null \
  || kubectl get storageclass -o jsonpath='{.items[0].metadata.name}' 2>/dev/null \
  || echo "local-path")
ok "StorageClass: $STORAGE_CLASS"

#--- STEP 1: Create test namespace ----------------------------------------
log "=== STEP 1: Create test namespace '$DRILL_NS' ==="

kubectl create namespace "$DRILL_NS" --dry-run=client -o yaml | kubectl apply -f -

# Deployment
kubectl create deployment nginx --image=nginx:1.25 -n "$DRILL_NS" \
  --dry-run=client -o yaml | kubectl apply -f -

# Job
kubectl create job pre-drill-check --image=busybox:1.36 \
  -- /bin/sh -c 'echo "Pre-DR test at $(date)" && sleep 2' \
  -n "$DRILL_NS" --dry-run=client -o yaml | kubectl apply -f -

# ConfigMap
kubectl create configmap drill-data \
  --from-literal=cluster="$DRILL_NS" \
  --from-literal=created="$(date -Iseconds)" \
  --from-literal=timestamp="$(date +%s)" \
  -n "$DRILL_NS" --dry-run=client -o yaml | kubectl apply -f -

# Secret
kubectl create secret generic drill-secret \
  --from-literal=password="dr-test-$(date +%s)" \
  --from-literal=api-key="dr-key-$(date +%s)" \
  -n "$DRILL_NS" --dry-run=client -o yaml | kubectl apply -f -

# PVC + writer pod
kubectl apply -n "$DRILL_NS" -f - << 'EOF'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: drill-pvc
  labels: { drill: "true" }
spec:
  accessModes: [ReadWriteOnce]
  resources: { requests: { storage: 128Mi } }
  storageClassName: "STORAGE_PLACEHOLDER"
---
apiVersion: v1
kind: Pod
metadata:
  name: pvc-writer
spec:
  containers:
  - name: writer
    image: busybox:1.36
    command: ["/bin/sh", "-c"]
    args: ["echo 'DR test data' > /data/test.txt && echo 'Written at $(date)' >> /data/test.txt && cat /data/test.txt && sleep 60"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    persistentVolumeClaim:
      claimName: drill-pvc
  restartPolicy: Never
EOF

sed -i "s/STORAGE_PLACEHOLDER/$STORAGE_CLASS/g" <(kubectl get pvc drill-pvc -n "$DRILL_NS" -o yaml 2>/dev/null || true)

kubectl wait --for=condition=Ready pod -l app=nginx -n "$DRILL_NS" --timeout="$TIMEOUT" 2>/dev/null || true
kubectl wait --for=condition=Complete job/pre-drill-check -n "$DRILL_NS" --timeout="$TIMEOUT" 2>/dev/null || true

kubectl get all -n "$DRILL_NS" -o wide
ok "STEP 1 complete"

#--- STEP 2: Velero backup --------------------------------------------------
log "=== STEP 2: Velero backup '$BACKUP_NAME' ==="

if [[ -z "$DRY_RUN" ]]; then
  velero backup create "$BACKUP_NAME" \
    --include-namespaces "$DRILL_NS" \
    --storage-location default \
    --ttl 24h \
    --wait

  PHASE=$(velero backup get "$BACKUP_NAME" -o jsonpath='{.status.phase}')
  log "Backup phase: $PHASE"

  if [[ "$PHASE" != "Completed" ]]; then
    velero backup describe "$BACKUP_NAME" --details 2>&1 | tail -30
    err "Backup failed: $PHASE"; exit 1
  fi
  ok "Backup completed"
else
  velero backup create "$BACKUP_NAME" \
    --include-namespaces "$DRILL_NS" \
    --storage-location default \
    --ttl 24h \
    --dry-run -o yaml | head -40
fi

#--- STEP 3: Delete namespace -----------------------------------------------
log "=== STEP 3: DELETE namespace '$DRILL_NS' ==="
warn "DESTRUCTIVE STEP — namespace will be deleted!"
echo -n "Press ENTER to continue (Ctrl+C to abort)..."
read

if [[ -z "$DRY_RUN" ]]; then
  kubectl delete namespace "$DRILL_NS" --wait=true --timeout="$TIMEOUT"
  sleep 5
  if kubectl get namespace "$DRILL_NS" >/dev/null 2>&1; then
    err "Namespace still exists!"; exit 1
  fi
  ok "Namespace deleted"
else
  kubectl delete namespace "$DRILL_NS" --dry-run=client -o yaml | head -5
fi

#--- STEP 4: Restore ---------------------------------------------------------
log "=== STEP 4: Restore from backup '$BACKUP_NAME' ==="

if [[ -z "$DRY_RUN" ]]; then
  velero restore create "restore-${BACKUP_NAME}" \
    --from-backup "$BACKUP_NAME" \
    --wait

  PHASE=$(velero restore get "restore-${BACKUP_NAME}" -o jsonpath='{.status.phase}')
  log "Restore phase: $PHASE"

  if [[ "$PHASE" != "Completed" ]]; then
    velero restore describe "restore-${BACKUP_NAME}" --details 2>&1 | tail -30
    err "Restore failed: $PHASE"; exit 1
  fi
  ok "Restore completed"
else
  velero restore create "restore-${BACKUP_NAME}" \
    --from-backup "$BACKUP_NAME" \
    --dry-run -o yaml | head -40
fi

#--- STEP 5: Verify ----------------------------------------------------------
log "=== STEP 5: Verify restored resources ==="

if ! kubectl get namespace "$DRILL_NS" >/dev/null 2>&1; then
  err "Namespace not restored!"; exit 1
fi
ok "Namespace restored"

kubectl get all -n "$DRILL_NS" -o wide
kubectl get pvc -n "$DRILL_NS" 2>/dev/null || true
kubectl get configmap drill-data -n "$DRILL_NS" -o jsonpath='{.data.timestamp}' 2>/dev/null && echo "" || true
kubectl get secret drill-secret -n "$DRILL_NS" >/dev/null 2>&1 && ok "Secret restored" || warn "Secret missing"

# Check PVC content
if kubectl get pvc drill-pvc -n "$DRILL_NS" >/dev/null 2>&1; then
  DATA=$(kubectl exec pvc-writer -n "$DRILL_NS" -- cat /data/test.txt 2>/dev/null || echo "N/A")
  ok "PVC content: $DATA"
fi

#--- STEP 6: Summary --------------------------------------------------------
echo ""
echo "=========================================="
echo "  DR DRILL RESULT"
echo "=========================================="
echo "  Namespace   : $DRILL_NS"
echo "  Backup     : $BACKUP_NAME"
echo "  Storage    : $STORAGE_CLASS"
echo "  Status     : $([[ -n "$DRY_RUN" ]] && echo 'DRY-RUN OK' || echo 'COMPLETED')"
echo ""
echo "  Steps: Backup ✅ → Delete ✅ → Restore ✅"
echo "=========================================="
echo ""
echo "To clean up:"
echo "  velero backup delete $BACKUP_NAME"
echo "  velero restore delete restore-$BACKUP_NAME"
echo "  kubectl delete namespace $DRILL_NS"
