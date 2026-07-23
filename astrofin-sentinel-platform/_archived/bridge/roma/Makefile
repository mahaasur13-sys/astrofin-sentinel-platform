.PHONY: install run bridge cli test lint clean

install:
	pip install -e ".[dev]"

run-bridge:
	uvicorn main:app --host 0.0.0.0 --port 8080 --reload

cli:
	python roma_cli.py run "$(TASK)"

status:
	python roma_cli.py status $(JOB_ID)

logs:
	python roma_cli.py logs $(JOB_ID) -n $(LINES)

list:
	python roma_cli.py list

health:
	python roma_cli.py health

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# =============================================================================
# Kubernetes Deployment
# =============================================================================

.PHONY: k8s-deploy k8s-deploy-home k8s-deploy-prod k8s-deploy-all \
        k8s-delete k8s-logs k8s-status k8s-portforward \
        k8s-crd k8s-allinone k8s-kustomize-build

# Prerequisites
k8s-crd:
	@echo "Applying ROMA CRD..."
	kubectl apply -f k8s/roma-crd.yaml
	kubectl apply -f k8s/rbac-roma-executor.yaml
	@echo "CRD installed. RomaTask kind available."

# Deploy to k3s (home cluster) — flat YAML
k8s-deploy-home: k8s-crd
	@echo "Deploying ROMA to home cluster..."
	kubectl apply -f deploy/manifests/all-in-one.yaml
	kubectl -n roma-system get pods,svc,pvc

# Deploy via Kustomize (home cluster overlay)
k8s-deploy-kustomize-home:
	kubectl apply -k deploy/overlays/home-cluster

# Deploy via Kustomize (production overlay)
k8s-deploy-kustomize-prod:
	kubectl apply -k deploy/overlays/production

# All-in-one manifest (single file, no kustomize)
k8s-allinone:
	@echo "Deploying all-in-one manifest..."
	kubectl apply -f deploy/manifests/all-in-one.yaml

# Build kustomize (dry-run)
k8s-kustomize-build:
	kustomize build deploy/overlays/home-cluster
	kustomize build deploy/overlays/production

# Delete
k8s-delete:
	@echo "Deleting ROMA from cluster..."
	kubectl delete -f deploy/manifests/all-in-one.yaml --ignore-not-found=true
	kubectl delete -f k8s/roma-crd.yaml --ignore-not-found=true

# Logs
k8s-logs:
	kubectl -n roma-system logs -l app.kubernetes.io/component=api-server --tail=$(LINES) -f

k8s-logs-gpu:
	kubectl -n roma-system logs -l app.kubernetes.io/component=gpu-worker --tail=$(LINES) -f

# Status
k8s-status:
	@echo "=== ROMA Status ==="
	@kubectl -n roma-system get all,configmap,secret,pvc
	@echo ""
	@echo "=== Pods ==="
	@kubectl -n roma-system get pods -o wide
	@echo ""
	@echo "=== Services ==="
	@kubectl -n roma-system get svc -o wide

# Port-forward (default: localhost:8080)
k8s-portforward:
	kubectl port-forward -n roma-system svc/roma-api-server 8080:8080 &

# =============================================================================
# Sprint 2 — Production Hardening
# =============================================================================

.PHONY: sprint2 sprint2-task1 sprint2-task2 sprint2-task3 sprint2-task4 sprint2-task5 \
        vault-init vault-seal vault-status vault-secrets \
        vault-seal-all vault-unseal-all

# Sprint 2 — Run all tasks in sequence
sprint2: sprint2-task1 sprint2-task2 sprint2-task3 sprint2-task4 sprint2-task5
	@echo "✅ Sprint 2 complete"

# -----------------------------------------------------------------------------
# Task 1: Vault + SealedSecrets (P0)
# -----------------------------------------------------------------------------

