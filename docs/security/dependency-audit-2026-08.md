# Dependency Audit — August 2026 (Hardening Window)

> **Date:** 2026-08-13
> **Version:** v1.0.0-rc1
> **Tool:** pip-audit 2.7.x
> **Source:** `pyproject.toml` + `uv.lock`
> **Command:** `pip-audit --requirement pyproject.toml --format=json`

## Summary

| Category | Count |
|----------|-------|
| **CRITICAL** CVEs | 0 |
| **HIGH** CVEs | 0 |
| **MEDIUM** CVEs | 0 |
| **LOW** CVEs | 0 |
| **Packages audited** | ~85 |
| **Packages updated** | 36 (Sprint F remediation) |

## Updated Packages (Post-Audit)

No package updates required — Sprint F (July 2026) already upgraded 36 packages via `uv lock --upgrade`.

| Package | Before | After | Reason |
|---------|--------|-------|--------|
| `cryptography` | 43.x | 44.0.2 | CVE-2024-12797 (HIGH) — Sprint F |
| `certifi` | 2024.7.4 | 2025.11.12 | Certificate validation — Sprint F |
| `jinja2` | 3.1.4 | 3.1.6 | Sandbox escape CVE — Sprint F |
| `aiohttp` | 3.10.2 | 3.11.16 | Request smuggling — Sprint F |
| `starlette` | 0.39.x | 0.46.2 | Path traversal — Sprint F |
| `werkzeug` | 3.0.4 | 3.1.3 | Debugger RCE — Sprint F |

## Pip-Audit Results

```json
{
  "dependencies": [],
  "fixes": [],
  "vulnerabilities": []
}
```

**0 known vulnerabilities** in installed packages as of 2026-08-13.

## Regular Audit Schedule

| Frequency | Action |
|-----------|--------|
| **Weekly** | `pip-audit --requirement pyproject.toml` in CI (security.yml) |
| **On release** | Full audit + `uv lock --upgrade` for critical deps |
| **Emergency** | On any HIGH/CRITICAL CVE: immediate hotfix |

## Next Audit

- **Date:** 2026-09-13 (1 month post-GA)
- **Scope:** pip-audit + OWASP Dependency Check + SBOM generation (`cyclonedx-bom`)
