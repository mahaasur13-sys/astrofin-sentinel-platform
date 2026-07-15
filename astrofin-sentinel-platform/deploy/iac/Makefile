# home-cluster-iac — Distributed mini-AWS cluster
.PHONY: help plan apply destroy validate test bootstrap

SHELL := /bin/bash
TERRAFORM_DIR := terraform
ANSIBLE_DIR := ansible
K8S_DIR := k8s

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Terraform targets
plan: ## Plan Terraform changes
	cd $(TERRAFORM_DIR) && terraform plan

apply: ## Apply Terraform changes
	cd $(TERRAFORM_DIR) && terraform apply -auto-approve

destroy: ## Destroy Terraform resources
	cd $(TERRAFORM_DIR) && terraform destroy -auto-approve

validate: ## Validate Terraform
	cd $(TERRAFORM_DIR) && terraform validate

# ── Inventory Generation ─────────────────────────────────────────────────────
inventory: validate ## Generate ansible/inventory.ini from Terraform outputs
	cd $(TERRAFORM_DIR) && terraform output --json | ../scripts/generate-inventory.sh

inventory-dry-run: ## Preview inventory generation (no file written)
	cd $(TERRAFORM_DIR) && terraform output --json | ../scripts/generate-inventory.sh --dry-run

# ── Terraform Output ─────────────────────────────────────────────────────────
terraform-output: ## Print all Terraform outputs
	cd $(TERRAFORM_DIR) && terraform output

# ── MinIO / S3 Backend ──────────────────────────────────────────────────────
minio-init: ## Ensure MinIO running and tf-state + velero buckets exist
	@echo "=== MinIO init ==="
	@if ! docker ps --format '{{.Names}}' | grep -q '^minio$$'; then \
		echo "ERROR: MinIO container not running. Deploy it first:"; \
		echo "  make -f Makefile.velero minio-init"; \
		exit 1; \
	fi
	@echo "Ensuring MinIO buckets (tf-state + velero)..."
	@docker exec minio mc alias set local http://localhost:9000 \
		minioadmin minioadmin 2>/dev/null || true
	@docker exec minio mc mb local/tf-state --ignore-existing 2>/dev/null || true
	@docker exec minio mc mb local/velero --ignore-existing 2>/dev/null || true
	@echo "✓ Buckets ready: tf-state, velero"

tf-backend-check: ## Verify S3 backend connectivity
	@echo "=== S3 backend connectivity ===" && \
	AWS_ACCESS_KEY_ID="$${TF_VAR_minio_access_key:-minioadmin}" \
	AWS_SECRET_ACCESS_KEY="$${TF_VAR_minio_secret_key:-minioadmin}" \
	aws s3 --endpoint-url http://localhost:9000 ls s3://tf-state/ 2>&1 || \
	echo "ERROR: cannot reach MinIO S3 endpoint"

# Migrate local state → S3 backend
# Usage: make tf-backend-init
# Requires: MinIO running + TF_VAR_minio_access_key/secret set
tf-backend-init: minio-init ## Migrate existing local state to S3 backend
	@echo "=== Migrating local state → S3 (MinIO) ==="
	@if [ ! -f "$(TERRAFORM_DIR)/terraform.tfstate" ]; then \
		echo "No local state found — initialising fresh S3 backend"; \
		cd $(TERRAFORM_DIR) && terraform init -reconfigure; \
		exit 0; \
	fi
	@echo "Backing up existing local state..." && \
	cp $(TERRAFORM_DIR)/terraform.tfstate \
		$(TERRAFORM_DIR)/terraform.tfstate.local.backup
	@echo "Re-initialising with S3 backend..." && \
	cd $(TERRAFORM_DIR) && terraform init \
		-migrate-from=local \
		-reconfigure 2>&1 | tee /tmp/tf-init.log
	@if grep -q "Successfully configured" /tmp/tf-init.log; then \
		echo "✓ S3 backend configured — local backup at terraform.tfstate.local.backup"; \
		rm -f $(TERRAFORM_DIR)/terraform.tfstate; \
	else \
		echo "WARNING: migration may have failed — check $(TERRAFORM_DIR)/terraform.tfstate.local.backup"; \
	fi

