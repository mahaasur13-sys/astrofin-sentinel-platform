.PHONY: help lint format test pre-commit install clean infra tsdb monitor self-healing ml-train ml-api ml-api-run ml-api-run-prod ml-api-stop ml-api-test ml-api-docker-build ml-api-docker-run ml-api-docker-stop loadtest correction argocd-sync argocd-status argocd-deploy

help:
	@echo "Available targets:"
	@echo "  lint                  : Run ruff linter"
	@echo "  format                : Run black formatter"
	@echo "  test                  : Run pytest with coverage"
	@echo "  pre-commit            : Run pre-commit hooks on all files"
	@echo "  install               : Install dev dependencies"
	@echo "  infra                 : Bootstrap cluster (Day 1-7)"
	@echo "  tsdb                  : Deploy TimescaleDB"
	@echo "  monitor               : Deploy Prometheus + Grafana"
	@echo "  self-healing          : Deploy watchdog"
	@echo "  ml-train              : Train ML models"
	@echo "  ml-api                : Start inference API (uvicorn, dev)"
	@echo "  ml-api-run            : Start inference API (uvicorn, auto-reload)"
	@echo "  ml-api-run-prod       : Start inference API (gunicorn, 4 workers)"
	@echo "  ml-api-stop           : Stop API process"
	@echo "  ml-api-test           : Run API unit tests"
	@echo "  ml-api-docker-build   : Build Docker image"
	@echo "  ml-api-docker-run     : Run container (detached)"
	@echo "  ml-api-docker-stop    : Stop and remove container"
	@echo "  loadtest              : Run load tests"
	@echo "  correction            : Run system correction"
	@echo "  argocd-sync           : Sync all ArgoCD applications"
	@echo "  argocd-status         : Show ArgoCD application status"
	@echo "  argocd-deploy         : Apply ArgoCD App-of-Apps to cluster"

lint:
	ruff check .

format:
	black .

test:
	pytest --cov=acos --cov-report=term

pre-commit:
	pre-commit run --all-files

install:
	pip install -e .[dev]

infra:
	ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags infra

tsdb:
	ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags tsdb

monitor:
	ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags monitoring

self-healing:
	ansible-playbook -i ansible/inventory.ini ansible/playbook.yml --tags self_healing

ml-train:
	python -m ml_engine.training.trainer

ml-api:
	uvicorn ml_engine.inference.api:app --host 0.0.0.0 --port 8081

ml-api-run:
	uvicorn ml_engine.inference.api:app --host 0.0.0.0 --port 8081 --reload

ml-api-run-prod:
	gunicorn -w 4 -b 0.0.0.0:8081 ml_engine.inference.api:app

ml-api-stop:
	@echo "Stopping API process..."
	@pkill -f uvicorn || true
	@pkill -f gunicorn || true

ml-api-test:
	pytest tests/test_ml_api.py -v

ml-api-docker-build:
	docker build -t ml-api .

ml-api-docker-run:
	docker run -d -p 8081:8081 --name ml-api-container ml-api

ml-api-docker-stop:
	docker stop ml-api-container || true
	docker rm ml-api-container || true

loadtest:
	pytest load_test/scenarios/

correction:
	python acos_correction/corrector.py

# ArgoCD GitOps targets
ARGOCD_NAMESPACE ?= argocd
ARGOCD_URL ?= http://localhost:8080

argocd-deploy:
	@echo "Deploying ArgoCD App-of-Apps..."
	kubectl apply -n $(ARGOCD_NAMESPACE) -f argocd/app-of-apps.yaml
	kubectl apply -n $(ARGOCD_NAMESPACE) -f argocd/applications/ml-services.yaml
	@echo "Done. Monitor at $(ARGOCD_URL)"

argocd-sync:
	@echo "Syncing ArgoCD applications..."
	argocd app set asurdev-root --sync-policy automated || true
	argocd app sync asurdev-ml-serving --force || true
	argocd app sync asurdev-ml-training --force || true
	argocd app sync asurdev-timescale --force || true

argocd-status:
	@echo "=== ArgoCD Application Status ==="
	@argocd app list -o wide || echo "Install argocd CLI: brew install argocd"
	@echo ""
	@echo "=== asurdev-ml-serving ==="
	@argocd app get asurdev-ml-serving 2>/dev/null || echo "App not found"
	@echo ""
	@echo "=== asurdev-ml-training ==="
	@argocd app get asurdev-ml-training 2>/dev/null || echo "App not found"
	@echo ""
	@echo "=== asurdev-timescale ==="
	@argocd app get asurdev-timescale 2>/dev/null || echo "App not found"
