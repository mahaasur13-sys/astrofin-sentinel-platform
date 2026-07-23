# ATOM-KARL-015: Полная интеграция KARL в основной контур

**Priority:** P0 — немедленный запуск
**Status:** APPROVED (awaiting implementation)
**Complexity:** HIGH
**Generated:** 2026-03-29
**Prerequisites:** None (P0)

---

## Core Principle

> observe → learn → ACT (闭环自适应交易系统)

**Все вмешательства должны быть:**
- ✅ монотонно безопасными (не ломают базовую стратегию)
- ✅ регулируемыми (feature flags)
- ✅ измеряемыми (audit → KPI)
- ✅ откатываемыми (auto-disable при критическом падении)

---

## Problem Statement

**Текущее состояние:**
- KARL собирает данные, но не влияет на решения
- Sharpe Ratio: 0.71 < 1.0 ❌
- Win Rate: 47% < 50% ❌
- OOS Fail Rate: 12% ❌

**Причина:** observability ≠ control — классическая ошибка

**После KARL-015:**
- Интеллект не просто наблюдает, а управляет
- Self-correcting system (не rule-based, не LLM-agent)

---

## Feature Flags (обязательно)

```python
KARL_FLAGS = {
    "oap_weighting": True,       # Phase 1
    "reward_position": True,     # Phase 2
    "selfq_flip": True,          # Phase 3
    "grounding_gate": True,      # Phase 4
    "lag_control": True,         # Phase 5
    "auto_rollback": True,       # Safety
}
```

---

## Phase 1: OAP → Soft Weighting (P0)

### Текущая проблема
```python
# ❌ ЖЁСТКОЕ ИСКЛЮЧЕНИЕ — опасно
if perf.sharpe_ratio < -0.5:
    exclude_names.add(agent_name)
```
**Риск:** policy collapse, потеря exploration

### Исправление: мягкое подавление весов

```python
def _compute_agent_weight(perf, min_weight=0.1):
    """Мягкое подавление, не жёсткое исключение"""
    if perf is None or perf.sharpe_ratio is None:
        return 1.0
    # sharpe -0.8 → 0.2 weight (не 0!)
    return max(min_weight, 1.0 + perf.sharpe_ratio)

def _select_for_flow(pool, weights=None, excluded=None, k=None):
    """Thompson sampling с весами"""
    weights = weights or {a.name: 1.0 for a in pool}
    excluded = excluded or set()

    valid = [a for a in pool if a.name not in excluded]
    if not valid:
        valid = pool  # fallback

    # Weighted sampling
    probs = np.array([weights.get(a.name, 1.0) for a in valid])
    probs = probs / probs.sum()

    indices = np.random.choice(len(valid), size=min(k or len(valid), len(valid)),
                              replace=False, p=probs)
    return [valid[i] for i in indices]
```

**Эффект:**
- Плохие агенты → подавляются, но не исчезают
- Exploration сохраняется
- Policy collapse исключён

### Impact: ⭐⭐⭐⭐⭐ (основной драйвер)

---

## Phase 2: Reward → Smoothed Position Sizing (P1)

### Текущая проблема
```python
# ❌ ШУМНЫЙ REWARD → скачки position
reward_mult = 0.5 + reward
```

### Исправление: экспоненциальное сглаживание

```python
def smooth_reward(reward, alpha=0.3, prev=0.0):
    """EMA smoothing — убирает volatility"""
    return alpha * reward + (1 - alpha) * prev

# В классе:
self.prev_reward = 0.0  # инициализация

# Применение:
reward_smoothed = smooth_reward(reward, alpha=0.3, prev=self.prev_reward)
self.prev_reward = reward_smoothed  # сохраняем для следующего шага

reward_mult = 1.0 + 0.5 * reward_smoothed
position_size = base_size * reward_mult
```

**Эффект:**
- Убирает volatility
- Стабилизирует equity curve
- Position не скачет на шуме

### Impact: ⭐⭐⭐⭐

---

## Phase 3: SelfQ → Double-Trigger Flip (P1)

### Текущая проблема
```python
# ❌ СЛИШКОМ АГРЕССИВНО — много NEUTRAL
if contradiction_score > 0.7:
    signal = "NEUTRAL"
```

### Исправление: тройное условие

```python
def _should_flip(sq_result, uncertainty):
    """Триггер только при совпадении условий"""
    return (
        sq_result.contradiction_score > 0.7 and
        sq_result.confidence_adjustment < -15 and
        uncertainty > 0.4  # ВАЖНО: неопределённость
    )

if KARL_FLAGS["selfq_flip"] and _should_flip(sq_result, uncertainty):
    signal = "NEUTRAL"
    selfq_triggered = True
```

**Условия (все должны выполняться):**
1. ✅ Есть противоречие (contradiction > 0.7)
2. ✅ Низкая уверенность (confidence_adj < -15)
3. ✅ Высокая неопределённость (uncertainty > 0.4)

