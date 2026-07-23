# ROMA — Kubernetes Deployment Guide

## 📋 Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Kubernetes | 1.28+ | k3s / kubeadm / EKS / GKE |
| StorageClass | Longhorn or Rook Ceph | `kubectl get storageclass` |
| NVIDIA Device Plugin | v0.14+ | For GPU workloads |
| Helm | 3.12+ | For Helm chart install |

### Storage Classes

```bash
# Longhorn (recommended for home cluster)
kubectl get storageclass
# NAME                 PROVISIONER
# longhorn (default)   driver.longhorn.io

# Rook Ceph (production)
kubectl get storageclass
# NAME                 PROVISIONER
# rook-ceph-block      rook.storageclass.xyz
# rook-cephfs          rook.storageclass.xyz
```

### GPU Nodes

```bash
# Label GPU nodes
kubectl label nodes <node-name> gpu=true
# Or via k3s (auto-labelled):
kubectl get nodes -o wide --show-labels | grep gpu
```

---

## 🚀 Quick Deploy (Flat YAML — fastest)

```bash
cd deploy/k8s

# 1. Namespace + RBAC
kubectl apply -f namespaces/roma-system.yaml
kubectl apply -f RBAC/roma-rbac.yaml
kubectl apply -f RBAC/roma-extras.yaml

# 2. Storage (adjust StorageClass if needed)
kubectl apply -f storage/roma-pvc.yaml

# 3. Config + Secrets
kubectl apply -f configmaps/roma-configmap.yaml
kubectl apply -f secrets/roma-secrets.yaml

# 4. Deployments
kubectl apply -f deployments/roma-api-server.yaml
kubectl apply -f deployments/roma-gpu-worker.yaml

# 5. External access
kubectl apply -f services/roma-ingress-nodeport.yaml

# Verify
kubectl -n roma-system get pods,svc,pvc
```

**Access:**
- API: `http://<node-ip>:30080/submit`
- Docs: `http://<node-ip>:30080/docs`

---

## 🎯 Helm Chart Deploy (production / white-label)

```bash
# Add repo (if published)
helm repo add roma https://charts.roma.ai
helm repo update

# Install with defaults
helm install roma roma/roma-execution-bridge \
  --namespace roma-system \
  --create-namespace \
  --values charts/roma-execution-bridge/values.yaml

# Or with overrides
helm install roma roma/roma-execution-bridge \
  --namespace roma-system \
  --create-namespace \
  --set apiServer.replicaCount=3 \
  --set persistence.checkpoints.size=500Gi \
  --set persistence.checkpoints.storageClass=rook-ceph-block \
  --set global.storageClass=rook-ceph-block
```

---

## 🔧 Kustomize Deploy (GitOps-ready)

```bash
# Overlay for production
kubectl apply -k overlays/production
# Or:
kustomize build overlays/production | kubectl apply -f -
```

---

## ⚙️ Configuration

### Storage Backend (Longhorn / Rook Ceph)

```yaml
# values.yaml or kustomization.yaml
global:
  storageClass: longhorn  # or rook-ceph-block or rook-cephfs
```

### GPU Workers

```yaml
gpuWorker:
  replicaCount: 2
  nodeSelector:
    gpu: "true"
  tolerations:
    - key: "nvidia.com/gpu"
      operator: "Exists"
      effect: "NoSchedule"
```

### S3 / MinIO

```yaml
# Update configmap with your MinIO credentials
data:
  S3_ENDPOINT: "http://roma-minio:9000"
  S3_ACCESS_KEY: "minioadmin"
  S3_BUCKET: "roma-artifacts"
```

### Stripe (Production)

```bash
# Save Stripe keys as secrets
kubectl create secret generic roma-stripe-secret \
  --from-literal=stripe-secret-key=sk_live_xxxx \
  --from-literal=stripe-webhook-secret=whsec_xxxx \
  -n roma-system
```

### Auth / JWT

```bash
# Generate strong JWT secret
openssl rand -base64 32
# Update roma-auth-secret with production value
kubectl patch secret roma-auth-secret \
  -n roma-system \
  -p '{"stringData":{"jwt-secret":"<generated>"}}'
```

### Tailscale VPN

```bash
# Set Tailscale auth key
kubectl patch secret roma-network-secret \
  -n roma-system \
  -p '{"stringData":{"tailscale-authkey":"tskey-auth-xxxx"}}'
```

---

## 📊 Observability

### Prometheus Metrics

Metrics exposed at `/metrics` on:
- API Server: `:8080/metrics`
- GPU Worker: `:8000/metrics`

```yaml
# serviceMonitor (Prometheus Operator)
serviceMonitor:
  enabled: true
  namespace: monitoring
  interval: 30s
```

### Grafana Dashboards

Import dashboard IDs:
| Dashboard | ID |
|-----------|-----|
| Node Exporter Full | 1860 |
| K8s Pods | 15757 |
| Redis | 11835 |

