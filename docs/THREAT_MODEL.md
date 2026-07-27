# AstroFin Sentinel V5 — Threat Model & Accepted Vulnerability Exceptions

> **Version:** v1.0.0  
> **Last updated:** 2026-07-27  
> **Audit:** Phase 2 — Deep Audit & Consolidation  
> **Next review:** 2026-09-01 (quarterly)

---

## 1. Threat Model Overview

### Data Flow Boundaries

```
┌──────────────┐     ┌──────────────┐     ┌────────────────────┐
│   User/API   │────▶│  FastAPI      │────▶│  Agent Council     │
│   (port 8000)│     │  rate_limit   │     │  (RAG-first)       │
└──────────────┘     └──────┬───────┘     └─────────┬──────────┘
                            │                       │
                   ┌────────▼───────┐     ┌─────────▼──────────┐
                   │  dash (8050)   │     │  data_room/        │
                   │  @require_auth │     │  circuit_breaker   │
                   └────────────────┘     └─────────┬──────────┘
                                                    │
                              ┌─────────────────────┼─────────────────────┐
                      ┌───────▼──────┐  ┌───────────▼──────────┐  ┌───────▼──────┐
                      │  Coingecko   │  │  SEC EDGAR (public)  │  │  Yahoo Fin   │
                      │  (rate lim)  │  │  (rate lim, cache)   │  │  (rate lim)  │
                      └──────────────┘  └──────────────────────┘  └──────────────┘
```

### Trust Boundaries

| Boundary | Classification | Protection |
|----------|---------------|------------|
| API → Agent Board | Internal | LLM Router + RAG-only validation |
| Agent → data_room | Internal | Circuit breaker, retry budget |
| data_room → External APIs | **Trust boundary** | Rate limiting, cache, timeout (30s) |
| Dash (8050) → End user | **Trust boundary** | `@require_auth` on 5/6 routes, HTTPS on GA |
| PostgreSQL (5432) | Internal | Unix socket only, no external binding |
| SEC EDGAR resolver | **Public trust boundary** | User-Agent rotation, rate limiting, 30s timeout |

### Assets at Risk

| Asset | Impact | Protection |
|-------|--------|------------|
| API keys / tokens | HIGH | `.env` only, GitHub Secrets for CI, `detect-secrets` pre-commit |
| Trade signals | MEDIUM | Audit trail (JSONL), WAL-G PostgreSQL backups |
| User sessions (SQLite) | LOW | Local-only, no network export |
| Planetary positions (Swiss Ephemeris) | LOW | Local compute, no external I/O |
| SEC EDGAR cache | LOW | `~/.cache/sec_edgar_cache`, 0o700 |

---

## 2. Accepted Vulnerability Exceptions (v1.0.0)

The following vulnerabilities are acknowledged and accepted for v1.0.0 GA.
Each exception includes a risk assessment, mitigation, and review date.

| CVE / PYSEC | Package | Version | Risk | Mitigation | Review Date |
|-------------|---------|---------|------|------------|-------------|
| PYSEC-2026-311 | chromadb | 1.5.5 | **Medium** — DoS via crafted HTTP request to ChromaDB server; pre-auth code injection | ChromaDB used in embedded mode only (no external server). Vector store runs as local process, never exposed to network. No RCE vector in our usage — we do not accept external embeddings or metadata that could trigger the injection path. Monitor upstream; pin to >=1.6.0 when available. | 2026-09-01 |
| PYSEC-2026-2447 | diskcache | 5.6.3 | **Low** — Local privilege escalation via symlink attack on cache directory | Cache directory is `~/.cache/astrofin` with `0o700` permissions. Deployment is sandboxed (gVisor container on Zo, systemd unit on Pop!_OS). No multi-tenant filesystem access. Monitor upstream; upgrade when fix released. | 2026-09-01 |
| PYSEC-2026-3046 | ragas | 0.4.3 | **Medium** — SSRF vulnerability in multi-modal faithfulness metric | RAG evaluation runs exclusively against internal vector store (`knowledge/rag_index.py`). No external URLs or user-supplied HTTP endpoints are passed to ragas metrics. SSRF vector not reachable in current architecture. Pin to >=0.5.0 when available. | 2026-09-01 |

### Dependency Audit Summary

```
$ pip-audit
Found 3 known vulnerabilities in 3 packages
  0 HIGH
  0 CRITICAL
  3 MEDIUM (1 chromadb, 1 diskcache, 1 ragas)
  0 UNKNOWN (fixed: 8 internal deps not on PyPI — expected)
```

---

## 3. Security Measures (Implemented)

### Pre-Commit & CI

| Check | Status | Tool |
|-------|--------|------|
| Secrets detection | ✅ Active | `detect-secrets` (pre-commit) |
| SAST (static analysis) | ✅ Active | `bandit` — 0 HIGH, 1 MEDIUM (B108 fixed 2026-07-27) |
| Code quality | ✅ Active | `ruff` — 0 violations on core/agents/data_room |
| Architecture linter | ✅ Active | `scripts/architecture_linter.py` — 0 violations |
| Dependencies | ✅ Active | `pip-audit` (nightly + security.yml) |
| Secrets runtime scan | ✅ Active | `gitleaks` in `security.yml` |

### Runtime Protections

| Protection | Module | Details |
|------------|--------|---------|
| API auth | `web/middleware/` | `@require_auth` decorator on 5/6 production routes |
| Rate limiting | `core/rate_limit.py` | Token bucket per IP, Redis-backed |
| Circuit breaker | `data_room/circuit_breaker.py` | Fail-fast after 3 consecutive errors, 30s reset |
| Input validation | `api/main.py` | Pydantic models for all API inputs |
| SQL injection | `core/` | Parameterized queries exclusively (fixed per Wave 3 audit) |
| Secret management | `.env` | No hardcoded credentials (0 HIGH bandit as of 2026-07-25) |
| JWT auth | `core/auth_jwt_middleware.py` | Flask middleware for legacy web routes |
| Log sanitization | `core/logging.py` | Redacts secrets from log output |

---

## 4. Known Attack Vectors (Not Vulnerabilities)

These are design choices, not defects:

| Vector | Risk | Rationale |
|--------|------|-----------|
| Local SQLite history (`core/history_db.py`) | Low | Trade history is local; no network export. Acceptable for v1.0.0. GA target: postgres migration. |
| Port 8050 (Dash) in dev mode | Low | Dev-only. Production: Nginx reverse proxy + HTTPS on GA. |
| Swiss Ephemeris files on disk | Low | Ephemeris data is public-domain planetary data. No secrets. |
| data_room HTTP calls to public APIs | Low | All calls to public, documented APIs. No auth tokens in URL. Rate-limited. |

---

## 5. Review Cycle

- **Quarterly review:** every 3 months (next: 2026-09-01)
- **Trigger events:**
  - New pip-audit finding → immediate review
  - New agent or data source → threat model update
  - Production deployment → full reassessment
- **Owner:** Felix (mahaasur13-sys)
- **Review includes:**
  - Re-scan: `pip-audit`, `bandit`, `ruff`, `detect-secrets`
  - Check for upstream fixes to accepted exceptions
  - Update this document with findings

---

## 6. References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Bandit documentation](https://bandit.readthedocs.io/)
- [pip-audit](https://pypi.org/project/pip-audit/)
- [CVE-2026-311 (chromadb)](https://osv.dev/PYSEC-2026-311)
- [CVE-2026-2447 (diskcache)](https://osv.dev/PYSEC-2026-2447)
- [CVE-2026-3046 (ragas)](https://osv.dev/PYSEC-2026-3046)
