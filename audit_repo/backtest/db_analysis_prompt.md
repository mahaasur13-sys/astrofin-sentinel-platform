# AstroFin Sentinel V5 — Deep Database Research Prompt

## 🎯 Цель

Провести **полное исследование** всех баз данных AstroFin Sentinel V5 и сформулировать **конкретные actionable рекомендации** для улучшения системы.

---

## 📊 Структура данных

### Базы и их назначение

| База | Таблицы | Назначение |
|------|---------|-----------|
| `core/history.db` | `sessions` (71), `sessions` дубликат | Все сессии оркестратора |
| `core/belief.db` | `agent_beliefs`, `agent_belief_history`, `agent_selection_log` | Thompson Sampling Beta-распределения |
| `backtest/metrics_history.db` | `backtest_runs` (12) | Результаты бэктестов |
| `core/code_io.db` | ? | ? (нужно исследовать) |

---

## 🔬 Задачи исследования

### 1. АНАЛИЗ СИГНАЛОВ (Signal Distribution)

```sql
-- Распределение всех финальных сигналов
SELECT final_signal,
       COUNT(*) as count,
       AVG(final_confidence) as avg_conf,
       MIN(final_confidence) as min_conf,
       MAX(final_confidence) as max_conf
FROM sessions
GROUP BY final_signal
ORDER BY count DESC;
```

**Исследовать:**
- Почему 100% сессий = NEUTRAL 50? (Это аномалия!)
- Какой % BUY/SELL vs NEUTRAL?
- Есть ли AVOID сигналы?

### 2. THOMPSON SAMPLING ЭФФЕКТИВНОСТЬ

```sql
-- Текущие Beta-распределения
SELECT agent_name, alpha, beta,
       ROUND(alpha / (alpha + beta), 3) as mean_accuracy,
       alpha + beta - 2 as total_trials
FROM agent_beliefs
ORDER BY mean_accuracy DESC;

-- История обновлений убеждений
SELECT agent_name, is_success, COUNT(*) as count
FROM agent_belief_history
GROUP BY agent_name, is_success;
```

**Исследовать:**
- Сколько агентов отслеживается?
- Какой агент "горячий" (high α), какой "холодный" (low α)?
- Правильно ли обновляются Beta-распределения?
- Есть ли агенты с α = β = 1 (неизученные)?

### 3. АНАЛИЗ АГЕНТНЫХ СИГНАЛОВ

```sql
-- Извлечь сигналы из final_output JSON
-- Для каждой сессии показать: какие агенты дали какой сигнал
```

**Исследовать:**
- Какие агенты дают BUY/SELL а какие NEUTRAL?
- Есть ли корреляция между агентами?
- Какой агент самый "бычий" / "медвежий"?

### 4. ВРЕМЕННОЙ АНАЛИЗ

```sql
-- Сессии по дням
SELECT DATE(created_at) as day,
       COUNT(*) as sessions,
       AVG(final_confidence) as avg_conf,
       SUM(CASE WHEN final_signal IN ('BUY','LONG','STRONG_BUY') THEN 1 ELSE 0 END) as bullish,
       SUM(CASE WHEN final_signal IN ('SELL','SHORT','STRONG_SELL') THEN 1 ELSE 0 END) as bearish
FROM sessions
GROUP BY day
ORDER BY day DESC
LIMIT 30;
```

**Исследовать:**
- Есть ли тренд во времени (улучшение/ухудшение)?
- Лучший и худший дни?
- Сезонность?

### 5. SYMBOL / TIMEFRAME АНАЛИЗ

```sql
-- Распределение по символам
SELECT symbol, timeframe, COUNT(*) as sessions,
       AVG(final_confidence) as avg_conf
FROM sessions
GROUP BY symbol, timeframe
ORDER BY sessions DESC;
```

### 6. BACKTEST PERFORMANCE

```sql
-- Сводка по бэктестам
SELECT symbol, timeframe,
       COUNT(*) as runs,
       AVG(win_rate) as avg_wr,
       AVG(sharpe_ratio) as avg_sr,
       SUM(total_trades) as total_trades,
       AVG(max_drawdown_pct) as avg_mdd,
       MAX(total_return_pct) as best_return,
       MIN(total_return_pct) as worst_return
FROM backtest_runs
GROUP BY symbol, timeframe;
```

**Исследовать:**
- Какой timeframe лучше работает?
- Средний win rate > 50%?
- Максимальная просадка приемлема?

### 7. VOLATILITY REGIME АНАЛИЗ

```sql
-- Извлечь regime из final_output JSON
-- Regime: LOW / NORMAL / HIGH / EXTREME
```

**Исследовать:**
- Как regime влияет на accuracy?
- Система правильно определяет EXTREME?

### 8. ASTROCOUNCIL АНАЛИЗ

```sql
-- Извлечь AstroCouncil сигналы из final_output
-- BradleyAgent, GannAgent, CycleAgent, ElectoralAgent
```

**Исследовать:**
- Как часто Astro согласуется с Fund+Quant?
- Эффективен ли конфликт-резолвинг (Astro -30%)?

### 9. KARL AMRE МЕТРИКИ

```sql
-- Есть ли таблицы для AuditLog, OAP, Calibration?
-- Нужно проверить все базы на наличие этих данных
```

### 10. DATA QUALITY

**Проверить:**
- Битый JSON в final_output / thompson_selections
- Missing values
- Дубликаты session_id
- Некорректные confidence (0 или >100)

---

## 📋 ВЫХОДНОЙ ФОРМАТ

Вернуть как **Markdown отчёт**:

```markdown
# 📊 AstroFin Sentinel V5 — Database Research Report

## Executive Summary
- Дата анализа
- Всего сессий: N
- В среднем: win_rate=X%, sharpe=Y, return=Z%

## 1. Signal Distribution
[ТАБЛИЦА + ВИЗУАЛИЗАЦИЯ]

## 2. Agent Performance
[ТАБЛИЦА Beta-распределений]

## 3. Temporal Analysis
[ГРАФИК сессий по дням]

...

## 🚨 Critical Issues Found
- Issue 1: [описание]
- Issue 2: [описание]

## ✅ Recommendations
1. [Конкретная рекомендация с обоснованием]
2. [Конкретная рекомендация с обоснованием]
```

---

## 🔧 Полезные SQL-запросы для копирования

```sql
-- Все сессии с деталями
SELECT session_id, symbol, timeframe, final_signal, final_confidence, created_at
FROM sessions ORDER BY created_at DESC LIMIT 20;

-- Агентные убеждения
SELECT * FROM agent_beliefs;

-- История убеждений
SELECT * FROM agent_belief_history ORDER BY created_at DESC LIMIT 20;

-- Бэктесты
SELECT * FROM backtest_runs ORDER BY created_at DESC;

-- Thompson selection log
SELECT * FROM agent_selection_log LIMIT 20;

-- Проверка целостности JSON
SELECT session_id, final_signal,
       substr(final_output, 1, 100) as output_preview
FROM sessions WHERE final_output IS NOT NULL LIMIT 5;
```

---

## 🎯 Ключевые вопросы для ответа

1. **Почему 100% NEUTRAL?** Это баг в данных или в агентах?
2. **Какие агенты реально работают?** Thompson selection coverage
3. **Какой timeframe работает лучше?** INTRADAY vs SWING vs POSITIONAL
4. **Есть ли систематический bias?** Всегда BUY или всегда SELL?
5. **Как улучшить accuracy?** Конкретные действия
