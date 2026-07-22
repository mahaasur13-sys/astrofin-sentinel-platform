# Threat Model — AstroFin Sentinel Platform

> **Scope:** AstroFin Sentinel V5 (multi-agent trading intelligence) and its sibling services
> (roma-execution-bridge, atom-federation-os, acos-contracts).
> **Audience:** Engineers, security reviewers, ops.
> **Last reviewed:** 2026-06-26
> **Status:** Living document — update when surface area or data flows change.

This document applies the **STRIDE** classification to the system and an **Attack Tree**
to the highest-impact paths. It is intentionally short and pragmatic — not a formal
penetration test plan.

---

## 1. System Overview

```
                         ┌───────────────────────┐
                         │   External Users      │
                         └───────────┬───────────┘
                                     │ HTTPS (Dash)
                                     ▼
                         ┌───────────────────────┐
                         │  web/app.py (Dash)    │
                         │  port 8050            │
                         └───────────┬───────────┘
                                     │ internal RPC
              ┌──────────────────────┼────────────────────────┐
              ▼                      ▼                        ▼
   ┌────────────────────┐  ┌────────────────────┐   ┌─────────────────────┐
   │ orchestration/     │  │ agents/_impl/*     │   │ meta_rl/            │
   │ sentinel_v5.py     │  │ (12+ agents)       │   │ (calibration /      │
   │ (coordinator)      │  │                    │   │  A/B testing)       │
   └─────────┬──────────┘  └─────────┬──────────┘   └─────────┬───────────┘
             │                       │                       │
             ▼                       ▼                       ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │            core/  (ephemeris, aspects, history_db, risk)            │
   └────────────────────────────────────────────────────────────────────┘
             │                       │                       │
             ▼                       ▼                       ▼
   ┌────────────────────┐  ┌────────────────────┐   ┌─────────────────────┐
   │ data_room (Flask   │  │ integrations/      │   │ brokers (Alpaca,    │
   │ blueprint)         │  │ (CoinGecko,        │   │ Tinkoff, Binance)   │
   │ /data-room/...     │  │  Yahoo, SEC)       │   │                     │
   └────────────────────┘  └────────────────────┘   └─────────┬───────────┘
                                                              │ orders
                                                              ▼
                                                    ┌─────────────────────┐
                                                    │ External Exchanges  │
                                                    └─────────────────────┘
```

Trust boundaries (red lines in the diagram):

| Boundary | From | To | Mitigations |
|----------|------|----|-------------|
| **TB-1** | Internet | Dash web (8050) | TLS, auth headers, ALLOWED_ORIGINS, validate_startup() |
| **TB-2** | Dash | Internal agents | localhost-only, no auth (single-host deployment) |
| **TB-3** | Agents | External brokers | broker API keys, IP allowlist (broker-side) |
| **TB-4** | All | PostgreSQL | TLS, least-privilege role, no root in app |
| **TB-5** | CI | Secrets store | OIDC, short-lived tokens, no long-lived secrets in repo |

---

## 2. STRIDE Classification

### 2.1 Spoofing (S)

| Threat | Asset | Mitigation |
|--------|-------|------------|
| Forged broker order attribution | Trading account | Broker-side API key + IP allowlist; orders tagged with nonces. |
| Forged GitHub identity opening malicious PR | Codebase | Branch protection + CODEOWNERS + required reviews. |
| Forged CI artifacts | Docker images | (Future) cosign signing; for now, GH Actions provenance only. |

### 2.2 Tampering (T)

| Threat | Asset | Mitigation |
|--------|-------|------------|
| Modified signal weights | `meta_rl/ab_testing.py` | PR review + CODEOWNERS; weights stored in version-controlled config. |
| Tampered session history | `core/history_db.py` (SQLite) | File-level filesystem permissions; backup job in `docs/RUNBOOK.md`. |
| Modified ephemeris output | `core/ephemeris.py` | Swiss Ephemeris library pinned in `requirements.txt`; deterministic seed. |

### 2.3 Repudiation (R)

| Threat | Asset | Mitigation |
|--------|-------|------------|
| Operator denies placing trade | Audit log | `agents/_impl/amre/audit.py` DecisionRecord; every decision persisted with timestamp. |
| Untraceable config change | Configs | Git history + signed commits (recommended, not yet enforced). |

### 2.4 Information Disclosure (I)

| Threat | Asset | Mitigation |
|--------|-------|------------|
| API key leak via logs | Broker creds | `secrets_loader.load()` redaction; pre-commit detect-secrets; `.secrets.baseline`. |
| Ephemeris license in repo | License file | `.gitignore` Swiss Ephemeris license; license not committed. |
| Data room conflict dumps | Internal | Data room only on localhost; auth-gated in Dash; no public URL. |

### 2.5 Denial of Service (D)

| Threat | Asset | Mitigation |
|--------|-------|------------|
| Dash endpoint flooded | Web tier | Dash behind reverse proxy (nginx/Caddy) with rate limit; `validate_startup()` rejects misconfig. |
| Ephemeris CPU exhaustion | Compute | Cached planetary positions; bounded `orb` calculation. |
| Broker rate-limit breach | Trading | Internal request throttler; queue + backoff. |

### 2.6 Elevation of Privilege (E)

| Threat | Asset | Mitigation |
|--------|-------|------------|
| Container escape | Host | Non-root `appuser`, read-only fs, drop ALL capabilities (see Dockerfile). |
| SQL injection via RAG query | Data room | Parameterised queries; SQLAlchemy ORM where applicable. |
| Code execution via eval in agent | Process | `ruff` E9 rules + manual review; `pickle` blocked in agent I/O. |

---

## 3. Attack Tree — Top-Impact Path: Unauthorised Trade Execution

```
                            [Unauthorised Trade]
              ┌─────────────┬────────────┬─────────────┬─────────────┐
              ▼             ▼            ▼             ▼             ▼
       [Broker creds    [RCE in       [Config       [Replay       [API key
        stolen]         agent]        tampering]    attack]       rotation
                                                                        miss]
              │             │            │             │             │
   ┌──────────┴───────┐  ┌───┴────┐  ┌────┴────┐  ┌─────┴─────┐  ┌────┴────┐
   ▼                  ▼  ▼        ▼  ▼         ▼  ▼           ▼  ▼         ▼
[log leak]  [.env leak] [RCE in   [weights   [signed     [GH Actions  [no expiry]
                          web/]     file       payload      token leak]
                                    edit]      capture]
```

Highest-likelihood leaves (red):

1. **`.env` leak** → mitigated by `secrets_loader`, `detect-secrets` CI, secrets rotation
   procedure in `secrets-policy.md`.
2. **Weights file tampering** → mitigated by CODEOWNERS + required reviews.
3. **Broker key rotation miss** → mitigated by 90-day rotation policy (see `secrets-policy.md`).

---

## 4. Out of Scope

- Physical security of the host (handled by hosting provider).
- DDoS at the network edge (handled by Cloudflare / hosting provider).
- Insider threat with admin access to the host OS — a separate HR/process concern.

---

## 5. Review Cadence

| Trigger | Action |
|---------|--------|
| New external integration | Add to STRIDE table, re-classify. |
| Quarterly review (next: **2026-09-26**) | Walk through STRIDE, retire obsolete threats. |
| Post-incident | Update Attack Tree with the actual chain. |

---

## 6. References

- OWASP STRIDE: https://owasp.org/www-community/Threat_Modeling
- OWASP Attack Tree: https://owasp.org/www-community/Attack_Tree
- Project: `docs/SECURITY.md`, `security/secrets-policy.md`, `security/rbac-matrix.md`.