## Deploy Vault (HashiCorp) + SealedSecrets + init ROMA secrets
sprint2-task1:
	@echo "=== Sprint 2 Task 1: Vault + SealedSecrets ==="
	@mkdir -p deploy/vault deploy/sealed-secrets deploy/values/sealed-secrets
	# Deploy Vault (Helm)
	@echo "[INFO] Deploying Vault via Helm..."
	helm upgrade --install vault deploy/vault \
	  --namespace roma-system --create-namespace \
	  --values deploy/vault/values.yaml \
	  --wait --timeout 5m || true
	@echo "[INFO] Waiting for Vault pod..."
	@kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=vault \
	  -n roma-system --timeout=120s 2>/dev/null || \
	  kubectl -n roma-system get pods -l app.kubernetes.io/name=vault
	@echo "[INFO] Deploying SealedSecrets controller..."
	helm upgrade --install sealed-secrets sealed-secrets \
	  --repo https://charts.bitnami.com/bitnami \
	  --namespace kube-system --create-namespace \
	  --wait --timeout 3m || true
	@echo ""
	@echo "✅ Task 1: Vault + SealedSecrets deployed"
	@echo ""
	@echo "Next: make vault-init   # Initialize Vault and create ROMA secrets"
	@echo "       make vault-status # Verify deployment"

## Initialize Vault, create KV engine + ROMA static secrets
vault-init:
	@echo "=== Vault Init ==="
	@kubectl exec -n roma-system vault-0 -- vault status 2>/dev/null && \
	  echo "[INFO] Vault already initialized" || \
	  (echo "[INFO] Vault dev-mode: auto-unsealed, reading token from logs..." && \
	   kubectl logs -n roma-system vault-0 2>/dev/null | grep "Root Token" | head -1)
	@echo "[INFO] KV engine 'roma' enabled (idempotent)"
	@kubectl exec -n roma-system vault-0 -- vault secrets enable -path=roma -version=2 kv 2>/dev/null || true
	@kubectl exec -n roma-system vault-0 -- vault secrets list 2>/dev/null | grep roma || true
	@echo ""
	@echo "✅ Vault initialized"
	@echo "✅ KV engine 'roma' enabled at path: roma/"
	@echo ""
	@echo "⚠️  Static secrets (Stripe, DB) — set values in:"
	@echo "   deploy/vault/scripts/vault-init.sh → create_static_secrets()"
	@echo ""
	@echo "   To apply real secrets, exec into vault pod:"
	@echo "   kubectl exec -n roma-system vault-0 -it -- /bin/sh"
	@echo "   vault kv put roma/stripe secret_key=sk-REDACTED-xxx webhook_secret=whsec-REDACTED-xxx"

## Verify Vault deployment
vault-status:
	@echo "=== Vault Status ==="
	@kubectl -n roma-system get pods -l app.kubernetes.io/name=vault
	@echo ""
	@kubectl exec -n roma-system vault-0 -- vault status 2>/dev/null || \
	  kubectl -n roma-system logs vault-0 2>/dev/null | tail -5
	@echo ""
	@echo "=== SealedSecrets ==="
	@kubectl -n kube-system get pods -l app.kubernetes.io/name=sealed-secrets

## Seal Vault (lock down after initial setup)
vault-seal:
	@echo "[WARN] Sealing Vault..."
	kubectl exec -n roma-system vault-0 -- vault operator seal
	@echo "✅ Vault sealed"

## Unseal Vault
vault-unseal:
	@echo "[INFO] Unsealing Vault..."
	kubectl exec -n roma-system vault-0 -- vault operator unseal

# -----------------------------------------------------------------------------
# Task 2: API Gateway (P1)
# -----------------------------------------------------------------------------

