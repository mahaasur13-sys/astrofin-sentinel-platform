"""backtest/engine.py — G-01/G-03 Backtesting Engine (with real agent support + metrics)"""

from __future__ import annotations

import asyncio
import math
import random
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import requests

from agents._impl.astro_council.agent import AstroCouncilAgent
from agents._impl.elliot_agent import ElliotAgent
from agents._impl.macro_agent import MacroAgent
from agents._impl.ml_predictor_agent import MLPredictorAgent
from agents._impl.options_flow_agent import OptionsFlowAgent
from agents._impl.sentiment_agent import SentimentAgent
from agents._impl.synthesis_agent import SynthesisAgent
from agents._impl.technical_agent import TechnicalAgent
from core.thompson import ASTRO_POOL, MACRO_POOL, TECHNICAL_POOL, get_thompson_sampler
from tools.metrics_server import BACKTEST_REAL_RUNS, BACKTEST_SYNTHETIC_RUNS

BINANCE_BASE = "https://api.binance.com/api/v3"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_INTERVAL = "1h"


@dataclass
class OHLCV:
    timestamp: int
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def dt(self):
        return datetime.fromtimestamp(self.timestamp / 1000, tz=timezone.utc)

    @classmethod
    def from_binance_kline(cls, k):
        return cls(
            timestamp=int(k[0]),
            open=float(k[1]),
            high=float(k[2]),
            low=float(k[3]),
            close=float(k[4]),
            volume=float(k[5]),
        )


@dataclass
class Trade:
    entry_time: datetime
    exit_time: datetime
    direction: str
    entry_price: float
    exit_price: float
    pnl_pct: float
    confidence: int
    signal_reasoning: str
    session_id: str


@dataclass
class BacktestResult:
    session_id: str
    symbol: str
    start_date: str
    end_date: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    total_return_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    avg_confidence: float
    trades: list = field(default_factory=list)
    equity_curve: list = field(default_factory=list)

    def summary(self):
        sep = "============================================================"
        return (
            f"\n{sep}\n"
            f"  BACKTEST {self.symbol}  [{self.start_date} -> {self.end_date}]\n"
            f"{sep}\n"
            f"  Sessions:       {self.total_trades}\n"
            f"  Win Rate (G-01): {self.win_rate:.1f}%  ({self.winning_trades}W/{self.losing_trades}L)\n"
            f"  Avg Win:       +{self.avg_win_pct:.2f}%  |  Avg Loss: {self.avg_loss_pct:.2f}%\n"
            f"  Total Return:  {self.total_return_pct:+.1f}%\n"
            f"  Max Drawdown:  {self.max_drawdown_pct:.1f}%\n"
            f"  Sharpe (G-03): {self.sharpe_ratio:.2f}\n"
            f"  Avg Confidence: {self.avg_confidence:.0f}\n"
            f"{sep}"
        )


def _synthetic_ohlcv(
    start_dt: datetime,
    end_dt: datetime,
    interval_hours: int = 1,
    base_price: float = 50000.0,
) -> list:
    result = []
    current_dt = start_dt
    price = base_price
    while current_dt < end_dt:
        change = random.gauss(0, 0.008)
        open_p = price
        close_p = price * (1 + change)
        high_p = max(open_p, close_p) * (1 + abs(random.gauss(0, 0.003)))
        low_p = min(open_p, close_p) * (1 - abs(random.gauss(0, 0.003)))
        volume = random.uniform(100, 500)
        result.append(
            OHLCV(
                timestamp=int(current_dt.timestamp() * 1000),
                open=round(open_p, 2),
                high=round(high_p, 2),
                low=round(low_p, 2),
                close=round(close_p, 2),
                volume=round(volume, 2),
            )
        )
        price = close_p
        current_dt = datetime.fromtimestamp(
            current_dt.timestamp() + interval_hours * 3600, tz=timezone.utc
        )
    return result


def fetch_ohlcv(
    symbol=DEFAULT_SYMBOL,
    interval=DEFAULT_INTERVAL,
    start_time=None,
    end_time=None,
    limit=1000,
):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    if start_time:
        params["startTime"] = start_time
    if end_time:
        params["endTime"] = end_time
    try:
        r = requests.get(f"{BINANCE_BASE}/klines", params=params, timeout=10)
        return [OHLCV.from_binance_kline(k) for k in r.json()]
    except Exception:
        st = (
            datetime.fromtimestamp(start_time / 1000, tz=timezone.utc)
            if start_time
            else datetime.now(timezone.utc)
        )
        et = (
            datetime.fromtimestamp(end_time / 1000, tz=timezone.utc) if end_time else st
        )
        return _synthetic_ohlcv(st, et, interval_hours=1, base_price=50000.0)


