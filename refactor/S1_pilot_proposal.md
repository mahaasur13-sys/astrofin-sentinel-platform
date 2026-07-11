# S1 Pilot — 3 файла, измеримый результат

> **Sprint:** S1 (1 неделя)
> **Цель:** Убрать 1-file cycles + ввести протоколы для God Nodes, чтобы снизить centralities на 20 %.
> **Метрика:** `pydeps --show-deps --max-depth=4 agents/_impl/technical_agent.py core/ephemeris.py AsurDev/acos/storage/schema.py` — нет самоссылки, нет импорта из `*_archived/`, God Nodes: `AgentResponse` ≥ 3 реализаций, `BaseAgent` ≥ 3 реализации, `SignalDirection` — протокол.

---

## 1. Пилотные файлы (актуальные пути в `/home/workspace/`)

| # | Путь | Размер | Зачем в пилоте | Ожидаемый эффект |
|---|---|---:|---|---|
| 1 | `agents/_impl/technical_agent.py` | 294 строки | Самый «божественный» (импортирует `BaseAgent`, `AgentResponse`, `EPHEMERIS_UNAVAILABLE`, `UNKNOWN`, напрямую лезет в `core.ephemeris`) | Демонстрация изоляции домена `agents/`, замена прямого импорта протоколом |
| 2 | `core/ephemeris.py` | 252 строки | Используется 8+ агентами, ключевая точка детерминизма (seed = дата) | Извлечь `EphemerisProtocol` в `common/interfaces.py` |
| 3 | `AsurDev/acos/storage/schema.py` | 44 строки | 1-file cycle + `datetime.utcnow()` (нарушение детерминизма) | Inject `Clock` (детерминистичный), `TraceRecord` → `common/contracts/` |

---

## 2. План работы (5 дней)

| День | Задача | Результат |
|---|---|---|
| D1 | Создать `common/interfaces.py` с протоколами (см. §3) | Файл + mypy `--strict` проходит |
| D2 | Создать `common/contracts.py` с DTO (см. §4) | Файл + unit-тесты на сериализацию |
| D3 | Рефакторинг `agents/_impl/technical_agent.py` (см. §5) | Все импорты God Nodes заменены на протоколы, `pydeps` без циклов |
| D4 | Рефакторинг `core/ephemeris.py` (выделить протокол) | `EphemerisProtocol` в `common/interfaces.py`, обратная совместимость через `__getattr__` |
| D5 | Рефакторинг `AsurDev/acos/storage/schema.py` (DI Clock) | Тесты детерминизма зелёные |

---

## 3. `common/interfaces.py` — черновик протоколов

```python
"""common/interfaces.py — протоколы для God Nodes (S1).

Цель: разорвать жёсткие импорты `agents → core`, `core → agents`,
позволить подменять реализации в тестах и replay-режиме.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AgentResponseProtocol(Protocol):
    """Минимум, что агенты обязаны вернуть в SynthesisAgent."""
    agent_name: str
    signal: str
    confidence: int
    reasoning: str
    sources: list[str]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class BaseAgentProtocol(Protocol):
    """Любой агент, который может вызвать оркестратор."""
    name: str
    domain: str
    weight: float

    async def run(self, state: dict[str, Any]) -> AgentResponseProtocol: ...


@runtime_checkable
class EphemerisProtocol(Protocol):
    """Абстракция над Swiss Ephemeris для тестируемости."""
    def is_available(self) -> bool: ...
    def julian_day(self, dt: datetime) -> float: ...
    def calculate_planet(self, name: str, jd: float) -> Any: ...


@runtime_checkable
class ClockProtocol(Protocol):
    """Inject часов: реальные в проде, фиксированные в replay."""
    def now(self) -> datetime: ...
    def seed(self) -> int: ...


@runtime_checkable
class StorageProtocol(Protocol):
    """Persist trace records (заменяет TraceRecord direct-instantiation)."""
    def save(self, record: Any) -> None: ...
    def find(self, trace_id: str) -> Any | None: ...
```

**Принципы:**
- Все протоколы `@runtime_checkable` — чтобы `isinstance(x, EphemerisProtocol)` работал без mypy-juggling.
- Никаких ABC. Никаких зависимостей от `core.*` или `agents.*` — только stdlib.
- Конкретные классы (`AgentResponse`, `BaseAgent`, `SwissEphemeris`, `TraceRecord`) реализуют протоколы явно через `Protocol` structural matching — без `isinstance` в бизнес-коде.

---

## 4. `common/contracts.py` — DTO

