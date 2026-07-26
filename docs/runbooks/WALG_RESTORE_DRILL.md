# WAL-G Restore Drill — AstroFin Sentinel v1.0.0-beta (Sprint G-06)

**Дата:** 2026-07-26 | **Владелец:** Felix | **Периодичность:** Monthly

---

## Pre-requisites

- Docker Compose stack running (PostgreSQL + WAL-G sidecar)
- `WALG_S3_PREFIX`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` в `.env`
- Достаточно места в S3 для backup (~размер БД × 1.5)

---

## Procedure

### Step 1: Проверить текущее состояние БД

```bash
# Размер БД
docker-compose exec postgres psql -U astrofin -d astrofin -c "
  SELECT pg_size_pretty(pg_database_size('astrofin'));
"

# Количество записей
docker-compose exec postgres psql -U astrofin -d astrofin -c "
  SELECT schemaname, tablename, n_live_tup
  FROM pg_stat_user_tables
  ORDER BY n_live_tup DESC
  LIMIT 10;
"
```

Ожидаемый размер: ~50–200 MB (v1.0.0-beta)
Ожидаемое количество записей: `market_data` > 0

### Step 2: Создать backup

```bash
# Push WAL archive
docker-compose exec postgres wal-g wal-push

# Create full backup
docker-compose exec postgres wal-g backup-push /var/lib/postgresql/data

# List backups
docker-compose exec postgres wal-g backup-list
```

Ожидаемый результат: backup появился в `wal-g backup-list`

### Step 3: Симулировать disaster

```bash
# Остановить PostgreSQL
docker-compose stop postgres

# Переименовать data directory (симуляция потери)
mv ./pg_data ./pg_data_corrupted
mkdir ./pg_data
chmod 700 ./pg_data
```

### Step 4: Восстановить из backup

```bash
# Fetch latest backup
docker-compose run --rm postgres wal-g backup-fetch /var/lib/postgresql/data LATEST

# Apply WAL segments
docker-compose run --rm postgres wal-g wal-fetch /var/lib/postgresql/data/wal_005

# Запустить PostgreSQL
docker-compose up -d postgres
sleep 10
```

### Step 5: Integrity check

```bash
# Проверить количество записей после restore
docker-compose exec postgres psql -U astrofin -d astrofin -c "
  SELECT count(*) FROM market_data;
"

# Сравнить с pre-backup значением
# Если совпадает → restore успешен
```

---

## Результаты тестового restore

| Метрика | Pre-Backup | Post-Restore | Match? |
|---------|-----------|-------------|--------|
| **market_data rows** | [заполнить] | [заполнить] | ⬜ |
| **Backup size** | [заполнить] | — | — |
| **Backup time** | [заполнить] | — | — |
| **Restore time** | — | [заполнить] | — |

---

## Emergency contacts

При проблемах с WAL-G restore — эскалация по `docs/on-call.md`
