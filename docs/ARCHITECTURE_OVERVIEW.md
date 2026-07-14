# AstroFin Sentinel V5 — Архитектура системы

**Версия:** 1.0 | **Дата:** 2026-04-01 | **Статус:** Production-Beta

---

## 1. Общее описание

**AstroFin Sentinel V5** — интеллектуальная многоагентная система для анализа рынков и генерации торговых стратегий.

Система состоит из **двух частей**:
1. **Backend** (`AstroFinSentinelV5/`) — Python-код, который делает всю работу
2. **Frontend** (`astrofin-meta-rl/`) — React-дашборд для управления и мониторинга

**Что умеет:**
- 14 специализированных агентов анализируют рынок с разных точек зрения
- Meta-RL Engine автоматически генерирует, тестирует и улучшает торговые стратегии
- Генетическая эволюция (поколения стратегий)
- A/B тестирование лучших стратегий
- Визуальный мониторинг через дашборд

---

## 2. Архитектура системы

### Поток данных

```
Пользователь (Browser)
    ↓ http://127.0.0.1:5173 (Frontend React)
    ↓ HTTP REST
Flask API (wsgi.py)
    ↓ http://127.0.0.1:8050 (Backend)
    ↓
├── Agents x14 (анализ рынка)
├── Meta-RL Engine (эволюция стратегий)
├── Persistence (JSONL — сохранение сессий)
└── LiveData (CCXT — реальные данные)
```

### Компоненты

| Компонент | Порт | Задача |
|---|---|---|
| Frontend (React) | 5173 | Пользовательский интерфейс |
| Backend (Flask) | 8050 | REST API, оркестрация |
| Meta-RL Engine | — | Эволюция стратегий |
| Agents | — | Анализ рынка |
| LiveData (CCXT) | — | Реальные рыночные данные |

---

## 3. 14 агентов — веса и задачи

| # | Агент | Вес | Задача |
|---|---|---|---|
| 1 | FundamentalAgent | 20% | P/E, MVRV, revenue growth |
| 2 | QuantAgent | 20% | ML-модели, бэктестирование |
| 3 | MacroAgent | 15% | VIX, DXY, Fed rates |
| 4 | OptionsFlowAgent | 15% | Опционный поток, gamma exposure |
| 5 | SentimentAgent | 10% | Fear&Greed, Twitter, Reddit |
| 6 | TechnicalAgent | 10% | RSI, MACD, Bollinger (фильтр) |
| 7 | BullResearcher | 5% | Бычьи паттерны + астро-факторы |
| 8 | BearResearcher | 5% | Медвежьи паттерны + астро-факторы |
| 9 | CycleAgent | 5% | Циклы 20/40/80 дней |
| 10 | BradleyAgent | 3% | Сезонность S&P + планет.аспекты |
| 11 | ElectoralAgent | 3% | Muhurta timing (Choghadiya) |
| 12 | GannAgent | 3% | Углы Ганна, квадрат цены/времени |
| 13 | TimeWindowAgent | 2% | Окна 4H/1D/1W |
| 14 | RiskAgent | 5% | Position sizing, ATR, stop-loss |

**Итого: 100%** — SynthesisAgent объединяет все голоса в итоговый сигнал.

---

## 4. Meta-RL Engine — как работает

**Meta-RL** = Meta Learning + Reinforcement Learning + Генетический алгоритм.

Цикл:
1. **Генерация** — случайная популяция стратегий
2. **Оценка** — Backtester тестирует на исторических данных
3. **Отбор** — лучшие стратегии получают higher reward
4. **Скрещивание** — crossover между лучшими
5. **Мутация** — random variation
6. **KARL Update** — каждые 5 поколений
7. **Alpha Decay** — если reward падает 5 поколений = force reset

### Ключевые файлы

- `evolution.py` — главный цикл
- `meta_agent.py` — управление популяцией
- `strategy_evaluator.py` — Backtest → EvaluationResult
- `walkforward.py` — Walk-Forward Validation (проверка на overfitting)
- `ranking.py` — Composite ranking
- `ab_testing.py` — A/B тестирование
- `persistence.py` — сохранение сессий
- `live_data.py` — CCXT live/sandbox данные
- `config.py` — все feature flags
- `cli.py` — командная строка

---

## 5. Как запустить

```bash
# 1. Backend
cd AstroFinSentinelV5
python -m meta_rl.cli --gens 20 --pop 20

# 2. Дашборд (в другом терминале)
bash start-dashboard.sh start
```

**Endpoints:**
- Дашборд: http://127.0.0.1:5173
- API: http://127.0.0.1:8050
- Health: http://127.0.0.1:8050/api/health

---

## 6. Дашборд — вкладки

### Explorer
Просмотр всех сессий эволюции, ranking стратегий, сравнение по метрикам (Sharpe, WinRate, PnL).

### A/B Testing
Сравнение двух версий стратегий: statistical significance (Welch t-test), Cohen's d effect size.

### Live
Реальные данные с биржи (опционально, требует API-ключ).

---

## 7. Переход в live-режим

```bash
cp AstroFinSentinelV5/.env.example AstroFinSentinelV5/.env
# Заполнить .env:
# CCXT_API_KEY=your_key
# CCXT_API_SECRET=your_secret
# CCXT_SANDBOX_MODE=false
```

**Безопасность:** ключи НИКОГДА не коммитятся в git.