```python
"""common/contracts.py — DTO и валидаторы (S1)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentResponseDTO:
    agent_name: str
    signal: str          # "STRONG_BUY" | "BUY" | "NEUTRAL" | "SELL" | "STRONG_SELL"
    confidence: int      # 0..100
    reasoning: str
    sources: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not 0 <= self.confidence <= 100:
            raise ValueError(f"confidence={self.confidence} out of [0,100]")
        if self.signal not in {"STRONG_BUY", "BUY", "NEUTRAL", "SELL", "STRONG_SELL"}:
            raise ValueError(f"unknown signal={self.signal}")


@dataclass(frozen=True, slots=True)
class TraceRecordDTO:
    trace_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
```

**Зачем `frozen=True, slots=True`:** хешируемость, immutability, меньше памяти — и явный сигнал, что DTO не модифицируются in-place.

---

## 5. Рефакторинг `agents/_impl/technical_agent.py` (diff-стиль)

### 5.1 До (фрагмент — текущая «жёсткая связка»)

```python
# Прямой импорт God Nodes — делает невозможным подмену в тестах
from core.base_agent import EPHEMERIS_UNAVAILABLE, UNKNOWN, AgentResponse, BaseAgent
from agents._impl.ephemeris_decorator import EphemerisUnavailableError, require_ephemeris

class TechnicalAgent(BaseAgent[AgentResponse]):
    def __init__(self):
        super().__init__(name="Technical", domain="technical", weight=0.10)

    @track_agent_metrics
    async def run(self, state): ...

    def _call_ephemeris(self, dt: datetime) -> dict:
        from core.ephemeris import HAS_SWISS_EPHEMERIS, _julian_day, calculate_planet
        # ... смешение бизнес-логики и адаптера ...
```

### 5.2 После (S1-рефакторинг)

```python
"""agents/_impl/technical_agent.py — рефакторинг S1.

Изменения:
  - God Nodes заменены протоколами из common.interfaces
  - Ephemeris инжектируется через __init__ (DI)
  - Hard-coded URL OKX вынесен в config
  - Прямой импорт core.* заменён на self._ephemeris.* (через протокол)
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from common.interfaces import AgentResponseProtocol, BaseAgentProtocol, ClockProtocol, EphemerisProtocol
from common.contracts import AgentResponseDTO
from agents._impl.ephemeris_decorator import EphemerisUnavailableError

logger = logging.getLogger(__name__)


class TechnicalAgent:
    """Технический анализ: RSI, MACD, Bollinger, Volume.
    Вес: 10%. 85% technical + 15% astro бонус.
    """

    def __init__(
        self,
        *,
        ephemeris: EphemerisProtocol,
        clock: ClockProtocol,
        ohlcv_fetcher: "OHLCVFetcherProtocol | None" = None,
    ) -> None:
        self.name = "Technical"
        self.domain = "technical"
        self.weight = 0.10
        self._ephemeris = ephemeris
        self._clock = clock
        self._fetch_ohlcv = ohlcv_fetcher or _DefaultOKXFetcher()

    async def run(self, state: dict[str, Any]) -> AgentResponseProtocol:
        try:
            return await self.analyze(state)
        except EphemerisUnavailableError as e:
            return self._degraded("EPHEMERIS_UNAVAILABLE", str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("agent_run_unhandled", extra={"agent": self.name})
            return self._degraded("UNKNOWN", repr(e))

    async def analyze(self, state: dict[str, Any]) -> AgentResponseProtocol:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price") or state.get("price") or 50_000
        dt = state.get("datetime") or self._clock.now()

        eph = self._compute_astro(dt)
        price_data = await self._fetch_ohlcv(symbol, "1d", 50)
        indicators = self._calculate_indicators(price_data, current_price)
        score = self._calculate_technical_score(indicators, eph)
        signal = self._score_to_signal(score)

        return AgentResponseDTO(
            agent_name=self.name,
            signal=signal,
            confidence=min(88, int(score)),
            reasoning=self._build_reasoning(indicators, score),
            sources=["Binance API", "Technical analysis"],
            metadata={
                "technical_score": score,
                "rsi": indicators.get("rsi"),
                "macd": indicators.get("macd"),
                "bollinger": indicators.get("bollinger"),
                "volume": indicators.get("volume_trend"),
                "astro_influence": f"Yoga: {eph['yoga']}, score: {eph['score']}",
                "source": "binance + astrological_bonus",
            },
        )

    def _compute_astro(self, dt: datetime) -> dict[str, Any]:
        """Делегирует протоколу — не лазит в core.ephemeris напрямую."""
        if not self._ephemeris.is_available():
            return {"yoga": "unknown", "score": 50}
        jd = self._ephemeris.julian_day(dt)
        mars = self._ephemeris.calculate_planet("mars", jd)
        moon = self._ephemeris.calculate_planet("moon", jd)
        venus = self._ephemeris.calculate_planet("venus", jd)
        return _score_mars_venus_moon(mars.longitude, moon.longitude, venus.longitude)

    def _degraded(self, reason: str, detail: str) -> AgentResponseProtocol:
        return AgentResponseDTO(
            agent_name=self.name,
            signal="NEUTRAL",
            confidence=0,
            reasoning=f"degraded: {reason} ({detail})",
            sources=[],
            metadata={"degraded": reason},
        )

    # _calculate_indicators, _ema, _calculate_technical_score,
    # _score_to_signal, _build_reasoning — без изменений (pure functions)
    # ...


# ── helpers вынесены в pure-модуль для тестируемости ─────────────
def _score_mars_venus_moon(mars: float, moon: float, venus: float) -> dict[str, Any]:
    score = 50
    mars_moon = abs(mars - moon) % 360
    if mars_moon < 30 or mars_moon > 330:
        score += 10
    elif 85 < mars_moon < 95:
        score -= 10
    ven_moon = abs(venus - moon) % 360
    if ven_moon < 30 or ven_moon > 330:
        score += 5
    return {"yoga": "mars_venus_moon", "score": max(0, min(100, score))}
```

