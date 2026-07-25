"""Strategy Explorer callbacks — extracted from web/callbacks.py (Wave 2 P1-3).

Covers the Explorer tab: session/strategy selectors, deploy-to-KARL, paper test,
JSON/Python export, backtest, and the detailed strategy view (charts + KPIs).
"""

from __future__ import annotations

import logging

import dash
import dash_bootstrap_components as dbc
import numpy as np
import plotly.graph_objects as go
from dash import Input, Output, State, html

logger = logging.getLogger(__name__)


# ── Chart / badge helpers (module-level; were nested in the monolith) ────────
def _build_radar_fig(ev):
    labels = ["Sharpe", "Win Rate", "Trades", "Stability", "PnL"]
    metrics = [
        min(ev.get("sharpe", 0) / 3, 1),
        ev.get("win_rate", 0),
        min(ev.get("trades", 0) / 30, 1),
        max(0, 1 - ev.get("max_drawdown", 0)),
        (
            max(0, min((ev.get("risk_adjusted_pnl", 0) + 1) / 2, 1))
            if ev.get("risk_adjusted_pnl") is not None
            else 0.5
        ),
    ]
    fig = go.Figure(
        go.Scatterpolar(
            r=metrics + [metrics[0]],
            theta=labels + [labels[0]],
            fill="toself",
            line_color="#00d4ff",
            fillcolor="rgba(0,212,255,0.2)",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=220,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
        polar=dict(bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def _build_equity_and_dd(ec):
    fig = go.Figure()
    dd_fig = go.Figure()
    if ec and len(ec) > 1:
        arr = np.array(ec) if isinstance(ec, list) else ec
        if arr.ndim == 2 and arr.shape[1] > 1:
            arr = arr[:, 1]
        arr = arr.flatten()
        # Equity
        fig.add_trace(
            go.Scatter(
                y=arr,
                mode="lines",
                name="Equity",
                line=dict(color="#00d4ff", width=1.5),
                fill="tozeroy",
                fillcolor="rgba(0,212,255,0.15)",
            )
        )
        # Drawdown
        peak = np.maximum.accumulate(arr)
        dd_pct = (peak - arr) / peak * 100
        dd_fig.add_trace(
            go.Scatter(
                y=-dd_pct,
                mode="lines",
                fill="tozeroy",
                fillcolor="rgba(255,80,80,0.3)",
                line=dict(color="#ff5252", width=1),
                name="Drawdown %",
            )
        )
        max_dd = float(np.max(dd_pct))
        dd_fig.add_annotation(
            x=int(np.argmax(dd_pct)),
            y=-max_dd,
            text=f"Max: {max_dd:.1f}%",
            showarrow=True,
            arrowhead=2,
            font=dict(color="#ff5252", size=10),
        )
    for f in (fig, dd_fig):
        f.update_layout(
            template="plotly_dark",
            height=220,
            margin=dict(l=40, r=20, t=20, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(
                title="Equity" if f is fig else "Drawdown %",
                showgrid=True,
                gridcolor="rgba(255,255,255,0.05)",
            ),
        )
    return fig, dd_fig


def _build_signal_chart(ec):
    """Build a signal strip chart from equity curve returns."""
    fig = go.Figure()
    if not ec or len(ec) < 2:
        fig.update_layout(
            template="plotly_dark",
            height=220,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        return fig
    arr = np.array(ec)
    if arr.ndim == 2 and arr.shape[1] > 1:
        arr = arr[:, 1]
    arr = arr.flatten()
    rets = np.diff(arr) / arr[:-1]
    # Quantize signals: > 0.005 → LONG(+1), < -0.005 → SHORT(-1), else NEUTRAL(0)
    signals = np.where(rets > 0.005, 1, np.where(rets < -0.005, -1, 0))
    colors = np.where(
        signals == 1, "#00c853", np.where(signals == -1, "#ff1744", "#ffd600")
    )
    fig.add_trace(
        go.Bar(
            y=signals[-50:],
            marker_color=colors[-50:],
            name="Signal",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        height=220,
        margin=dict(l=40, r=10, t=20, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(
            title="Signal",
            tickvals=[-1, 0, 1],
            ticktext=["SHORT", "NEUT", "LONG"],
            showgrid=True,
            gridcolor="rgba(255,255,255,0.05)",
        ),
        showlegend=False,
    )
    return fig


def _alpha_badge(risk_adj_pnl, sharpe, trades):
    """Color-coded alpha decay / out-of-sample health badge."""
    score = 0
    if sharpe and sharpe > 1.5:
        score += 2
    elif sharpe and sharpe > 1.0:
        score += 1
    if trades and trades >= 10:
        score += 1
    if risk_adj_pnl and risk_adj_pnl > 0:
        score += 1
    if score >= 4:
        color, label = "success", "Healthy Alpha"
    elif score >= 2:
        color, label = "warning", "Mild Decay"
    else:
        color, label = "danger", "Alpha Decay"
    return dbc.Badge(label, color=color, pill=True)


def register_strategy_callbacks(app):
    """Register Strategy Explorer callbacks on the app."""

    @app.callback(
        Output("strategy-selector", "options"),
        Output("strategy-selector", "value"),
        Input("session-selector", "value"),
    )
    def load_session_strategies(session_id):
        if not session_id:
            return [], None
        from meta_rl.persistence import get_persistence

        p = get_persistence()
        records = p.load_scored_strategies(session_id)
        records.sort(key=lambda r: r.get("reward", 0), reverse=True)
        opts = [
            {
                "label": f"Gen {r.get('generation', 0)} | {r.get('reward', 0):+.4f} | {r.get('id', '?')[:6]}",
                "value": r.get("id", ""),
            }
            for r in records
        ]
        return opts, (opts[0]["value"] if opts else None)

    # ── Session selector population (Explorer tab uses same dropdown) ──────
    @app.callback(
        Output("session-selector", "options"),
        Output("session-selector", "value"),
        Input("main-tabs", "value"),
    )
    def populate_explorer_sessions(tab):
        if tab != "tab-explorer":
            raise dash.exceptions.PreventUpdate
        try:
            from meta_rl.persistence import get_persistence

            p = get_persistence()
            sessions = p.list_sessions()
            opts = [{"label": s, "value": s} for s in sessions[-50:]]
            return opts, (opts[-1]["value"] if opts else None)
        except Exception:
            return [], None

    # ══════════════════════════════════════════════════════════════════════════
    # EXPLORER: DEPLOY TO KARL
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("toast-container", "children", allow_duplicate=True),
        Output("deploy-karl-btn", "disabled"),
        Input("deploy-karl-btn", "n_clicks"),
        State("selected-strategy-store", "data"),
        prevent_initial_call=True,
    )
    def deploy_to_karl(n_clicks, strategy_data):
        if not n_clicks or not strategy_data:
            return dash.no_update, dash.no_update
        from web.utils.notifications import make_toast

        try:
            from meta_rl.meta_agent import MetaAgent
            from meta_rl.persistence import get_persistence
            from meta_rl.strategy_pool import ScoredStrategy

            sid = strategy_data.get("session_id", "")
            s_id = strategy_data.get("id", "")
            p = get_persistence()
            records = p.load_scored_strategies(sid)
            record = next((r for r in records if r.get("id") == s_id), None)
            if not record:
                return (
                    make_toast(
                        f"Strategy {s_id[:8]} not found in session",
                        "Deploy Failed",
                        "danger",
                    ),
                    dash.no_update,
                )
            ss = ScoredStrategy.from_dict(record)
            agent = MetaAgent()
            agent.pool.add(ss)
            karl_state = agent.update_karl([ss])
            qstar = karl_state.get("current_q_star", 0.0)
            return (
                make_toast(
                    f"Strategy {s_id[:8]} deployed to KARL. Q*={qstar:+.4f}",
                    "Deploy Success",
                    "success",
                ),
                True,
            )
        except Exception as e:
            return (
                make_toast(f"Deploy error: {e}", "Deploy Failed", "danger"),
                dash.no_update,
            )

    # ══════════════════════════════════════════════════════════════════════════
    # EXPLORER: PAPER TEST
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("toast-container", "children", allow_duplicate=True),
        Input("paper-test-btn", "n_clicks"),
        State("selected-strategy-store", "data"),
        prevent_initial_call=True,
    )
    def paper_test(n_clicks, strategy_data):
        if not n_clicks or not strategy_data:
            return dash.no_update
        from web.utils.notifications import make_toast

        msg = f"Paper test queued for {strategy_data.get('id', '?')[:8]}. Live paper mode coming soon."
        return make_toast(msg, "Paper Test", "info")

    # ══════════════════════════════════════════════════════════════════════════
    # EXPLORER: EXPORT JSON
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("toast-container", "children", allow_duplicate=True),
        Output("export-json-btn", "disabled"),
        Input("export-json-btn", "n_clicks"),
        State("selected-strategy-store", "data"),
        prevent_initial_call=True,
    )
    def export_json(n_clicks, strategy_data):
        if not n_clicks or not strategy_data:
            return dash.no_update, dash.no_update
        import json
        import os
        from datetime import datetime

        from web.utils.notifications import make_toast

        s_id = strategy_data.get("id", "unknown")
        safe = f"strategy_{s_id[:8]}_{datetime.now().strftime('%H%M%S')}.json"
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "exports"
        )
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, safe)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(strategy_data, f, indent=2, default=str, ensure_ascii=False)
        return (
            make_toast(f"Saved to data/exports/{safe}", "Export JSON", "success"),
            True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # EXPLORER: EXPORT PYTHON
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("toast-container", "children", allow_duplicate=True),
        Output("export-py-btn", "disabled"),
        Input("export-py-btn", "n_clicks"),
        State("selected-strategy-store", "data"),
        prevent_initial_call=True,
    )
    def export_python(n_clicks, strategy_data):
        if not n_clicks or not strategy_data:
            return dash.no_update, dash.no_update
        import os
        from datetime import datetime

        from web.utils.notifications import make_toast

        s_id = strategy_data.get("id", "unknown")
        safe = f"strategy_{s_id[:8]}_{datetime.now().strftime('%H%M%S')}.py"
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "exports"
        )
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, safe)
        chrom = strategy_data.get("strategy_params", {})
        py_code = (
            f'"""strategy/{safe} — Generated by AstroFinSentinelV5"""\n'
            f"from strategies.generator import GeneratedStrategy\n\n"
            f"DEFAULT_CHROMOSOME = {repr(chrom)}\n\n"
            f"def make_strategy() -> GeneratedStrategy:\n"
            f'    return GeneratedStrategy.from_dict({{"chromosome": DEFAULT_CHROMOSOME}})\n'
        )
        with open(path, "w", encoding="utf-8") as f:
            f.write(py_code)
        return (
            make_toast(f"Saved to data/exports/{safe}", "Export Python", "success"),
            True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # EXPLORER: BACKTEST
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("toast-container", "children", allow_duplicate=True),
        Input("backtest-btn", "n_clicks"),
        State("selected-strategy-store", "data"),
        prevent_initial_call=True,
    )
    def backtest_strategy(n_clicks, strategy_data):
        if not n_clicks or not strategy_data:
            return dash.no_update
        from web.utils.notifications import make_toast

        msg = f"Backtest queued for {strategy_data.get('id', '?')[:8]}. Results in Sessions tab."
        return make_toast(msg, "Backtest Queued", "info")

    # ══════════════════════════════════════════════════════════════════════════
    # EXPLORER: UPDATED show_strategy_detail — now also updates KPIs, badge, signals
    # ══════════════════════════════════════════════════════════════════════════
    @app.callback(
        Output("strategy-chromosome-display", "children"),
        Output("strategy-equity-chart", "figure"),
        Output("radar-chart", "figure"),
        Output("drawdown-chart", "figure"),
        Output("reward-history-chart", "figure"),
        Output("signal-chart", "figure"),
        Output("alpha-badge", "children"),
        Output("kpi-reward", "children"),
        Output("kpi-sharpe", "children"),
        Output("kpi-risk-pnl", "children"),
        Output("kpi-trades", "children"),
        Output("kpi-winrate", "children"),
        Output("kpi-dd", "children"),
        Output("kpi-karl-qstar", "children"),
        Output("strategy-id-display", "children"),
        Output("selected-strategy-store", "data"),
        Output("deploy-karl-btn", "disabled", allow_duplicate=True),
        Output("paper-test-btn", "disabled", allow_duplicate=True),
        Output("export-json-btn", "disabled", allow_duplicate=True),
        Output("export-py-btn", "disabled", allow_duplicate=True),
        Output("backtest-btn", "disabled", allow_duplicate=True),
        Input("strategy-selector", "value"),
        State("session-selector", "value"),
        prevent_initial_call=True,
    )
    def show_strategy_detail(sid, session_id):
        def empty_fig():
            return go.Figure().update_layout(template="plotly_dark", height=220)

        if not sid or not session_id:
            return (
                html.Div("Select a strategy"),
                empty_fig(),
                empty_fig(),
                empty_fig(),
                empty_fig(),
                empty_fig(),
                dash.no_update,
                "\u2014",
                "\u2014",
                "\u2014",
                "\u2014",
                "\u2014",
                "\u2014",
                "\u2014",
                html.Span("No strategy selected", className="text-muted small"),
                {},
                True,
                True,
                True,
                True,
                True,
            )

        from meta_rl.persistence import get_persistence

        p = get_persistence()
        records = p.load_scored_strategies(session_id)
        record = next((r for r in records if r.get("id") == sid), None)
        if not record:
            return (
                (html.Div("Strategy not found"),)
                + (empty_fig(),) * 5
                + (
                    dash.no_update,
                    "\u2014",
                    "\u2014",
                    "\u2014",
                    "\u2014",
                    "\u2014",
                    "\u2014",
                    html.Span("Not found", className="text-danger small"),
                    {},
                    True,
                    True,
                    True,
                    True,
                    True,
                )
            )

        chrom = record.get("strategy_params", {})
        ev = record.get("evaluation", {})
        rh = record.get("reward_history", [])
        eval_dict = record.get("evaluation", {})

        # Alpha badge
        alpha = _alpha_badge(
            risk_adj_pnl=eval_dict.get("risk_adjusted_pnl"),
            sharpe=eval_dict.get("sharpe", 0),
            trades=eval_dict.get("trades", 0),
        )

        # KPIs
        r = eval_dict.get("sharpe", 0)
        sharpe_str = f"{r:.2f}" if r else "\u2014"
        pnl = eval_dict.get("risk_adjusted_pnl")
        pnl_str = f"{pnl:+.3f}" if pnl is not None else "\u2014"
        tr = eval_dict.get("trades", 0)
        wr = eval_dict.get("win_rate", 0)
        wr_str = f"{wr:.0%}" if wr else "\u2014"
        dd = eval_dict.get("max_drawdown", 0)
        dd_str = f"{dd:.1%}" if dd else "\u2014"
        reward_val = record.get("reward", 0)
        reward_str = f"{reward_val:+.4f}" if reward_val else "\u2014"
        karl_q = ev.get("sharpe", 0)  # reuse sharpe as KARL proxy
        karl_str = f"{karl_q:+.3f}"

        # Strategy ID bar
        id_display = html.Div(
            [
                html.Code(sid[:12], className="text-info me-2"),
                html.Span(
                    f"Gen {record.get('generation', '?')} \u2022 ",
                    className="text-muted small",
                ),
                html.Span(
                    f"reward={reward_str}", className="text-success small fw-bold"
                ),
            ]
        )

        # Chromosome table
        rows = [
            html.Tr(
                [
                    html.Td(k, className="small text-muted"),
                    html.Td(str(v), className="small font-monospace"),
                ]
            )
            for k, v in sorted(chrom.items())
        ]
        chrom_html = dbc.Table(
            (
                [html.Thead(html.Tr([html.Th("Parameter"), html.Th("Value")]))]
                + [html.Tbody(rows)]
                if rows
                else [html.Tbody()]
            ),
            bordered=False,
            size="sm",
        )

        equity_fig, dd_fig = _build_equity_and_dd(ev.get("equity_curve", []))
        radar_fig = _build_radar_fig(eval_dict)

        # Reward history
        rh_fig = go.Figure()
        if rh:
            rh_fig.add_trace(
                go.Scatter(
                    y=list(rh),
                    mode="lines+markers",
                    name="Reward",
                    line=dict(color="#00d4ff", width=2),
                    marker=dict(size=5),
                )
            )
        rh_fig.update_layout(
            template="plotly_dark",
            height=200,
            margin=dict(l=40, r=20, t=20, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(
                title="Reward", showgrid=True, gridcolor="rgba(255,255,255,0.05)"
            ),
        )

        # Signal chart (simulate from equity curve)
        sig_fig = _build_signal_chart(ev.get("equity_curve", []))
        record["session_id"] = session_id
        return (
            chrom_html,
            equity_fig,
            radar_fig,
            dd_fig,
            rh_fig,
            sig_fig,
            alpha,
            reward_str,
            sharpe_str,
            pnl_str,
            str(tr),
            wr_str,
            dd_str,
            karl_str,
            id_display,
            record,
            False,
            False,
            False,
            False,
            False,
        )

    logger.debug("[DASH] Strategy Explorer callbacks registered")
