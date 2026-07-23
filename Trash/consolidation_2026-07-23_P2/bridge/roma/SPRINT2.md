# Sprint 2 — Production Hardening

**Status:** 🔄 In Progress  
**Start:** 2026-04-18  
**Goal:** Production-ready roma-execution-bridge deployment for partners

---

## Background

Sprint 1 deliverables (✅ complete):
- Helm charts + manifests
- Storage: Longhorn + Rook Ceph + MinIO
- White-label features (branding, revenue-share, email)
- GPU worker infrastructure

**This sprint:** closes the gap between "working cluster" and "deployable by partners"

---

## Scope: 5 Tasks

### Task 1 — Vault / Sealed Secrets (🔴 Critical)
**Owner:** Agent  
**Priority:** P0

Secure secret storage layer:

```
┌─────────────────────────────────────────────────────────┐
│                    K8s Cluster                          │
│  ┌──────────────┐    ┌─────────────┐    ┌───────────┐ │
│  │   Vault      │    │ SealedSecrets│   │ External  │ │
│  │  (Data Plane)│    │   (Control)  │   │ Secrets   │ │
│  └──────┬───────┘    └──────┬──────┘    └─────┬─────┘ │
│         │                   │                 │       │
│         └───────────────────┴─────────────────┘       │
│                    Secret Injection                   │
└─────────────────────────────────────────────────────────┘
```

**Deliverables:**
- `deploy/vault/` — Helm values for production
- `deploy/sealed-secrets/` — controller + key management
- `deploy/values/secrets.yaml.gotpl` — encrypted secret templates
- Integration with Stripe, DB, API keys
- Rotation strategy

**Acceptance criteria:**
- [ ] Vault auto-unseal (AWS KMS / auto)
- [ ] Dynamic secrets for PostgreSQL
- [ ] Static secrets via SealedSecrets (GitOps-friendly)
- [ ] Vault UI accessible via internal LB
- [ ] CLI tool: `make vault-init` initializes secrets

---

### Task 2 — API Gateway (🟠 High)
**Owner:** Agent  
**Priority:** P1

Finalize rate limiting, tenant routing, branding injection:

**Deliverables:**
- Rate limiting (Redis backend)
- Per-tenant routing
- Branding injection middleware
- Health endpoint
- OpenAPI validation

**Acceptance criteria:**
- [ ] Rate limit: 100 req/min per tenant
- [ ] Branding: `X-Branding-*` headers injected
- [ ] Health: `/health/ready` + `/health/live`
- [ ] Tenant isolation verified

---

### Task 3 — Stripe Webhook (🟠 High)
**Owner:** Agent  
**Priority:** P1

Production-ready Stripe webhook deployment:

**Deliverables:**
- `deploy/stripe-webhook/` — K8s deployment
- Webhook endpoint verification
- Idempotent processing
- Dead-letter queue for failures
- `stripe-cli` sidecar for local testing

**Acceptance criteria:**
- [ ] Signature verification enforced
- [ ] Events processed idempotently
- [ ] Retry with exponential backoff
- [ ] Dashboard: processed events count

---

### Task 4 — TLS + cert-manager (🟡 Medium)
**Owner:** Agent  
**Priority:** P2

HTTPS for all services + custom domain for white-label:

**Deliverables:**
- cert-manager + Let's Encrypt
- wildcard cert for `*.roma.example.com`
- Dashboard: cert expiry monitoring
- Custom domain per tenant

**Acceptance criteria:**
- [ ] All services HTTPS by default
- [ ] Auto-renewal 30 days before expiry
- [ ] Custom domain per partner verified

---

### Task 5 — ROMA CRD + Controller (🟡 Medium)
**Owner:** Agent  
**Priority:** P2

Custom Resource Definition for roma deployments:

**Deliverables:**
- `config/crd/bases/roma.io_partners.yaml`
- Controller reconciler
- `config/samples/partner-basic.yaml`
- CLI: `kubectl get partners`

**Acceptance criteria:**
- [ ] CRD installed via Helm
- [ ] Controller manages partner lifecycle
- [ ] Status reflects deployment health

---

## Dependencies

```
Task 1 (Vault) ──┬──► Task 2 (API Gateway)
                 └──► Task 3 (Stripe Webhook)

Task 4 (TLS) ──► Task 5 (CRD) [loose]
```

---

## Environment

**GitHub:** https://github.com/mahaasur13-sys/roma-execution-bridge

**Storage available:**
- Longhorn (`longhorn` SC, 50Gi+)
- Rook Ceph (`rook-ceph-block`, `rook-cephfs`, `rook-ceph-object`)
- MinIO (S3: `http://minio:30900`)

**Monitoring:** Prometheus 30d + Grafana + Loki (stages 15-20 from Pop!_OS)

---

## Progress

| Task | Status | Notes |
|------|--------|-------|
| 1. Vault | 🔴 Todo | P0 — start here |
| 2. API Gateway | 🟡 Todo | |
| 3. Stripe Webhook | 🟡 Todo | |
| 4. TLS | 🟡 Todo | |
| 5. CRD + Controller | 🟡 Todo | |

---

## Commands

```bash
# Enter roma-execution-bridge
cd /home/workspace/roma-execution-bridge

# Check charts
ls charts/

# Current K8s state
kubectl get nodes
kubectl get pods -A

# Stage-by-stage Sprint 2
# Task 1: Vault
make sprint2-task1

# Task 2: API Gateway
make sprint2-task2

# etc.
```