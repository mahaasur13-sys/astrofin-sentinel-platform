# ATOM-DEDUP-001: Дедупликация агентов

**Priority:** P0
**Status:** PROPOSED
**Complexity:** MEDIUM
**Generated:** 2026-03-29

## Problem
12 backtests = insufficient data. Sharpe 0.71 — шум, не сигнал.
При 6 парах дубликатов агентов — зашумлённость выборки усугубляется.

## Задача
Завершить дедупликацию оставшихся 6 пар агентов.

## Impact
- Чище данные для обучения
- Меньше noise в KARL feedback
- Подготовка к GitAgent экспорту (конфликты исключены)

## Execution
После KARL-015 Phase 1 (чтобы было видно, что именно дублируется)
