#!/bin/bash
# =====================================================================
# STEP 5b — CONTAINER IMAGE BUILD + PUSH
# Atom Federation OS — Operator Image Lifecycle
# =====================================================================
set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/atom-federation/atom-operator}"
TAG="${TAG:-7.0.0}"
FULL_IMAGE="${IMAGE}:${TAG}"
LATEST_IMAGE="${IMAGE}:latest"

info()  { echo "[INFO]  $*" ; }
warn()  { echo "[WARN]  $*" ; }
fail()  { echo "[FAIL]  $*" ; exit 1 ; }

for cmd in docker buildx kubectl; do
    command -v $cmd >/dev/null 2>&1 || fail "$cmd not found"
done

# ── Build Args ───────────────────────────────────────────────────────
PYTHON_VERSION="${PYTHON_VERSION:-3.11-slim}"
OPERATOR_BASE="${OPERATOR_BASE:-python:3.11-slim}"

# ── Build ────────────────────────────────────────────────────────────
info "Building operator image: $FULL_IMAGE"
info "Base: $OPERATOR_BASE"

docker build \
    --build-arg PYTHON_VERSION="$PYTHON_VERSION" \
    --build-arg OPERATOR_BASE="$OPERATOR_BASE" \
    -t "$FULL_IMAGE" \
    -t "$LATEST_IMAGE" \
    --progress=plain \
    kubernetes/operator/

info "Image built successfully"

# ── Test locally (optional) ─────────────────────────────────────────
info "Running smoke test..."
docker run --rm "$FULL_IMAGE" \
    python -c "
import sys, os
sys.path.insert(0, '/app')

# Smoke test — import all modules
from state import ClusterState, NodeState
from client import K8sClient
from reconciler import Reconciler
from controller import ATOMController

print('All modules imported OK')
print('ClusterState fields:', [f.name for f in ClusterState.__dataclass_fields__.values()])
print('Reconciler methods:', [m for m in dir(Reconciler) if not m.startswith('_')])
" || fail "Smoke test failed"

# ── Push ─────────────────────────────────────────────────────────────
info "Pushing to GHCR: $FULL_IMAGE"
docker push "$FULL_IMAGE" || fail "Push failed (check GHCR credentials: 'docker login ghcr.io')"
docker push "$LATEST_IMAGE" || warn "Failed to push latest tag"

info "Image pushed: $FULL_IMAGE"

# ── Update deployment manifests ──────────────────────────────────────
sed -i "s|image: ghcr.io/atom-federation/atom-operator:.*|image: $FULL_IMAGE|" \
    kubernetes/manifests/deployment.yaml

info "Updated deployment.yaml → image: $FULL_IMAGE"
grep "image:" kubernetes/manifests/deployment.yaml | head -3
