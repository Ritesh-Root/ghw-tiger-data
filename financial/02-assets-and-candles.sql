-- NOTE: run these statements ONE AT A TIME (e.g. tiger db query --command "..." or the console SQL editor).
-- `tiger db query --file` wraps a file in a single transaction, and CREATE MATERIALIZED VIEW ... WITH DATA
-- cannot run inside a transaction block.

-- Relational lookup table
INSERT INTO crypto_assets (symbol, "name") VALUES ('BTC/USD', 'Bitcoin / US Dollar')
ON CONFLICT (symbol) DO NOTHING;

-- One-day OHLCV candles as a continuous aggregate (from the tutorial)
CREATE MATERIALIZED VIEW IF NOT EXISTS one_day_candle
WITH (timescaledb.continuous) AS
    SELECT
        time_bucket('1 day', time) AS bucket,
        symbol,
        FIRST(price, time) AS "open",
        MAX(price) AS high,
        MIN(price) AS low,
        LAST(price, time) AS "close",
        LAST(day_volume, time) AS day_volume
    FROM crypto_ticks
    GROUP BY bucket, symbol;

SELECT add_continuous_aggregate_policy('one_day_candle',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => true);

-- Refresh now so today's ticks show up straight away
CALL refresh_continuous_aggregate('one_day_candle', NULL, NULL);

-- Tutorial query: OHLCV for the past 14 days
SELECT * FROM one_day_candle
WHERE symbol = 'BTC/USD' AND bucket >= NOW() - INTERVAL '14 days'
ORDER BY bucket;