def fetch_range(symbol, interval, start_dt, end_dt):
    all_c = []
    cur = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    chunk_ms = 1000 * 3600 * 1000
    try:
        while cur < end_ms:
            chunk = fetch_ohlcv(
                symbol=symbol,
                interval=interval,
                start_time=cur,
                end_time=min(cur + chunk_ms, end_ms),
            )
            if not chunk or len(chunk) < 2:
                break
            all_c.extend(chunk)
            cur = chunk[-1].timestamp + 1
            if len(chunk) < 500:
                break
        if len(all_c) > 100:
            return all_c
    except Exception:
        pass
    return _synthetic_ohlcv(start_dt, end_dt, interval_hours=1, base_price=50000.0)


async def generate_synthetic_signal(price, prev_price, timestamp):
    momentum = (price - prev_price) / prev_price if prev_price else 0
    h = timestamp.hour + timestamp.minute / 60
    d = timestamp.day + h / 24
    astro = (
        math.sin(2 * math.pi * h / 4) * 0.010
        + math.sin(2 * math.pi * d / 28) * 0.015
        + math.sin(2 * math.pi * d / 7) * 0.008
    )
    comb = momentum + astro
    if comb > 0.003:
        sig = "LONG"
        conf = min(92, 50 + int(abs(comb) * 5000))
    elif comb < -0.003:
        sig = "SHORT"
        conf = min(92, 50 + int(abs(comb) * 5000))
    else:
        sig = "NEUTRAL"
        conf = 50
    return {
        "signal": sig,
        "confidence": conf,
        "reasoning": f"momentum={momentum:.4f} astro={astro:.4f}",
    }


