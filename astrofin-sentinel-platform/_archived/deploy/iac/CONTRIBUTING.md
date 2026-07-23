# Contributing to home-cluster-iac

Thank you for contributing! This is an IaC monorepo. Please read before submitting.

## 🛠️ Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Terraform | ≥1.6 | `apt install terraform` |
| Ansible | ≥2.15 | `pip install ansible` |
| Python | ≥3.10 | built-in |
| `ansible-lint` | latest | `pip install ansible-lint` |
| `tfenv` | — | for Terraform version management |

## 🔧 Initial Setup

```bash
git clone https://github.com/mahaasur13-sys/home-cluster-iac.git
cd home-cluster-iac

# Day 0: bootstrap
make bootstrap        # Install all tool dependencies

# Day 1: bring up cluster
make cluster-up      # Terraform + Ansible full run

# Verify
make cluster-status
```

## ✅ PR Checklist

Before opening a PR:

- [ ] `make tf-validate` passes (Terraform validate + fmt)
- [ ] `make tf-plan` generates clean plan (no diff = approve)
- [ ] `make ansible-lint` passes
- [ ] `make checkov` passes (security扫描)
- [ ] No hardcoded IPs or credentials (use `vars/` + `.env.example`)
- [ ] New Terraform modules have `outputs.tf`
- [ ] New Ansible roles have `molecule/` tests

## 🏗️ Directory Structure

```
home-cluster-iac/
├── terraform/           # Terraform modules (network, vpn_mesh, storage, compute)
├── ansible/              # Ansible roles (wireguard, slurm, ceph, ray, velero)
│   └── roles/
├── scripts/              # Day 1-7 setup scripts
├── k8s/manifests/        # Kubernetes manifests (ArgoCD, Velero)
├── Makefile              # Top-level commands
├── Makefile.velero       # DR commands
└── .github/workflows/    # CI (Terraform + Ansible + Checkov)
```

## 🧪 Testing

```bash
# Terraform
make tf-validate
make tf-plan

# Ansible
make ansible-lint
make ansible-check     # ansible-playbook --check --diff

# Full cluster dry-run
make cluster-plan
```

## 🔒 Security

- All secrets via `.env` (never committed)
- Terraform `backend.tf` uses MinIO S3 — credentials in env vars
- Network: VLAN isolation (mgmt/storage/compute/vpn)
- WireGuard mesh: preshared keys rotated via Ansible vault
- Run `make trivy-scan` on Docker images before deployment

## 🚀 Adding New Nodes

1. Add to `terraform/inventory.tftpl`
2. Update `ansible/inventory.yml`
3. `make tf-plan` → review → `make tf-apply`
4. Run Day-N playbook for node role

## 🆘 DR / Restore

```bash
# Test Velero restore (interactive!)
make dr-restore

# Full DR drill
./dr-drill.sh
```

## 📡 Terraform Backend Init

```bash
# Initialize MinIO S3 backend
make tf-backend-init
```

## 🛰️ GitOps (ArgoCD)

```bash
# Deploy ArgoCD apps from manifests/
make argocd-deploy

# Sync all apps
make argocd-sync
```
