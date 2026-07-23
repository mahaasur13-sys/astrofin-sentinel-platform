"""meta_rl/calibration.py -- ATOM-META-RL-014: CalibrationTracker.

Tracks agent predictions vs. realized outcomes to compute calibration
metrics (Brier score, Expected Calibration Error, reliability bins).

Storage: SQLite at data/meta_rl/calibration.db (WAL mode).

Public API:
    tracker = get_calibration_tracker()
    pid = tracker.record_prediction("macro_agent", "LONG", 72.5, ...)
    tracker.record_outcome(pid, actual_label=1, observed_at=..., pnl=...)
    report = tracker.get_calibration(agent="macro_agent", window_days=30)
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ── Storage layout ────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data" / "meta_rl"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "calibration.db"

N_BINS = 10
BIN_EDGES = [i / N_BINS for i in range(N_BINS + 1)]  # [0.0, 0.1, ..., 1.0]

SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    agent        TEXT    NOT NULL,
    signal       TEXT    NOT NULL,
    confidence   REAL    NOT NULL,
    predicted_at TEXT    NOT NULL,
    context_json TEXT,
    outcome_id   INTEGER,
    FOREIGN KEY (outcome_id) REFERENCES outcomes(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS outcomes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    prediction_id INTEGER NOT NULL UNIQUE,
    actual_label INTEGER NOT NULL,        -- 1 = correct, 0 = wrong
    observed_at  TEXT    NOT NULL,
    pnl          REAL    NOT NULL DEFAULT 0.0,
    FOREIGN KEY (prediction_id) REFERENCES predictions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_predictions_agent_time
    ON predictions(agent, predicted_at);

CREATE INDEX IF NOT EXISTS idx_predictions_outcome
    ON predictions(outcome_id);
"""


# ── Data classes ──────────────────────────────────────────────────────────────


@dataclass
class ReliabilityBin:
    """One reliability-diagram bin: predicted vs. observed frequency."""

    lo: float
    hi: float
    count: int
    mean_predicted: float
    mean_observed: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "lo": round(self.lo, 4),
            "hi": round(self.hi, 4),
            "count": self.count,
            "mean_predicted": round(self.mean_predicted, 4),
            "mean_observed": round(self.mean_observed, 4),
        }


@dataclass
class CalibrationReport:
    agent: str | None
    n_predictions: int
    n_resolved: int
    brier_score: float
    ece: float
    accuracy: float
    bins: list[ReliabilityBin] = field(default_factory=list)
    window_start: str | None = None
    window_end: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "n_predictions": self.n_predictions,
            "n_resolved": self.n_resolved,
            "brier_score": round(self.brier_score, 6),
            "ece": round(self.ece, 6),
            "accuracy": round(self.accuracy, 6),
            "bins": [b.to_dict() for b in self.bins],
            "window_start": self.window_start,
            "window_end": self.window_end,
        }


# ── Tracker ───────────────────────────────────────────────────────────────────


