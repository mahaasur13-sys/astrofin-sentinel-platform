# MAS Design — закрытие оставшихся 20% Multi-Agent System

> **Source of truth:** `docs/STATUS.md` (все 20 агентов ✅), `docs/ARCHITECTURE.md` (Layer 2).
> **Скоуп:** только то, что осталось довести до production-grade после Phase 1 (architecture overhaul).
> **Не в скоупе:** event bus, PostgreSQL+pgvector, dashboard rewrite (Q3/Q4 2026, см. STATUS.md §8).

---

## 1. Текущее состояние MAS (по факту репозитория)

| Слой | Что есть | Чего не хватает |
|------|----------|-----------------|
| **Агенты (20 шт.)** | Все 20 в `agents/_impl/*` (см. `docs/STATUS.md` §1) | CompromiseAgent (trade-off риск↔доходность) — отсутствует как класс; сейчас `SynthesisAgent` жёстко решает конфликт через `ASTRO_REDUCTION`/`FUNDAMENTAL_BOOST` |
| **Метрики** | `@track_agent_metrics` (Pattern A) + ручной Pattern B — `agents/metrics.py` | **12–14 агентов не подключены к Pattern A**: у них `analyze()` без декоратора `run()`, нет `try/except` с `_degraded()`. Validator помечает их как "partial coverage" |
| **Обработка ошибок** | У `SynthesisAgent` есть `try/except EphemerisUnavailableError → _degraded(EPHEMERIS_UNAVAILABLE)` и общий `except → _degraded(UNKNOWN)` (`agents/_impl/synthesis_agent.py:121–132`) | Этот же паттерн не единообразен: ~14 агентов возвращают «голый» `NEUTRAL` без reason-кода, без структурированного лога, без инкремента метрики с `signal="DEGRADED"` |
| **Мета-контроллер** | `MetaAgent` (`meta_rl/meta_agent.py:103`) — Thompson sampling, evolution, drift detection через `analyze_oap_drift` | Нет regime-детектора на лету, нет явного kill-switch, нет per-agent attribution PnL, нет online A/B между пулами стратегий |
| **Обратная связь (online learning)** | `KARLState`, `RewardCalculator`, `ScoredStrategy` — скоринг стратегий | Per-agent **accuracy tracker** и **calibration** (Brier score) отсутствуют; в `core/history_db.py` есть записи, но нет слоя, который сводит «агент X сказал LONG @ conf 80 → реальный исход ±X%» |
| **Координатор** | `SynthesisAgent` (фактически координатор с весом 100%) | Контрактные проверки готовы (Phase 1), но нет формального **observability hooks** для каждого шага синтеза: `record_meta_step()` уже есть в `agents/_impl/amre/audit.py`, но `SynthesisAgent` его не вызывает |

---

## 2. Целевое состояние (что считаем "готово на 100%")

Три критерия готовности (каждый проверяемый):

1. **CI-валидатор (`scripts/validate_agent.py`)** проходит по всем 20 агентам: каждый имеет `@track_agent_metrics` на `run()` (или Pattern B с явными `agent_counter`/`agent_latency`), структурированный `try/except` → `_degraded(reason)`, и обязательные импорты из `core/base_agent` + `agents/_impl/ephemeris_decorator` + `agents/metrics`.
2. **`pytest -q`** зелёный; добавлены тесты: `tests/agents/test_compromise_agent.py`, `tests/meta_rl/test_regime_detector.py`, `tests/agents/test_calibration_tracker.py`.
3. **Grafana-дашборд** `docs/monitoring/mas_health.json` показывает per-agent метрики (latency p50/p95, success/degraded ratio, calibration) — JSON генерируется автоматически из `meta_rl/metrics.py`.

---

## 3. Дизайн четырёх компонентов

### 3.1. CompromiseAgent (`agents/_impl/compromise_agent.py`) — НОВЫЙ

**Зачем:** сейчас `SynthesisAgent._detect_conflicts()` (`agents/_impl/synthesis_agent.py:368`) жёстко редуцирует астро-вес при конфликте с fundamental/quant. Это one-size-fits-all. Нужен явный агент-компромисс, который:

- Берёт **топ-2 конфликтующих сигнала** (например, `AstroCouncil=LONG@85` vs `FundamentalAgent=SHORT@70`).
- Считает **expected utility** каждого: `E[U] = p·gain − (1−p)·loss`, где `p = confidence/100`, `gain/loss` берутся из `VolatilityEngine.analyze()` (`core/volatility.py`).
- Возвращает `NEUTRAL@mid_confidence` с **reasoning**, в котором явно перечислены оба исхода и условия, при которых решение изменится (см. §3.2 — drift triggers).

**Контракт:**
```python
class CompromiseAgent(BaseAgent[AgentResponse]):
    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:
            logger.exception("[COMPROMISE] unexpected failure")
            return self._degraded(UNKNOWN, repr(e))

    async def analyze(self, state: dict) -> AgentResponse: ...
```

**Интеграция:** `SynthesisAgent._vote()` получает новый источник `compromise_signal`. Если он есть и `confidence >= 60`, финальное решение — `compromise_signal.signal`, иначе fallback на текущую логику.

