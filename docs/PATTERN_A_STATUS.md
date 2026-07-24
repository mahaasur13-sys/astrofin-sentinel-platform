# Pattern A Migration Status

**Дата:** 2026-06-18
**Ветка:** feature/pattern-a-migration
**Коммит:** 6cb9e82

## Summary
- Реальных агентов: 21
- Полностью compliant: **20/21**
- Специальный (B-hybrid): **1/21** — `astro_council/agent.py`

### Особенность astro_council
- Использует dict-контракт `{"astro_council_signal": {...}}`
- Не зависит от эфемерид → без `EphemerisUnavailableError` и `@require_ephemeris`
- Сохраняет `@track_agent_metrics` + внешний `try/except` + graceful degradation
- Backtest + pytest (16/16) passed

Остальные 20 агентов используют стандартный `run()` / `analyze()` + `_degraded()`.

