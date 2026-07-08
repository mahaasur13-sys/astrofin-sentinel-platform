# SOPS — Secrets Operations

> **Owner:** Security
> **Status:** ✅ Implemented (2026-07-08)
> **Version:** 1.0

---

## Why SOPS

Plain `env.example` files committed to the repo are a leak vector. SOPS
encrypts secrets at rest with KMS-backed keys and lets us keep them
versioned without exposing plaintext.

## Layout

| Path | Purpose | Committed? |
|------|---------|------------|
| `.sops.yaml` | SOPS rule: which key encrypts `*.enc.yaml` | ✅ Yes |
| `.env.prod.enc.yaml` | Encrypted production secrets | ✅ Yes (ciphertext) |
| `.env.prod.example` | Decrypted structure, no values | ✅ Yes |
| `.env.prod` | Decrypted local file | ❌ No (.gitignored) |

## Encrypt / Decrypt (CI)

```bash
# Decrypt (used by CI / local dev)
sops --decrypt .env.prod.enc.yaml > .env.prod

# Encrypt (after rotation)
sops --encrypt --in-place .env.prod.enc.yaml
```

The CI job `Deploy / decrypt-secrets` runs `sops --decrypt` before
deploying and exports the values to the pod via envFrom.

## KMS

- **Dev / CI:** `age` (public key in `.sops.yaml`)
- **Prod:** AWS KMS `arn:aws:kms:eu-central-1:ACCT:key/<id>`

Key rotation: every 90 days, tracked in `docs/SECURITY.md` §3.

## Related

- `docs/SECURITY.md` — threat model
- `docs/ENV.md` — full env var inventory
- ADR-0002 — SOPS selection rationale
