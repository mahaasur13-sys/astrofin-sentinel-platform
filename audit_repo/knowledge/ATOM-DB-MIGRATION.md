# ATOM-DB-MIGRATION: PostgreSQL + TimescaleDB + pgvector

**Priority:** P1
**Status:** PROPOSED
**Complexity:** HIGH
**Generated:** 2026-03-29

## Why P1?
После KARL и дедупликации — нужен надёжный storage для:
- Временных рядов (TimescaleDB)
- Agent embeddings (pgvector)
- Статистически значимой истории

## Components
1. PostgreSQL — основная БД
2. TimescaleDB — временные ряды для backtest history
3. pgvector — embeddings для agent similarity search

## Expected
- Быстрые queries для KARL
- Эффективное хранение истории
- Agent clustering через embeddings

## Dependencies
- ATOM-DEDUP-001 (чистые данные)
- ATOM-FIX-ROUTER (корректные данные)
