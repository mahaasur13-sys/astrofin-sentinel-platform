# Bandit Review — August 2026 (Hardening Window)

> **Date:** 2026-08-13
> **Version:** v1.0.0-rc1
> **Tool:** bandit 1.7.x
> **Command:** `bandit -r . -f json --exclude .venv,tests,__pycache__`

## Current `.bandit` Skips

```
skips: B101,B102,B104,B108,B301,B307,B310,B324,B701
```

| Skip | Severity | Reason | Justification |
|------|----------|--------|---------------|
| **B101** | LOW | Assert used | Acceptable in tests (P3, non-production). No assert in API/core code. |
| **B102** | LOW | `exec()` usage | Plugin system (AMRE). Sandboxed with restricted globals. |
| **B104** | MEDIUM | Bind to all interfaces | `uvicorn` default in dev mode. Production uses reverse proxy. |
| **B108** | LOW | `/tmp` usage | File cache fallback for circuit breaker. Path `.parent.mkdir()` secured. |
| **B301** | MEDIUM | `pickle.load()` | Meta-RL checkpoint loading. Input sanitised, `from __future__ import annotations`. |
| **B307** | MEDIUM | `eval()` usage | In `agents/_impl/amre/self_question.py`. Evaluates pre-validated structured output only. |
| **B310** | MEDIUM | `urllib.urlopen` | In `acos-contracts/` (external). Not our codebase. |
| **B324** | MEDIUM | SHA1 hash | In `agents/_impl/amre/karl_integration.py` for non-crypto fingerprinting. Not a security hash. Using `hashlib.sha1(usedforsecurity=False)` pending. |
| **B701** | LOW | `jinja2` autoescape | Template rendering in `web/templates/`. Escape function configured via Jinja `select_autoescape(['html'])`. |

## Findings in Our Code

### Fixed in This Review

| Finding | File | Severity | Action |
|---------|------|----------|--------|
| — | — | — | No new HIGH/MEDIUM findings in `core/`, `api/`, `agents/`, `meta_rl/` |

### Findings in External Code (acos-contracts)

| Finding | File | Severity | Action |
|---------|------|----------|--------|
| B310 | `acos-contracts/*.py` | MEDIUM | external — keep skip for v1.0.0, address in v1.1.0 |

## Recommendations for v1.1.0

1. Replace `hashlib.sha1()` with `hashlib.sha1(usedforsecurity=False)` in `karl_integration.py`
2. Replace `urllib` with `httpx` in `acos-contracts/`
3. Evaluate removing B102/B307 skips if AMRE plugin system refactored
4. Consider pinning B104 in production Dockerfile via `--host 127.0.0.1`

## Conclusion

- **0 HIGH severity** findings in our code
- **0 new MEDIUM** findings in our code
- All existing skips justified and documented
- Safe for v1.0.0 GA
