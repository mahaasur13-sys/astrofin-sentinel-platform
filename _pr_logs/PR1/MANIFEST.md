# PR1 — CompromiseAgent (preflight snapshot)

**Дата:** 2026-06-17  
**Снимок:** до коммита (репо не инициализировано)  
**Источник:** `unified-platform/` (см. `unified-platform/_pr_logs/PR1/`, реальный артефакт разработки)

## Изменённые / новые файлы

| Файл | Статус | Назначение |
|---|---|---|
| `agents/_impl/compromise_agent.py` | NEW | 21-й агент. Expected-utility между top-1 и top-2 сигналом: `gain = stop_distance × 2R`, `loss = stop_distance`. Канонический Pattern A (`@track_agent_metrics` + `try/except EphemerisUnavailableError → _degraded(EPHEMERIS_UNAVAILABLE)` + `except Exception → _degraded(UNKNOWN)`). |
| `tests/test_compromise_agent.py` | NEW | 7 кейсов: empty / consensus / multi-cat conflict / single direction / exception / single signal / runner. |
| `agents/_impl/synthesis_agent.py` | EDIT | В `analyze()`: после `_detect_conflicts()` зовётся `CompromiseAgent`; при `compromise_active and confidence ≥ 60` подменяются direction/confidence, иначе fallback. Результат в `metadata["compromise"]`. |

## Контракт сигналов

`CompromiseAgent.run()` возвращает dict:
- `compromise_active: bool`
- `dominant: str` (имя top-агента)
- `dominant_signal: dict` (`{agent, direction, confidence, confidence_pct}`)
- `compromise_signal: dict | None` (`{direction, confidence, reasoning, gain_pct, loss_pct, expected_utility}`)

## Тесты

`python3 tests/test_compromise_agent.py` → **7/7 PASS**, ruff clean.

## Грабли / нюансы

- `meta_rl` имеет сломанный `basket` import chain → test-файл **изолирует** сломанный пакет, чтобы smoke-тест агента запускался.
- `VolatilityEngine.atr_pct` используется для stop distance (R); fallback на `0.02` если ATR=0.

## Snapshot

Файлы скопированы в `_pr_logs/PR1/` с SHA256 (см. `SHA256`). Снимок — **pre-commit**, после инициализации git-репо коммит одним atomic commit: `feat(agents): PR1 CompromiseAgent + synthesis hook`.
