-- 0008: Market Data — OHLCV bars hypertable for backtesting & live trading
-- Sprint A (2026-07-25): Production TimescaleDB schema
-- Source: data_room/resolvers/binance.py, coingecko.py, yahoo.py

CREATE TABLE IF NOT EXISTS market_data (
    id              BIGSERIAL,
    symbol          TEXT        NOT NULL,          -- e.g. BTCUSDT, ETHUSDT
    exchange        TEXT        NOT NULL DEFAULT 'binance',
    timeframe       TEXT        NOT NULL,          -- 1m, 5m, 15m, 1h, 4h, 1d, 1w
    open            DOUBLE PRECISION,
    high            DOUBLE PRECISION,
    low             DOUBLE PRECISION,
    close           DOUBLE PRECISION,
    volume          DOUBLE PRECISION,
    trades_count    INTEGER,
    bucket_ts       TIMESTAMPTZ NOT NULL,          -- start of the candle bucket
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (symbol, exchange, timeframe, bucket_ts)
);

-- Convert to hypertable with 1-day chunks (market data is high-volume)
SELECT create_hypertable('market_data', 'bucket_ts',
    migrate_data => true,
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => true
);

-- Composite index for symbol+timeframe queries
CREATE INDEX IF NOT EXISTS idx_market_data_symbol_tf_time
    ON market_data (symbol, timeframe, bucket_ts DESC);

-- Partial index for 1m data (most queried)
CREATE INDEX IF NOT EXISTS idx_market_data_1m
    ON market_data (symbol, bucket_ts DESC)
    WHERE timeframe = '1m';

-- Partial index for 1h data (strategy backtesting)
CREATE INDEX IF NOT EXISTS idx_market_data_1h
    ON market_data (symbol, bucket_ts DESC)
    WHERE timeframe = '1h';

-- Retention: keep 1m for 90 days, 1h for 365 days, 1d forever
SELECT add_retention_policy('market_data', INTERVAL '90 days',
    if_not_exists => true
);

-- Compression: compress chunks older than 1 day
SELECT add_compression_policy('market_data', INTERVAL '1 day',
    if_not_exists => true
);

-- Reorder policy for recent data (optimises last-N queries)
SELECT add_reorder_policy('market_data', 'idx_market_data_symbol_tf_time',
    if_not_exists => true
);

COMMENT ON TABLE market_data IS 'OHLCV bars — primary market data store. Populated by data_room/resolvers via INSERT ON CONFLICT DO NOTHING.';
