# Ingest real-time financial data into Tiger Cloud

A working version of the Tiger Data tutorial
[Ingest real-time financial data](https://www.tigerdata.com/docs/learn/tutorials/ingest-real-time-financial-data),
built for MLH Global Hack Week: Hacktoberfest 2026.

A Python script streams live crypto prices from the Twelve Data websocket, batches them in
memory, and inserts them into a Tiger Cloud (TimescaleDB) hypertable. A continuous aggregate
turns the ticks into daily OHLCV candles.

## What is here

| File | What it does |
|---|---|
| `01-schema.sql` | `crypto_ticks` hypertable (segmentby `symbol`, orderby `time DESC`) plus the `crypto_assets` table |
| `pipeline.py` | Websocket pipeline: `on_event` filters price events, batches 100 rows, inserts each batch in one transaction |
| `02-assets-and-candles.sql` | Asset row, `one_day_candle` continuous aggregate, refresh policy, tutorial query |
| `sample-run-*.log` | Output of two real runs |
| `explorer.png` | Tiger Console showing `crypto_ticks`, its continuous aggregate and columnstore |

## Run it

```bash
python3 -m venv env && source env/bin/activate
pip install twelvedata websocket-client
export TWELVEDATA_API_KEY=...        # free Twelve Data account
tiger db query --file 01-schema.sql
python pipeline.py --symbols BTC/USD --max-rows 300
# then run the statements in 02-assets-and-candles.sql one at a time
```

## Result (real run, 11 Oct 2026)

- Two runs streamed live BTC/USD ticks; the table ended at 314 rows (batch inserts of 100, then a final flush).
- `one_day_candle` produced the daily candle: open 83150.09, high 83150.10, low 83129.91, close 83129.92.

## Honest notes

- **No psycopg2.** The tutorial inserts with psycopg2. I flush each batch through the Tiger CLI (`tiger db query`) instead, so the script never needs the database password. The batching logic is the same.
- **Free-tier limits.** Twelve Data's free plan accepted only BTC/USD in my subscription (ETH/USD was rejected), and timestamps arrive at minute resolution, so many ticks share a timestamp.
- **Grafana step skipped.** The tutorial's optional Grafana dashboard is not included; the data is checked with SQL and the Tiger Console explorer.
- `day_volume` is empty (NULL) on the free plan, so the candle has no volume.
- Crypto was used because stock markets were closed on the day of the run.
