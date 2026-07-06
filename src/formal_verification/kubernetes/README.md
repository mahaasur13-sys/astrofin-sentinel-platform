# Kubernetes Operator v7.0 — ATOM Federation OS Control Plane

## Что сделано

### Структура

```
kubernetes/
├── crd/
│   └── atomcluster.yaml               # ATOMCluster CRD (openAPIV3Schema, v1)
├── operator/
│   ├── main.py                        # Entrypoint (signal handling, kubeconfig)
│   ├── controller.py                  # ATOMController (watch loop + per-cluster threads)
│   ├── reconciler.py                 # Reconciler (SBS/healing/drift/quorum/scale)
│   ├── state.py                       # ClusterState + NodeState dataclasses
│   └── client.py                      # K8sClient wrapper
├── manifests/
│   ├── install.yaml                   # Namespace + SA + CRD + RBAC + ClusterRoleBinding
│   ├── deployment.yaml               # Operator StatefulSet + Service
│   ├── rbac.yaml                      # Standalone RBAC (SA + ClusterRole + ClusterRoleBinding)
│   └── sample.yaml                    # Example ATOMCluster
└── helm/atom-os/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── _rbac.tpl
        ├── crd.yaml
        └── operator.yaml
```

## Реакционный цикл

```
metrics → sbs_violation > threshold → _heal_cluster()
                                       ├─ delete unhealthy pod
                                       └─ patch StatefulSet restart annotation

         coherence_drift > max       → _throttle_cluster()
                                       └─ patch cluster annotation (throttle=true)

         quorum_breach              → phase = Failed

         health_ratio < 0.99        → _scale_up() (cooldown 60s)
```

## Как развернуть

```bash
# 1. Установка CRD + RBAC + Operator
kubectl apply -f kubernetes/manifests/install.yaml

# 2. Создать ATOMCluster
kubectl apply -f kubernetes/manifests/sample.yaml

# 3. Проверить статус
kubectl get atomclusters
kubectl describe atomcluster demo

# Или через Helm
helm install atom-os kubernetes/helm/atom-os/ \
  --set operator.image=ghcr.io/atom-federation/atom-operator:7.0.0
```

## Режимы работы

| Параметр | Default | Описание |
|----------|---------|----------|
| `RECONCILE_INTERVAL` | 5s | Частота опроса |
| `WATCH_NAMESPACE` | default | Namespace для ATOMCluster |
| `LOG_LEVEL` | INFO | DEBUG/INFO/WARNING |

## Healing cooldown

- Heal: 30s между heal-действиями на один кластер
- Scale: 60s между scale-событиями
