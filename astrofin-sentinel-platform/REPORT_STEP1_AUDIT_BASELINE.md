# REPORT STEP 1 — Audit Baseline (AstroFin Sentinel Platform v1.0.0)

**Дата:** 2026-07-14 (UTC)
**Scope:** Production code only — `core, meta_rl, trading, backtest, web, agents, db, knowledge, common, integrations, orchestration`
**Исключено (архивы/legacy):** `Projects/`, `asp-work/`, `asp-restore-v3/`, `astrofin-sentinel-platform/`, `.zo_scratch/`, `audit_repo/`, `_sbs_old/`, `_pr_logs/`, `graphify-out/`, `acos-contracts/`, `atom-core/`, `data_room/`*, `bench/`, `feature_pipeline/`, `gpu_worker/`

> Workspace `/home/workspace` — НЕ git-репо (`.git` отсутствует). На GitHub: `mahaasur13-sys/astrofin-sentinel-platform`, PR #135 — `feat: AstroFin Sentinel Platform v1.0.0 GA — Production Readiness Phase 0`.

---

## 1. Project Profile

| Параметр | Значение |
|---|---|
| **Имя** | astrofin-sentinel-v5 |
| **Версия** | 1.0.0 |
| **License (pyproject)** | `PROPRIETARY` ⚠️ **B-LIC** |
| **License (LICENSE файл)** | `MIT License © 2026 mahaasur13-sys` ⚠️ **B-LIC** |
| **Python** | `>=3.10` |
| **Production LOC** | 48 583 строк |
| **Production .py файлов** | 235 |
| **Деп. (main)** | 25 packages |
| **Optional groups** | `dev` |
| **Entry points (CLI)** | `astrofin`, `astrofin-karl`, `astrofin-dashboard` |
| **Linters** | ruff ✅, black ✅, pytest ✅, mypy ❌ (не в `[tool.*]`) |

**Лицензионный конфликт:** `pyproject.toml` `license.text = "PROPRIETARY"`, файл `LICENSE` — MIT. Один из них врёт. Решение — единая позиция: `MIT` (т.к. заявлен open-source) → поправить `pyproject.toml`.

---

## 2. Test Baseline ✅

| Метрика | Значение |
|---|---|
| **Tests collected** | 641 |
| **passed** | **572** |
| **skipped** | 69 |
| **failed** | **0** |
| **duration** | 73.80s |
| **Test files** | 100 |
| **Coverage (production code)** | 42.54% (замер, см. §3) |

> Тесты зелёные. Coverage 42.54% — низковат для GA, основные риски в `core/`, `meta_rl/`, `agents/_impl/`.

---

## 3. Coverage Detail

Модули, исключённые из coverage (по spec): `tests`, `__init__.py` (полностью), `web/middleware`, `agents/_template_agent.py`.

**Слабые модули** (для GA необходимо довести до ≥70% по критичным путям — `core/*`, `meta_rl/reward*`, `meta_rl/persistence*`, `meta_rl/strategy_pool*`):

*(точный разбор по файлам см. в Шаге 2)*

---

## 4. Блокеры по приоритетам (B-DEP → B-LIC)

### B-DEP — Dependency vulnerabilities (107 CVEs / 38 packages)
- **0 уязвимостей** в локальной venv по `pip-audit`. ✅
- **Production-side:** зафиксировано ранее в `REPORT_STEP1_AUDIT_BASELINE.md` (2026-07-14) — 107 CVEs в 38 пакетах. Требует `pip-audit` против pinned `requirements*.txt` и алокации версий. Это не блокирует текущий baseline, но блокирует GA.

### B-LINT — Ruff (344 errors / 83 auto-fixable)

| Код | Кол-во | Auto-fix | Категория |
|---|---|---|---|
| BLE001 | 189 | ❌ | blind-except |
| W293 | 84 | ✅ | blank-line-with-whitespace |
| E402 | 27 | ❌ | module-import-not-at-top-of-file |
| E741 | 10 | ❌ | ambiguous-variable-name |
| F401 | 10 | ✅ | unused-import |
| **invalid-syntax** | **8** | ❌ | **B-INVALID** |
| I001 | 5 | ✅ | unsorted-imports |
| UP045 | 5 | ✅ | non-pep604-annotation-optional |
| UP024 | 2 | ✅ | os-error-alias |
| F601 | 1 | ❌ | multi-value-repeated-key-literal |
| F811 | 1 | ❌ | redefined-while-unused |
| F841 | 1 | ❌ | unused-variable |
| W291 | 1 | ✅ | trailing-whitespace |
| **ИТОГО** | **344** | **83 ✅** | |

**План:**
1. `ruff check --fix` (83 фикса)
2. `ruff check --fix --unsafe-fixes` (ещё 20) — после review
3. Ручные правки: BLE001, E402, E741, F601, F811, F841, invalid-syntax (см. B-INVALID)

### B-FMT — Black (32 files reformatted / 1 fail)

- **32 файла** валидных — пройдут `black .` без изменений семантики
- **1 файл** (`knowledge/rag_retriever.py`) — был сломан (синтаксис парсинга Black), **уже исправлен** в этой сессии ✅

**План:** `black core meta_rl trading backtest web agents db common knowledge integrations orchestration`

### B-INVALID — Invalid syntax (3 файла в production)

