# Contributing to roma-execution-bridge

Thank you! This is the control plane for GPU job scheduling with Raft consensus.

## 🛠️ Dev Environment

```bash
git clone https://github.com/mahaasur13-sys/roma-execution-bridge.git
cd roma-execution-bridge

# Install deps
pip install -e .

# Verify
python roma_cli.py --help
```

## ✅ PR Checklist

Before opening a PR:

- [ ] `pytest tests/ -v` passes
- [ ] `ruff check .` clean
- [ ] `black --check .` clean
- [ ] New CRDs have Helm chart entries
- [ ] New Python deps pinned with upper bounds: `>=X.Y.Z,<X.Y+1.0`
- [ ] RBAC changes reviewed (auth/rbac/)
- [ ] HPA/PDB updated for new stateful workloads

## 🏗️ Architecture Overview

```
roma-execution-bridge/
├── auth/           # JWT + RBAC (tenant isolation)
├── billing/        # Stripe metering + invoice ledger
├── compiler/       # DAG → execution plan
├── control_plane/  # API server (FastAPI)
├── gpu_worker/     # GPU job runner
├── k8s/            # Kubernetes manifests
├── operator_sdk/   # RomaTenant CRD operator
├── queue_manager/  # Priority job queue
├── rafts/          # Raft consensus layer
├── roma/           # Core domain models
├── scheduler/       # Scheduler logic
├── charts/         # Helm chart
└── scripts/        # Deployment scripts
```

## 🧪 Testing

```bash
# All tests
pytest tests/ -v --cov=.

# Specific suite
pytest tests/test_ci.py -v

# GPU integration (requires CUDA)
pytest tests/test_gpu_integration.py -v
```

## 🔒 Security

- All secrets via Vault or SealedSecrets
- JWT tokens: 1h expiry, refresh token rotation
- Tenant isolation: RomaTenant CRD enforces hard limits
- cert-manager for all internal TLS
- Report vulnerabilities via GitHub Security Advisories

## 🚀 Release Process

1. Bump version in `pyproject.toml` + `charts/*/Chart.yaml`
2. Update `CHANGELOG.md`
3. Tag: `git tag vX.Y.Z && git push --tags`
4. GitHub Actions: lint → test → build → push to GHCR
5. SLSA attestations auto-generated in `release-artifacts/`
6. Helm chart published via GitHub Releases

## 🛰️ GitOps (ArgoCD)

Manifests in `deploy/manifests/` auto-sync via ArgoCD.

```bash
# Manual sync (if needed)
make argocd-sync

# Check status
make argocd-status
```

## 📊 Observability

- Prometheus metrics at `/metrics`
- Loki for structured logs
- Grafana dashboards in `grafana/` (import manually)

## ⚠️ Breaking Changes

Any change to these requires major version bump:
- RomaTenant CRD schema
- Raft consensus protocol
- Billing ledger format
- Auth token format