class BacktestEngine:
    def __init__(
        self,
        symbol=DEFAULT_SYMBOL,
        interval=DEFAULT_INTERVAL,
        initial_capital=10000.0,
        risk_pct=0.02,
    ):
        self.symbol = symbol
        self.interval = interval
        self.initial_capital = initial_capital
        self.risk_pct = risk_pct
        self.results_db = Path(__file__).parent / "results.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(str(self.results_db)) as conn:
            conn.executescript(
                "CREATE TABLE IF NOT EXISTS backtest_runs ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "session_id TEXT NOT NULL UNIQUE, "
                "symbol TEXT, start_date TEXT, end_date TEXT, "
                "total_trades INTEGER, winning_trades INTEGER, losing_trades INTEGER, "
                "win_rate REAL, avg_win_pct REAL, avg_loss_pct REAL, "
                "total_return_pct REAL, max_drawdown_pct REAL, "
                "sharpe_ratio REAL, avg_confidence REAL)"
            )
            conn.commit()

    def _build_state(self, bar_index: int, candles: list) -> dict:
        candle = candles[bar_index]
        return {
            "symbol": self.symbol,
            "current_price": candle.close,
            "price": candle.close,
            "datetime": candle.dt,
            "price_data": [
                {
                    "timestamp": c.timestamp,
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles[max(0, bar_index - 50) : bar_index + 1]
            ],
        }

    async def run(
        self,
        start_date,
        end_date,
        use_real_agents=False,
        use_thompson=False,
        use_synthesis=False,
        session_id=None,
    ):
        session_id = session_id or str(uuid.uuid4())[:8]
        candles = fetch_range(
            self.symbol,
            self.interval,
            datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc),
            datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc),
        )
        if len(candles) < 10:
            print(f"[Backtest] Not enough data: {len(candles)}")
            return None
        print(f"[Backtest] Got {len(candles)} candles. Generating signals...")
        signals = []

        if use_real_agents:
            if use_thompson:
                sampler = get_thompson_sampler()
                tech_selected = sampler.select(TECHNICAL_POOL, k=2)
                macro_selected = sampler.select(MACRO_POOL, k=2)
                astro_selected = sampler.select(ASTRO_POOL, k=2)
                selected_names = [
                    name for name, _ in tech_selected + macro_selected + astro_selected
                ]
                agents = []
                if "TechnicalAgent" in selected_names:
                    agents.append(TechnicalAgent())
                if "MacroAgent" in selected_names:
                    agents.append(MacroAgent())
                if "AstroCouncilAgent" in selected_names:
                    agents.append(AstroCouncilAgent())
                if not agents:
                    agents = [TechnicalAgent()]
            else:
                agents = [
                    TechnicalAgent(),
                    MacroAgent(),
                    AstroCouncilAgent(),
                    SentimentAgent(),
                    OptionsFlowAgent(),
                    ElliotAgent(),
                    MLPredictorAgent(),
                ]

            for i in range(len(candles)):
                curr = candles[i]
                signals_for_bar = []
                for agent in agents:

                    async def mock_fetch(symbol, interval, limit, idx=i):
                        start = max(0, idx - limit + 1)
                        return candles[start : idx + 1]

                    agent._fetch_ohlcv = mock_fetch
                    state = self._build_state(i, candles)
                    try:
                        raw_resp = await agent.run(state)
                        if isinstance(raw_resp, dict):
                            signal_data = raw_resp.get("astro_council_signal", raw_resp)
                            resp = type("AgentResponse", (), signal_data)()
                        else:
                            resp = raw_resp
                    except Exception as e:
                        resp = type(
                            "AgentResponse",
                            (),
                            {
                                "signal": "NEUTRAL",
                                "confidence": 30,
                                "reasoning": f"Agent error: {str(e)[:100]}",
                            },
                        )()
                    signals_for_bar.append(resp)

                chosen = None
                for r in signals_for_bar:
                    if r and r.signal != "NEUTRAL":
                        chosen = r
                        break
                if chosen is None:
                    chosen = signals_for_bar[0]

                signals.append(
                    {
                        "time": curr.dt,
                        "price": curr.close,
                        "signal": chosen.signal,
                        "confidence": chosen.confidence,
                        "reasoning": chosen.reasoning,
                    }
                )

            if use_synthesis:
                synthesis_agent = SynthesisAgent()
                try:
                    state_for_synth = {
                        "all_signals": signals,
                        "symbol": self.symbol,
                        "timeframe_requested": "1h",
                        "current_price": candles[-1].close if candles else 0,
                    }
                    synth_result = await synthesis_agent.run(state_for_synth)
                    final_signal = (
                        synth_result.signal
                        if hasattr(synth_result, "signal")
                        else "NEUTRAL"
                    )
                    final_confidence = (
                        synth_result.confidence
                        if hasattr(synth_result, "confidence")
                        else 50
                    )
                    final_reasoning = (
                        synth_result.reasoning
                        if hasattr(synth_result, "reasoning")
                        else "Synthesis complete"
                    )
                    signals = [
                        {
                            "time": (
                                candles[-1].dt
                                if candles
                                else datetime.now(timezone.utc)
                            ),
                            "price": candles[-1].close if candles else 0,
                            "signal": final_signal,
                            "confidence": final_confidence,
                            "reasoning": final_reasoning,
                        }
                    ]
                except Exception:
                    pass
        else:
            for i in range(1, len(candles)):
                prev = candles[i - 1]
                curr = candles[i]
                sig = await generate_synthetic_signal(curr.close, prev.close, curr.dt)
                signals.append({"time": curr.dt, "price": curr.close, **sig})

        # Инкрементируем счётчики метрик
        if use_real_agents:
            BACKTEST_REAL_RUNS.inc()
        else:
            BACKTEST_SYNTHETIC_RUNS.inc()

        trades = self._simulate_trades(signals, session_id)
        m = self._calc_metrics(trades)
        result = BacktestResult(
            session_id=session_id,
            symbol=self.symbol,
            start_date=start_date,
            end_date=end_date,
            **m,
            trades=trades,
            equity_curve=[],
        )
        self._save(result)
        return result

    def _make_trade(self, pos, bar, exit_price, pnl_pct, reason, sid):
        return Trade(
            entry_time=pos["time"],
            exit_time=bar["time"],
            direction=pos["dir"],
            entry_price=pos["entry"],
            exit_price=exit_price,
            pnl_pct=pnl_pct,
            confidence=pos["conf"],
            signal_reasoning=pos.get("reasoning", ""),
            session_id=sid,
        )

    def _simulate_trades(self, signals, sid):
        trades = []
        pos = None
        sp = self.risk_pct * 2
        tp = self.risk_pct * 3
        for i in range(len(signals) - 1):
            s = signals[i]
            n = signals[i + 1]
            np = n["price"]
            if pos:
                d = pos["dir"]
                e = pos["entry"]
                pnl = (np - e) / e if d == "LONG" else (e - np) / e
                exit_r = None
                exit_p = None
                if d == "LONG" and pnl <= -sp:
                    exit_r = "SL"
                    exit_p = e - sp * e
                elif d == "SHORT" and pnl <= -sp:
                    exit_r = "SL"
                    exit_p = e + sp * e
                elif d == "LONG" and pnl >= tp:
                    exit_r = "TP"
                    exit_p = e + tp * e
                elif d == "SHORT" and pnl >= tp:
                    exit_r = "TP"
                    exit_p = e - tp * e
                if exit_r:
                    trades.append(
                        self._make_trade(
                            pos, signals[i + 1], exit_p, pnl * 100, exit_r, sid
                        )
                    )
                    pos = None
                    continue
            if pos and s["signal"] in ("SHORT", "NEUTRAL") and pos["dir"] == "LONG":
                trades.append(
                    self._make_trade(
                        pos,
                        signals[i + 1],
                        np,
                        (np - pos["entry"]) / pos["entry"] * 100,
                        "FLIP",
                        sid,
                    )
                )
                pos = None
            if pos and s["signal"] in ("LONG", "NEUTRAL") and pos["dir"] == "SHORT":
                trades.append(
                    self._make_trade(
                        pos,
                        signals[i + 1],
                        np,
                        (pos["entry"] - np) / pos["entry"] * 100,
                        "FLIP",
                        sid,
                    )
                )
                pos = None
            if not pos and s["signal"] in ("LONG", "SHORT"):
                pos = {
                    "dir": s["signal"],
                    "entry": np,
                    "time": signals[i + 1]["time"],
                    "conf": s["confidence"],
                    "reasoning": s.get("reasoning", ""),
                }
        if pos and signals:
            last = signals[-1]
            lp = last["price"]
            d = pos["dir"]
            pnl = (
                (lp - pos["entry"]) / pos["entry"] * 100
                if d == "LONG"
                else (pos["entry"] - lp) / pos["entry"] * 100
            )
            trades.append(self._make_trade(pos, last, lp, pnl, "EOD", sid))
        return trades

    def _calc_metrics(self, trades):
        total = len(trades)
        wins = sum(1 for t in trades if t.pnl_pct > 0)
        wl = [t.pnl_pct for t in trades if t.pnl_pct > 0]
        ll = [t.pnl_pct for t in trades if t.pnl_pct <= 0]
        eq = self.initial_capital
        peak = eq
        mdd = 0.0
        for t in trades:
            eq *= 1 + t.pnl_pct / 100
            peak = max(peak, eq)
            mdd = max(mdd, (peak - eq) / peak * 100)
        daily_returns = [
            (trades[i].pnl_pct - trades[i - 1].pnl_pct) / 100
            for i in range(1, len(trades))
        ]
        if daily_returns and sum(daily_returns) != 0:
            mean_r = sum(daily_returns) / len(daily_returns)
            std_r = (
                sum((r - mean_r) ** 2 for r in daily_returns) / len(daily_returns)
            ) ** 0.5
            shr = round((mean_r / std_r) * (252**0.5), 4) if std_r > 0 else 0.0
        else:
            shr = 0.0
        return dict(
            total_trades=total,
            winning_trades=wins,
            losing_trades=total - wins,
            win_rate=round(wins / total * 100, 2) if total else 0.0,
            avg_win_pct=round(sum(wl) / len(wl), 4) if wl else 0.0,
            avg_loss_pct=round(sum(ll) / len(ll), 4) if ll else 0.0,
            total_return_pct=round(
                (eq - self.initial_capital) / self.initial_capital * 100, 2
            ),
            max_drawdown_pct=round(mdd, 2),
            sharpe_ratio=shr,
            avg_confidence=(
                round(sum(t.confidence for t in trades) / total, 1) if total else 0
            ),
        )

    def _save(self, r):
        with sqlite3.connect(str(self.results_db)) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO backtest_runs "
                "(session_id,symbol,start_date,end_date,total_trades,winning_trades,losing_trades,"
                "win_rate,avg_win_pct,avg_loss_pct,total_return_pct,max_drawdown_pct,sharpe_ratio,avg_confidence) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    r.session_id,
                    r.symbol,
                    r.start_date,
                    r.end_date,
                    r.total_trades,
                    r.winning_trades,
                    r.losing_trades,
                    r.win_rate,
                    r.avg_win_pct,
                    r.avg_loss_pct,
                    r.total_return_pct,
                    r.max_drawdown_pct,
                    r.sharpe_ratio,
                    r.avg_confidence,
                ),
            )
            conn.commit()


async def run_backtest(
    symbol="BTCUSDT", start_date="2025-01-01", end_date="2025-03-25"
):
    return await BacktestEngine(symbol=symbol).run(start_date, end_date)


if __name__ == "__main__":
    import sys

    sym = sys.argv[1] if len(sys.argv) > 1 else "BTCUSDT"
    sd = sys.argv[2] if len(sys.argv) > 2 else "2025-01-01"
    ed = sys.argv[3] if len(sys.argv) > 3 else "2025-03-25"
    result = asyncio.run(run_backtest(sym, sd, ed))
    if result:
        print(result.summary())