**Метрики:** стандартные `sentinel_compromise_agent_runs_total{signal}` + `sentinel_compromise_agent_latency_seconds`.

---

### 3.2. Унификация Pattern A (12–14 агентов)

**Проблема:** по `scripts/validate_agent.py` (Phase 2 plan) агенты без `@track_agent_metrics` на `run()` и без `_degraded()` помечаются как «partial coverage». Кандидаты (см. STATUS.md §1):

- `BradleyAgent`, `GannAgent`, `CycleAgent`, `ElectoralAgent`, `TimeWindowAgent` (5 astro)
- `FundamentalAgent`, `MacroAgent`, `QuantAgent`, `OptionsFlowAgent`, `SentimentAgent` (5 misc)
- `MLPredictorAgent`, `MarketAnalyst`, `InsiderAgent`, `ElliotAgent` (4 quant/tech)

**Паттерн (канонический, из `agents/_impl/synthesis_agent.py:121-132`):**

```python
from __future__ import annotations  # всегда первая строка

import logging
from agents._impl.ephemeris_decorator import EphemerisUnavailableError
from agents.metrics import track_agent_metrics
from core.base_agent import (
    EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent, SignalDirection,
)

logger = logging.getLogger(__name__)

class XxxAgent(BaseAgent[AgentResponse]):
    @track_agent_metrics
    async def run(self, state: dict) -> AgentResponse:
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded(EPHEMERIS_UNAVAILABLE, str(e))
        except Exception as e:
            logger.exception("[XXX_AGENT] unexpected failure")
            return self._degraded(UNKNOWN, repr(e))

    async def analyze(self, state: dict) -> AgentResponse:
        # ... ЛОГИКА АГЕНТА НЕ ТРОГАЕМ ...
```

**Что НЕ меняем:** тело `analyze()` — только обёртку `run()`. Это критично, чтобы не сломать существующую семантику сигналов.

**Известный фрикшен из профиля пользователя:** `meta_rl/basket.py` — `from __future__ import annotations` стоит НЕ первой строкой (после docstring/комментариев), что валит ruff `E402`. Фикс: переместить в позицию 1, до любого импорта. Аналогично проверить `meta_rl/baseline_*.py` и `agents/_impl/quant_agent.py` (есть `dead code` — несвязанные переменные из старого PR).

---

### 3.3. Per-agent Calibration & Attribution (`agents/_impl/calibration.py`) — НОВЫЙ

**Зачем:** закрываем gap "60% обратная связь" (см. §1). Сейчас `MetaAgent` оценивает стратегии, но **не связывает сигнал конкретного агента с PnL**. Без этого `Thompson sampling` в `MetaAgent.select()` сэмплирует «вслепую».

**Дизайн:**

```python
@dataclass
class AgentOutcome:
    agent_name: str
    symbol: str
    signal: SignalDirection
    confidence: int        # 0-100, то что вернул агент
    actual_return: float   # % за горизонт H (default H=24h)
    brier_component: float # (p - outcome)^2, outcome ∈ {0,1}

class CalibrationTracker:
    """Sliding-window Brier score + per-agent accuracy."""

    def record(self, outcome: AgentOutcome) -> None: ...
    def brier(self, agent_name: str, window: int = 200) -> float: ...
    def attribution(self, agent_name: str, window: int = 200) -> float:
        """Σ confidence·sign(return) for this agent's correct calls."""
        ...
```

**Хранение:** SQLite через `core/history_db.py` (уже есть, добавляем таблицу `agent_outcomes`). **Не** нужен PostgreSQL — этого хватит до Q4 2026 cutover (см. STATUS.md §2).

**Интеграция с MetaAgent:** в `MetaAgent.select()` при выборе elites — вес стратегии умножается на `1 - brier(agent_name)` для тех агентов, которые дёргаются в этой стратегии. Это даёт online self-correction.

**Метрики:** `sentinel_agent_calibration_brier{agent}` (Gauge), `sentinel_agent_attribution_pnl{agent}` (Counter).

---

### 3.4. Regime Detector + Kill-Switch (`meta_rl/regime_detector.py`) — НОВЫЙ

**Зачем:** закрываем gap "40% мета-контроллер". Сейчас `MetaAgent` реагирует на drift **постфактум** (через `analyze_oap_drift`), но не детектирует смену режима на лету и не имеет явного kill-switch уровня MAS.

**Дизайн:**

```python
class Regime(str, Enum):
    TREND = "TREND"
    RANGE = "RANGE"
    HIGH_VOL = "HIGH_VOL"
    CRISIS = "CRISIS"   # → kill-switch

@dataclass
class RegimeSignal:
    regime: Regime
    confidence: float
    triggers: list[str]  # e.g. ["VIX>35", "BTC.d>60%", "drawdown>15%"]

class RegimeDetector:
    """Heuristic + lightweight statistical detector.

    Sources (in order):
      1. VolatilityEngine.regime (core/volatility.py) — already ✅
      2. VIX / DXY proxy from MacroAgent.last_response
      3. Recent drawdown from RiskEngineV2
    """
    def detect(self, state: dict) -> RegimeSignal: ...
```

