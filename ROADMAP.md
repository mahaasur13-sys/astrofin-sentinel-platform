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
# AstroFin Sentinel Platform — Roadmap (2026-07-21)

## ✅ Completed Milestones

| Phase | Description | PR/Commit | Delta |
|-------|------------|-----------|-------|
| **P0** | Security + Architecture fixes (SEC-01, SEC-02, ARCH-01) | `ff8f35d` | 5 роутов под auth, убран hardcoded ключ |
| **P1** | Dead code removal + deduplication | `9e18977` | −472 файла, −70 823 строки |
| **P2** | Code quality + Ruff 0 errors | `5b2565c` | 13→0 ruff, структурированы deps |
| **P3** | Infrastructure hardening | `e1133bb` | 6 healthchecks, pre-commit, documentation |
| **4.8a** | Architecture Linter R3.5/R7/R10/R12 | `26a28af` | 4→8 правил |
| **4.8b** | Production RAG Index | `3dab21b` | 0→1981 чанков, FAISS+BM25+RRF |
| **4.8c** | PostgreSQL Dual-Engine | `67290ad` | DatabaseManager, pgvector, TimescaleDB |

---

## 🟢 Phase 5: Activation & Observability (Next ~2-3 days)

| ID | Task | EST | Priority |
|----|------|-----|----------|
| 5.1 | Activate PostgreSQL — set DATABASE_URL on production | 2h | P0 |
| 5.2 | Dual-write period — monitor 14 days, then disable SQLite | 14d | P0 |
| 5.3 | RAG integration in BaseAgent.generate() | 4h | P1 |
| 5.4 | Dash dashboard → React migration | 8h | P2 |
| 5.5 | Prometheus + Grafana dashboards | 4h | P2 |

## 🟡 Phase 6: Quality & Hardening (~3-5 days)

| ID | Task | EST | Priority |
|----|------|-----|----------|
| 6.1 | Coverage 80%+ for new modules (RAG, DB Manager) | 8h | P1 |
| 6.2 | Performance baseline — RAG <100ms, DB <50ms | 4h | P1 |
| 6.3 | Chaos testing — kill PG, verify SQLite fallback | 2h | P2 |
| 6.4 | Security audit — CodeRabbit + bandit clean | 2h | P2 |

## 🟣 Phase 7: ML & Trading Enhancements (~1-2 weeks)

| ID | Task | EST | Priority |
|----|------|-----|----------|
| 7.1 | HMM Regime Detector — production-ready | 8h | P1 |
| 7.2 | Meta-RL training loop — AB testing framework | 12h | P2 |
| 7.3 | AMRE backtest pipeline — full historical | 8h | P2 |
| 7.4 | Council Orchestrator wireup — multi-agent debate | 6h | P1 |
