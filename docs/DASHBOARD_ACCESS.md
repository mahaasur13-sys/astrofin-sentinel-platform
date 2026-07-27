# Dashboard Access Guide (v1.0.0-rc)

> **Freeze-compliant** — documentation only. No production code changes.  
> **Last updated:** 2026-07-27

---

## Quick Start

```bash
python scripts/start-dashboard.py
```

Opens FastAPI (port 8000) + Dash (port 8050) on `127.0.0.1`.

---

## Service URLs

### Local Access (рекомендуется)

| Сервис | URL | Авторизация | Примечание |
|--------|-----|-------------|------------|
| **FastAPI — Swagger** | `http://127.0.0.1:8000/docs` | API Key (`X-API-Key` header) | Интерактивная документация |
| **FastAPI — ReDoc** | `http://127.0.0.1:8000/redoc` | API Key | Альтернативный формат |
| **Health Check** | `http://127.0.0.1:8000/health` | Нет | Проверка работоспособности |
| **Metrics** | `http://127.0.0.1:8000/metrics` | Нет | Prometheus-совместимые метрики |
| **Dash Dashboard** | `http://127.0.0.1:8050` | Session | Интерактивная аналитика |
| **React Frontend** | `http://127.0.0.1:5173` | Нет | Vite dev server |
| **Grafana** | `http://127.0.0.1:3000` | admin/admin | Мониторинг (если поднят) |
| **PostgreSQL** | `127.0.0.1:5432` | SCRAM-SHA-256 | База данных |

### Устаревшие (deprecated в v1.0.0, удалены в v1.1.0)

| Сервис | URL | Статус |
|--------|-----|--------|
| Flask WSGI | `http://127.0.0.1:5000` | Deprecated — заменён на FastAPI |

---

## Remote Access (SSH Tunnel)

Для удалённого доступа используйте SSH-туннель — **не открывайте порты наружу**.

```bash
# Туннелируем оба порта
ssh -L 8000:localhost:8000 -L 8050:localhost:8050 user@ваш-сервер

# Только API
ssh -L 8000:localhost:8000 user@ваш-сервер

# С Grafana
ssh -L 8000:localhost:8000 -L 3000:localhost:3000 user@ваш-сервер
```

После этого открывай в браузере:

```
http://localhost:8000/docs     ← FastAPI Swagger
http://localhost:8050           ← Dash Dashboard
http://localhost:3000           ← Grafana (если поднят)
```

---

## Правила безопасности (v1.0.0)

| Правило | Статус |
|---------|--------|
| Все сервисы на `127.0.0.1` | ✅ Применено в `scripts/start-dashboard.py` |
| `AUTH_MODE=api_key` | ✅ В `.env.example` |
| `REQUIRE_AUTH=true` | ✅ В `.env.example` |
| API-ключи через `X-API-Key` header | ✅ |
| PostgreSQL — только локальные подключения | ✅ SCRAM-SHA-256 |
| Не коммитить реальные `.env` | ✅ Добавлено в `.gitignore` |

---

## Известные проблемы (Known Issues)

### KI-2026-07-27-01: 0.0.0.0 в production-коде

**Затронутые файлы:**

| Файл | Строка | Содержимое | Severity |
|------|--------|------------|----------|
| `web/app.py` | 266 | `host="0.0.0.0"  # nosec B104 — dev dashboard` | **MEDIUM** |
| `web/wsgi.py` | 166 | `host="0.0.0.0", port=8000, debug=False` | **MEDIUM** |
| `web/app.py` | 14 | `gunicorn -w 4 -b 0.0.0.0:8050` (comment) | LOW |
| `web/app.py` | 223 | Log message `http://0.0.0.0:{PORT}` | LOW |

**Риск:** При запуске без `--host 127.0.0.1` дашборд слушает все интерфейсы.

**Митигация:** Используйте `--host 127.0.0.1` при запуске. Исправление запланировано на v1.1.0.

**Workaround (немедленный):**

```bash
# Вместо прямого запуска:
python -m web.app
# Используйте:
python scripts/start-dashboard.py --host 127.0.0.1
```

---

## Environment Variables

Файл `.env.example` содержит все необходимые переменные. Секция доступа:

```bash
# ─── Dashboard Access ─────────────────────────────────
WEB_PORT=8050                  # Dash dashboard port
API_PORT=8000                  # FastAPI port
DASH_HOST=127.0.0.1           # Bind address (NEVER 0.0.0.0 in production)
AUTH_MODE=api_key              # api_key | none
REQUIRE_AUTH=true              # Enable auth on protected routes
API_KEY=your_api_key_here      # Set your actual key in .env (NOT committed)
```

---

## Troubleshooting

### Порт занят

```bash
# Найти процесс на порту
lsof -ti:8050   # Dash
lsof -ti:8000   # FastAPI

# Убить
kill $(lsof -t -i:8050)
```

### Дашборд не открывается

```bash
# Проверить статус
python tools/healthcheck.py

# Проверить PostgreSQL
pg_isready

# Проверить процессы
ps aux | grep -E "uvicorn|dash|gunicorn"
```

### API Key не работает

```bash
# Проверить .env
grep API_KEY .env

# Проверить без авторизации (health endpoint)
curl http://127.0.0.1:8000/health
```

---

## Changelog

| Дата | Изменение |
|------|-----------|
| 2026-07-27 | Initial release. Documented 0.0.0.0 as KI-2026-07-27-01. Added start script. |

---

## Grafana (Мониторинг)

**URL:** http://127.0.0.1:3000  
**Логин:** `admin`  
**Пароль:** `admin` (**сменить после первого входа!**)  
**Статус:** Local only (127.0.0.1) ✅ Запущен  
**Binary:** `/opt/stack/grafana/bin/grafana-server`  
**Log:** `/dev/shm/grafana.log`

### Запуск

```bash
cd /opt/stack/grafana
nohup ./bin/grafana-server --config=conf/defaults.ini --homepath=/opt/stack/grafana web \
  > /dev/shm/grafana.log 2>&1 &
```

### Проверка

```bash
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:3000/
# → 302 (redirect to /login)
```

### SSH-туннель

```bash
ssh -L 3000:localhost:3000 user@ваш-сервер
```

