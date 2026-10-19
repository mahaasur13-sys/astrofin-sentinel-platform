# План: запуск оркестратора + cycles + честная телеметрия

Цель: сделать так, чтобы панель Sentinel показывала **реальные** Cycles и Uptime
(а не демо «2,689» / «89.9h»), и чтобы оркестратор реально гонял 6 движков.

## Факты (проверено по коду)

- **«Цикл» = сессия оркестратора.** Отдельной таблицы `cycles` НЕТ. Есть:
  - SQLite `core/history.db` → таблица `sessions` (R-08, каждый `run_sentinel_v5()` пишет строку).
  - AMRE-слой `db/models.py` → `sessions`, `agent_signals`, `astro_positions`, `audit_log`, `agent_beliefs`, `decisions`.
- **Оркестратор** = `python -m orchestration.sentinel_v5 --once --mode paper` (CLI; без `--once` — daemon-цикл с `KARL_SYNC_INTERVAL`).
- **Рыночный фид**: цена берётся внутри через `_fetch_price` (CoinGecko), с жёстким фолбэком `$50,000` — это надо убрать/пометить.
- **Телеметрия**: Prometheus `/metrics` уже встроен (`_start_metrics_server()`), работает только в daemon-режиме.
- **БД**: Platform PG на `5432/astrofin` **не поднят**. ROMA PG на `5433/roma` поднят, но это execution/billing — cycles там нет.
- **Демо на лендинге**: `system.html:165` (`Uptime 89.9h`) и `:166` (`Cycles 2,689`).

---

## Этап 1 — Источник для «Cycles» (решение)

Рекомендую **вариант A**: `Cycles = COUNT(sessions)` из `core/history.db`.
- Плюс: ноль миграций, данные уже пишутся.
- Минус: поля decision/coherence лежат в JSON (`final_output`), а не отдельными колонками.

**Вариант B** (если нужны отдельные колонки): миграция таблицы `cycles`:

```sql
CREATE TABLE IF NOT EXISTS cycles (
    id            BIGSERIAL PRIMARY KEY,
    session_id    TEXT NOT NULL,
    symbol        TEXT NOT NULL DEFAULT 'BTCUSDT',
    started_at    TIMESTAMPTZ,
    finished_at   TIMESTAMPTZ,
    decision      TEXT,               -- BUY | HOLD | SELL
    coherence     DOUBLE PRECISION,   -- NULL если нет голосов
    entropy       DOUBLE PRECISION,
    pxq_edge_bps  DOUBLE PRECISION,
    gate_result   TEXT,               -- ok | blocked
    created_at    TIMESTAMPTZ DEFAULT now()
);
```

`coherence` остаётся `NULL`, когда движки idle (это честно — не выдумываем).

---

## Этап 2 — Поднять Platform PG (5432) — только если выбран B или нужен AMRE-слой

```bash
cd ~/Projects/astrofin-sentinel-platform
docker compose up -d postgres redis   # если есть docker-compose
# либо локально: создать БД astrofin, пользователь astrofin
```

Проверка:
```bash
pg_isready -h localhost -p 5432
psql "postgresql://astrofin:...@localhost:5432/astrofin" -c "SELECT 1"
```

Затем применить схему (`db/init.py` создаёт таблицы из `db/models.py`).

> Если выбран вариант A — этот этап можно пропустить (оркестратор пишет в SQLite).

---

## Этап 3 — Запустить оркестратор (один прогон)

```bash
cd ~/Projects/astrofin-sentinel-platform
source .venv/bin/activate
python -m orchestration.sentinel_v5 --once --mode paper --symbol BTCUSDT
```

Проверки после прогона:
```bash
# сессия записалась в history.db (таблица sessions +1)
ls -la core/history.db
# лог: "Session <id> completed: N signals"
```

