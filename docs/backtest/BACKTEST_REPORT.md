# Backtest Report — v1.0.0-beta (Sprint G-04)

**Дата:** 2026-07-26 | **Окно:** 2026-06-26 → 2026-07-26 (30 дней)
**Символ:** BTCUSDT | **Таймфрейм:** 1h

---

## Сводка

| Метрика | Значение | Цель | Статус |
|---------|----------|------|--------|
| **Всего сделок** | 617 | — | — |
| **Win Rate** | 42.0% (259W / 358L) | >50% | 🔴 |
| **Avg Win** | +1.10% | — | — |
| **Avg Loss** | −0.99% | — | — |
| **Total Return** | −12.2% | >0% | 🔴 |
| **Max Drawdown** | 21.9% | <15% | 🔴 |
| **Sharpe Ratio** | 0.01 | >1.0 | 🔴 |
| **Avg Confidence** | 87 | — | — |

---

## Анализ

1. **Win Rate ниже целевого** (42% vs 50%). Причина: bear market June–July 2026.
2. **Sharpe ~0** — стратегия не генерирует избыточной доходности на этом периоде.
3. **Max Drawdown 21.9%** — превышает целевой порог 15%.
4. **Высокий Avg Confidence (87)** при низком Win Rate — возможен overconfidence bias агентов.

---

## Рекомендации

- [ ] Проверить calibration confidence vs actual win rate
- [ ] Расширить окно до 90 дней для полной картины
- [ ] Добавить risk management stop-loss на уровне агента
- [ ] Интегрировать Meta-RL nightly training в backtest pipeline

---

## Команда запуска

```bash
cd /home/workspace
source .venv/bin/activate
python -c "
import asyncio
from backtest.engine import run_backtest
from datetime import date, timedelta
end = date.today().isoformat()
start = (date.today() - timedelta(days=90)).isoformat()
result = asyncio.run(run_backtest('BTCUSDT', start, end))
if result:
    print(result.summary())
"
```
