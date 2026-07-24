# Code Review Architecture — AstroFin Sentinel V5

> **Версия:** 5.0.0  
> **Дата:** 2026-06-02  
> **Владелец:** Principal Software Architect  
> **Цикл пересмотра:** Quarterly (см. ADR-001 в `docs/ARCHITECTURE.md`)

---

## 1. Цель

Один фразой: **"Enforce architecture compliance (R1–R9), catch security issues, and ensure Data Room pattern adherence before merge."**

Три измеримые метрики:

1. **Architecture violation count per PR** (target: **0** для P1 правил R1, R3, R5, R8, R9)  
2. **Security issues caught pre-merge** — secrets, unauth routes, f-string SQL (цель: 100% перехват до merge)  
3. **Degradation coverage** — доля агентов с `try/except` в `run()`, возвращающих graceful `NEUTRAL` (target: ≥90%)

---

## 2. Конфигурация ревью

### 2.1. Trigger

**`pull_request`** (не push, не manual `/review`).  
Причина: CodeRabbit — это ревью для **автора PR**, а не для CI-гейта. Автор получает feedback и фиксит до merge.

### 2.2. Audience

- **Primary:** PR author (assertive style, обращается напрямую к автору)  
- **Secondary:** team reviewers, архитектор

### 2.3. Язык и стиль

- **Language:** `ru` (русский)  
- **Style:** assertive  
- **Output:** code snippets с примерами "как должно быть"  
- **Blocking:** P1 (R1, R3, R5, R8, R9) → `request_changes`; soft (S1–S3) → комментарии

---

## 3. Overlap Matrix — кто что делает

| Категория проверки | Pre-commit (локально) | CodeRabbit (PR) |
|--------------------|----------------------|----------------|
| **Ruff formatting** | ✅ | ❌ |
| **Ruff lint** | ✅ | ❌ |
| **Bandit (security AST)** | ✅ | ❌ (CodeRabbit только рассуждает) |
| **detect-secrets baseline** | ✅ | ❌ |
| **architecture_linter.py (R1–R9 AST)** | ✅ (validate на staged files) | ✅ (объясняет WHY и даёт fix) |
| **validate_registry.py (R5 coverage)** | ✅ | ❌ |
| **end-of-file fixer, trailing whitespace** | ✅ | ❌ |
| **Architectural reasoning** (почему R3 → data_room) | ❌ | ✅ |
| **KNOWN_ISSUES context** (KI-001/007/011/012) | ❌ | ✅ |
| **Cross-file impact analysis** (новая функция ломает synthesis?) | ❌ | ✅ |
| **Test coverage gaps** (BlackRock Six) | ❌ | ✅ |
| **Soft rules S1–S3** (docstrings, ARCHITECTURE.md) | ❌ | ✅ |
| **Pydantic/dataclass advice** | ❌ | ✅ |
| **Performance / look-ahead bias** | ❌ | ✅ (specific to backtest) |

**Принцип:** pre-commit = fast syntactic gates. CodeRabbit = slow semantic reviewer.

---

## 4. Архитектурные правила (R1–R9)

Полная спецификация — в `scripts/architecture_linter.py`. Краткая сводка:

| Rule | Severity | Что проверяет |
|------|----------|---------------|
| **R1** | FAIL | Все агенты наследуют `BaseAgent[AgentResponse]` |
| **R2** | FAIL | `@require_ephemeris` на астрологических методах |
| **R3** | FAIL | НЕТ `requests.*` в `agents/` (Data Room pattern) |
| **R4** | FAIL | `@require_auth` на non-public web routes |
| **R5** | FAIL | Агент зарегистрирован в `AGENT_AGENTS` |
| **R6** | WARN | НЕТ top-level `print` |
| **R7** | FAIL | НЕТ f-string SQL |
| **R8** | FAIL | НЕТ hardcoded secrets |
| **R9** | FAIL | Экспортируется `run_<agent_name>(state)` async |

**P1 (блокирующие merge):** R1, R3, R5, R8, R9  
**P2 (warn, не блокируют):** R2, R4, R6, R7 — информативные или про UX

### 4.1. Soft rules (S1–S3)

- **S1** — docstring на классах и методах
- **S2** — type hints completeness
- **S3** — обновить `docs/ARCHITECTURE.md` при structural changes

---

## 5. P1 blockers (KNOWN_ISSUES.md)

CodeRabbit упоминает эти блокеры в комментариях, если релевантно:

- **KI-001** — Data Room — draft, не runtime contract. Любой `requests.*` в `agents/` — нарушение.
- **KI-007** — `.bak` файлы в `core/`, `web/`, `meta_rl/`, `agents/`. Удалить или в `.archive/`.
- **KI-011** — backwards-compat stubs в `agents/__init__.py`. R5 coverage.
- **KI-012** — secrets в `.env`, hardcoded API keys. Требуй `Settings()`.

---

## 6. Exclusions

Расширено по сравнению с pre-commit:

```yaml
exclude:
  - "**/__pycache__/**"
  - "**/.pytest_cache/**"
  - "**/.mypy_cache/**"
  - "**/data/raw/**"
  - "**/data/processed/**"
  - "**/*.log"
  - "**/.env*"
  - "**/venv/**"
  - "**/node_modules/**"
  - "**/agents/_archived/**"   # deprecated
  - "**/*.bak"                  # KI-007/KI-008
  - "**/dist/**"
  - "**/build/**"
  - "**/.eggs/**"
  - "**/roma-execution-bridge/**"  # nested git repo
```

---

## 7. Review Cycle

**Quarterly** — каждые 3 месяца `@architect` + `@lead` пересматривают:

1. `path_instructions` — релевантны ли новым модулям?
2. `focus_areas` — изменились ли приоритеты?
3. `knowledge_base.instructions` — обновилась ли terminology?
4. `KNOWN_ISSUES.md` P1 — закрыты ли старые, появились ли новые?

Review checklist для каждого цикла — в `docs/CODE_REVIEW_REVIEW.md` (создаётся при первом ревью).

---

## 8. Auto-fix policy

CodeRabbit предлагает исправления там, где они **безопасны**:

- ✅ `@require_auth` на новом route — тривиальная вставка декоратора
- ✅ Импорт `data_room.blueprint` вместо `requests` в агенте
- ✅ `logger.info()` вместо `print()`  
- ❌ **НЕ** меняет логику сигналов, веса, risk_pct
- ❌ **НЕ** правит SQL на parameterized query автоматически (может изменить семантику)
- ❌ **НЕ** удаляет файлы (`.bak`, `_archived`) — только комментирует

---

## 9. Связанные документы

- `docs/ARCHITECTURE.md` — общая архитектура
- `docs/KNOWN_ISSUES.md` — P1 blockers
- `docs/CONTRIBUTING.md` — гайд для контрибьюторов
- `scripts/architecture_linter.py` — AST валидация R1–R9
- `scripts/validate_agent.py` — per-agent валидация (9 checks)
- `scripts/validate_registry.py` — R5 coverage
- `.pre-commit-config.yaml` — pre-commit hooks
- `.coderabbit.yaml` — текущая конфигурация

---

## 10. История изменений

| Дата | Изменение |
|------|-----------|
| 2026-06-02 | Initial version. Quarterly review cycle established. |


<!-- coderabbit-config-verify: 2026-06-23 -->