class CalibrationTracker:
    """Records agent predictions and resolves them with realized outcomes."""

    def __init__(self, db_path: Path | str = DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_schema()

    # ── Schema management ──────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        try:
            with self._connect() as conn:
                conn.executescript(SCHEMA)
        except sqlite3.Error as exc:
            logger.warning(f"[CALIBRATION] schema init failed: {exc}")

    @contextmanager
    def _cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            conn = self._connect()
            try:
                cur = conn.cursor()
                yield cur
            finally:
                conn.close()

    # ── Writes ─────────────────────────────────────────────────────────────

    def record_prediction(
        self,
        agent: str,
        signal: str,
        confidence: float,
        predicted_at: str | datetime | None = None,
        context: dict[str, Any] | None = None,
    ) -> int:
        """Record a prediction. Returns its ID (used to record the outcome)."""
        ts = self._ts(predicted_at)
        conf = self._clip_confidence(confidence)
        ctx_json = json.dumps(context or {}, default=str, ensure_ascii=False)
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO predictions (agent, signal, confidence, predicted_at, context_json) "
                "VALUES (?, ?, ?, ?, ?)",
                (agent, signal, conf, ts, ctx_json),
            )
            new_id = int(cur.lastrowid)
        logger.debug(f"[CALIBRATION] recorded prediction {new_id} for {agent} conf={conf:.2f}")
        return new_id

    def record_outcome(
        self,
        prediction_id: int,
        actual_label: int,
        observed_at: str | datetime | None = None,
        pnl: float = 0.0,
    ) -> int:
        """Resolve a prediction. actual_label: 1 (correct) or 0 (wrong). Returns outcome ID."""
        if actual_label not in (0, 1):
            raise ValueError(f"actual_label must be 0 or 1, got {actual_label}")
        ts = self._ts(observed_at)
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO outcomes (prediction_id, actual_label, observed_at, pnl) " "VALUES (?, ?, ?, ?)",
                (int(prediction_id), int(actual_label), ts, float(pnl)),
            )
            outcome_id = int(cur.lastrowid)
            cur.execute(
                "UPDATE predictions SET outcome_id = ? WHERE id = ?",
                (outcome_id, int(prediction_id)),
            )
        logger.debug(f"[CALIBRATION] resolved {prediction_id} -> label={actual_label}")
        return outcome_id

    # ── Reads ──────────────────────────────────────────────────────────────

    def get_calibration(
        self,
        agent: str | None = None,
        window_days: int = 30,
        asof: datetime | None = None,
    ) -> CalibrationReport:
        """Compute calibration metrics over a recent window."""
        asof_dt = self._asof(asof)
        start_dt = asof_dt - timedelta(days=window_days)
        start_iso = start_dt.isoformat()
        end_iso = asof_dt.isoformat()

        with self._cursor() as cur:
            if agent is None:
                cur.execute(
                    "SELECT confidence, actual_label FROM predictions p "
                    "JOIN outcomes o ON p.outcome_id = o.id "
                    "WHERE p.predicted_at >= ? AND p.predicted_at <= ?",
                    (start_iso, end_iso),
                )
                cur.execute(
                    "SELECT COUNT(*) FROM predictions WHERE predicted_at >= ? AND predicted_at <= ?",
                    (start_iso, end_iso),
                )
            else:
                cur.execute(
                    "SELECT confidence, actual_label FROM predictions p "
                    "JOIN outcomes o ON p.outcome_id = o.id "
                    "WHERE p.agent = ? AND p.predicted_at >= ? AND p.predicted_at <= ?",
                    (agent, start_iso, end_iso),
                )
                cur.execute(
                    "SELECT COUNT(*) FROM predictions " "WHERE agent = ? AND predicted_at >= ? AND predicted_at <= ?",
                    (agent, start_iso, end_iso),
                )

            pairs = cur.fetchall()
            n_predictions_row = cur.fetchone()
            n_predictions = int(n_predictions_row[0]) if n_predictions_row else 0

        return self._build_report(agent, pairs, n_predictions, start_iso, end_iso)

    def get_reliability_bins(
        self,
        agent: str | None = None,
        window_days: int = 30,
        asof: datetime | None = None,
    ) -> list[ReliabilityBin]:
        """Return the 10-bin reliability diagram for the given window."""
        return self.get_calibration(agent=agent, window_days=window_days, asof=asof).bins

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _clip_confidence(confidence: float) -> float:
        try:
            v = float(confidence)
        except (TypeError, ValueError):
            return 50.0
        if v > 1.0 and v <= 100.0:
            return v / 100.0
        if v < 0.0:
            return 0.0
        if v > 1.0:
            return 1.0
        return v

    @staticmethod
    def _ts(value: str | datetime | None) -> str:
        if value is None:
            return datetime.now(timezone.utc).isoformat()
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=timezone.utc)
            return value.isoformat()
        return str(value)

    @staticmethod
    def _asof(value: datetime | None) -> datetime:
        if value is None:
            return datetime.now(timezone.utc)
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    @staticmethod
    def _build_report(
        agent: str | None,
        pairs: list[sqlite3.Row],
        n_predictions: int,
        start_iso: str,
        end_iso: str,
    ) -> CalibrationReport:
        n_resolved = len(pairs)
        if n_resolved == 0:
            empty_bins = [ReliabilityBin(BIN_EDGES[i], BIN_EDGES[i + 1], 0, 0.0, 0.0) for i in range(N_BINS)]
            return CalibrationReport(
                agent=agent,
                n_predictions=n_predictions,
                n_resolved=0,
                brier_score=0.0,
                ece=0.0,
                accuracy=0.0,
                bins=empty_bins,
                window_start=start_iso,
                window_end=end_iso,
            )

        brier = 0.0
        accuracy = 0.0
        for row in pairs:
            conf = float(row["confidence"])
            label = float(row["actual_label"])
            brier += (conf - label) ** 2
            accuracy += 1.0 if label >= 0.5 else 0.0
        brier /= n_resolved
        accuracy /= n_resolved

        bin_totals: list[list[float]] = [[0.0, 0.0, 0] for _ in range(N_BINS)]
        for row in pairs:
            conf = float(row["confidence"])
            label = float(row["actual_label"])
            idx = min(int(conf * N_BINS), N_BINS - 1)
            if conf >= 1.0:
                idx = N_BINS - 1
            bin_totals[idx][0] += conf
            bin_totals[idx][1] += label
            bin_totals[idx][2] += 1

        bins: list[ReliabilityBin] = []
        ece = 0.0
        for i, (sum_conf, sum_label, count) in enumerate(bin_totals):
            if count > 0:
                mean_p = sum_conf / count
                mean_o = sum_label / count
                ece += (count / n_resolved) * abs(mean_p - mean_o)
            else:
                mean_p = 0.0
                mean_o = 0.0
            bins.append(
                ReliabilityBin(
                    lo=BIN_EDGES[i],
                    hi=BIN_EDGES[i + 1],
                    count=count,
                    mean_predicted=mean_p,
                    mean_observed=mean_o,
                )
            )

        return CalibrationReport(
            agent=agent,
            n_predictions=n_predictions,
            n_resolved=n_resolved,
            brier_score=brier,
            ece=ece,
            accuracy=accuracy,
            bins=bins,
            window_start=start_iso,
            window_end=end_iso,
        )


# ── Singleton ─────────────────────────────────────────────────────────────────

_tracker: CalibrationTracker | None = None
_tracker_lock = threading.Lock()


def get_calibration_tracker() -> CalibrationTracker:
    """Return the process-wide CalibrationTracker singleton."""
    global _tracker
    if _tracker is None:
        with _tracker_lock:
            if _tracker is None:
                _tracker = CalibrationTracker()
    return _tracker


def reset_calibration_tracker() -> None:
    """Drop the singleton (used by tests)."""
    global _tracker
    with _tracker_lock:
        _tracker = None


__all__ = [
    "CalibrationTracker",
    "CalibrationReport",
    "ReliabilityBin",
    "get_calibration_tracker",
    "reset_calibration_tracker",
    "N_BINS",
    "BIN_EDGES",
]
