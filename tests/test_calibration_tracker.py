"""tests/test_calibration_tracker.py — CalibrationTracker unit tests."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from meta_rl.calibration import (
    CalibrationTracker,
    N_BINS,
    get_calibration_tracker,
    reset_calibration_tracker,
)


class CalibrationTrackerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp()
        self.db = Path(self.tmpdir) / "test_calibration.db"
        self.tracker = CalibrationTracker(db_path=self.db)

    def test_schema_creates_tables(self) -> None:
        import sqlite3

        with sqlite3.connect(self.db) as conn:
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        self.assertIn("predictions", tables)
        self.assertIn("outcomes", tables)

    def test_record_and_resolve_round_trip(self) -> None:
        pid = self.tracker.record_prediction(
            agent="macro_agent",
            signal="LONG",
            confidence=70.0,
        )
        self.assertGreater(pid, 0)
        oid = self.tracker.record_outcome(pid, actual_label=1, pnl=1.5)
        self.assertGreater(oid, 0)
        report = self.tracker.get_calibration(agent="macro_agent", window_days=1)
        self.assertEqual(report.n_resolved, 1)
        self.assertEqual(report.n_predictions, 1)
        # Brier for (conf=0.7, label=1): (0.7 - 1)^2 = 0.09
        self.assertAlmostEqual(report.brier_score, 0.09, places=4)
        self.assertEqual(report.accuracy, 1.0)

    def test_confidence_clipped_to_unit_interval(self) -> None:
        # Confidence 150% should clip to 1.0
        pid = self.tracker.record_prediction("a", "LONG", 150.0)
        self.tracker.record_outcome(pid, 1)
        report = self.tracker.get_calibration(agent="a", window_days=1)
        self.assertEqual(report.brier_score, 0.0)
        self.assertEqual(report.accuracy, 1.0)

    def test_confidence_under_1_treated_as_fraction(self) -> None:
        pid = self.tracker.record_prediction("a", "LONG", 0.5)
        self.tracker.record_outcome(pid, 0)
        report = self.tracker.get_calibration(agent="a", window_days=1)
        # Brier for (0.5, 0) = 0.25
        self.assertAlmostEqual(report.brier_score, 0.25, places=4)

    def test_window_filter(self) -> None:
        # Insert old + new
        old_iso = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
        new_iso = datetime.now(timezone.utc).isoformat()

        old_pid = self.tracker.record_prediction("a", "LONG", 90.0, predicted_at=old_iso)
        self.tracker.record_outcome(old_pid, 0, observed_at=old_iso)

        new_pid = self.tracker.record_prediction("a", "LONG", 60.0, predicted_at=new_iso)
        self.tracker.record_outcome(new_pid, 1, observed_at=new_iso)

        report_30 = self.tracker.get_calibration(agent="a", window_days=30)
        self.assertEqual(report_30.n_resolved, 1)
        self.assertAlmostEqual(report_30.brier_score, (0.6 - 1) ** 2, places=4)

    def test_reliability_bins_shape(self) -> None:
        # 5 predictions, one in each of 5 different bins
        confs = [0.05, 0.25, 0.45, 0.65, 0.85]
        labels = [0, 1, 0, 1, 1]
        for c, l in zip(confs, labels):  # noqa: E741
            pid = self.tracker.record_prediction("a", "LONG", c * 100)
            self.tracker.record_outcome(pid, l)

        report = self.tracker.get_calibration(agent="a", window_days=1)
        self.assertEqual(len(report.bins), N_BINS)
        self.assertEqual(report.bins[0].lo, 0.0)
        self.assertEqual(report.bins[-1].hi, 1.0)
        total_in_bins = sum(b.count for b in report.bins)
        self.assertEqual(total_in_bins, len(confs))

    def test_empty_report(self) -> None:
        report = self.tracker.get_calibration(agent="ghost", window_days=7)
        self.assertEqual(report.n_resolved, 0)
        self.assertEqual(report.n_predictions, 0)
        self.assertEqual(report.brier_score, 0.0)
        self.assertEqual(report.ece, 0.0)
        self.assertEqual(len(report.bins), N_BINS)
        self.assertTrue(all(b.count == 0 for b in report.bins))

    def test_ece_perfect_calibration(self) -> None:
        # Perfect calibration: predicted probability == observed frequency per bin
        # Bin 0.0-0.1: 10 predictions at 0.05, 0 correct
        # Bin 0.9-1.0: 10 predictions at 0.95, 10 correct
        for _ in range(10):
            pid = self.tracker.record_prediction("a", "LONG", 5.0)
            self.tracker.record_outcome(pid, 0)
        for _ in range(10):
            pid = self.tracker.record_prediction("a", "LONG", 95.0)
            self.tracker.record_outcome(pid, 1)

        report = self.tracker.get_calibration(agent="a", window_days=1)
        # ECE should be very small (only 0.05 offset on each bin)
        self.assertLess(report.ece, 0.06)
        self.assertAlmostEqual(report.accuracy, 0.5, places=2)

    def test_invalid_label_rejected(self) -> None:
        pid = self.tracker.record_prediction("a", "LONG", 50.0)
        with self.assertRaises(ValueError):
            self.tracker.record_outcome(pid, 2)

    def test_singleton_returns_same_instance(self) -> None:
        a = get_calibration_tracker()
        b = get_calibration_tracker()
        self.assertIs(a, b)
        reset_calibration_tracker()
        c = get_calibration_tracker()
        self.assertIsNot(a, c)

    def test_to_dict_serializable(self) -> None:
        pid = self.tracker.record_prediction("a", "LONG", 60.0)
        self.tracker.record_outcome(pid, 1)
        report = self.tracker.get_calibration(agent="a", window_days=1)
        d = report.to_dict()
        self.assertIn("bins", d)
        self.assertIsInstance(d["bins"], list)
        self.assertEqual(len(d["bins"]), N_BINS)
        self.assertIn("brier_score", d)


if __name__ == "__main__":
    unittest.main()
