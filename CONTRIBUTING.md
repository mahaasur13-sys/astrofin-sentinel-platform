# 🤝 Contributing to AstroFin Sentinel

> **Status:** ✅ Active (last reviewed 2026-07-04)
> **Welcome!** We're glad you're here. This guide covers everything you need to make your first contribution.

---

## 1. 🎯 Quick Start (5 minutes)

```bash
# 1. Fork & clone
gh repo fork mahaasur13-sys/astrofin-sentinel-platform --clone --remote
cd astrofin-sentinel-platform

# 2. Setup (assumes Python 3.11+ and uv)
make setup   # creates venv, installs deps, pre-commit hooks

# 3. Run tests
make test    # pytest -q

# 4. Pick an issue
gh issue list --label "good-first-issue" --state open
```

**That's it!** You're ready to contribute. For deeper context, read on.

---

## 2. 📚 Table of Contents

1. [Quick Start](#1-🎯-quick-start-5-minutes)
2. [Code of Conduct](#3-📜-code-of-conduct)
3. [How to Contribute](#4-🛠️-how-to-contribute)
4. [Development Workflow](#5-🔄-development-workflow)
5. [Pull Request Process](#6-✅-pull-request-process)
6. [Coding Standards](#7-🎨-coding-standards)
7. [Testing Requirements](#8-🧪-testing-requirements)
8. [Documentation](#9-📖-documentation)
9. [Release Process](#10-🚀-release-process)
10. [Getting Help](#11-❓-getting-help)

---

## 3. 📜 Code of Conduct

**Be kind, respectful, and constructive.** This is a small project with 1.5 FTE — every contribution matters.

### Our Pledge

- **Use welcoming language** — "Great catch!" beats "You missed..."
- **Respect differing viewpoints** — disagree on technical merit, not personal
- **Accept constructive criticism gracefully** — PR reviews are learning opportunities
- **Focus on what's best for the project** — not personal preference

### Unacceptable behavior

- Harassment, discrimination, trolling
- Publishing others' private information
- Personal attacks or insults
- Unwelcome sexual attention

**Report violations:** Open issue with label `conduct-violation` or email `conduct@astrofin.dev`.

---

## 4. 🛠️ How to Contribute

### 4.1 Types of contributions

We welcome:

- 🐛 **Bug fixes** — open issue first, then PR
- ✨ **New features** — discuss in issue before implementing (avoid wasted work)
- 📖 **Documentation** — typos, clarifications, examples
- 🧪 **Tests** — increase coverage, edge cases
- 🔍 **Code review** — review open PRs, even if you don't have context yet
- 💡 **Ideas** — open discussion in GitHub Discussions

### 4.2 What NOT to contribute (without prior discussion)

- **New agent types** (e.g., new `*_agent.py`) — affects hybrid signal weights
- **New data sources** — needs compliance review (SEC EDGAR, Polygon.io terms)
- **Schema changes** (`migrations/`) — needs ADR + DB team review
- **CI/CD pipeline changes** — affects all deploys
- **Renaming public APIs** — breaking change, needs major version bump

### 4.3 First-time contributors

Look for these labels:
- `good-first-issue` — small, well-defined, mentoring-friendly
- `help-wanted` — needs extra hands, no specific expertise required
- `documentation` — docs improvements

**No issue too small.** Typos, broken links, missing examples — all welcome.

---

## 5. 🔄 Development Workflow

### 5.1 Branching strategy

```
main (protected)
  │
  ├── release/1.0.0 (release branch, frozen after W5)
  │     │
  │     ├── feature/issue-XXX-short-desc
  │     ├── feature/issue-YYY-other-desc
  │     └── fix/issue-ZZZ-bug-desc
  │
  └── develop (post-GA, after v1.0.0)
        │
        └── feature/...
```

**Pre-GA (сейчас):** все PR → `release/1.0.0`
**Post-GA (после 2026-08-09):** все PR → `develop`, потом → `main` через release branch

### 5.2 Branch naming

```bash
# Features
git checkout -b feature/issue-123-add-bradley-agent

# Bug fixes
git checkout -b fix/issue-456-jwt-refresh-bug

# Documentation
git checkout -b docs/issue-789-update-readme

# Refactor
git checkout -b refactor/extract-ephemeris-cache
```

### 5.3 Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
<type>(<scope>): <subject>

# Examples
feat(agents): add Bradley seasonality agent with astro weights
fix(auth): JWT refresh token expires 1h early on DST change
docs(readme): add Quick Start section with 5-min setup
test(rag): add hypothesis-based tests for pgvector retriever
refactor(db): extract connection pool to db/pool.py
chore(deps): bump structlog to 24.4.0
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`, `ci`, `revert`

**Scope:** `agents`, `auth`, `db`, `web`, `observability`, `security`, `deps`, etc.

### 5.4 Pre-commit hooks

Установлены через `pre-commit install`. Проверяют перед каждым commit:

- `ruff` (linting)
- `ruff format` (formatting)
- `mypy` (type checking)
- `bandit` (security)
- `detect-secrets` (секреты в коде)
- `architecture_linter.py` (R1–R9 alignment)

**Обход (только для WIP):** `git commit --no-verify -m "WIP"`

---

## 6. ✅ Pull Request Process

### 6.1 Before opening PR

- [ ] Branch rebased on `release/1.0.0` (or `develop` post-GA)
- [ ] `make test` — все тесты зелёные
- [ ] `make lint` — ruff + mypy без ошибок
- [ ] `pre-commit run --all-files` — все hooks зелёные
- [ ] Issue linked в PR description: `Closes #123` или `Refs #456`
- [ ] Description заполнен по template (см. §6.3)
- [ ] Self-review пройден (diff читается как narrative)

### 6.2 PR size guidelines

| Size | Lines changed | Review time | Approval |
|------|---------------|-------------|----------|
| **XS** | < 50 | < 1 hour | 1 reviewer |
| **S** | 50–200 | 1–4 hours | 1 reviewer |
| **M** | 200–500 | 4–8 hours | 1 reviewer + 1 approval от owner zone |
| **L** | 500–1000 | 1–2 days | 2 reviewers + ADR если архитектурно |
| **XL** | > 1000 | 🚫 **Разбей на меньшие PR** | N/A |

**Рекомендация:** PR < 200 строк = быстрый review, меньше конфликтов.

### 6.3 PR template

```markdown
## 🎯 What

[1-2 sentences: что меняется и зачем]

Closes #XXX

## 🔍 Why

[Context: какую проблему решает, какие trade-offs]

## 🧪 How to test

[Steps для reviewer — как воспроизвести/проверить]

## ✅ Checklist

- [ ] Tests added/updated
- [ ] Documentation updated (если user-facing)
- [ ] CHANGELOG.md updated (если влияет на release)
- [ ] No new warnings в CI
- [ ] Architecture linter passes (`python scripts/validate_agent.py ...`)
- [ ] Self-reviewed
- [ ] No merge conflicts

## 📸 Screenshots / Output

[Если UI change — скриншоты. Если CLI — sample output.]
```

### 6.4 Review SLA

| Priority | First response | Approval target |
|----------|----------------|-----------------|
| 🔴 Critical (P0) | < 4 hours | < 24 hours |
| 🟧 High (P1) | < 1 day | < 3 days |
| 🟨 Medium (P2) | < 3 days | < 1 week |
| 🟦 Low (P3) | < 1 week | < 2 weeks |

**Если превышен SLA** — ping в PR comment или Slack.

### 6.5 Merge strategy

- **Squash merge** — для большинства PR (clean history)
- **Merge commit** — для PR с несколькими логическими commits
- **Rebase merge** — для trivial fixes (1 commit)

**Default:** squash, с auto-generated commit message:

```
feat(agents): add Bradley seasonality agent (#123)

* add Astro-council sub-agent for Bradley model
* include S&P 500 seasonality + planetary aspects
* add 12 tests, 100% coverage
* update docs/AGENTS.md weights table
* Closes #123
```

---

## 7. 🎨 Coding Standards

### 7.1 Python style

- **PEP 8** enforced via `ruff` (line length: 100, see `pyproject.toml`)
- **Type hints** required для public API (mypy strict mode)
- **Docstrings** — Google style для public functions/classes

```python
def calculate_aspect_orb(planet_a: str, planet_b: str, aspect: AspectType) -> float:
    """Calculate the orb (angular distance) between two planets for a given aspect.

    Args:
        planet_a: Name of the first planet (e.g., "Sun", "Moon").
        planet_b: Name of the second planet.
        aspect: The aspect type (e.g., AspectType.SQUARE).

    Returns:
        The orb in degrees. Smaller = more exact aspect.

    Raises:
        EphemerisError: If planetary positions cannot be calculated.
    """
    ...
```

### 7.2 Architecture rules (R1–R9)

См. `docs/ARCHITECTURE.md` (будет создан в W3). Ключевые:

- **R1:** Agent implementations only in `agents/_impl/`, never `agents/`
- **R2:** `core/` modules — pure functions, no I/O (use `db/`, `web/` для I/O)
- **R3:** All async code uses `asyncio` + `asyncpg`/`httpx`, no blocking calls
- **R4:** Secrets только через `core/secrets.py` (SOPS-backed)
- **R5:** No `print()` in production code (`ruff T201`)
- **R6:** All DB access через `db/session.py` (no raw connections)
- **R7:** External API calls wrapped in `core/rate_limit.py`
- **R8:** All agents return `AgentResponse` (см. `agents/_impl/types.py`)
- **R9:** RAG search через `knowledge/rag_retriever.py` (no direct FAISS/pgvector access)

**Enforcement:** `python scripts/validate_agent.py <new_agent.py>` — 9 checks.

### 7.3 Imports

```python
# ✅ Good
from core.ephemeris import get_planetary_positions
from agents._impl.fundamental_agent import FundamentalAgent
from web.app import app

# ❌ Bad (R1 violation)
from agents.fundamental_agent import FundamentalAgent  # archived version

# ❌ Bad (R9 violation)
import faiss  # use knowledge/rag_retriever.py instead
```

### 7.4 Error handling

```python
# ✅ Good — specific exceptions
try:
    positions = get_planetary_positions(planet="Sun", dt=now)
except EphemerisNotFound as e:
    logger.warning("Ephemeris not found for Sun at %s, using fallback", now)
    positions = get_fallback_position("Sun")
except EphemerisError as e:
    logger.error("Unexpected ephemeris error: %s", e)
    raise

# ❌ Bad — bare except
try:
    positions = get_planetary_positions(...)
except:  # noqa
    pass
```

### 7.5 Logging

```python
# ✅ Good — structured logging
logger.info("agent_decision",
    extra={
        "agent": "FundamentalAgent",
        "symbol": "BTCUSDT",
        "decision": "LONG",
        "confidence": 0.78,
        "request_id": request_id,
    })

# ❌ Bad — unstructured
logger.info(f"FundamentalAgent decided LONG for BTCUSDT with confidence 0.78")
```

---

## 8. 🧪 Testing Requirements

### 8.1 Test pyramid

```
       ╱╲
      ╱  ╲         E2E (5%)
     ╱────╲        — full system tests
    ╱      ╲       — slow, run nightly
   ╱────────╲
  ╱          ╲     Integration (25%)
 ╱            ╲    — DB, API, multi-agent
╱──────────────╲
                ╲   Unit (70%)
                 ╲  — fast, pure functions
```

### 8.2 Coverage requirements

| Layer | Min coverage | Comment |
|-------|--------------|---------|
| `core/` | 90% | Pure logic, easy to test |
| `agents/_impl/` | 85% | Includes mock tests |
| `orchestration/` | 80% | Integration-heavy |
| `web/` | 75% | API endpoints |
| `db/` | 70% | SQL queries |
| `knowledge/` | 80% | RAG retrieval |

**CI gates:** PR fails if coverage drops > 1% или ниже минимума.

### 8.3 Test naming

```python
# ✅ Good — describes behavior
def test_pydantic_validation_rejects_missing_symbol():
    ...

def test_rag_retriever_returns_top_5_within_80ms_on_100k_docs():
    ...

# ❌ Bad — describes implementation
def test_pydantic_v2_works():
    ...
```

### 8.4 Test data

- **No real secrets** in tests (use `conftest.py` fixtures with mocks)
- **No real network calls** (mock httpx, asyncpg, etc.)
- **Hypothesis-based** для DB roundtrip, API fuzzing
- **Deterministic timestamps** (freeze `datetime.now()`)

### 8.5 Running tests

```bash
# All tests
make test

# Specific file
pytest tests/test_rag_retriever.py -v

# With coverage
make test-coverage

# Property-based
pytest tests/test_db_roundtrip.py --hypothesis-show-statistics

# Markers
pytest -m "not slow"          # skip slow tests
pytest -m "integration"       # only integration
pytest -m "chaos"             # only chaos tests
```

---

## 9. 📖 Documentation

### 9.1 When to update docs

| Change type | Update required |
|-------------|-----------------|
| New agent | `docs/AGENTS.md` (weights table) + ADR |
| New API endpoint | `docs/API.md` (если есть) + OpenAPI spec |
| New env var | `.env.prod.example` + `docs/ENVIRONMENT.md` |
| Breaking change | `CHANGELOG.md` + major version bump |
| New deploy step | `RUNBOOK.md` + on-call briefing |
| New ADR | `docs/adr/XXXX-title.md` (increment number) |

### 9.2 ADR template

```markdown
# ADR-XXXX: <Title>

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-YYYY]

## Context
[What is the issue that we're seeing that's motivating this decision?]

## Decision
[What is the change that we're proposing or have agreed to implement?]

## Consequences
[What becomes easier or more difficult because of this change?]

## Alternatives Considered
[What other options were evaluated? Why were they rejected?]

## References
[Links to relevant docs, discussions, benchmarks]
```

См. `docs/adr/0001-hybrid-agents.md` для примера.

---

## 10. 🚀 Release Process

### 10.1 Versioning

[Semantic Versioning](https://semver.org/):
- **MAJOR** (1.0.0) — breaking API changes, schema migrations requiring manual intervention
- **MINOR** (0.1.0) — new features, backward-compatible
- **PATCH** (0.0.1) — bug fixes, no API change

**Pre-1.0:** anything goes, but document breaking changes loudly.

### 10.2 Release cadence

| Type | Cadence | Examples |
|------|---------|----------|
| **Major** | Quarterly / quarter-end | v1.0.0 (GA), v2.0.0 (breaking) |
| **Minor** | Monthly | v1.1.0 (new agent), v1.2.0 (new data source) |
| **Patch** | On-demand | v1.0.1 (critical bug), v1.0.2 (security fix) |

### 10.3 Release procedure

1. **Code freeze** — `release/X.Y.Z` branch cut from `develop`
2. **RC period** — 1 week (для major) / 1 day (для minor) / on-demand (для patch)
3. **Testing** — full test suite + manual smoke + canary deploy
4. **Sign-off** — Tech Lead approval в `RELEASE_CHECKLIST.md`
5. **Tag & publish** — `git tag -s vX.Y.Z`, `gh release create`
6. **Announce** — stakeholder update, GitHub Discussions, optional blog post
7. **Post-release** — monitor metrics 24h, retro на следующий день

См. `RELEASE_CHECKLIST.md` для полного go/no-go gate.

---

## 11. ❓ Getting Help

### 11.1 Stuck on something?

1. **Read the docs** — `docs/`, `README.md`, `RUNBOOK.md`
2. **Search issues** — `gh issue list --search "your query"`
3. **Ask in Discussions** — https://github.com/mahaasur13-sys/astrofin-sentinel-platform/discussions
4. **Open an issue** — if no existing answer

### 11.2 Reporting bugs

Use [bug report template](.github/ISSUE_TEMPLATE/bug_report.md) (если есть) или:

```markdown
**Environment:**
- OS: [Pop!_OS 22.04 / macOS 14 / WSL2]
- Python: [3.11.9]
- Branch/commit: [release/1.0.0 @ abc123]
- Install method: [pip / uv / docker]

**Steps to reproduce:**
1. ...
2. ...
3. ...

**Expected:** ...
**Actual:** ...

**Logs:**
```
[paste relevant logs, redact secrets]
```

**Screenshots:** (if UI)
```

### 11.3 Security issues

**DO NOT open public issue.** See `SECURITY.md` для disclosure policy.

Кратко: email `security@astrofin.dev` (или TBD — создаётся в W3 по P4-07), GPG key в `SECURITY.md`.

---

## 12. 🙏 Recognition

Contributors recognized in:

- `README.md` — Contributors section
- `CHANGELOG.md` — per release
- `docs/CONTRIBUTORS.md` — long-term contributors (создаётся в W4)
- GitHub — automatic via contribution graph

---

## 13. 🔗 Related Documents

- `file 'docs/TEAM_ROLES.md'` — кто есть кто, эскалация
- `file 'docs/DEFINITION_OF_DONE.md'` — что считать готовым
- `file 'docs/RISK_REGISTER.md'` — что может пойти не так
- `file 'RELEASE_CHECKLIST.md'` — go/no-go gate
- `file 'docs/ARCHITECTURE.md'` — R1–R9 (создаётся в W3)

---

*Last updated: 2026-07-04*

**Thank you for contributing! 🚀**
