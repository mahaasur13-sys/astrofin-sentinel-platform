#!/usr/bin/env python3
"""Fetch PAXGUSDT 4h klines and write the XAUUSD_4h.json cache consumed by trading_engine.

Schema matches the historical cache: [{"date","open","high","low","close","volume"}],
date = "%Y-%m-%d %H:%M" in UTC (no TZ suffix).

Default host is Binance's public market-data mirror: api.binance.com returns HTTP 451
from this sandbox (restricted location), data-api.binance.vision serves the same klines.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_HOST = "https://data-api.binance.vision"
INTERVAL_MS = {"1h": 3_600_000, "4h": 14_400_000}
MIN_BARS = 300


def fetch_klines(host: str, symbol: str, interval: str, limit: int, timeout: float = 20.0) -> list:
    url = f"{host}/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    req = urllib.request.Request(url, headers={"User-Agent": "astrofin-xauusd-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def to_bars(raw: list, step_ms: int, now_ms: int) -> list[dict]:
    bars = []
    for k in raw:
        open_ms, close_ms = k[0], k[6]
        if close_ms > now_ms:  # unclosed candle
            continue
        bars.append(
            {
                "date": datetime.fromtimestamp(open_ms / 1000, timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
        )
    bars.sort(key=lambda b: b["date"])
    return bars


def grid_gaps(raw_ms: list, step_ms: int) -> int:
    return sum(1 for a, b in zip(raw_ms, raw_ms[1:]) if b - a != step_ms)


def write_atomic(path: str, bars: list[dict]) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(bars, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--out", default="/tmp/xauusd_4h.json")
    p.add_argument("--bars", type=int, default=1000, help="klines to request (Binance max 1000)")
    p.add_argument("--symbol", default="PAXGUSDT")
    p.add_argument("--interval", default="4h", choices=sorted(INTERVAL_MS))
    p.add_argument("--host", default=DEFAULT_HOST)
    args = p.parse_args()

    if not 1 <= args.bars <= 1000:
        print(f"error: --bars must be 1..1000, got {args.bars}", file=sys.stderr)
        return 2

    step_ms = INTERVAL_MS[args.interval]
    try:
        raw = fetch_klines(args.host, args.symbol, args.interval, args.bars)
    except urllib.error.HTTPError as exc:
        print(f"error: HTTP {exc.code} from {args.host}: {exc.read()[:200]!r}", file=sys.stderr)
        return 3
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"error: fetch failed: {exc}", file=sys.stderr)
        return 3

    if not isinstance(raw, list) or not raw:
        print(f"error: unexpected payload from {args.host}: {str(raw)[:200]}", file=sys.stderr)
        return 3

    now_ms = int(time.time() * 1000)
    bars = to_bars(raw, step_ms, now_ms)
    gaps = grid_gaps([k[0] for k in raw if k[6] <= now_ms], step_ms)

    if len(bars) < MIN_BARS:
        print(f"error: only {len(bars)} closed bars, need >= {MIN_BARS}", file=sys.stderr)
        return 4
    if gaps:
        print(f"error: {gaps} gap(s) in {args.interval} grid", file=sys.stderr)
        return 5

    write_atomic(args.out, bars)

    last = datetime.strptime(bars[-1]["date"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    age_h = (now_ms / 1000 - last.timestamp()) / 3600
    print(f"out={args.out} bars={len(bars)} first={bars[0]['date']} last={bars[-1]['date']}")
    print(f"last_open_age_h={age_h:.2f} last_close_age_h={age_h - step_ms / 3600000:.2f} close={bars[-1]['close']:.2f} gaps={gaps} dropped_unclosed={len(raw) - len(bars)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
