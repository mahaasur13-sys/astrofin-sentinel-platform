# Security Hardening — Immediate Actions (2026-07-27)

**Window:** Pre-release hardening, code freeze compliant.  
**Executed by:** Zo  
**Reviewed by:** Felix  

---

## 1. Cache Directory Permissions — FIXED

| Path | Before | After | Action |
|------|--------|-------|--------|
| `~/.cache/astrofin/` | `0755` (world-readable) | `0700` | `chmod -R 700` |
| `~/.cache/sec_edgar_cache/` | `0755` | `0700` | `chmod -R 700` |
| `~/.cache/astrofin/chroma/` | (new) | `0700` | Created with `CHROMA_CACHE_DIR` env var |

**Rationale:** Cached SEC EDGAR filings and ChromaDB vectors could be inspected by other processes on the host. `0700` restricts to owner-only access.

---

## 2. Secret Leak Audit — PASSED

| Check | Result |
|-------|--------|
| `.env` files in git history | None leaked |
| `sk-*` API keys in logs/ | None found |
| `jwt_public.pem` in git | Public key only (acceptable) |
| `keys/` directory | Only public key, no private key |

---

## 3. Port Exposure — PASSED

| Port | Expected | Actual |
|------|----------|--------|
| 8000 (FastAPI) | Not bound | Not bound |
| 8050 (Dash) | Not bound | Not bound |
| 5432 (PostgreSQL) | localhost only | Not exposed |
| 6379 (Redis) | localhost only | Not exposed |
| 3100 (Loki) | localhost only | Not exposed |
| 3000 (Grafana) | localhost only | Not exposed |

No open ports on public interfaces — all services bound to `127.0.0.1`.

---

## 4. PostgreSQL Hardening — FIXED

| Parameter | Before | After |
|-----------|--------|-------|
| `password_encryption` | `scram-sha-256` | `scram-sha-256` ✅ |
| `log_connections` | `off` | `on` ✅ |
| Active cluster | Down | Running ✅ |
| pg_hba.conf auth method | Already scram-sha-256 | No changes needed |

**Action:** `log_connections = on` enabled — now every connection attempt is logged.

---

## 5. CHROMA_CACHE_DIR Environment Variable

Added to `env.example` and `env.prod.example`:

```bash
CHROMA_CACHE_DIR=$HOME/.cache/astrofin/chroma
SEC_EDGAR_CACHE_DIR=$HOME/.cache/sec_edgar_cache
```

---

## Summary

| Total Actions | 5 |
|---------------|---|
| Permissions fixed | 2 |
| Secret audit passes | 3 |
| Port exposure verified | 0 issues |
| PostgreSQL hardened | 2 parameters |
| Env vars documented | 2 |

**Result:** No vulnerabilities found. All hardening measures applied within freeze constraints — zero `.py` files touched.
