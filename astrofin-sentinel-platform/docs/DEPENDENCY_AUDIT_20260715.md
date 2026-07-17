# Dependency Audit & CVE Report

**Date:** 2026-07-15
**Branch:** consolidation-v1
**Commit:** eb1e3a4

## 1. Vulnerabilities (pip-audit)

| Package | Version | CVE | Fix Version | Severity |
|---------|---------|-----|-------------|----------|
| mcp | 1.12.4 | PYSEC-2026-1617 | 1.23.0 | HIGH |
| nltk | 3.9.3 | PYSEC-2026-597, -2085, -2235, -2236, -2237 | 3.9.4 | MEDIUM |
| ragas | 0.2.15 | PYSEC-2026-3046, -3047 | 0.3.0rc1 | MEDIUM |
| setuptools | 82.0.1 | PYSEC-2026-3447 | 83.0.0 | MEDIUM |
| starlette | 0.49.3 | PYSEC-2026-161, -248, -249, -2280, -2281 | 1.0.1+ | HIGH |
| uv | 0.6.14 | PYSEC-2026-2001, -2295, GHSA-w476, -pjjw, -4gg8 | 0.11.15 | HIGH |

**Action:** Upgrade mcp, nltk, setuptools, starlette, uv immediately. ragas upgrade is optional (rc version).

## 2. Dependency Conflicts (pip check — 15 conflicts)

### Group A: OpenTelemetry version drift (2 conflicts)
- opentelemetry-sdk 1.40.0 requires api==1.40.0 (have 1.42.1)
- opentelemetry-sdk 1.40.0 requires semantic-conventions==0.61b0 (have 0.63b1)
- **Fix:** `pip install opentelemetry-sdk==1.42.1`

### Group B: LangChain ecosystem (4 conflicts)
- langchain 0.3.28 requires langchain-core<1.0.0 (have 1.2.22)
- langchain-openai 0.3.35 requires langchain-core<1.0.0 (have 1.2.22)
- nemoguardrails 0.17.0 requires langchain-core<0.4.0 (have 1.2.22)
- langchain-classic 1.0.3 requires langchain-text-splitters>=1.1.1 (have 0.3.11)
- **Fix:** Downgrade langchain-core to 0.3.x OR upgrade all langchain packages to 1.x compatible versions

### Group C: FastAPI/Uvicorn (3 conflicts)
- aiqtoolkit 1.1.0 requires fastapi~=0.115.5 (have 0.139.0)
- aiqtoolkit 1.1.0 requires uvicorn~=0.32.0 (have 0.51.0)
- acos 6.0.0 requires fastapi<0.116 (have 0.139.0), uvicorn<0.32 (have 0.51.0)
- **Fix:** Update pyproject.toml constraints in acos to allow fastapi>=0.115, uvicorn>=0.32

### Group D: Pydantic (2 conflicts)
- llama-index-instrumentation 0.5.0 requires pydantic>=2.11.5 (have 2.10.6)
- llama-index-workflows 2.17.1 requires pydantic>=2.11.5 (have 2.10.6)
- **Fix:** `pip install pydantic>=2.11.5`

### Group E: Protobuf (1 conflict)
- autogen-core 0.7.5 requires protobuf~=5.29.3 (have 6.33.6)
- **Fix:** Downgrade protobuf to 5.29.x OR upgrade autogen-core

### Group F: Pillow (1 conflict)
- fastembed 0.6.0 requires pillow<12.0.0 (have 12.3.0)
- **Fix:** Upgrade fastembed or pin pillow<12

### Group G: Ansible (1 conflict)
- ansible 13.5.0 requires ansible-core~=2.20.4 (have 2.16.18)
- **Fix:** Upgrade ansible-core to 2.20.x

## 3. Recommended Fix Order

1. **Critical CVEs first:** starlette, mcp, uv, nltk, setuptools
2. **Easy wins:** opentelemetry-sdk, pydantic
3. **Medium:** protobuf, pillow, ansible-core
4. **Complex (needs testing):** langchain ecosystem, fastapi/uvicorn constraints

## 4. Non-auditable local packages (8)
acos, acos-contracts, astrofin-sentinel, astrofin-sentinel-v5, asurdev-sentinel, atom-federation-os, atomos-agents, supervisor
- These are internal packages, not on PyPI. Safe to ignore.
