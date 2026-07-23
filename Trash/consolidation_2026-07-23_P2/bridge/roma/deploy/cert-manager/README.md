# Sprint 2 — Task 4: cert-manager + TLS

## Overview

Installs cert-manager via Helm and configures Let's Encrypt ClusterIssuers for automatic TLS certificate management.

## Architecture

```
Ingress → cert-manager → ACME (Let's Encrypt) → Certificate + Secret
              ↑                              ↓
         HTTP-01 challenge verification  ┌─────────────────────────────────┐
                                         │ letsencrypt-staging  (test)     │
                                         │ letsencrypt-prod    (prod)      │
                                         └─────────────────────────────────┘
```

## Components

| Component | Version | Purpose |
|-----------|---------|---------|
| cert-manager | v1.16.2 | ACME certificate controller |
| ClusterIssuer (staging) | — | Let's Encrypt staging (unlimited test certs) |
| ClusterIssuer (prod) | — | Let's Encrypt production (rate-limited 50/week) |

## Files

```
cert-manager/
├── crd/
│   └── (CRDs applied via kustomize from GitHub releases)
├── issuer/
│   └── issuers.yaml        ← ClusterIssuers + example Ingress TLS
├── scripts/
│   └── setup.sh            ← Helm install + issuer creation
├── values.yaml             ← Helm chart values (HA config)
└── kustomization.yaml      ← Kustomize overlay
```

## Usage

### Quick Start (Helm)

```bash
# 1. Install CRDs
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.2/cert-manager.crds.yaml

# 2. Install via Helm
helm repo add jetstack https://charts.jetstack.io --force-update
helm repo update
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager \
  --create-namespace \
  --version v1.16.2 \
  -f deploy/cert-manager/values.yaml

# 3. Apply issuers
kubectl apply -f deploy/cert-manager/issuer/issuers.yaml

# 4. Verify
kubectl get clusterissuer
kubectl get pods -n cert-manager
```

### Via Make

```bash
make sprint2-task4        # Install + configure
make cert-manager-status  # Check pods
```

## Adding TLS to Existing Ingress

```yaml
metadata:
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-staging  # or letsencrypt-prod
spec:
  tls:
    - hosts:
        - your-domain.com
      secretName: your-tls-secret  # created automatically
  rules:
    - host: your-domain.com
      ...
```

## DNS-01 Challenge (for wildcard / custom domain)

Replace `http01` with `dns01` in ClusterIssuer:

```yaml
spec:
  acme:
    solvers:
      - dns01:
          cloudflare:
            email: your@email.com
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
```

Required secret:
```bash
kubectl create secret generic cloudflare-api-token \
  -n cert-manager \
  --from-literal=api-token=your_cloudflare_api_token
```

## Verify Certificate

```bash
# Check certificate status
kubectl get certificate -A

# Describe for errors
kubectl describe certificate <name> -n <namespace>

# Check ACME account status
kubectl describe clusterissuer letsencrypt-prod

# View cert details
kubectl get secret <tls-secret> -n <namespace> -o yaml | grep -A5 "tls.crt"
```

## Troubleshooting

### Pending certificate
```bash
kubectl describe order <order-name>
kubectl describe challenge <challenge-name>
```
Most common: Ingress not in `nginx` class or webhook not reachable.

### ACME account errors
```bash
kubectl logs -n cert-manager deploy/cert-manager-webhook
```

### DNS-01 not working
Check Cloudflare/Route53 token has `Zone:Read` and `DNS:Write` permissions.

## Next Steps

- **Task 5**: ROMA CRD + Controller (custom resource for tenant management)
- **Task 6**: End-to-end TLS with Kong plugin for mTLS

## Notes

- Staging issuer: unlimited test certs from `acme-staging-v02.api.letsencrypt.org`
- Prod issuer: 50 certs/week limit from `acme-v02.api.letsencrypt.org`
- Test with staging first, switch to prod when confident
- Certificates auto-renew 30 days before expiry