sprint2-task2:
	@echo "=== Sprint 2 Task 2: API Gateway (Kong) ==="
	@mkdir -p deploy/kong/deploy/kong/templates/plugins deploy/kong/templates/ingress \
	         deploy/values/kong deploy/kong/scripts
	# Deploy Kong via Helm
	@echo "[INFO] Deploying Kong Gateway via Helm..."
	helm repo add kong https://charts.konghq.com --force-update 2>/dev/null || true
	helm repo update 2>/dev/null || true
	kubectl create namespace kong --dry-run=client -o yaml | kubectl apply -f -
	helm upgrade --install kong kong/kong \
	  --version 2.36.0 \
	  --namespace kong \
	  --values deploy/kong/values.yaml \
	  --wait --timeout 10m --atomic --create-namespace || true
	@echo "[INFO] Applying KongPlugin CRDs..."
	kubectl apply -f deploy/kong/templates/plugins/tenant-plugins.yaml
	kubectl apply -f deploy/kong/templates/plugins/rate-limit-tenant.yaml
	kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=kong \
	  --namespace kong --timeout=120s 2>/dev/null || kubectl -n kong get pods
	@echo ""
	@echo "✅ Task 2: Kong Gateway deployed with rate limiting + tenant routing"
	@echo ""
	@echo "   make kong-init     # Full init: DB, Redis, consumers, routes"
	@echo "   make kong-status   # Verify Kong + plugins"
	@echo "   make kong-plugins  # Apply all KongPlugin CRDs"

## Kong Gateway — full init (plugins + consumers + routes)
kong-init: kong-plugins
	@echo "=== Kong Init ==="
	@kubectl exec -n kong deploy/kong -c kong -- kong health 2>/dev/null && \
	  echo "[INFO] Kong is healthy" || echo "[WARN] Kong not yet ready"
	@kubectl apply -f deploy/kong/templates/ingress.yaml
	@echo ""
	@echo "✅ Kong init complete"
	@echo "   Proxy: kubectl -n kong get svc kong-proxy"

## Apply all KongPlugin CRDs
kong-plugins:
	@echo "[INFO] Applying KongPlugin CRDs..."
	kubectl apply -f deploy/kong/templates/plugins/tenant-plugins.yaml
	kubectl apply -f deploy/kong/templates/plugins/rate-limit-tenant.yaml
	@echo "✅ KongPlugin CRDs applied"

## Verify Kong deployment
kong-status:
	@echo "=== Kong Status ==="
	@kubectl -n kong get pods -l app.kubernetes.io/name=kong
	@echo ""
	@echo "=== KongPlugin CRDs ==="
	@kubectl get kongplugin -n roma-system
	@echo ""
	@echo "=== Kong Services ==="
	@kubectl -n kong get svc

## Kong Gateway teardown
kong-clean:
	@echo "[WARN] Removing Kong from cluster..."
	helm uninstall kong -n kong --wait 2>/dev/null || true
	kubectl delete namespace kong --ignore-not-found=true
	@echo "✅ Kong removed"

# -----------------------------------------------------------------------------
# Task 3: Stripe Webhook (P1)
# -----------------------------------------------------------------------------

sprint2-task3:
	@echo "=== Sprint 2 Task 3: Stripe Webhook ==="
	@mkdir -p deploy/stripe-webhook/app deploy/stripe-webhook/deploy deploy/stripe-webhook/scripts
	@echo "[INFO] Building Docker image..."
	docker build -t roma-stripe-webhook:latest -f deploy/stripe-webhook/Dockerfile .
	@echo ""
	@echo "=== Deploying Stripe Webhook to k3s ==="
	kubectl apply -f deploy/stripe-webhook/deploy/deployment.yaml
	@echo ""
	@echo "✅ Task 3: Stripe Webhook deployed"
	@echo ""
	@echo "   make stripe-webhook-logs     # View logs"
	@echo "   make stripe-webhook-restart # Rolling restart"

stripe-webhook-logs:
	@echo "[INFO] Streaming logs..."
	kubectl logs -n roma-system -l app.kubernetes.io/name=stripe-webhook -f --tail=50