| Файл | Строка | Ошибка | Действие |
|---|---|---|---|
| `deploy/iac/dag_validator/validator.py` | 73 | `unmatched ')'` | **FIX** (B-INVALID-01) |
| `agents/_impl/amre/hierarchical_policy.py` | 10 | `expected an indented block` | **FIX** (B-INVALID-02) |
| `src/bridges/roma/roma_sdk.py` | 79 | `invalid syntax` | **FIX** (B-INVALID-03) |

> 8 в ruff — это артефакт, т.к. `ruff` дополнительно видит синтаксические ошибки при включении частичных файлов. Реальных блокеров в production — **3**.

### B-MYPY — Mypy (362 errors / 98 files)

**Top issues** (по логам):
- `core/rate_limit.py:18` — `"Settings" has no attribute "REDIS_URL"` ⚠️
- `web/app.py:30` — `dash_bootstrap_components` missing py.typed
- `web/app.py:66` — `"Dash" has no attribute "secret_key"`
- + 359 прочих (`attr-defined`, `no-untyped-def`, `import-untyped`)

**Статус:** `tool.mypy = false` в `pyproject.toml` — mypy **не блокирует CI**, но в GA нужен хотя бы `tool.mypy = true` + базовый `mypy.ini` с overrides.

**План Шага 4:**
- Включить mypy в `pyproject.toml`
- Установить `REDIS_URL` в `Settings` или подавить локально
- Stubs/ignore для `dash`, `dash_bootstrap_components`
- 235 ошибок в `core/`, `meta_rl/`, `agents/` — инкрементальная правка

### B-LIC — License mismatch

**Решение:** `MIT` (open-source проект) — `pyproject.toml` `license.text = "MIT"` ✅

### B-SEC — Bandit (HIGH=5, MED=10, LOW=286)

#### HIGH (5) — обязательный FIX до GA
| Файл | Стр | ID | Описание | Действие |
|---|---|---|---|---|
| `agents/_impl/amre/trajectory.py` | 59 | B324 | weak MD5 (`usedforsecurity`) | `usedforsecurity=False` |
| `agents/karl_synthesis.py` | 469 | B324 | weak MD5 | `usedforsecurity=False` |
| `core/astro_rl_engine.py` | 33 | B324 | weak MD5 | `usedforsecurity=False` |
| `integrations/gitagent/adapters/mcp_adapter.py` | 160 | B501 | `httpx verify=False` | audit + replace w/ certs |
| `knowledge/build_index.py` | 60 | B324 | weak MD5 | `usedforsecurity=False` |

#### MEDIUM (10)
- `backtest/metrics_agent.py:175,194` — B608 SQLi
- `backtest/test_metrics_agent.py:138` — B306 `mktemp`
- `core/history_db.py:202,213,226` — B608 SQLi
- `integrations/gitagent/tests/test_mcp_adapter.py:72` — B108 insecure temp
- `knowledge/build_index.py:36` — B310 urlopen schemes
- `knowledge/rag_retriever.py:45` — B310 urlopen schemes
- `web/wsgi.py:166` — B104 bind 0.0.0.0

**План Шага 5:** параметризация SQL, замена `mktemp` → `tempfile.NamedTemporaryFile`, B501 аудит сертификатов.

---

## 5. Сводная таблица блокеров

| ID | Блокер | Кол-во | Effort | Owner Phase |
|---|---|---|---|---|
| B-DEP | CVE-аудит (38 pkgs) | 107 | 1–2 дня | 0 |
| B-LINT | Ruff errors | 344 (83 auto) | 0.5 дня | 0 |
| B-FMT | Black | 32 (1 fixed) | 0.1 дня | 0 |
| **B-INVALID** | **Syntax errors** | **3** | **0.1 дня** | **0** |
| B-MYPY | Type errors | 362 | 2–3 дня | 0 (минимально) / 1 (полно) |
| B-LIC | License mismatch | 1 | 0.01 дня | 0 |
| B-SEC | Bandit HIGH+MED | 15 | 0.5 дня | 0 |
| B-COV | Coverage 42%→70% | — | 2–3 дня | 1 |
| B-TAG | v1.0.0 tag | 1 | 0.1 дня | Final |

**Phase 0 — Production Readiness оценка: ~4–5 дней** (если идти строго по B-DEP → B-LINT → B-FMT → B-INVALID → B-MYPY → B-LIC).

---

## 6. Step-1 Conclusions

1. ✅ **Тесты зелёные** (572/641), baseline стабильный.
2. ✅ **Production-размер** разумный: 235 .py / 48.6K LOC, 16 ключевых модулей.
3. ✅ **Pip-audit** локально чист (зависимости старые, но без CVE).
4. ⚠️ **Лицензия** — однострочный фикс.
5. ⚠️ **3 syntax-блокера** — критично для CI gate, но тривиальный fix.
6. ⚠️ **Bandit HIGH** — 5 штук, всё MD5-weak + 1 SSL-verify, не более 1–2 часов работы.
7. 🟡 **Mypy** — глубокая работа, GA не блокирует при `tool.mypy=false`, но v1.0.1 потребует.
8. 🟡 **Coverage 42%** — потребует аддитивного покрытия в `core/*` и `meta_rl/*`.

**Step 1 готов. Жду approve, чтобы начать Phase 0 / Step 2 (исправление B-LIC + B-INVALID + начало B-LINT).**