**Kill-switch контракт:** `RegimeSignal.regime == CRISIS` → `SynthesisAgent.run()` (в `orchestration/sentinel_v5.py`) **до** основной логики возвращает `AgentResponse(signal=AVOID, confidence=100, reasoning="KILL_SWITCH: regime=CRISIS triggers=[...])`. Это **жёсткий bypass** — обходит и KARL, и vote, и conflict resolution.

**Метрики:** `sentinel_mas_regime{regime}` (Gauge, 1=active), `sentinel_mas_killswitch_total` (Counter).

---

## 4. План реализации (по итерациям, каждая ≤ 1 PR)

### PR 1 — `phase2/bugfix-imports` (≤ 30 мин, low risk)
- [ ] `meta_rl/basket.py`: переместить `from __future__ import annotations` в первую строку.
- [ ] `meta_rl/baseline_*.py` (2 файла): тот же фикс.
- [ ] `agents/_impl/quant_agent.py`: удалить `dead code` (несвязанные переменные из старого PR).
- [ ] `ruff check .` зелёный.

### PR 2 — `phase2/pattern-a-uniform` (≤ 2ч, medium risk)
- [ ] Взять 12 агентов из §3.2, обернуть `run()` по каноническому паттерну.
- [ ] **НЕ трогать** тело `analyze()`.
- [ ] Прогнать `pytest -q tests/agents/` — все 241+ тесты зелёные.
- [ ] Добавить snapshot в `docs/monitoring/mas_health.json` (Grafana datasource).

### PR 3 — `phase2/compromise-agent` (≤ 3ч, medium risk)
- [ ] Создать `agents/_impl/compromise_agent.py` по §3.1.
- [ ] Зарегистрировать в `agents/__init__.py` (entry point registry).
- [ ] Интегрировать в `SynthesisAgent._vote()`.
- [ ] Тест: `tests/agents/test_compromise_agent.py` — 5 кейсов (конфликт LONG/SHORT, одинаковые сигналы, degraded inputs).

### PR 4 — `phase2/calibration-tracker` (≤ 4ч, medium risk)
- [ ] `agents/_impl/calibration.py` по §3.3.
- [ ] Миграция `core/history_db.py`: добавить таблицу `agent_outcomes`.
- [ ] Хук в `orchestration/sentinel_v5.py` после fan-out: запись `AgentOutcome` для каждого `AgentResponse`.
- [ ] Интеграция в `MetaAgent.select()`.
- [ ] Тест: `tests/agents/test_calibration_tracker.py`.

### PR 5 — `phase2/regime-detector` (≤ 3ч, medium risk)
- [ ] `meta_rl/regime_detector.py` по §3.4.
- [ ] Kill-switch в `orchestration/sentinel_v5.py` **до** `await asyncio.gather(...)`.
- [ ] Тест: `tests/meta_rl/test_regime_detector.py` — 4 режима + kill-switch.
- [ ] Grafana-алерт: `increase(sentinel_mas_killswitch_total[1h]) > 0`.

---

## 5. Что НЕ входит в этот план (явно)

- **Event bus / Kafka** — Q4 2026, отдельный roadmap.
- **PostgreSQL + pgvector** — Q4 2026; до тех пор SQLite через `core/history_db.py`.
- **TypeScript dashboard rewrite** — Q3 2026, ортогонально MAS.
- **Agent hot-reload via entry points** — Q3 2026, требует registry refactor.
- **AstroCouncil sub-agents refactor** — уже ✅ (STATUS.md §1: Bradley/Gann/Cycle/Electoral/TimeWindow — все 5 ✅).

---

## 6. Метрики успеха (Definition of Done)

| Метрика | До (текущая) | После (цель) | Как мерять |
|---------|--------------|--------------|------------|
| Агентов с `@track_agent_metrics` | ~6 | 20 | `scripts/validate_agent.py --metrics` |
| Агентов со структурированным `_degraded()` | ~6 | 20 | `scripts/validate_agent.py --errors` |
| Per-agent calibration видна в Grafana | ❌ | ✅ | `sentinel_agent_calibration_brier` query |
| Kill-switch срабатывает на CRISIS | ❌ | ✅ | `tests/meta_rl/test_regime_detector.py::test_kill_switch` |
| PnL attribution per agent | ❌ | ✅ | `sentinel_agent_attribution_pnl` query |
| `pytest -q` | 241 ✅ | 260+ ✅ | CI |
| `ruff check .` | warnings | 0 errors | CI |

---

## 7. Открытые вопросы (требуют решения до старта PR 3+)

1. **CompromiseAgent: использовать `VolatilityEngine` напрямую или просить state от оркестратора?** Предлагаю state — проще тестировать, единый контракт.
2. **Calibration window: 200 или 500 сделок?** По умолчанию 200 (быстрее адаптация к drift), настраивается через `config/agent_weights.yaml`.
3. **Kill-switch: только в `sentinel_v5.py` или также в `langgraph_schema.py`?** Только в v5 (это production path; `langgraph_schema.py` — 🟡 experimental).
