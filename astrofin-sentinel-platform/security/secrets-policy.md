# Secrets Policy — AstroFin Sentinel Platform

> **Status:** Living document
> **Owner:** Platform team
> **Last reviewed:** 2026-06-26

This document is the **source of truth** for how secrets are created, stored, rotated,
and revoked across the platform. It binds to:

- `.github/workflows/ci.security.yml` (automated detect-secrets + pip-audit + safety)
- `web/data_room.py` (auth-gated data endpoints)
- `core/auth.py` / `core_determinism/auth.py` (`validate_startup()`)
- `requirements.txt` (no hard-coded keys; pinned versions only)

---

## 1. Classification

| Class | Examples | Storage | Rotation |
|-------|----------|---------|----------|
| **C0 — Public** | Ephemeris data files, public market data | Repo, public registries | N/A |
| **C1 — Internal** | Aggregated metrics, internal API URLs | Repo, internal docs | N/A |
| **C2 — Confidential** | DB passwords, broker API keys, OAuth tokens | Env vars / `secrets_loader.load()` | **90 days** |
| **C3 — Critical** | Broker **secret** keys, withdrawal keys | Vault / 1Password / GitHub Actions Secrets | **30 days** |

> **No secret of any class may be committed to git.** Pre-commit (`detect-secrets`)
> blocks C2/C3. If a secret was ever committed, treat it as compromised (see §6).

---

## 2. Creation

1. Generate the secret with a cryptographically secure source
   (`openssl rand -hex 32`, broker-side key generator, or GitHub Actions secret).
2. Store it in the **narrowest** scope possible:
   - **Local dev** → `.env` (gitignored) loaded via `secrets_loader.load()`.
   - **CI** → GitHub Actions → Settings → Secrets → *Repository* (preferred) or
     *Environment* for `production` / `staging`.
   - **Production** → injected by deployer (Zo `register_user_service` env_vars,
     k8s `Secret`, or platform secret store).
3. Document the secret's **owner**, **purpose**, and **rotation cadence** in this file
   (see §4 inventory).

---

## 3. Storage Rules

### 3.1 Filesystem

- `.env`, `.env.*` are in `.gitignore`.
- `.secrets.baseline` (detect-secrets) **is** committed; it contains hashed signatures,
  not the secrets themselves.
- No literal credentials in code, even for tests. Use mocks
  (`tests/fixtures/` with `MOCK_*` placeholders).

### 3.2 Environment variables

| Var | Required by | Notes |
|-----|-------------|-------|
| `ALPACA_API_KEY_ID` / `ALPACA_API_SECRET_KEY` | `integrations/alpaca*` | C3 — 30-day rotation |
| `TINKOFF_TOKEN` | `integrations/tinkoff*` | C3 — 30-day rotation |
| `BINANCE_API_KEY` / `BINANCE_API_SECRET` | `integrations/binance*` | C3 — 30-day rotation |
| `DATABASE_URL` | `db/`, `core/history_db.py` | C2 — 90-day rotation |
| `REDIS_URL` | meta_rl persistence, queue | C2 — 90-day rotation |
| `SECRET_KEY` (Dash) | `web/app.py` | C2 — auto-generated per process |
| `ALLOWED_ORIGINS` | `web/app.py` | C1 — set per environment |
| `GH_TOKEN_CODERABBIT` (CI) | `.github/workflows/*` | C2 — GitHub-managed |

### 3.3 Never store

- Hard-coded `sk_live_*`, `whsec_*`, or any production secret.
- Private keys (`-----BEGIN ... PRIVATE KEY-----`) in repo.
- Real broker testnet creds paired with production order logic.

---

## 4. Rotation

### 4.1 Cadence

| Class | Cadence | Procedure owner |
|-------|---------|-----------------|
| C3 | **30 days** | Platform on-call |
| C2 | **90 days** | Service owner |
| C1 / C0 | N/A | — |

### 4.2 Procedure (C2 / C3)

1. Generate the new secret at the provider.
2. Add the new secret alongside the old (both valid for ≤24 h grace period
   where the provider supports it).
3. Roll out the new value via the deployer.
4. Verify: integration smoke test (`pytest tests/integration/test_*broker*.py`).
5. Revoke the old secret at the provider.
6. Update the inventory (see §5) with the new timestamp.

### 4.3 Emergency rotation (suspected leak)

1. **Immediately** revoke the secret at the provider.
2. Generate a new one; deploy.
3. Search git history (`git log -p --all -S '<partial-secret>'`) and external
   sources for the leak.
4. If the secret was committed, follow §6.

---

## 5. Inventory (template)

Maintain the active secret list in this table. **Do not write the secret value.**

| Name | Owner | Provider | Class | Created | Last rotated | Next rotation | Storage |
|------|-------|----------|-------|---------|--------------|---------------|---------|
| `ALPACA_API_KEY_ID` | TBA | Alpaca | C3 | TBA | TBA | TBA | GitHub Actions Secret |
| `ALPACA_API_SECRET_KEY` | TBA | Alpaca | C3 | TBA | TBA | TBA | GitHub Actions Secret |
| `TINKOFF_TOKEN` | TBA | Tinkoff | C3 | TBA | TBA | TBA | GitHub Actions Secret |
| `BINANCE_API_KEY` | TBA | Binance | C3 | TBA | TBA | TBA | GitHub Actions Secret |
| `BINANCE_API_SECRET` | TBA | Binance | C3 | TBA | TBA | TBA | GitHub Actions Secret |
| `DATABASE_URL` | TBA | Postgres | C2 | TBA | TBA | TBA | Zo env_vars |
| `REDIS_URL` | TBA | Redis | C2 | TBA | TBA | TBA | Zo env_vars |

> **Action item:** fill `TBA` on first deploy. This is a placeholder template.

---

## 6. Incident: secret committed to repo

1. **Assume the secret is compromised**, even if later removed.
2. Rotate immediately (§4.3).
3. Use `git filter-repo` or BFG to scrub history; force-push.
4. File an incident under `docs/incidents/YYYY-MM-DD-secret-leak.md`.
5. Update this policy with the lesson learned.

---

## 7. Detection

| Mechanism | Coverage | Owner |
|-----------|----------|-------|
| `detect-secrets` pre-commit | Local dev | Each contributor |
| `detect-secrets` CI (`.secrets.baseline`) | PR + push | `ci.security.yml` |
| `pip-audit` + `safety` (CI) | Dependency vulns | `ci.security.yml` |
| Manual review | CODEOWNERS | Reviewers |

---

## 8. References

- GitHub: Removing sensitive data from a repository — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- OWASP Secrets Management Cheat Sheet — https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
- `docs/RUNBOOK.md` — operational procedures for secret rotation during incidents.