stripe-webhook-restart:
	@echo "[INFO] Rolling restart..."
	kubectl rollout restart deployment/stripe-webhook -n roma-system
	kubectl rollout status deployment/stripe-webhook -n roma-system --timeout=60s

# -----------------------------------------------------------------------------
# Task 4: TLS + cert-manager (P2)
# -----------------------------------------------------------------------------

sprint2-task4:
	@echo "=== Sprint 2 Task 4: TLS + cert-manager ==="
	@kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.crds.yaml 2>/dev/null || true
	@helm repo add jetstack https://charts.jetstack.io --force-update 2>/dev/null || true
	@helm repo update 2>/dev/null || true
	@helm install cert-manager jetstack/cert-manager \
		--namespace cert-manager \
		--create-namespace \
		--version v1.16.2 \
		--set startupapicheck.enabled=false \
		--wait --timeout 120s 2>/dev/null || true
	@kubectl apply -f deploy/cert-manager/issuer/issuers.yaml
	@echo "✅ Task 4 complete — cert-manager + ClusterIssuers installed"
	@echo "   Run: kubectl get clusterissuer"

# -----------------------------------------------------------------------------
# Task 5: ROMA CRD + Controller (P2)
# -----------------------------------------------------------------------------

sprint2-task5:
	@echo "=== Sprint 2 Task 5: ROMA CRD + Tenant Controller ==="
	@mkdir -p config/crd/bases config/crd/samples config/crd/controller deploy/roma-tenant/scripts
	@echo "[INFO] 1/4 — Applying RomaTenant CRD..."
	@kubectl apply -f config/crd/bases/roma.io_romatenants.yaml
	@echo "[INFO] 2/4 — Building operator image..."
	@docker build -t ghcr.io/mahaasur13-sys/roma-tenant-operator:latest \
		-f config/crd/Dockerfile.operator .
	@echo "[INFO] 3/4 — Pushing to GHCR..."
	@docker push ghcr.io/mahaasur13-sys/roma-tenant-operator:latest 2>/dev/null || \
		echo "[WARN] GHCR push skipped — authenticate with: docker login ghcr.io"
	@echo "[INFO] 4/4 — Deploying operator to cluster..."
	@kubectl apply -f config/crd/controller/deployment.yaml
	@echo ""
	@echo "   Waiting for operator to be ready..."
	@kubectl wait --for=condition=ready pod \
		-l app.kubernetes.io/name=roma-tenant-operator \
		-n roma-tenant-operator --timeout=120s 2>/dev/null || \
		kubectl -n roma-tenant-operator get pods
	@echo ""
	@echo "✅ Task 5: ROMA Tenant CRD + Controller deployed"
	@echo ""
	@echo "   Try it:"
	@echo "   kubectl apply -f config/crd/samples/romatenant-free.yaml"
	@echo "   kubectl get romatenants"
	@echo "   kubectl get ns -l roma.io/tenant"
	@echo "   kubectl describe romatenant partner-acme-free"

# =============================================================================
# Helm
# =============================================================================

.PHONY: helm-template helm-diff

helm-template:
	helm template roma charts/roma-execution-bridge \
	  --namespace roma-system \
	  --values charts/roma-execution-bridge/values.yaml

helm-diff:
	helm diff upgrade roma charts/roma-execution-bridge \
	  --namespace roma-system \
	  --values charts/roma-execution-bridge/values.yaml || true
# =============================================================================
# Integration Testing (Sprint 2 → v1.0.0 Release Gate)
# =============================================================================

.PHONY: integration-test integration-test-mock

# Full integration test pipeline (~10 min, requires k8s cluster)
# Delegates to scripts/integration-test.sh for clean bash logic
integration-test:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║   ROMA — Integration Test (Sprint 2 → v1.0.0 Release Gate)     ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@bash scripts/integration-test.sh

# Mock mode — no cluster, validate manifests only
integration-test-mock:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║   ROMA — Integration Test (MOCK MODE)                          ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"
	@bash scripts/integration-test.sh mock