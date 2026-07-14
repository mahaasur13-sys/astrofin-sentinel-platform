# Технологический стек

| Категория | Технология | Версия/Особенности |
|-----------|------------|-------------------|
| **Язык** | Python | 3.12 |
| **Оркестрация** | LangGraph | граф состояний |
| **ORM** | SQLAlchemy | async + PostgreSQL/SQLite |
| **Векторный поиск** | FAISS | IndexFlatIP, эмбеддинги 768d |
| **Эмбеддинги** | Ollama | nomic-embed-text |
| **СУБД** | PostgreSQL / SQLite | pg16 + TimescaleDB |
| **Кэш** | Redis | 7.x |
| **Метрики** | Prometheus | + Grafana 8+ |
| **Логирование** | structlog | структурированное |
| **Тестирование** | pytest, httpx | + pytest-asyncio |
| **Астро‑расчёты** | pyswisseph | Swiss Ephemeris |
| **Аутентификация** | Flask-Limiter | API keys + rate limiting |
| **Деплой** | Docker Compose | app + DB + Redis + Prometheus |