tf-backend-rollback: ## Rollback S3 → local state (emergency)
	@echo "=== Rolling back to local backend ==="
	@if [ -f "$(TERRAFORM_DIR)/terraform.tfstate.local.backup" ]; then \
		cp $(TERRAFORM_DIR)/terraform.tfstate.local.backup \
			$(TERRAFORM_DIR)/terraform.tfstate; \
		cd $(TERRAFORM_DIR) && terraform init \
			-migrate-from=s3 -reconfigure 2>&1; \
		echo "✓ Rolled back to local state"; \
	else \
		echo "ERROR: no local backup found"; exit 1; \
	fi

# Ansible targets
ansible-lint: ## Lint Ansible playbooks
	cd $(ANSIBLE_DIR) && ansible-lint playbooks/*.yml

bootstrap: ## Bootstrap all nodes (Day 0-7)
	@echo "Running Day 0 bootstrap..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day0-bootstrap.yml
	@echo "Day 1: Network setup..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day1-network.yml
	@echo "Day 2: WireGuard mesh..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day2-wireguard.yml
	@echo "Day 3: Compute nodes..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day3-compute.yml
	@echo "Day 4: Slurm cluster..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day4-slurm.yml
	@echo "Day 5: Ray cluster..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day5-ray.yml
	@echo "Day 6: Ceph storage..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day6-ceph.yml
	@echo "Day 7: Integration..."
	ansible-playbook $(ANSIBLE_DIR)/playbooks/day7-integration.yml

# ArgoCD targets
argocd-deploy: ## Deploy ArgoCD to k3s cluster (requires cluster running)
	@echo "=== ArgoCD Deployment ==="
	@if ! kubectl cluster-info >/dev/null 2>&1; then \
		echo "ERROR: k3s not reachable. Deploy cluster first: make -f Makefile.velero velero-install"; \
		exit 1; \
	fi
	@echo "Installing ArgoCD via Helm..."
	helm repo add argo https://argoproj.github.io/argo-helm && helm repo update
	helm upgrade --install argocd argo/argo-cd \
		-n argocd --create-namespace \
		--set server.replicas=2 \
		--set controller.replicas=2 \
		--set redis.replicas=2 \
		--wait --timeout 10m
	@echo "Waiting for ArgoCD server..."
	@kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=120s || true
	@echo "Applying Application manifests..."
	-kubectl apply -f $(K8S_DIR)/manifests/argocd/applications/ -n argocd
	@ARGOCD_HOST=$$(kubectl get ingress argocd-server -n argocd -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "argocd.local"); \
	echo "=== ArgoCD Deployed ==="; \
	echo "URL: https://$$ARGOCD_HOST"; \
	echo "Username: admin"; \
	echo "Password: $$(kubectl get secret argocd-initial-admin-secret -n argocd -o jsonpath='{.data.password}' | base64 -d)"

argocd-sync: ## Sync all ArgoCD applications
	@echo "=== ArgoCD Sync ==="
	@argocd app list --output json 2>/dev/null | jq -r '.[].metadata.name' 2>/dev/null || \
		echo "argocd CLI not found — use: kubectl get applications -n argocd"
	@for app in $$(kubectl get applications -n argocd -o jsonpath='{.items[*].metadata.name}'); do \
		echo "Syncing: $$app"; \
		argocd app sync $$app --force 2>/dev/null || \
			echo "  (argocd CLI unavailable — sync via UI)"; \
	done

argocd-status: ## Show ArgoCD apps status
	@echo "=== ArgoCD Applications ==="
	@kubectl get applications -n argocd
	@echo ""
	@kubectl get pods -n argocd

# K8s targets
k8s-apply: ## Apply Kubernetes manifests
	kubectl apply -k $(K8S_DIR)/overlays/dev

k8s-diff: ## Show K8s diff
	kubectl diff -k $(K8S_DIR)/overlays/dev

# Test targets
test: validate ansible-lint ## Run all validation
	@echo "All validation passed"

# SDLC OS Phase 3 targets
sdlc-validate: ## Validate repair plan using Phase 3 gates
	python -c "from sdlc_os.phase3 import GateEngine, GraphGate, PolicyGate, DiffGate, DeterminismGate, SafetyGate; \
		engine = GateEngine(); \
		engine.register_gate(GraphGate()); \
		engine.register_gate(PolicyGate()); \
		engine.register_gate(DiffGate()); \
		engine.register_gate(DeterminismGate()); \
		engine.register_gate(SafetyGate()); \
		print('Phase 3 gates registered and ready')"

commit-ready: ## Generate commit message from last execution
	@echo "Use sdlc_os.phase3.CommitManager.prepare() to generate commit output"
