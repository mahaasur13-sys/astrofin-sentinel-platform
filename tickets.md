# AstroFin Sentinel V5 – Бэклог для Ralph Loop

## P0 (Критические)
- [x] Настроить реальный webhook (Slack) в Alertmanager вместо blackhole ✅
- [x] Добавить e2e-тест для run_sentinel_v5 с моком внешних API ✅

## P1 (Важные)
- [x] Заменить f-строки на structlog ✅ (completed)
- [x] Написать unit-тесты для модуля meta_rl/ab_testing.py (покрытие >80%) ✅
- [x] Добавить кэширование результатов агентов в Redis ✅

## P2 (Желательные)
- [ ] Реализовать параллельный запуск агентов через ProcessPoolExecutor
- [ ] Добавить метрику длительности выполнения каждого агента в Prometheus
