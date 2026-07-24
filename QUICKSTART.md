# 🚀 AstroFin Sentinel — Quick Start

Быстрый запуск полного стека (React Frontend + FastAPI Backend).

## Предварительные требования

- Python 3.10+
- Node.js 18+ (для фронтенда)
- Git

## Установка и запуск

### 1. Клонирование репозитория (если еще не сделано)

```bash
git clone https://github.com/mahaasur13-sys/astrofin-sentinel-platform.git
cd astrofin-sentinel-platform/astrofin-sentinel-platform
```

### 2. Backend Setup

```bash
# Установка Python зависимостей
pip install fastapi uvicorn sqlalchemy pydantic python-dateutil swisseph

# Инициализация базы данных
python -m db.init

# Запуск API сервера
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

API запустится на `http://localhost:8000`

**Проверка:**
```bash
curl http://localhost:8000/health
# Ожидается: {"status":"ok","version":"0.4.0"}

curl http://localhost:8000/api/v1/dashboard
# Ожидается: JSON с agents[], regime, ensemble
```

### 3. Frontend Setup

Откройте **новый терминал**:

```bash
cd web-react

# Установка зависимостей
npm install

# Development server (с hot reload)
npm run dev
```

Frontend запустится на `http://localhost:5173`

**Или production build:**

```bash
npm run build
# Собранный build будет в web-react/dist/
# API автоматически сервит его на http://localhost:8000
```

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (web-react/)                                    │
│  • Dashboard, SessionTable, ContextDrawer                       │
│  • Redux Toolkit + RTK Query                                    │
│  • MUI components                                               │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTP REST API
                 │ /api/v1/dashboard, /api/v1/sessions, etc.
┌────────────────▼────────────────────────────────────────────────┐
│  FastAPI Backend (api/)                                         │
│  • Routes: dashboard, sessions, astro, agent                    │
│  • Models & DB: SQLite (db/astrofin.db)                         │
│  • Core agents: Gann, Bradley, Elliot                           │
└─────────────────────────────────────────────────────────────────┘
```

## Основные эндпоинты

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/v1/dashboard` | Полное состояние dashboard |
| `GET` | `/api/v1/sessions/` | Список сессий (пагинация) |
| `GET` | `/api/v1/sessions/{id}/details` | Детали сессии + KARL решения |
| `POST` | `/api/v1/agent/run` | Запуск агента с LLM роутингом |
| `GET` | `/api/v1/astro/aspects` | Текущие астрологические аспекты |

Полная документация: [docs/API_SETUP.md](docs/API_SETUP.md)

## Структура проекта

```
astrofin-sentinel-platform/
├── api/                    # FastAPI backend
│   ├── main.py            # Главный файл API
│   ├── routes/
│   │   └── sessions.py    # Эндпоинты сессий
│   └── schemas.py         # Pydantic модели
├── web-react/             # React frontend
│   ├── src/
│   │   ├── App.tsx        # Главный компонент dashboard
│   │   ├── components/    # UI компоненты
│   │   ├── api/           # RTK Query API
│   │   └── store/         # Redux store
│   └── dist/              # Production build (после npm run build)
├── db/                    # Database & models
│   ├── models.py          # SQLAlchemy models
│   └── init.py            # DB initialization
├── agents/                # Trading agents
│   └── _impl/             # Agent implementations
├── core/                  # Core business logic
└── docs/                  # Documentation
```

## Troubleshooting

### Backend: "No module named 'fastapi'"

```bash
pip install -r requirements.txt
# или
pip install fastapi uvicorn sqlalchemy pydantic
```

### Backend: "No module named 'core'"

Убедитесь, что запускаете из корня `astrofin-sentinel-platform/`:
```bash
cd astrofin-sentinel-platform/astrofin-sentinel-platform
python -m uvicorn api.main:app
```

### Frontend: "Failed to connect: HTTP 404"

1. Проверьте, что backend запущен на порту 8000
2. Проверьте `web-react/vite.config.ts` — proxy должен указывать на `http://localhost:8000`

### Database: "Table does not exist"

```bash
python -m db.init
```

## Следующие шаги

После успешного запуска:

1. **Dashboard** — откройте `http://localhost:5173` (dev) или `http://localhost:8000` (production)
2. **API Docs** — откройте `http://localhost:8000/docs` (Swagger UI)
3. **Создайте первую сессию** — используйте POST `/api/v1/agent/run`

---

**Проект:** AstroFin Sentinel — Multi-agent trading system with KARL, AMRE, Astro Council  
**Автор:** mahaasur13-sys  
**Репозиторий:** [github.com/mahaasur13-sys/astrofin-sentinel-platform](https://github.com/mahaasur13-sys/astrofin-sentinel-platform)