Если CoinGecko недоступен — `_fetch_price` вернёт фолбэк. **Убрать нечестный фолбэк $50,000**:
в `orchestration/sentinel_v5.py` строки `current_price = current_price or 50000` → заменить на
`current_price = current_price or 0` + пометить «no live price».

---

## Этап 4 — Телеметрия Cycles / Uptime

Оркестратор уже отдаёт `/metrics` (Prometheus) в daemon-режиме. Добавить 2 метрики:

```python
# в sentinel_v5.py, после save_session():
from prometheus_client import Counter, Gauge
CYCLES = Counter("sentinel_cycles_total", "Total decision cycles run")
CYCLES.inc()
UPTIME = Gauge("sentinel_process_uptime_seconds", "Orchestrator uptime")
# UPTIME.set(time.monotonic() - START_TIME)
```

**Для лендинга** — маленький read-only sidecar (std-lib, без зависимостей), который отдаёт JSON:

```python
# telemetry.py — запускается рядом с оркестратором
# GET /telemetry -> {"cycles": N, "uptime_h": 89.9, "decision": "HOLD", "coherence": null}
# N = sqlite3 count(sessions) из core/history.db
```

(Либо лендинг читает напрямую `/metrics` — но парсить Prometheus-формат в JS тяжело; JSON-сайдкар проще.)

---

## Этап 5 — Лендинг: демо → реальные значения

`system.html:165-166` сейчас:
```html
<span class="meta-chip">Uptime: <b>89.9h</b> — pg:true 2.1.0 pool 2/10</span>
<span class="meta-chip">Cycles: <b>2,689</b> — Decision HOLD · Coherence — — 0 of 6 active — agents idle</span>
```

Заменить на подстановку из телеметрии:
```html
<span class="meta-chip">Uptime: <b id="tele-uptime">—</b> — pg:true 2.1.0 pool 2/10</span>
<span class="meta-chip">Cycles: <b id="tele-cycles">—</b> — Decision HOLD · Coherence — · 0 of 6 active</span>
```

Плюс JS (в конце body):
```js
fetch('http://127.0.0.1:PORT/telemetry')
  .then(r => r.json())
  .then(t => {
    document.getElementById('tele-cycles').textContent = t.cycles;
    document.getElementById('tele-uptime').textContent = t.uptime_h + 'h';
  })
  .catch(() => { /* оставить «—» — честно, если телеметрия недоступна */ });
```

Пока сайдкар не поднят — на лендинге будет честное `—` вместо демо `2,689`/`89.9h`.

---

## Этап 6 — Проверка

1. `python -m orchestration.sentinel_v5 --once` → `core/history.db` sessions +1.
2. `/metrics` (или `/telemetry`) отдаёт `sentinel_cycles_total` / `cycles`.
3. Лендинг после `Ctrl+Shift+R` показывает реальные Cycles и Uptime (или `—`).

---

## Риски / открытые вопросы

| Риск | Что сделать |
|---|---|
| CoinGecko rate-limit | `COINGECKO_DEMO_API_KEY` уже в tree A `.env`; или перейти на Binance public API |
| Фолбэк `$50,000` — нечестный | убрать (см. Этап 3) |
| AMRE PG (5432) не поднят | вариант A не требует PG; вариант B — поднять docker postgres |
| `coherence` всегда null при idle | это честно; не подставлять дефолт |
| Лендинг открыт через `file://` | `fetch` к `127.0.0.1` требует CORS на сайдкаре (`Access-Control-Allow-Origin: *`) |

## Порядок внедрения (минимальный путь)

1. Убрать фолбэк $50k → пометить «no live price».
2. Запустить `--once` → убедиться, что сессия пишется.
3. Поднять JSON-сайдкар `telemetry.py` (Cycles + Uptime из history.db).
4. В `system.html` заменить `2,689`/`89.9h` на `id="tele-*"` + fetch.
5. (Опционально) миграция `cycles` + PG 5432, если нужен вариант B.
