# Proposed ATOMs — Roadmap 2 Weeks

Generated: 2026-03-29
Last Updated: 2026-03-29

---

## P0 — Immediate (Foundation First)

### ATOM-KARL-015: Полная интеграция KARL в основной контур

**Status:** APPROVED
**Priority:** P0
**Complexity:** HIGH

#### Why P0?
- Архитектурный дефект: KARL собирает данные, но не влияет на решения
- Это фундамент для всего остального

#### Phases
| Phase | What | Risk | Impact | Status |
|-------|------|------|--------|--------|
| P0 | OAP → Soft Weighting | min_weight=0.1 | ⭐⭐⭐⭐⭐ | ✅ DONE (2026-03-29) |
| **P1** | **Reward → EMA Smoothing (α=0.3)** | **alpha=0.3** | **⭐⭐⭐⭐** | **✅ DONE (2026-03-29)** |
| **P1** | **SelfQ → Triple Trigger** | **3 conditions** | **⭐⭐⭐** | **✅ DONE (2026-03-29)** |
| **P2** | **OAP → Per-Agent Adjustment** | **per-agent dict** | **⭐⭐⭐⭐⭐** | **✅ DONE (2026-03-29)** |
| P2 | Grounding → Soft Degrade | confidence min 35 | ⭐⭐ | ⬜ |
| P2 | Lag → Windowing | window=50 | ⭐⭐ | ⬜ |

#### Feature Flags
```python
KARL_FLAGS = {
    "oap_weighting": True,
    "reward_position": True,
    "selfq_flip": True,
    "grounding_gate": True,
    "lag_control": True,
    "auto_rollback": True,  # Sharpe < 0.5 → disable
}
```

#### Expected (after 2 weeks measurement)
| Metric | Before | Target |
|--------|--------|--------|
| Sharpe | 0.71 | 0.85-0.95 |
| Win Rate | 47% | 50-52% |

**Files:** `orchestration/sentinel_v5.py`, `agents/karl_synthesis.py`

---

### ATOM-DEDUP-001: Дедупликация 6 пар агентов

**Status:** ✅ APPROVED + DONE (2026-03-29)
**Priority:** P0
**Complexity:** MEDIUM

#### Why P0?
- 12 backtests = insufficient data
- 6 пар дубликатов = extra noise
- Нельзя экспортировать агентов (GitAgent) с конфликтами

#### Task
Завершить дедупликацию оставшихся 6 пар.

#### Changes Made
- Moved 4 stub files to `agents/_archived/`:
  - `electoral_agent.py`, `technical_agent.py`, `market_analyst.py`, `synthesis_agent.py`
- Updated 6 files with new imports pointing to `_impl/`:
  - `astro_council_agent.py`, `karl_synthesis.py`, `sentinel_v5_mas.py`
  - `langgraph_schema.py`, `test_orchestrator.py`, `atom_014_stress_test.py`
- Created `agents/_archived/DEDUPLICATION_LOG.md`

#### Dependencies
← ATOM-KARL-015 Phase 1 (чтобы видеть что дублируется) ✅

---

### ATOM-FIX-ROUTER: Исправление бага с timeframe

**Status:** ✅ APPROVED + DONE (2026-03-29)
**Priority:** P0
**Complexity:** LOW

#### Bug
`UnboundLocalError: local variable 'timeframe' referenced before assignment` при `has_electional=True`.

#### Root Cause
В `orchestration/router.py` блок определения `timeframe` (строки ~113–119) находился **после** early return в ветке `elif has_electional:` (строка ~96), которая уже использовала `timeframe`.

#### Fix Applied
Переместил определение `timeframe` **выше** всех branch-возвратов, до начала условной логики. Это минимальный фикс без изменения поведения.

#### Changes
- `orchestration/router.py`: блок `timeframe = "SWING"` перенесён на 11 строк выше

#### Verification
```bash
✅ Test 1 (обычный): single_symbol | tf: SWING
✅ Test 2 (electional): electional_only | tf: SWING  ← БЫВШИЙ БАГ
✅ Test 3 (electional+technical): electional_only | tf: SWING
✅ Test 4 (intraday): single_symbol | tf: INTRADAY
✅ Test 5 (electional+intraday): electional_only | tf: INTRADAY
✅ Test 6 (positional): single_symbol | tf: POSITIONAL
```

