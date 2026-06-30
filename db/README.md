# AstroFin Sentinel V5 — Database Layer

**Атом:** ATOM-DB-MIGRATION-002 (P0)
**Статус:** ✅ PostgreSQL + TimescaleDB + pgvector + Docker + CI/CD полностью готовы

---

## Быстрый старт

### 1. Копировать env-файл

```bash
cp .env.db.example .env
# Заполнить POSTGRES_PASSWORD в .env
```

### 2. Поднять инфраструктуру

```bash
docker-compose up -d postgres redis

# Проверить статус
docker-compose ps
```

### 3. Инициализировать схему

```bash
cd AstroFinSentinelV5

# Автоматически (при импорте db/)
python3 -c "from db import init_db_if_needed; print(init_db_if_needed())"

# Или через CLI
python3 -m db.init --status
python3 -m db.init              # init schema
python3 -m db.init --migrate   # миграция из SQLite
```

### 4. Запустить приложение

```bash
python3 -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING
```

---

## Архитектура

```
┌──────────────────────────────────────────────────────┐
│                   Application                          │
│  sentinel_v5 | karl_synthesis | backtest_loop | ...   │
└──────────────────────┬───────────────────────────────┘
                       │ db/repositories
           ┌───────────┴───────────┐
           │                       │
    ┌──────▼──────┐        ┌───────▼──────┐
    │ PostgreSQL   │        │   SQLite      │
    │ + TimescaleDB│        │  (fallback)   │
    │ + pgvector   │        │               │
    └──────────────┘        └───────────────┘
```

**Fallback:** Если PostgreSQL недоступен → автоматически переключается на SQLite. Конфигурируется через `DB_BACKEND=sqlite`.

---

## Файлы

```
db/
├── __init__.py          — exports
├── __main__.py          — CLI: python -m db.init
├── session.py           — Connection pooling + retry + SQLite fallback
├── models.py            — 22 SQLAlchemy моделей
├── repositories.py      — CRUD для всех сущностей
├── init.py             — Auto-init, TimescaleDB setup
├── migrate_from_sqlite.py — миграция из SQLite
├── karl_replay.py      — KARL trajectory replay buffer
└── README.md           — этот файл

schema/
├── 001_initial.sql     — Полная схема (PostgreSQL + TimescaleDB)
└── init-timescale.sql  — Init script для docker-entrypoint-initdb.d
```

---

## Volume mounts (docker-compose)

| Mount | Описание |
|-------|----------|
| `postgres_data:/var/lib/postgresql/data` | Персистентные данные |
| `./schema:/docker-entrypoint-initdb.d:ro` | Автоматическое применение схемы при первом старте |

---

## Команды Docker Compose

```bash
# Поднять все сервисы
docker-compose up -d

# Проверить логи
docker-compose logs -f postgres

# Проверить health
docker-compose ps

# Остановить
docker-compose down

# Остановить с удалением данных
docker-compose down -v

# Пересоздать (после изменения схемы)
docker-compose up -d --force-recreate postgres
```

---

## Переменные окружения

```bash
# Database backend: postgresql | sqlite (default: postgresql)
DB_BACKEND=postgresql

# PostgreSQL
POSTGRES_USER=astrofin
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=astrofin
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# SQL echo (for debugging)
SQL_ECHO=1
```

---

## Таблицы

| Таблица | Тип | Описание |
|---------|-----|----------|
| `sessions` | Hypertable | Trading sessions |
| `agent_signals` | Hypertable | Agent outputs |
| `karl_decision_records` | Hypertable | All KARL decisions |
| `karl_trajectories` | Regular | KARL replay buffer |
| `karl_trajectory_steps` | Regular | Trajectory steps |
| `agent_beliefs` | Regular | Thompson sampling |
| `agent_selection_log` | Hypertable | Agent selection log |
| `astro_positions` | Regular | Planetary positions |
| `rag_embeddings` | Regular + HNSW | Vector embeddings |
| `audit_log` | Hypertable | Immutable audit |
| `backtest_runs` | Regular | Backtest results |

**TimescaleDB:** retention policy 90 дней, compression включён.

---

## Миграция из SQLite

```bash
# Миграция всех данных
python3 -m db.init --migrate

# Idempotent — безопасно запускать несколько раз
```

Безопасность: существующие записи пропускаются (upsert по UUID).

---

## CI/CD

```yaml
# .github/workflows/ci.yml
jobs:
  test-sqlite:  # fast, every PR
  test-postgres: # full integration, PostgreSQL + TimescaleDB
```

PostgreSQL в CI:
- `services: postgres` — TimescaleDB latest-pg16
- `services: redis` — Redis 7-alpine
- Healthcheck перед тестами
- Init schema перед запуском
- tmpfs для скорости

---

## Troubleshooting

### PostgreSQL connection refused

```bash
# Проверить, запущен ли контейнер
docker-compose ps postgres

# Посмотреть логи
docker-compose logs postgres

# Пересоздать
docker-compose rm -sf postgres && docker-compose up -d postgres
```

### TimescaleDB extension not found

```bash
# Подключиться и проверить
docker-compose exec postgres psql -U astrofin -d astrofin -c "SELECT extname FROM pg_extension;"
```

### SQLite fallback active

Если `DB_BACKEND` не задан и PostgreSQL недоступен — используется SQLite. Это нормально для разработки.

### Сброс схемы

```bash
python3 -m db.init --reset
# или с подтверждением
python3 -m db.init --reset --force
```