### Impact: ⭐⭐⭐

---

## Phase 4: Grounding → Soft Degrade (P2)

### Текущая проблема
```python
# ❌ ЖЁСТКИЙ KILL — теряем слабые сигналы
if critical_issues:
    signal = "NEUTRAL"
```

### Исправление: мягкая деградация

```python
if KARL_FLAGS["grounding_gate"]:
    if critical_issues:
        confidence = min(confidence, 35)  # Degrade, not kill

    if confidence < 35:
        signal = "NEUTRAL"
        grounding_blocked = True
```

**Эффект:**
- Сохраняет слабые сигналы
- Убирает только агрессивные

### Impact: ⭐⭐

---

## Phase 5: Feedback Lag Control (P2)

### Проблема
```python
# ❌ ИСПОЛЬЗУЕМ ВСЮ ИСТОРИЮ → переобучение на старых данных
samples = bt.get_agent_samples(agent)  # вся история
```

### Исправление: windowing

```python
def get_recent_performance(agent, window=50):
    """Только свежие данные"""
    samples = bt.get_agent_samples(agent)[-window:]
    if len(samples) < 10:
        return None
    return compute_metrics(samples)
```

**Window = 50** — около 2 месяцев для daily trading

### Impact: ⭐⭐⭐

---

## DecisionRecord — расширенный

```python
DecisionRecord = {
    # Base
    "date": "2026-03-29",
    "signal": "BULL",
    "confidence": 72,

    # Phase 1: OAP Weighting
    "selected_agents": ["TrendAgent", "MomentumAgent"],
    "excluded_agents": [],
    "agent_weights": {"TrendAgent": 1.2, "MomentumAgent": 0.8},

    # Phase 2: Reward Sizing
    "position_size": 0.85,  # было бы 1.0 без smoothing
    "reward": 0.3,
    "reward_smoothed": 0.15,

    # Phase 3: SelfQ
    "selfq_triggered": False,
    "contradiction_score": 0.4,

    # Phase 4: Grounding
    "grounding_blocked": False,
    "confidence_degraded": False,

    # Phase 5: Lag Control
    "window_used": 50,

    # KPIs
    "kpi_sharpe_before": 0.71,
    "kpi_sharpe_after": None,  # заполняется позже
}
```

---

## KPI Guard (обязательно)

```python
# Safety: автоматический rollback
if KARL_FLAGS["auto_rollback"]:
    if kpi.sharpe_ratio < 0.5:
        disable_karl_feedback()
        logger.warning("KARL feedback DISABLED: Sharpe < 0.5")
        notify_user("KARL-015 auto-rollback triggered")
```

**Kill Criteria:**
- Sharpe Ratio < baseline - 0.1 после 2 недель
- Win Rate < 40% (катастрофический сбой)

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Model collapse (жёсткое исключение) | HIGH | Soft weighting (Phase 1) |
| Overfitting to recent regime | MEDIUM | Windowing (Phase 5) |
| False suppression of good agents | MEDIUM | Min weight 0.1, fallback to full pool |
| Volatility from noisy reward | HIGH | EMA smoothing (Phase 2) |
| Over-triggering SelfQ | MEDIUM | Triple condition (Phase 3) |
| Killing valid signals (Grounding) | LOW | Soft degrade to 35 (Phase 4) |

---

## Execution Order

```
KARL-015 Phase 1 (OAP weighting)     ← день 1-2
KARL-015 Phase 2 (reward sizing)     ← день 3-4
KARL-015 Phase 3 (SelfQ)             ← день 5-6
KARL-015 Phase 4 (grounding)         ← день 7-8
KARL-015 Phase 5 (lag control)      ← день 9-10
↓
Измерение: 2 недели
↓
R-043 (sandbox, pressure field)      ← после метрик
R-044 (UX, CrewAI)                   ← позже
```

---

## Expected Results (честно)

| Metric | Before | After | Target |
|--------|--------|-------|--------|
| Sharpe Ratio | 0.71 | 0.85-0.95 | 1.0+ |
| Win Rate | 47% | 50-52% | 52%+ |
| OOS Fail Rate | 12% | <10% | <8% |

**Основной драйвер:** Phase 1 (OAP weighting)

---

## Files to Modify

- `file 'AstroFinSentinelV5/orchestration/sentinel_v5.py'` — Phase 1, 2, KPI guard
- `file 'AstroFinSentinelV5/agents/karl_synthesis.py'` — Phase 2, 3, 4, 5, DecisionRecord
- `file 'AstroFinSentinelV5/core/backtest.py'` — get_recent_performance

---

## Next Steps

1. ✅ ATOM-KARL-015 APPROVED
2. ⬜ Подтвердить — какой файл открыть первым?
3. ⬜ Phase 1 implementation
4. ⬜ A/B test setup vs baseline
