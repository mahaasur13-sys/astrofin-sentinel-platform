# ROMA — Agent Memory

## System Identity

**ROMA = Closed-Loop Execution SaaS Platform**

Every action completes the full cycle:

```
Compute → Cost → Decision → Execution → Observation → Billing → Repeat
```

## System Class

- **Not**: platform, scheduler, control plane, architecture
- **Is**: operational product with deterministic compute economics
- **Status**: feature-complete, product-market fit phase ready, no longer architecture-driven

## Maturity State

| Property | Value |
|----------|-------|
| Missing layers | None — "no missing layers problem" |
| Core changes value | <1% (scheduler, consensus, event sourcing) |
| Growth vectors | Onboarding, activation, retention, monetization |
| Distribution vectors | K8s managed, cloud marketplaces, multi-region |

## Architecture (Frozen, Layer 1)

Layer 1 frozen since 2026-04-17. All Layer 2 modules exist.

## Kubernetes Deployment (Sprint 1 — Complete, 2026-04-18)

| Layer | Status | Location |
|-------|--------|---------|
| Helm Chart | ✅ v1.0.0 | `charts/roma-execution-bridge/` |
| Kustomize Overlays | ✅ | `deploy/overlays/{home-cluster,production}/` |
| Flat YAML (all-in-one) | ✅ | `deploy/manifests/all-in-one.yaml` |
| RBAC + SA | ✅ | `deploy/k8s/RBAC/roma-rbac.yaml` |
| PVC (Longhorn/Rook) | ✅ | `deploy/k8s/storage/roma-pvc.yaml` |
| ConfigMaps + Secrets | ✅ | `deploy/k8s/configmaps/, secrets/` |
| HPA manifests | ✅ | `charts/.../templates/hpa.yaml` |
| NetworkPolicy | ✅ | `charts/.../templates/rbac.yaml` |
| PrometheusRule | ✅ | `charts/.../templates/ingress.yaml` |
| Makefile k8s targets | ✅ | `make k8s-deploy-home` etc. |

**Quick deploy:**
```bash
make k8s-deploy-home        # home cluster (Longhorn)
make k8s-deploy-kustomize-prod  # production (Rook Ceph)
make k8s-status             # verify
make k8s-portforward        # localhost:8080
```

**Storage backends:** Longhorn (home), Rook Ceph Block/FS (production), MinIO S3 (artifacts)

## Growth Targets (Layer 2 Active)

- Onboarding: time-to-first-job <30s → <10s
- Activation rate increase
- Retention loops
- Pricing tiers tuning
- Enterprise contracts
- Plugin marketplace revenue

## Files

Total: 87 Python files across:
- Execution kernel (scheduler, Raft, event sourcing, K8s)
- Plugin runtime
- Cost engine
- Billing (Stripe-integrated)
- Auth (API keys, RBAC, enterprise SSO)
- SaaS control plane (org, onboarding, bootstrap)
- Dashboard (observability, projection)

## ROMA Version

v1.0.0 — SaaS MVP Complete (2026-04-17)
v1.1.0 — K8s Production Ready (2026-04-18)
