"""Real-time crypto ticks from the Twelve Data websocket into a Tiger Cloud hypertable.

Follows the Tiger Data tutorial "Ingest real-time financial data", with one change:
batches are written through the Tiger CLI (`tiger db query`) instead of psycopg2, so the
script never needs a database password. The API key is read from TWELVEDATA_API_KEY.

Usage: TWELVEDATA_API_KEY=... python pipeline.py [--symbols BTC/USD ETH/USD] [--max-rows 300]
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

from twelvedata import TDClient

TIGER = shutil.which("tiger") or os.path.expanduser("~/.local/bin/tiger")


class WebsocketPipeline:
    DB_TABLE = "crypto_ticks"
    DB_COLUMNS = ["time", "symbol", "price", "day_volume"]  # same order as the hypertable
    MAX_BATCH_SIZE = 100  # insert in batches, not row by row

    def __init__(self, max_rows):
        self.current_batch = []
        self.insert_counter = 0
        self.rows_inserted = 0
        self.max_rows = max_rows

    @staticmethod
    def _lit(s):
        return "'" + str(s).replace("'", "''") + "'"

    def _insert_values(self, data):
        """One transaction per batch: a multi-row INSERT sent through the Tiger CLI."""
        rows = ",".join(
            f"({self._lit(t.isoformat())},{self._lit(sym)},{float(p)},{'NULL' if v is None else float(v)})"
            for t, sym, p, v in data
        )
        sql = f"INSERT INTO {self.DB_TABLE} ({','.join(self.DB_COLUMNS)}) VALUES {rows};"
        subprocess.run([TIGER, "db", "query", "--command", sql], check=True, capture_output=True, text=True)

    def flush(self):
        if self.current_batch:
            self._insert_values(self.current_batch)
            self.insert_counter += 1
            self.rows_inserted += len(self.current_batch)
            print(f"Batch insert #{self.insert_counter}: {len(self.current_batch)} rows (total {self.rows_inserted})", flush=True)
            self.current_batch = []

    def _on_event(self, event):
        if event.get("event") == "price":  # a data record, not websocket metadata
            ts = datetime.fromtimestamp(event["timestamp"], tz=timezone.utc)
            self.current_batch.append((ts, event["symbol"], event["price"], event.get("day_volume")))
            print(f"Current batch size: {len(self.current_batch)}", flush=True)
            if len(self.current_batch) >= self.MAX_BATCH_SIZE:
                self.flush()
        elif event.get("event") != "heartbeat":
            print(event, flush=True)

    def start(self, symbols, api_key):
        td = TDClient(apikey=api_key)
        ws = td.websocket(on_event=self._on_event)
        ws.subscribe(symbols)
        ws.connect()
        try:
            while self.rows_inserted + len(self.current_batch) < self.max_rows:
                ws.heartbeat()
                time.sleep(5)
        finally:
            self.flush()
            ws.reset()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=["BTC/USD", "ETH/USD"])
    ap.add_argument("--max-rows", type=int, default=300)
    args = ap.parse_args()
    key = os.environ.get("TWELVEDATA_API_KEY")
    if not key:
        sys.exit("Set TWELVEDATA_API_KEY")
    WebsocketPipeline(args.max_rows).start(args.symbols, key)
