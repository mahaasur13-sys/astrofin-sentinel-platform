"""backtest/metrics_agent.py — G-01, G-03 Metrics Agent
===============================================================
Persists all backtest runs, computes G-01 (win rate) and G-03
(Sharpe ratio), tracks per-symbol performance over time.

G-01: Win Rate = LONG_correct / (LONG + SHORT) × 100
G-03: Sharpe Ratio = (mean_daily_return / std_daily_return) × √252

Usage:
  from backtest.metrics_agent import MetricsAgent, load_results, get_summary

  agent = MetricsAgent()
  agent.record("BTCUSDT", 2025, win_rate=63.5, sharpe=1.42, trades=142)
  summary = agent.get_summary()
"""

import sqlite3
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

# ─── Dataclasses ───────────────────────────────────────────────────────────────


@dataclass
class BacktestRun:
    session_id: str
    symbol: str
    start_date: str
    end_date: str
    timeframe: str
    win_rate: float  # G-01
    sharpe_ratio: float  # G-03
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win_pct: float
    avg_loss_pct: float
    total_return_pct: float
    max_drawdown_pct: float
    avg_confidence: float
    initial_capital: float
    final_capital: float
    created_at: str

    def to_dict(self):
        return asdict(self)

    @property
    def expectancy(self) -> float:
        wr = self.win_rate / 100
        avg_w = self.avg_win_pct / 100
        avg_l = abs(self.avg_loss_pct / 100)
        return wr * avg_w - (1 - wr) * avg_l


@dataclass
class MetricsSummary:
    symbol: str
    period: str
    total_runs: int
    avg_win_rate: float  # G-01 average
    avg_sharpe: float  # G-03 average
    best_sharpe: float
    worst_sharpe: float
    avg_return: float
    avg_drawdown: float
    best_win_rate: float
    worst_win_rate: float
    expectancy: float
    trending: str  # "improving", "declining", "stable"

    def summary(self) -> str:
        sep = "=" * 60
        return (
            f"\n{sep}\n"
            f"  METRICS SUMMARY — {self.symbol} [{self.period}]\n"
            f"{sep}\n"
            f"  Total runs:     {self.total_runs}\n"
            f"  Win Rate (G-01): {self.avg_win_rate:.1f}%  "
            f"(best={self.best_win_rate:.1f}% worst={self.worst_win_rate:.1f}%)\n"
            f"  Sharpe (G-03): {self.avg_sharpe:.2f}  "
            f"(best={self.best_sharpe:.2f} worst={self.worst_sharpe:.2f})\n"
            f"  Avg Return:    {self.avg_return:+.1f}%\n"
            f"  Avg Drawdown:  {self.avg_drawdown:.1f}%\n"
            f"  Expectancy:    {self.expectancy * 100:.2f}%/trade\n"
            f"  Trend:         {self.trending}\n"
            f"{sep}"
        )


# ─── Database ─────────────────────────────────────────────────────────────────

_DB_PATH = Path(__file__).parent / "metrics_history.db"


def _db_path() -> Path:
    global _DB_PATH
    if False:  # always use defined path
        _DB_PATH = Path(__file__).parent / "results.db"
    return _DB_PATH


_SCHEMA = """
    CREATE TABLE IF NOT EXISTS backtest_runs (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id        TEXT    NOT NULL UNIQUE,
        symbol            TEXT    NOT NULL,
        start_date        TEXT    NOT NULL,
        end_date          TEXT    NOT NULL,
        timeframe         TEXT    NOT NULL DEFAULT 'SWING',
        win_rate          REAL    NOT NULL DEFAULT 0.0,
        sharpe_ratio      REAL    NOT NULL DEFAULT 0.0,
        total_trades      INTEGER NOT NULL DEFAULT 0,
        winning_trades    INTEGER NOT NULL DEFAULT 0,
        losing_trades     INTEGER NOT NULL DEFAULT 0,
        avg_win_pct       REAL    NOT NULL DEFAULT 0.0,
        avg_loss_pct      REAL    NOT NULL DEFAULT 0.0,
        total_return_pct  REAL    NOT NULL DEFAULT 0.0,
        max_drawdown_pct  REAL    NOT NULL DEFAULT 0.0,
        avg_confidence    REAL    NOT NULL DEFAULT 0.0,
        initial_capital   REAL    NOT NULL DEFAULT 0.0,
        final_capital     REAL    NOT NULL DEFAULT 0.0,
        created_at        TEXT    NOT NULL DEFAULT (datetime('now'))
    );
    CREATE INDEX IF NOT EXISTS idx_runs_symbol ON backtest_runs(symbol);
    CREATE INDEX IF NOT EXISTS idx_runs_created ON backtest_runs(created_at);
"""


