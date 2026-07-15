"""meta_rl/reports.py — ATOM-META-RL-006: HTML/PDF Report Generator (P1.2)

Auto-generates evolution reports after each run:
  - Generation-by-generation reward curve
  - Top strategies table with composite scores
  - Walk-forward overfit report (if WFA enabled)
  - KARL state snapshot
  - Strategy chromosome details

Feature flag: HTML_REPORTS_ENABLED (default True)
Output: data/meta_rl/reports/<session_id>.html
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from meta_rl.config import (
    HTML_REPORTS_ENABLED,
    REPORTS_BASE_URL,
    REPORTS_OUTPUT_DIR,
)

logger = logging.getLogger(__name__)


class HTMLReportGenerator:
    """
    Generates standalone HTML reports for evolution sessions.

    Usage:
        gen = HTMLReportGenerator()
        path = gen.generate(
            session_id="btc_run_001",
            history=stats_history,
            elites=ranked_strategies,
            overfit_report=wfa_report,
            karl_state=karl_snapshot,
        )
    """

    def __init__(self, output_dir: str | None = None, base_url: str | None = ""):
        self.enabled = HTML_REPORTS_ENABLED
        self.output_dir = Path(output_dir or REPORTS_OUTPUT_DIR)
        self.base_url = base_url or REPORTS_BASE_URL
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        session_id: str,
        history: list[Any],
        elites: list[Any],
        overfit_report: Any | None = None,
        karl_state: dict | None = None,
        symbol: str = "BTC/USDT",
        metadata: dict | None = None,
    ) -> str:
        """
        Generate HTML report for a completed evolution session.

        Returns:
            Absolute path to the generated HTML file.
        """
        if not self.enabled:
            logger.info("[REPORTS] HTML reports disabled (HTML_REPORTS_ENABLED=false)")
            return ""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
        metadata = metadata or {}

        # Extract history data for chart
        gen_nums = [h.generation for h in history]
        max_rewards = [h.max_reward for h in history]
        mean_rewards = [h.mean_reward for h in history]

        # Extract top strategy
        top = elites[0] if elites else None
        top_info = self._format_top_strategy(top)

        # Overfit summary
        overfit_html = self._format_overfit(overfit_report)

        # KARL state
        karl_html = self._format_karl(karl_state)

        html = _HTML_TEMPLATE.format(
            session_id=session_id,
            timestamp=timestamp,
            symbol=symbol,
            gen_nums=_js_array(gen_nums),
            max_rewards=_js_array([round(r, 4) for r in max_rewards]),
            mean_rewards=_js_array([round(r, 4) for r in mean_rewards]),
            n_gens=len(history),
            n_elites=len(elites),
            best_reward=top_info.get("reward", "N/A"),
            best_sharpe=top_info.get("sharpe", "N/A"),
            best_dd=top_info.get("dd", "N/A"),
            best_trades=top_info.get("trades", "N/A"),
            top_strategy_table=self._strategies_table(elites),
            overfit_section=overfit_html,
            karl_section=karl_html,
            generation_rows=self._history_rows(history),
        )

        out_path = self.output_dir / f"{session_id}.html"
        out_path.write_text(html)
        logger.info(f"[REPORTS] Saved → {out_path}")
        return str(out_path)

    def _format_top_strategy(self, top) -> dict:
        if not top:
            return {"reward": "N/A", "sharpe": "N/A", "dd": "N/A", "trades": "N/A"}
        ev = getattr(top, "evaluation", None)
        reward = f"{getattr(top, 'reward', 0):+.4f}"
        sharpe = f"{getattr(ev, 'sharpe', 0):.3f}" if ev else "N/A"
        dd = f"{getattr(ev, 'max_drawdown', 0):.2%}" if ev else "N/A"
        trades = str(getattr(ev, "trades", 0)) if ev else "N/A"
        return {"reward": reward, "sharpe": sharpe, "dd": dd, "trades": trades}

    def _format_overfit(self, report) -> str:
        if not report:
            return "<tr><td colspan='4' class='text-muted'>No WFA data available</td></tr>"
        try:
            flag = getattr(report, "overall_overfit_flag", False)
            splits = getattr(report, "overfit_splits", 0)
            n_splits = getattr(report, "n_splits", 0)
            mean_oos = f"{getattr(report, 'mean_oos_sharpe', 0):.3f}"
            mean_is = f"{getattr(report, 'mean_is_sharpe', 0):.3f}"
            deg = f"{getattr(report, 'mean_degradation', 0):+.3f}"
            status = "⚠️ OVERFIT" if flag else "✅ PASSED"
            cls = "danger" if flag else "success"
            rows = ""
            for s in getattr(report, "splits", [])[:10]:
                rows += f"<tr><td>{s.split_index}</td><td>{s.is_sharpe:.3f}</td>"
                rows += f"<td>{s.oos_sharpe:.3f}</td><td>{s.sharpe_degradation:+.3f}</td></tr>"
            return f"""
            <table class='table table-sm'>
                <thead><tr><th>Split</th><th>IS Sharpe</th><th>OOS Sharpe</th><th>Degradation</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <div class='alert alert-{cls}'>Status: {status} | OOS={mean_oos} | IS={mean_is} | deg={deg} | overfit splits={splits}/{n_splits}</div>
            """
        except Exception as e:
            return f"<tr><td colspan='4' class='text-muted'>WFA error: {e}</td></tr>"

    def _format_karl(self, state: dict | None) -> str:
        if not state:
            return "<p class='text-muted'>No KARL state snapshot available</p>"
        try:
            lines = []
            for k, v in list(state.items())[:10]:
                val = f"{v:.4f}" if isinstance(v, float) else str(v)
                lines.append(f"<li><strong>{k}</strong>: {val}</li>")
            return f"<ul>{''.join(lines)}</ul>"
        except Exception as e:
            return f"<p class='text-muted'>KARL state error: {e}</p>"

    def _strategies_table(self, elites: list[Any]) -> str:
        if not elites:
            return "<tr><td colspan='7' class='text-muted'>No elite strategies</td></tr>"
        rows = ""
        for rank, e in enumerate(elites[:20], 1):
            ev = getattr(e, "evaluation", None)
            reward = f"{getattr(e, 'reward', 0):+.4f}"
            sharpe = f"{getattr(ev, 'sharpe', 0):.3f}" if ev else "N/A"
            wr = f"{getattr(ev, 'win_rate', 0):.0%}" if ev else "N/A"
            dd = f"{getattr(ev, 'max_drawdown', 0):.2%}" if ev else "N/A"
            trades = str(getattr(ev, "trades", 0)) if ev else "N/A"
            sid = getattr(e, "id", "?")[:12]
            rows += f"<tr><td>{rank}</td><td>{sid}</td><td>{reward}</td>"
            rows += f"<td>{sharpe}</td><td>{wr}</td><td>{dd}</td><td>{trades}</td></tr>"
        return rows

    def _history_rows(self, history: list[Any]) -> str:
        rows = ""
        for h in history[-50:]:  # last 50 gens
            gen = h.generation
            max_r = f"{h.max_reward:+.4f}"
            mean_r = f"{h.mean_reward:+.4f}"
            karl = "✓" if h.karl_updated else ""
            rows += f"<tr><td>{gen}</td><td>{max_r}</td><td>{mean_r}</td><td>{karl}</td></tr>"
        return rows


def _js_array(values: list[float]) -> str:
    return "[" + ", ".join(str(v) for v in values) + "]"


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meta-RL Report: {session_id}</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {{ background: #0d1117; color: #e6edf3; font-family: 'Segoe UI', sans-serif; }}
.card {{ background: #161b22; border: 1px solid #30363d; }}
.table {{ color: #e6edf3; }}
.table thead {{ background: #21262d; }}
.badge.bg-success {{ background: #238636 !important; }}
.badge.bg-danger {{ background: #da3633 !important; }}
.badge.bg-warning {{ background: #9e6a03 !important; }}
#rewardChart {{ width: 100%; height: 300px; }}
.alert-success {{ background: #0d1f17; border: 1px solid #238636; color: #3fb950; }}
.alert-danger {{ background: #1f1015; border: 1px solid #da3633; color: #f85149; }}
</style>
</head>
<body>
<div class="container-fluid py-4">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h2>🧬 AstroFin Sentinel — Meta-RL Report</h2>
    <small class="text-muted">{timestamp}</small>
  </div>

  <!-- Summary cards -->
  <div class="row mb-4">
    <div class="col-md-2">
      <div class="card p-3 text-center">
        <div class="text-muted small">Session</div>
        <div class="fs-5 text-warning">{session_id}</div>
      </div>
    </div>
    <div class="col-md-2">
      <div class="card p-3 text-center">
        <div class="text-muted small">Symbol</div>
        <div class="fs-5">{symbol}</div>
      </div>
    </div>
    <div class="col-md-2">
      <div class="card p-3 text-center">
        <div class="text-muted small">Generations</div>
        <div class="fs-4 text-info">{n_gens}</div>
      </div>
    </div>
    <div class="col-md-2">
      <div class="card p-3 text-center">
        <div class="text-muted small">Elites</div>
        <div class="fs-4">{n_elites}</div>
      </div>
    </div>
    <div class="col-md-2">
      <div class="card p-3 text-center">
        <div class="text-muted small">Best Reward</div>
        <div class="fs-4 text-success">{best_reward}</div>
      </div>
    </div>
    <div class="col-md-2">
      <div class="card p-3 text-center">
        <div class="text-muted small">Best Sharpe</div>
        <div class="fs-4 text-info">{best_sharpe}</div>
      </div>
    </div>
  </div>

  <!-- Reward chart -->
  <div class="card p-4 mb-4">
    <h5 class="card-title">📈 Reward Progression</h5>
    <canvas id="rewardChart"></canvas>
  </div>

  <!-- Top strategies -->
  <div class="card p-4 mb-4">
    <h5 class="card-title">🏆 Top Strategies (Composite Ranking)</h5>
    <table class="table table-hover">
      <thead>
        <tr><th>#</th><th>Strategy ID</th><th>Reward</th><th>Sharpe</th><th>Win Rate</th><th>Max DD</th><th>Trades</th></tr>
      </thead>
      <tbody>{top_strategy_table}</tbody>
    </table>
  </div>

  <!-- Generation history -->
  <div class="card p-4 mb-4">
    <h5 class="card-title">📋 Generation History</h5>
    <table class="table table-sm table-hover">
      <thead><tr><th>Gen</th><th>Max Reward</th><th>Mean Reward</th><th>KARL Update</th></tr></thead>
      <tbody>{generation_rows}</tbody>
    </table>
  </div>

  <!-- WFA / Overfit -->
  <div class="card p-4 mb-4">
    <h5 class="card-title">🔬 Walk-Forward Overfit Analysis</h5>
    {overfit_section}
  </div>

  <!-- KARL State -->
  <div class="card p-4 mb-4">
    <h5 class="card-title">🧠 KARL State Snapshot</h5>
    {karl_section}
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('rewardChart').getContext('2d');
new Chart(ctx, {{
  type: 'line',
  data: {{
    labels: {gen_nums},
    datasets: [
      {{
        label: 'Max Reward',
        data: {max_rewards},
        borderColor: '#3fb950',
        backgroundColor: 'rgba(63,185,80,0.1)',
        fill: true,
        tension: 0.3,
      }},
      {{
        label: 'Mean Reward',
        data: {mean_rewards},
        borderColor: '#58a6ff',
        backgroundColor: 'rgba(88,166,255,0.1)',
        fill: true,
        tension: 0.3,
      }}
    ]
  }},
  options: {{
    responsive: true,
    plugins: {{ legend: {{ labels: {{ color: '#e6edf3' }} }} }},
    scales: {{
      x: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }},
      y: {{ ticks: {{ color: '#8b949e' }}, grid: {{ color: '#30363d' }} }}
    }}
  }}
}});
</script>
</body>
</html>"""


def generate_report(
    session_id: str,
    history: list[Any],
    elites: list[Any],
    overfit_report: Any | None = None,
    karl_state: dict | None = None,
    **kwargs,
) -> str:
    """Convenience function — generate HTML report."""
    gen = HTMLReportGenerator()
    return gen.generate(
        session_id=session_id,
        history=history,
        elites=elites,
        overfit_report=overfit_report,
        karl_state=karl_state,
        **kwargs,
    )
