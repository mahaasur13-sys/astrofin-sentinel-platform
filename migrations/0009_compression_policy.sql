-- Migration 0009: TimescaleDB compression policy for market_data hypertable
-- Sprint E — DB optimization

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM timescaledb_information.hypertables
        WHERE hypertable_name = 'market_data'
    ) THEN
        ALTER TABLE market_data SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'symbol',
            timescaledb.compress_orderby = 'timestamp DESC'
        );

        PERFORM add_compression_policy('market_data', INTERVAL '7 days');

        RAISE NOTICE 'Compression policy added for market_data: 7-day delay';
    ELSE
        RAISE NOTICE 'Hypertable market_data not found — skipping compression policy';
    END IF;
END $$;