class MetricsDB:
    """SQLite-backed metrics store for all backtest runs."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or _db_path()
        self._init()

    def _conn(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._conn() as c:
            c.executescript(_SCHEMA)
            # Add timeframe column if missing ( preexisting DB)
            try:
                c.execute("ALTER TABLE backtest_runs ADD COLUMN timeframe TEXT NOT NULL DEFAULT 'SWING'")
                c.commit()
            except Exception:
                pass

    def save(self, run: BacktestRun) -> str:
        with self._conn() as c:
            c.execute(
                """
                INSERT OR REPLACE INTO backtest_runs
                (session_id, symbol, start_date, end_date, timeframe,
                 win_rate, sharpe_ratio, total_trades, winning_trades, losing_trades,
                 avg_win_pct, avg_loss_pct, total_return_pct, max_drawdown_pct,
                 avg_confidence, initial_capital, final_capital, created_at)
                VALUES
                (:session_id, :symbol, :start_date, :end_date, :timeframe,
                 :win_rate, :sharpe_ratio, :total_trades, :winning_trades, :losing_trades,
                 :avg_win_pct, :avg_loss_pct, :total_return_pct, :max_drawdown_pct,
                 :avg_confidence, :initial_capital, :final_capital, :created_at)
            """,
                run.to_dict(),
            )
            c.commit()
        return run.session_id

    def list(self, symbol: str = None, limit: int = 50) -> list[BacktestRun]:
        cols = list(BacktestRun.__dataclass_fields__.keys())
        sql = f"SELECT {','.join(cols)} FROM backtest_runs"
        args: list = []
        if symbol:
            sql += " WHERE symbol = ?"
            args.append(symbol)
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        with self._conn() as c:
            rows = c.execute(sql, args).fetchall()
        return [BacktestRun(**dict(zip(cols, row, strict=False))) for row in rows]

    def summary(self, symbol: str = None, days: int = 90) -> MetricsSummary | None:
        where = "WHERE created_at >= datetime('now', ?)"
        args = [f"-{days} days"]
        if symbol:
            where += " AND symbol = ?"
            args.append(symbol)

        with self._conn() as c:
            rows = c.execute(f"SELECT * FROM backtest_runs {where}", args).fetchall()
            if not rows:
                return None
            names = rows[0].keys()
            rows_data = []
            for row in rows:
                d = {k: row[k] for k in names if k != "id"}
                rows_data.append(d)
        runs = [BacktestRun(**d) for d in rows_data]

        def _f(v):
            return float(v) if v not in (None, "") else 0.0

        wr_list = [_f(r.win_rate) for r in runs]
        sh_list = [_f(r.sharpe_ratio) for r in runs]
        ret_list = [_f(r.total_return_pct) for r in runs]
        dd_list = [_f(r.max_drawdown_pct) for r in runs]

        avg_wr = statistics.mean(wr_list)
        avg_sh = statistics.mean(sh_list)
        avg_ret = statistics.mean(ret_list)
        avg_dd = statistics.mean(dd_list)

        # Trending: compare first half vs second half
        mid = len(runs) // 2
        first_half = runs[:mid] if mid else runs
        second_half = runs[mid:] if mid else runs
        if first_half and second_half:
            first_wr = statistics.mean(r.win_rate for r in first_half)
            second_wr = statistics.mean(r.win_rate for r in second_half)
            delta = second_wr - first_wr
            trending = "improving" if delta > 2 else "declining" if delta < -2 else "stable"
        else:
            trending = "stable"

        period = f"last {days} days"
        return MetricsSummary(
            symbol=symbol or "ALL",
            period=period,
            total_runs=len(runs),
            avg_win_rate=round(avg_wr, 2),
            avg_sharpe=round(avg_sh, 4),
            best_sharpe=round(max(sh_list), 4),
            worst_sharpe=round(min(sh_list), 4),
            avg_return=round(avg_ret, 2),
            avg_drawdown=round(avg_dd, 2),
            best_win_rate=round(max(wr_list), 2),
            worst_win_rate=round(min(wr_list), 2),
            expectancy=round(statistics.mean(r.expectancy for r in runs), 4),
            trending=trending,
        )

    def clear(self, older_than_days: int = None) -> int:
        with self._conn() as c:
            if older_than_days is None:
                deleted = c.execute("DELETE FROM backtest_runs").rowcount
            else:
                deleted = c.execute(
                    "DELETE FROM backtest_runs WHERE created_at < datetime('now', ?)",
                    (f"-{older_than_days} days",),
                ).rowcount
            c.commit()
        return deleted


# ─── Singleton ────────────────────────────────────────────────────────────────

_db: MetricsDB | None = None


def _get_db() -> MetricsDB:
    global _db
    if _db is None:
        _db = MetricsDB()
    return _db


# ─── Convenience API ──────────────────────────────────────────────────────────


def record_run(run_or_result) -> str:
    """Record a backtest run. Accepts BacktestRun or BacktestResult (engine.py)."""
    if isinstance(run_or_result, BacktestRun):
        run = run_or_result
    else:
        # Convert BacktestResult (engine.py) to BacktestRun
        r = run_or_result
        run = BacktestRun(
            session_id=r.session_id,
            symbol=r.symbol,
            start_date=r.start_date,
            end_date=r.end_date,
            timeframe="SWING",
            win_rate=r.win_rate,
            sharpe_ratio=r.sharpe_ratio,
            total_trades=r.total_trades,
            winning_trades=r.winning_trades,
            losing_trades=r.losing_trades,
            avg_win_pct=r.avg_win_pct,
            avg_loss_pct=r.avg_loss_pct,
            total_return_pct=r.total_return_pct,
            max_drawdown_pct=r.max_drawdown_pct,
            avg_confidence=r.avg_confidence,
            initial_capital=10000.0,
            final_capital=0.0,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    return _get_db().save(run)


def record(
    symbol: str,
    win_rate: float,
    sharpe_ratio: float,
    total_trades: int,
    winning_trades: int = 0,
    losing_trades: int = 0,
    total_return_pct: float = 0.0,
    max_drawdown_pct: float = 0.0,
    avg_confidence: float = 50.0,
    session_id: str = None,
    **kwargs,
) -> str:
    """Simple one-shot metric recording."""
    import uuid

    run = BacktestRun(
        session_id=session_id or str(uuid.uuid4())[:8],
        symbol=symbol,
        start_date=kwargs.get("start_date", ""),
        end_date=kwargs.get("end_date", ""),
        timeframe=kwargs.get("timeframe", "SWING"),
        win_rate=win_rate,
        sharpe_ratio=sharpe_ratio,
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades or max(0, total_trades - winning_trades),
        avg_win_pct=kwargs.get("avg_win_pct", 0.0),
        avg_loss_pct=kwargs.get("avg_loss_pct", 0.0),
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        avg_confidence=avg_confidence,
        initial_capital=kwargs.get("initial_capital", 10000.0),
        final_capital=kwargs.get("final_capital", 0.0),
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return _get_db().save(run)


def get_summary(symbol: str = None, days: int = 90) -> MetricsSummary | None:
    return _get_db().summary(symbol=symbol, days=days)


def load_results(symbol: str = None, limit: int = 50) -> list[BacktestRun]:
    return _get_db().list(symbol=symbol, limit=limit)


# ─── Metrics Agent ────────────────────────────────────────────────────────────


class MetricsAgent:
    """
    G-01/G-03 Metrics Agent.

    Records and analyzes backtest performance metrics.
    """

    def __init__(self):
        self.db = _get_db()

    async def run(self, state: dict = None) -> dict:
        """
        Analyze metrics for a symbol.

        Reads from backtest/results.db.
        Returns G-01 win rate and G-03 Sharpe ratio summary.
        """
        symbol = (state or {}).get("symbol", "BTCUSDT")
        days = (state or {}).get("days", 90)

        runs = self.db.list(symbol=symbol, limit=100)
        summary = self.db.summary(symbol=symbol, days=days)

        return {
            "agent_name": "MetricsAgent",
            "symbol": symbol,
            "total_runs": len(runs),
            "summary": summary.to_dict() if summary else None,
            "g01_win_rate": summary.avg_win_rate if summary else None,
            "g03_sharpe_ratio": summary.avg_sharpe if summary else None,
            "trend": summary.trending if summary else None,
            "recent_runs": [r.to_dict() for r in runs[:5]],
        }