---

## 🧪 Verify Deployment

```bash
# Check all resources
kubectl -n roma-system get all,pvc,configmap,secret

# Check pods
kubectl -n roma-system get pods -o wide

# Logs
kubectl -n roma-system logs -l app.kubernetes.io/component=api-server --tail=50
kubectl -n roma-system logs -l app.kubernetes.io/component=gpu-worker --tail=50

# Port-forward for local access
kubectl port-forward -n roma-system svc/roma-api-server 8080:8080

# Health check
curl http://localhost:8080/health
curl http://localhost:8080/ready

# Submit test job
curl -X POST http://localhost:8080/submit \
  -H "Content-Type: application/json" \
  -d '{"task":"train YOLOv8","gpu_required":true}'
```

---

## 🔄 Upgrades

```bash
# Helm
helm upgrade roma roma/roma-execution-bridge \
  --namespace roma-system \
  --values values.yaml

# Kustomize
kubectl apply -k overlays/production

# Flat YAML (rolling)
kubectl apply -f deployments/roma-api-server.yaml
kubectl apply -f deployments/roma-gpu-worker.yaml
```

---

## 🗑️ Uninstall

```bash
# Helm
helm uninstall roma -n roma-system

# Kustomize
kubectl delete -k overlays/production

# Flat YAML
kubectl delete -f services/roma-ingress-nodeport.yaml
kubectl delete -f deployments/roma-gpu-worker.yaml
kubectl delete -f deployments/roma-api-server.yaml
kubectl delete -f storage/roma-pvc.yaml
kubectl delete -f secrets/roma-secrets.yaml
kubectl delete -f configmaps/roma-configmap.yaml
kubectl delete -f RBAC/roma-rbac.yaml
kubectl delete -f RBAC/roma-extras.yaml
kubectl delete -f namespaces/roma-system.yaml
```

---

## 🏠 Home Cluster (k3s + Pop!_OS)

```bash
# 1. Install NVIDIA Device Plugin (if not already)
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.0/nvidia-device-plugin.yml

# 2. Label GPU nodes
kubectl label nodes <gpu-node> gpu=true

# 3. Deploy ROMA
kubectl apply -f deploy/k8s/namespaces/roma-system.yaml
kubectl apply -f deploy/k8s/RBAC/
kubectl apply -f deploy/k8s/storage/roma-pvc.yaml
kubectl apply -f deploy/k8s/configmaps/roma-configmap.yaml
kubectl apply -f deploy/k8s/secrets/roma-secrets.yaml
kubectl apply -f deploy/k8s/deployments/
kubectl apply -f deploy/k8s/services/roma-ingress-nodeport.yaml

# 4. Access via Tailscale (best for home cluster)
tailscale up --operator root
tailscale funnel 30443
```

---

## 🔐 Security Checklist (Production)

- [ ] Change `jwt-secret` from default
- [ ] Set `stripe-secret-key` and `stripe-webhook-secret`
- [ ] Enable NetworkPolicy (`network.policy.enabled: true`)
- [ ] Use Vault or Sealed Secrets for secrets management
- [ ] Enable `runAsNonRoot: true` (already set)
- [ ] Review `allowPrivilegeEscalation: false` (already set)
- [ ] Use TLS for external access (Tailscale Funnel or cert-manager)
- [ ] Enable `serviceMonitor` for Prometheus monitoring
- [ ] Set resource limits (already configured)
- [ ] Enable PodDisruptionBudget (already configured)

---

## 📁 File Structure

```
deploy/k8s/
├── kustomization.yaml              # Kustomize entrypoint
├── namespaces/
│   └── roma-system.yaml
├── configmaps/
│   └── roma-configmap.yaml
├── secrets/
│   └── roma-secrets.yaml
├── storage/
│   └── roma-pvc.yaml              # Longhorn + Rook Ceph
├── RBAC/
│   ├── roma-rbac.yaml             # Executor SA + Role + ClusterRole
│   └── roma-extras.yaml           # Controller SA + Role
├── deployments/
│   ├── roma-api-server.yaml       # API Server (HPA-ready)
│   └── roma-gpu-worker.yaml       # GPU Worker (nodeSelector: gpu=true)
└── services/
    └── roma-ingress-nodeport.yaml # NodePort + Tailscale Funnel
```

---

## 📦 ROMA CRD (RomaTask)

```bash
# Apply ROMA CRD
kubectl apply -f k8s/roma-crd.yaml

# Create RomaTask
kubectl apply -f - <<'EOF'
apiVersion: roma.ai/v1
kind: RomaTask
metadata:
  name: yolov8-training-001
  namespace: roma-jobs
spec:
  task: "train YOLOv8 on RTX3060 with COCO dataset"
  priority: 8
  gpuRequired: true
  executionMode: k8s_job
EOF

# Watch RomaTask status
kubectl get romatask -n roma-jobs -w
```
