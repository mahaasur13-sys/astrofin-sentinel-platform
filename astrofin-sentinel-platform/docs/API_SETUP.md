# AstroFin Sentinel API — Setup & Usage

## Быстрый старт

### 1. Установка зависимостей

```bash
cd astrofin-sentinel-platform
pip install -r requirements.txt
# или если используется uv:
uv pip install -r requirements.txt
```

### 2. Инициализация базы данных

```bash
# Создать таблицы (SQLite по умолчанию: db/astrofin.db)
python -m db.init
```

### 3. Запуск API сервера

```bash
# Вариант 1: через uvicorn напрямую
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Вариант 2: через Python модуль
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API будет доступен на `http://localhost:8000`

### 4. Проверка работоспособности

```bash
# Health check
curl http://localhost:8000/health

# Dashboard data
curl http://localhost:8000/api/v1/dashboard

# Sessions list
curl "http://localhost:8000/api/v1/sessions/?skip=0&limit=10"
```

## Эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/dashboard` | Полное состояние dashboard (агенты, режим, ансамбль) |
| `GET` | `/api/v1/sessions/` | Список сессий (пагинация: `?skip=0&limit=50`) |
| `GET` | `/api/v1/sessions/{id}/details` | Детали сессии + KARL решения |
| `POST` | `/api/v1/agent/run` | Запустить агент с LLM роутингом |
| `GET` | `/api/v1/astro/aspects` | Текущие астрологические аспекты |
| `GET` | `/api/v1/astro/interpretation` | Ведическая интерпретация для трейдеров |
| `WS` | `/ws/agent/{agent_id}` | WebSocket real-time стриминг агента |

## React Frontend Integration

API автоматически сервит production-билд React из `web-react/dist`:

```bash
# 1. Собрать фронтенд
cd web-react
npm install
npm run build

# 2. Запустить API (он подхватит dist/ автоматически)
cd ..
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Откройте `http://localhost:8000` в браузере — увидите React dashboard.

## Аутентификация (опционально)

По умолчанию `REQUIRE_AUTH=False` — API открыт без ключей. Для включения:

```bash
export REQUIRE_AUTH=true
export API_KEY=your_secret_key_here
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Запросы должны содержать заголовок:
```
X-API-Key: your_secret_key_here
```

## Troubleshooting

### Ошибка "No module named 'core'"

Убедитесь, что запускаете из корня проекта:
```bash
cd astrofin-sentinel-platform
python -m uvicorn api.main:app --reload
```

### БД не инициализирована

```bash
python -m db.init
```

### Порт 8000 занят

```bash
# Используйте другой порт
uvicorn api.main:app --port 8080
```
