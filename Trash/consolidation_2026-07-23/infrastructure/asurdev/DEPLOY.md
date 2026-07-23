# GitOps Deployment with ArgoCD

## Overview

This repo uses **ArgoCD App-of-Apps** pattern to manage all Kubernetes workloads via Git. Every change to `manifests/` or `argocd/` is automatically applied to the cluster when you push.

## Architecture

```
GitHub (main branch)
    │
    └── argocd/app-of-apps.yaml   ──→ ArgoCD root app (creates all child apps)
    │
    └── argocd/applications/
          ├── ml-services.yaml    ──→ Creates: ml-serving, ml-training, timescale
    │
    └── manifests/
          ├── ml-serving/         ──→ FastAPI inference (HPA, 2-10 replicas)
          ├── ml-training/        ──→ PyTorch CronJobs (daily 2AM + weekly backfill)
          └── timescale/          ──→ TimescaleDB StatefulSet (50Gi PVC)
```

## Quick Start

```bash
# 1. Install ArgoCD on the cluster
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Install argocd CLI
brew install argocd

# 3. Login to ArgoCD
argocd login --localhost:8080 --username admin --password $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)

# 4. Deploy App-of-Apps
make argocd-deploy

# 5. Watch sync status
make argocd-status

# 6. Force sync after a code change
make argocd-sync
```

## Application Inventory

| Application | Path | Description | Sync Policy |
|-------------|------|-------------|-------------|
| `asurdev-root` | `argocd/app-of-apps.yaml` | App-of-Apps root | Automated, self-heal |
| `asurdev-ml-serving` | `manifests/ml-serving/` | FastAPI inference API | Automated, self-heal |
| `asurdev-ml-training` | `manifests/ml-training/` | PyTorch training CronJobs | Automated, no self-heal |
| `asurdev-timescale` | `manifests/timescale/` | TimescaleDB StatefulSet | Automated, self-heal |

## Deployment Workflow

### Normal flow (automatic)

1. Push code to `main` branch or create a new tag `v*.*.*`
2. GitHub Actions builds and pushes Docker image to GHCR
3. ArgoCD Image Updater detects new image tag
4. ArgoCD syncs manifests to the cluster

### Manual sync

```bash
# Sync all apps
make argocd-sync

# Sync specific app
argocd app sync asurdev-ml-serving
```

### Rollback

```bash
# Rollback to previous version
argocd app rollback asurdev-ml-serving

# View history
argocd app history asurdev-ml-serving
```

## Image Updates

ArgoCD Image Updater automatically updates `latest` tag when you push a semver tag:

```bash
git tag v1.2.3 && git push --tags
```

The Image Updater will detect the new image at `ghcr.io/mahaasur13-sys/asurdev-ml-api:v1.2.3` and update the Deployment.

## Manifest Labels

All resources include ArgoCD-native labels:

```yaml
app.kubernetes.io/name: ml-api        # Resource identifier
app.kubernetes.io/part-of: asurdev     # Application group
app.kubernetes.io/component: inference # Component type
```

## Production Checklist

- [ ] Override `POSTGRES_PASSWORD` via Kubernetes Secret (`timescale-secret`)
- [ ] Configure `storageClassName` for PVC if not using `standard`
- [ ] Verify GPU node selectors match your cluster (`node-type: gpu-worker`)
- [ ] Set `ARGOCD_URL` in CI for webhook notifications
- [ ] Configure RBAC for ArgoCD AppProject if needed

## Monitoring

```bash
# ArgoCD dashboard
argocd app get asurdev-ml-serving

# Sync waves (if using sync waves)
argocd app get asurdev-ml-serving --show-waves

# Resource tree
argocd app resources asurdev-ml-serving
```