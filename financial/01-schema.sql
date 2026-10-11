-- Hypertable for real-time crypto ticks (from the Tiger Data tutorial)
CREATE TABLE IF NOT EXISTS crypto_ticks (
    "time" TIMESTAMPTZ,
    symbol TEXT,
    price DOUBLE PRECISION,
    day_volume NUMERIC
) WITH (
   tsdb.hypertable,
   tsdb.segmentby='symbol',
   tsdb.orderby='time DESC'
);

-- Regular PostgreSQL table for relational data
CREATE TABLE IF NOT EXISTS crypto_assets (
    symbol TEXT UNIQUE,
    "name" TEXT
);
