# Database Schema — astrofin-sentinel-platform

> **Engine:** SQLite (WAL mode, foreign keys ON) for the analytics DB
> (`core/history_db.py`). TimescaleDB is targeted for v1.1 once WAL-G and
> retention policies land (tracked in issue #131).

All schemas are applied via the migration files in `migrations/`. The
runtime schema version is tracked in `_schema_version`.

## Table inventory

| # | Table | Migration | Purpose |
|---|-------|-----------|---------|
| 1 | `sessions` | 0001 + 0006 | One row per orchestration run |
| 2 | `backtest_runs` | 0002 | Aggregated backtest metrics per session |
| 3 | `_row_count_snapshots` | 0003 / 0004 | DB monitor growth snapshots |
| 4 | `agent_beliefs` | 0005 | Beta(α,β) posterior per agent (Thompson sampling) |
| 5 | `agent_belief_history` | 0005 | Per-session belief updates |
| 6 | `agent_selection_log` | 0007 | Which agents were called per session |
| — | `_schema_version` | 0001 | Migration bookkeeping |

---

## `sessions` (0001, 0006)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | autoincrement |
| `session_id` | TEXT UNIQUE NOT NULL | external id used in URLs |
| `symbol` | TEXT NOT NULL | trading symbol (e.g. `BTCUSDT`) |
| `timeframe` | TEXT NOT NULL | `SWING`, `INTRADAY`, `SCALP` |
| `query_type` | TEXT NOT NULL | e.g. `META_RL`, `A_B_TEST` |
| `current_price` | REAL | snapshot at run start |
| `flows_run` | TEXT | JSON of which flows executed |
| `agent_count` | INTEGER | number of agents called |
| `final_signal` | TEXT | `BUY` / `SELL` / `NEUTRAL` |
| `final_confidence` | INTEGER | 0–100 |
| `final_reasoning` | TEXT | human-readable |
| `final_output` | TEXT | JSON payload |
| `thompson_selections` | TEXT | JSON, added in 0006 |
| `technical_agent_count` | INTEGER | denormalized, 0006 |
| `astro_agent_count` | INTEGER | denormalized, 0006 |
| `electoral_agent_count` | INTEGER | denormalized, 0006 |
| `started_at` / `finished_at` | TEXT | ISO 8601 |
| `created_at` | TEXT | `datetime('now')` default |

**Indexes:** `idx_sessions_symbol`, `idx_sessions_timeframe`, `idx_sessions_timestamp` (on `created_at`).

---

## `backtest_runs` (0002)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `session_id` | TEXT UNIQUE NOT NULL | joins to `sessions.session_id` |
| `symbol`, `timeframe` | TEXT | |
| `start_date`, `end_date` | TEXT | backtest window |
| `win_rate`, `sharpe_ratio`, `total_return_pct`, `max_drawdown_pct` | REAL | headline metrics |
| `total_trades`, `winning_trades`, `losing_trades` | INTEGER | counts |
| `avg_win_pct`, `avg_loss_pct`, `avg_confidence` | REAL | |
| `initial_capital`, `final_capital` | REAL | |
| `created_at` | TEXT | |

**Indexes:** `idx_bt_symbol`, `idx_bt_session`, `idx_bt_created`.

---

## `_row_count_snapshots` (0003, corrected in 0004)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `db_name` | TEXT NOT NULL | `sessions` / `backtest` |
| `table_name` | TEXT NOT NULL | source table |
| `row_count` | INTEGER NOT NULL | |
| `snapshot_at` | TEXT NOT NULL | `datetime('now')` default |

**Index:** `idx_snap_db_table` on `(db_name, table_name)`.
Note: the column layout was wrong in 0003; migration 0004 dropped and recreated
the table. The corrected schema above is the current one.

---

## `agent_beliefs` (0005)

| Column | Type | Notes |
|---|---|---|
| `agent_name` | TEXT PK | |
| `alpha`, `beta` | REAL NOT NULL | Beta(α,β) posterior parameters |
| `total_sessions` | INTEGER | running count |
| `updated_at` | TEXT | |

## `agent_belief_history` (0005)

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | |
| `agent_name` | TEXT NOT NULL | |
| `session_id` | TEXT NOT NULL | |
| `final_signal` | TEXT | ground truth |
| `agent_signal` | TEXT | what the agent said |
| `is_success` | INTEGER (0/1) | signal agreement |
| `posterior_alpha`, `posterior_beta` | REAL | snapshot after the update |
| `created_at` | TEXT | |

**Index:** `idx_belief_history_agent` on `(agent_name, created_at)`.

---

## `agent_selection_log` (0007)

| Column | Type | Notes |
|---|---|---|
| `session_id` | TEXT NOT NULL | composite PK part 1 |
| `agent_name` | TEXT NOT NULL | composite PK part 2 |
| `pool_name` | TEXT NOT NULL | `technical` / `astro` / `electoral` |
| `was_called` | INTEGER (0/1) CHECK | whether the agent was actually invoked |
| `success_flag` | INTEGER (0/1, NULL) | NULL when `was_called=0` |
| `created_at` | TEXT | |

**Indexes:** `idx_selection_log_agent` on `(agent_name, created_at)`,
`idx_selection_log_session` on `session_id`.

---

## Retention & TimescaleDB (planned)

The current SQLite store is not a hypertable. The roadmap is to move the
high-volume time series (`sessions`, `agent_selection_log`,
`agent_belief_history`) to TimescaleDB with:

- Chunk time interval: **1 day** on `created_at`.
- Compression policy: compress chunks older than **7 days**.
- Retention policy: drop raw rows older than **180 days**; keep aggregates
  (1-minute, 1-hour, 1-day rollups) indefinitely.

Tracked in issues #127 (ops docs) and #131 (TimescaleDB hypertable).
WAL-G PITR is not yet configured (see #131).
