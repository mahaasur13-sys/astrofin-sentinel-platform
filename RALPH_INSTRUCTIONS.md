# Ralph Loop Instructions for AstroFin Sentinel V5

## Общие правила
- Работай СТРОГО над одной задачей из docs/tickets.md за итерацию.
- Перед началом прочитай progress.md, чтобы понять контекст.
- Всегда начинай с тестов (TDD).
- После реализации запусти полный набор проверок:
  - `ruff check orchestration/ agents/ core/ meta_rl/ trading/ web/`
  - `pytest tests/ -v --cov=. --cov-fail-under=60`
  - `docker compose ps` (все сервисы должны быть healthy)
- Только если все проверки зелёные – делай коммит.
- Используй conventional commits: feat:, fix:, test:, chore:.
- Обнови progress.md после завершения задачи.
- **Никогда не изменяй защищённые файлы:** `docker-compose.yml`, `.env`, `core/tracing.py`.
- Если в процессе что-то пошло не так, агент автоматически откатит изменения.

## Обязательные проверки
- Линтер: `ruff check`
- Тесты: `pytest --cov --cov-fail-under=60`
- Инфраструктура: `docker compose ps`

## Запрещено
- Коммитить в master (ты работаешь в отдельной ветке ralph-iteration-...).
- Пушить без зелёных тестов.
- Менять защищённые файлы без явной задачи и human review.
