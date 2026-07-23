# AstroFin Sentinel V5 — SOUL

> «Внутренний совет директоров» — мультиагентная торговая платформа, где каждый агент имеет голос, вес и право вето.

---

## Философия

- **Гибридный сигнал — священен.** Astro (космо/циклы) + Quant (метрики/риск) + Fundamental (SEC/макро) + Sentiment (Fear&Greed/social). Ни один агент не говорит за всех.
- **RAG-First.** Любой ответ, в котором есть факты, должен сначала идти через RAG/knowledge layer. Догадки = деградация.
- **Conflict over Consensus.** Лучше открытый конфликт между агентами с явным арбитражем KARL, чем тихое усреднение.
- **Production-Ready с первого коммита.** Каждый PR должен проходить: unit + integration + linter + secrets scan + registry coverage.
- **ACOS Governance.** Любое долгосрочное решение фиксируется в ADR (`docs/architecture/decisions/`). Никаких «устных» архитектурных сдвигов.

## Принципы (R-01 … R-12)

| ID | Принцип |
|----|---------|
| R-01 | Все внешние HTTP — только через `data_room/` (no bare `requests` в агентах) |
| R-02 | Сетевой I/O допустим только в `data_room/`, `tools/`, `core/`, `amre/`, утилитах |
| R-03 | Архитектурный линтер — hard-fail в CI (см. `scripts/architecture_linter.py`) |
| R-04 | Каждый агент реализует `AgentResponse` (unified interface) |
| R-05 | `risk_pct` динамический, зависит от regime (`meta_rl/quant/risk.py`) |
| R-06 | Session history перситентна (SQLite, не в памяти) |
| R-07 | KARL синтез — единственная точка арбитража конфликтов |
| R-08 | Решения audit-trailed (JSONL) для последующего обучения |
| R-09 | Pre-commit hooks обязательны: `validate_agent`, `arch_linter` |
| R-10 | Secrets — только в `.env` / GitHub Secrets, никогда в коде |
| R-11 | Coverage нового агента = 100% unit + 1 integration |
| R-12 | Subtree/submodule — запрещены; всё inlined в master |

## Текущее состояние (2026-07-22 — GA-ready ✅ v1.0.0-ga)

- **Branch:** `main` @ `911b408` (Sprint 8.1 Paper Trading integration)
- **P0 Security:** 0 HIGH bandit (SQLi, RCE eval, weak hashes → sha256)
- **P1 Code Quality:** 97% print→structlog, 12 critical except:pass→log.warning
- **P2 Consolidation:** God-files split (2→6), dead code (539 files), requirements (7→3)
- **P3 Hygiene:** duplicate repos archived, stale branches deleted
- **Sprint 8.1:** Paper Trading — PaperBroker + factory + orchestrator wire-up
- **Tests:** 664 passed

## Правила для AI-агентов (обязательные)

1. **Прежде чем редактировать** — прочитай AGENTS.md, раздел «CI Checks» и `docs/architecture/`.
2. **Не трогай** `data_room/resolvers/` без согласования с @felix — это сетевой шлюз.
3. **Любой новый агент** — только в `agents/_impl/`, наследует `BaseAgent`, валидация `python scripts/validate_agent.py`.
4. **Любой новый web-роут** — обязательно `@require_auth` из `web/middleware/`.
5. **Любой коммит** — линтер локально: `python scripts/architecture_linter.py`.
6. **Сомневаешься** — спроси, не угадывай. Это production-beta, не прототип.
7. **Документация** — обновляется в том же PR, что и код.

## Антипаттерны (никогда)

- ❌ `import requests` в агенте
- ❌ `print()` в production-коде (используй `structlog`)
- ❌ `try/except: pass`
- ❌ Хардкод API-ключей
- ❌ Дублирование агента в корне (всё в `agents/_impl/`)
- ❌ `audit_repo/` (удалён)
- ❌ Submodule / subtree — inlined only

## Мантра

> «Каждый сигнал — решение совета, а не мнение одного агента.
> Каждое решение — задокументировано, аудитабельно, воспроизводимо.
> Каждый коммит — production-ready, иначе он не в master.»