### 5.3 Что изменилось — резюме

| До | После | Эффект |
|---|---|---|
| `from core.base_agent import AgentResponse, BaseAgent, ...` | Импорт только `common.interfaces.*` | Убран цикл `core ↔ agents` |
| `from core.ephemeris import ...` напрямую в методе | `self._ephemeris.*` (DI) | Подменяемо в тестах (FakeEphemeris) |
| `datetime.utcnow()` | `self._clock.now()` | Детерминизм + replay |
| `import httpx` + URL внутри метода | `OHLCVFetcherProtocol` | Swap на mock в unit-тестах |
| `class TechnicalAgent(BaseAgent[AgentResponse])` | `class TechnicalAgent` (struct) | Нет жёсткой зависимости от God Node |

### 5.4 Что НЕ меняется в S1

- Математика индикаторов (`_calculate_indicators`, `_ema`) — оставляем как есть, чисто numeric refactor вынесем в S3.
- Логика скоринга (`_calculate_technical_score`, `_score_to_signal`) — тестируем после извлечения.
- `_build_reasoning` — без изменений.

### 5.5 Тесты для S1

```python
# tests/agents/test_technical_agent_s1.py
import pytest
from agents._impl.technical_agent import TechnicalAgent, _score_mars_venus_moon
from common.interfaces import EphemerisProtocol, ClockProtocol


class FakeEphemeris:
    def is_available(self): return True
    def julian_day(self, dt): return 2451545.0
    def calculate_planet(self, name, jd):
        return type("P", (), {"longitude": 0.0, "longitude": 0.0})()


class FakeClock:
    fixed = __import__("datetime").datetime(2026, 1, 1, 12, 0)
    def now(self): return self.fixed
    def seed(self): return 20260101


async def test_analyze_uses_injected_ephemeris():
    agent = TechnicalAgent(ephemeris=FakeEphemeris(), clock=FakeClock())
    resp = await agent.analyze({"symbol": "BTCUSDT", "current_price": 50_000})
    assert resp.signal in {"BUY", "NEUTRAL", "SELL", "STRONG_BUY", "STRONG_SELL"}
    assert 0 <= resp.confidence <= 100


def test_pure_scoring_function():
    # Mars trine Moon (0°) + Venus trine Moon
    r = _score_mars_venus_moon(mars=0, moon=10, venus=20)
    assert r["score"] == 65  # 50 + 10 + 5

    # Mars square Moon (90°)
    r = _score_mars_venus_moon(mars=0, moon=90, venus=180)
    assert r["score"] == 50  # 50 - 10 + 5 (Venus trine) + 0
```

---

## 6. Рефакторинг `core/ephemeris.py` (S1-D4)

**Цель:** Спрятать `sweph` детали за `EphemerisProtocol`. Прямой импорт `from core.ephemeris import _julian_day` — убираем.

**Изменения:**
1. Переименовать публичные функции без подчёркивания: `_julian_day` → `julian_day` (теперь в `__all__`).
2. Класс-обёртка `SwissEphemerisAdapter` реализует `EphemerisProtocol`.
3. Старые функции оставлены как `__getattr__`-фасад для обратной совместимости, помечены `DeprecationWarning` (будут удалены в S3).

