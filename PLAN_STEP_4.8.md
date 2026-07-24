# Step 4.8+ Plan — RAG Index, Architecture Linter, PostgreSQL Migration

**Дата:** 2026-07-21
**База:** `feature/architecture-consolidation` (после merge в master)
**Статус:** План — ожидает подтверждения

---

## Executive Summary

После завершения P0–P3 консолидации (PR #245), проект готов к трём ключевым улучшениям:
1. **R3.5/R7–R12** — расширение архитектурного линтера до полного набора правил SOUL.md
2. **RAG Index** — построение production-ready индекса (FAISS/Chroma) для агентов
3. **PostgreSQL Migration** — миграция с SQLite на PostgreSQL + TimescaleDB + pgvector

---

## Фаза 4.8a: Architecture Linter R3.5, R7–R12 (EST: 4–6h)

### R3.5: Import Path Validation
Дополнить `scripts/architecture_linter.py` проверкой, что все импорты агентов идут из `agents/_impl/`, а не из `agents/` (архивных дублей).

```python
# Новая проверка: no imports from agents/*.py (archived duplicates)
for file in agent_files:
    if "from agents." in content and "from agents._impl" not in content:
        violations.append(...)
```

### R7: KARL Synthesis — Single Arbitration Point
Проверить, что ни один агент не вызывает синтез напрямую — только через `orchestration/sentinel_v5.py`.

### R8: Decision Audit Trail
Проверить наличие `audit_log.record()` в каждом пути принятия решений.

### R9: Pre-commit Hooks
Валидировать, что `scripts/validate_agent.py` вызывается для каждого агента.

### R10: Secrets
Проверить отсутствие хардкод-ключей через bandit + detect-secrets.

### R11: Coverage
Проверить `pytest-cov` порог для новых агентов (100% unit + 1 integration).

### R12: Submodule Ban
Проверить отсутствие `.gitmodules` и submodule references (mode 160000).

---

## Фаза 4.8b: Production RAG Index (EST: 6–8h)

### Текущее состояние
- `knowledge/rag_index.py` — прототип с sentence-transformers
- Индекс инициализируется лениво при первом `generate()`
- Тестовые документы по финансовой отчётности

### Задачи
| ID | Задача | Приоритет |
|----|--------|-----------|
| RAG-01 | Заменить sentence-transformers на `intfloat/multilingual-e5-large` (лучше для русского/английского) | P1 |
| RAG-02 | Создать пайплайн индексации: `docs/` + `knowledge/chunks/` → FAISS | P1 |
| RAG-03 | Интегрировать RAG во всех агентов через `BaseAgent.generate()` | P0 |
| RAG-04 | Добавить `knowledge/rebuild_index.py` — CLI для перестроения индекса | P2 |
| RAG-05 | Валидация качества retrieval: precision@k, recall@k | P2 |
| RAG-06 | Поддержка гибридного поиска (BM25 + dense embeddings) | P3 |

### Контракт
```python
# knowledge/rag_index.py
class RAGIndex:
    def retrieve(self, query: str, top_k: int = 5) -> list[Chunk]:
        """Возвращает релевантные чанки для запроса."""
    
    def rebuild(self, documents: list[Document]) -> None:
        """Полное перестроение индекса."""
    
    def add(self, documents: list[Document]) -> None:
        """Инкрементальное добавление документов."""
```

---

## Фаза 4.8c: PostgreSQL + TimescaleDB + pgvector Migration (EST: 8–12h)

### Текущее состояние
- `core/history_db.py` — SQLite (файловая БД)
- `db/session.py` — PostgreSQL session management (уже реализован, но не активирован)
- `db/models.py` — SQLAlchemy модели
- `db/repositories.py` — репозитории
- `db/migrate_from_sqlite.py` — мигратор

### Задачи
| ID | Задача | Приоритет |
|----|--------|-----------|
| DB-01 | Активировать PostgreSQL через `db/session.py` как default engine | P0 |
| DB-02 | Создать Alembic миграции для всех таблиц | P0 |
| DB-03 | Мигрировать исторические данные: SQLite → PostgreSQL (`db/migrate_from_sqlite.py`) | P1 |
| DB-04 | Добавить pgvector extension для RAG embeddings | P1 |
| DB-05 | Настроить TimescaleDB для metrics time-series | P2 |
| DB-06 | Dual-write период: SQLite + PostgreSQL → отключить SQLite | P1 |
| DB-07 | Обновить docker-compose: PostgreSQL как основной сервис | P0 |
| DB-08 | Healthcheck с fallback (PG → SQLite) | P2 |

### Схема (ключевые таблицы)
```sql
-- sessions
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    symbol VARCHAR(20),
    signal VARCHAR(20),
    confidence FLOAT,
    metadata JSONB
);

-- decisions (audit trail — R-08)
CREATE TABLE decisions (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES sessions(id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    agent_name VARCHAR(100),
    signal VARCHAR(20),
    confidence FLOAT,
    reasoning TEXT,
    state_hash VARCHAR(64),
    metadata JSONB
);

-- embeddings (pgvector — RAG)
CREATE TABLE embeddings (
    id UUID PRIMARY KEY,
    chunk_id VARCHAR(255),
    embedding VECTOR(1024),
    metadata JSONB
);
```

---

## Порядок выполнения

```
master (после merge PR #245)
  └── feature/step-4.8-rag-linter-migration
       ├── 4.8a: R3.5–R12 linter rules (1 PR, 4–6h)
       ├── 4.8b: RAG index production (1 PR, 6–8h)
       └── 4.8c: PostgreSQL migration (1-2 PR, 8–12h)
```

---

## Метрики успеха

- [ ] Architecture linter: 12/12 rules enforced (hard-fail в CI)
- [ ] RAG: precision@5 ≥ 0.7 на тестовом наборе
- [ ] PostgreSQL: все тесты проходят с `DATABASE_URL=postgresql://...`
- [ ] 0 SQLite references в production-коде (кроме fallback в healthcheck)
- [ ] Docker-compose: PostgreSQL healthcheck → healthy

---

## Риски

| Риск | Mitigation |
|------|------------|
| Миграция данных сломает продакшен | Dual-write период (SQLite + PG) 2 недели |
| pgvector несовместим с текущими эмбеддингами | Сохранить faiss как fallback |
| RAG-index перегружает агентов latency | Асинхронный retrieval + кэш TTL 60s |
| Линтер ломает CI на легаси-коде | Вводить правила через warning→error graduated rollout |
