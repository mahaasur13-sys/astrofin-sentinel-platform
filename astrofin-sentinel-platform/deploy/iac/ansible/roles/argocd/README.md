---
# file: ansible/roles/argocd/README.md
# ArgoCD Installation Role for k3s Cluster
# Version: 1.0.0
# Compatibility: home-cluster-iac (k3s, Kubernetes 1.29+)

## Overview

Installs ArgoCD (Community Edition) via official Helm chart with:
- Ingress (NGINX) + TLS termination
- Admin password via sealed-secrets (AES-256)
- High Availability (2 replicas)
- Resource limits / security contexts

## Usage

```bash
# Dry-run (check syntax)
ansible-playbook -i inventory.ini site.yml --tags argocd --check

# Apply
ansible-playbook -i inventory.ini site.yml --tags argocd

# Verify
kubectl get all -n argocd
kubectl get ingress -n argocd
```

## Required Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `argocd_domain` | `argocd.local` | FQDN for ArgoCD UI |
| `argocd_admin_password` | (sealed-secrets) | Initial admin password |
| `argocd_replicas` | `2` | HA mode |
| `argocd_version` | `7.1.0` | Helm chart version |

## Dependencies

- `kubernetes.core` (k8s modules)
- `cloud.common` (helm module)
- `kubectl` on control node

## Secrets

Admin password stored as SealedSecret in `argocd-admin-auth.yaml`.
Decrypt with: `kubeseal -n argocd --fetch-cert > cert.pem`

## Artifacts

- `tasks/main.yml` — Installation tasks
- `templates/argocd-values.yaml.j2` — Helm values
- `defaults/main.yml` — Default variables
- `k8s/manifests/argocd/applications/` — ArgoCD App manifests