```python
# core/ephemeris.py — фрагмент
from common.interfaces import EphemerisProtocol

class SwissEphemerisAdapter:
    """Адаптер, реализующий EphemerisProtocol."""
    def is_available(self) -> bool:
        return HAS_SWISS_EPHEMERIS

    def julian_day(self, dt: datetime) -> float:
        return _julian_day(dt)

    def calculate_planet(self, name: str, jd: float) -> Any:
        return _calculate_planet(name, jd)

# Backward-compat shim
import warnings as _w
def __getattr__(name: str):
    if name in ("_julian_day", "_calculate_planet"):
        _w.warn(f"{name} is deprecated, use SwissEphemerisAdapter", DeprecationWarning, stacklevel=2)
        return globals()[name.lstrip("_")]
    raise AttributeError(name)
```

---

## 7. Рефакторинг `AsurDev/acos/storage/schema.py` (S1-D5)

**Проблемы:**
- `datetime.utcnow()` — нарушение детерминизма.
- Жёсткая привязка к глобальному времени.

**Решение:** Inject `ClockProtocol`, дефолт — `SystemClock`, в replay-тестах — `FixedClock("2026-06-20")`.

```python
# AsurDev/acos/storage/schema.py — S1-версия
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
import os

from common.interfaces import ClockProtocol

DEFAULT_CLOCK: ClockProtocol = ...  # импортируется lazy


@dataclass
class TraceRecord:
    trace_id: str
    metadata: dict
    created_at: datetime = field(default=None)  # NB: НЕ default_factory — иначе при None перезатрёт

    def __post_init__(self):
        if self.created_at is None:
            object.__setattr__(self, "created_at", DEFAULT_CLOCK.now())

    def to_dict(self) -> dict: ...
    @classmethod
    def from_dict(cls, d: dict) -> "TraceRecord": ...
```

**Backwards-compat:** старый конструктор `TraceRecord(trace_id, metadata)` продолжает работать (created_at=None → factory).

**Determinism test:**
```python
def test_trace_record_is_deterministic():
    clock = FixedClock(datetime(2026, 6, 20, 12, 0))
    rec = TraceRecord(trace_id="t1", metadata={"k": 1}, _clock=clock)
    assert rec.created_at == datetime(2026, 6, 20, 12, 0)
```

---

## 8. Acceptance Criteria S1

| # | Проверка | Команда | Ожидаемо |
|---|---|---|---|
| 1 | `import-linter` контракт: `agents` не импортирует `core` напрямую | `lint-imports` | 0 violations |
| 2 | Циклов в графе нет | `pydeps --show-cycle --max-depth=6 agents/_impl/technical_agent.py core/ephemeris.py` | «No cycles» |
| 3 | God Nodes имеют ≥ 3 реализации | `grep -rn "class.*BaseAgent\b"` | ≥ 3 |
| 4 | Unit-тесты протоколов | `pytest tests/common/ tests/agents/test_technical_agent_s1.py` | All pass |
| 5 | Replay-тест: тот же seed → тот же score | `pytest tests/replay/test_technical_replay.py` | All pass |
| 6 | `mypy --strict common/` | `mypy common/` | 0 errors |
| 7 | Coverage `technical_agent.py` | `pytest --cov=agents/_impl/technical_agent` | ≥ 80 % |

---

## 9. Риски и митигации (S1-specific)

| Риск | Митигация |
|---|---|
| DI-constructor сломает существующие `TechnicalAgent()` без аргументов | `__init__(self, *, ephemeris=None, clock=None, ...)` — defaults берутся из `config/runtime.py` |
| `__getattr__` shim может замаскировать новые ошибки импорта | `DeprecationWarning` в shim + тест `test_legacy_imports_warn` |
| Перенос `common/` как пакета требует `pyproject.toml` правки | Минимальный: `packages = ["common"]` в `[tool.setuptools]` |
| Рефакторинг `technical_agent.py` ломает 8 импортирующих мест | `git grep "from agents._impl.technical_agent"` — pre-D3 audit, обновить call-sites |

---

## 10. Что НЕ входит в S1 (явно)

- Полная доменная реорганизация (`trading_agents/`, `risk_management/` и т.д.) — это S3.
- Извлечение чистой математики индикаторов в pure-модули — S3.
- Замена httpx-фетчера на типизированный `OHLCVFetcherProtocol` (сейчас просто default-класс) — S3, если потребуется.
- import-linter в CI — S4.

---

## 11. Changelog

- **2026-06-20** — Initial draft. Решение по working root: `/home/workspace/` (astrofin-sentinel-platform).
- _(будет обновляться по ходу S1)_
