# AstroFinSentinelV5 – Roadmap & Context Snapshot

**Дата:** 2026-06-24  
**Ветка:** master  
**Последний коммит:** `e4bbea4` (AstroFin: mock-адаптеры, регресс-тесты 9/9)

---

## 1. Статус компонентов

| Компонент | Готовность | Коммиты | Блокер |
|-----------|------------|---------|--------|
| **Hybrid Memory (graphify-out)** | ✅ 100% | `a421bc5` → `e1abe2f` → `2de2892` → `8ae5453` → `979a2c7` → `43b005e` | – |
| **AstroFinSentinelV5** | ✅ ~85% (mock-режим) | `e4bbea4` (mock-адаптеры, 9/9 тестов) | Ключи Polygon/UW |
| **pop-os-setup** | – пустышка | (только PROGRAMS.md) | Не требует доработок |
| **atom-federation-os** | ⏳ 60% | (отдельный подмодуль) | kind/k3s для живого тестирования |

---

## 2. Что уже работает (проверено)

- **MarketAdapter** – исправлен баг `self._cache` → `self._redis` (коммит `43b005e`).
  - Кэширование через Redis (если доступен), fallback на синтетику.
  - 6/6 регресс-тестов проходят.
- **Mock-источники данных** (Polygon / Unusual Whales):
  - `polygon` – детерминированный seeded-источник (опционные цепочки, бары).
  - `uw` – options-flow-like mock с реалистичной структурой.
  - 9/9 тестов зелёные (shape/invariants/fallback).
- **Бэктест** – работает в mock-режиме:
  - 89 прогонов, **Sharpe = 2.59** (на синтетике).
  - Поддерживает sanity-check, execution cost, метрики (PnL, win-rate, max DD).
- **Telegram-алерты** – уже есть через `alerts.py` (TelegramAlerter), отключены по флагу (нет токена).

---

## 3. Внешние блокеры (для перехода в live)

| Что нужно | Где | Статус |
|-----------|-----|--------|
| **Polygon API key** | `POLYGON_API_KEY` в `.env` | ❌ отсутствует |
| **Unusual Whales API key** | `UNUSUAL_WHALES_API_KEY` в `.env` | ❌ отсутствует |
| **Telegram Bot Token** | `TELEGRAM_BOT_TOKEN` в `.env` | ❌ отсутствует (опционально) |
| **Kind/k3s** (для atom-federation) | локальный кластер | ❌ не поднят |

Без ключей все внешние источники работают в **mock-режиме**. Это ожидаемое поведение, а не баг.

---

## 4. Как воспроизвести тесты (локально)

```bash
# Убедиться, что зависимости установлены
pip install -r requirements.txt

# Прогнать все тесты (9/9 должны быть зелёными)
pytest tests/ -v

# Запустить бэктест (7 дней синтетики)
python -m backtest.run_backtest --mode mock --days 7

# Проверить MarketAdapter вручную
python -c "from data.market_adapter import MarketAdapter; ma=MarketAdapter(); print(ma.fetch_ohlcv('BTC/USDT', '1h', limit=5))"
```

## 5. Следующие шаги (после появления ключей/кластера)

### Для AstroFinSentinelV5 (приоритет)
1. Вставить ключи в `.env` (уже есть `.env.example`).
2. Переключить `MODE=mock` → `MODE=live` (одна строка в конфиге).
3. Перезапустить бэктест – сравнить метрики с mock-режимом.
4. Если всё хорошо – включить Telegram-алерты (`TELEGRAM_ALERTS_ENABLED=true`).

### Для atom-federation-os
1. Поднять локальный кластер (kind/k3s).
2. Задеплоить AtomCluster CRD.
3. Прогнать Chaos / Failure Replay тесты.
4. Проверить phase2 orchestration.

---

## 6. Полезные ссылки (внутренние)

- `docs/adr/ADR-0004-override-mechanism.md` – контракт cross-file override.
- `docs/adr/ADR-0005-relation-weights.md` – калибровка весов.
- `docs/adr/ADR-0006-recall-formula-ab.md` – A/B-выбор формулы.
- `docs/adr/ADR-0007-override-aware-tie-break.md` – сортировка для override.

---

## 7. Контакты / авторство

- **Репозиторий:** `mahaasur13-sys/astrofin-sentinel-platform`
- **Текущий мейнтейнер:** (ваше имя)
- **Следующий сеанс** – по появлению ключей или кластера.