#### Dependencies
← ATOM-DEDUP-001 ✅

---

## P1 — After Foundation

### ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector

**Status:** PROPOSED
**Priority:** P1
**Complexity:** HIGH

#### Why P1?
После чистых данных и стабильного KARL — нужен надёжный storage для:
- Временных рядов (TimescaleDB)
- Agent embeddings (pgvector)
- Agent similarity search

#### Components
1. PostgreSQL — primary
2. TimescaleDB — backtest history time-series
3. pgvector — agent embeddings

#### Dependencies
← ATOM-DEDUP-001
← ATOM-FIX-ROUTER

---

### ATOM-MODEL-SPEC: Единая спецификация модели

**Status:** PROPOSED
**Priority:** P1
**Complexity:** MEDIUM

#### Why P1?
С ростом агентов нужна:
- Иерархия правил
- Делиберативное согласование
- Единый `MODEL_SPEC.md`

#### Dependencies
← ATOM-KARL-015 (понимание что влияет)
← ATOM-DB-MIGRATION (хранение)

---

### ATOM-R-043: Pressure Field Coordination (sandbox)

**Status:** PROPOSED (sandbox)
**Priority:** P1
**Complexity:** MEDIUM

#### Why sandbox, not production?
- Paper: лабораторный результат
- Domain: noisy financial signals
- Нужен prototype в AMRE перед продакшеном

#### Concrete Implementation
```python
pressure_score(agent) = (
    w1 * recent_sharpe +
    w2 * agreement_with_ensemble +
    w3 * regime_alignment -
    w4 * uncertainty
)
agent_weight = softmax(pressure_scores)
```

#### Dependencies
← ATOM-KARL-015 (управление должно быть замкнуто)

---

## P2 — Later

### ATOM-GITAGENT-003: Phase 3 GitAgent (MCP + Dashboard)

**Status:** PROPOSED
**Priority:** P2
**Complexity:** MEDIUM

#### When
Только после:
- ✅ Дедупликация завершена
- ✅ KARL интегрирован в core loop

#### Reason
Экспорт при дубликатах → конфликты имён

#### Dependencies
← ATOM-DEDUP-001
← ATOM-KARL-015 (стабильный core loop)

---

### ATOM-R-044: CrewAI v2.3 Integration

**Status:** PROPOSED (deferred)
**Priority:** P2
**Complexity:** MEDIUM

#### Decision
❌ Не сейчас
✅ После стабилизации KARL

#### Reason
Это DX улучшение (agent workflows), не alpha generation.

---

## Strategic Notes

### Why Sharpe < 1.0 is OK for now
> "При 12 бэктестах значение 0.71 — это шум, не сигнал"

### 2-Week Priority Order
```
Week 1:
  KARL-015 Phase 1 → Phase 2 → Phase 3

Week 2:
  KARL-015 Phase 4 → Phase 5
  DEDUP-001
  FIX-ROUTER

Week 3-4:
  DB-MIGRATION
  MODEL-SPEC
  R-043 sandbox

Later:
  GITAGENT-003
  R-044
```

### Live Trading Signals & Dashboard
❌ Not before 3-4 ATOMs (2-3 weeks)
✅ Need: stable learning core loop + reliable DB first

---

## Active ATOMs Status

| ATOM | Priority | Status |
|------|----------|--------|
| KARL-015 | P0 | ✅ Phase 1+2+3+4 DONE — OAP Weighting + EMA Reward + SelfQ Triple Trigger |
| DEDUP-001 | P0 | ✅ APPROVED + DONE (2026-03-29) |
| FIX-ROUTER | P0 | ✅ APPROVED + DONE (2026-03-29) |
| DB-MIGRATION | P1 | PROPOSED |
| MODEL-SPEC | P1 | PROPOSED |
| R-043 | P1 | PROPOSED (sandbox) |
| GITAGENT-003 | P2 | PROPOSED |
| R-044 | P2 | PROPOSED (deferred) |
