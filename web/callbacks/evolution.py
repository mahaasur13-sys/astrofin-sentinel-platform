"""Evolution tab callbacks — extracted from web/callbacks.py (Wave 2 P1-3).

Handles starting an evolution run and polling its live stats.
"""

from __future__ import annotations

import logging
import traceback

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import Input, Output, State, html

logger = logging.getLogger(__name__)


def _idle_status():
    empty_fig = go.Figure().update_layout(template="plotly_dark", height=220)
    return (
        html.Span(
            "No active evolution — configure and start above", className="text-muted"
        ),
        True,
        "—",
        "—",
        "—",
        "—",
        "—",
        "—",
        empty_fig,
        empty_fig,
    )


def register_evolution_callbacks(app, get_engine_ref):
    """Register evolution-run callbacks on the app."""

    @app.callback(
        Output("evolution-status", "children"),
        Output("evolution-interval", "disabled"),
        Output("current-gen-display", "children"),
        Output("best-reward-display", "children"),
        Output("mean-reward-display", "children"),
        Output("diversity-display", "children"),
        Output("trades-display", "children"),
        Output("karl-qstar-display", "children"),
        Output("evolution-chart", "figure"),
        Output("diversity-chart", "figure"),
        Input("start-evolution-btn", "n_clicks"),
        State("symbol-input", "value"),
        State("timeframe-input", "value"),
        State("gens-input", "value"),
        State("pop-input", "value"),
        State("walk-forward-toggle", "value"),
        prevent_initial_call=True,
    )
    def start_evolution(n_clicks, symbol, timeframe, gens, pop, walk_forward):
        if not n_clicks:
            return _idle_status()
        try:
            import time

            from meta_rl.config import WALK_FORWARD_ENABLED
            from meta_rl.evolution import EvolutionEngine
            from meta_rl.live_data import LiveDataProvider
            from meta_rl.meta_agent import EvolutionConfig, MetaAgent
            from meta_rl.strategy_evaluator import StrategyEvaluator

            provider = LiveDataProvider(sandbox=True, symbol=symbol)
            ohlcv = provider.fetch_ohlcv(symbol, timeframe)
            market_data = provider.to_market_data(ohlcv)
            wf = bool(walk_forward) and WALK_FORWARD_ENABLED
            cfg = EvolutionConfig(
                population_size=int(pop),
                elite_count=max(2, int(pop) // 5),
            )
            evaluator = StrategyEvaluator()
            agent = MetaAgent(evaluator=evaluator, config=cfg)
            engine = EvolutionEngine(
                agent=agent,
                market_data=market_data,
                max_generations=int(gens),
                walk_forward_enabled=wf,
                session_id=f"dash_{symbol.replace('/', '')}{int(time.time())}",
                visualize=False,
            )
            get_engine_ref._engine = engine
            empty_fig = go.Figure().update_layout(template="plotly_dark", height=220)
            return (
                html.Div(
                    [
                        dbc.Spinner(color="primary", size="sm"),
                        html.Span(f" Running {gens} gens..."),
                    ]
                ),
                False,
                "0",
                "—",
                "—",
                "—",
                "—",
                "—",
                empty_fig,
                empty_fig,
            )
        except Exception as e:
            logger.error(
                f"[DASH] Evolution start failed: {e}\n{traceback.format_exc()}"
            )
            empty_fig = go.Figure().update_layout(template="plotly_dark", height=220)
            return (
                html.Div(
                    [
                        html.Span("Error: ", className="text-danger"),
                        html.Span(str(e)[:200]),
                    ]
                ),
                True,
                "—",
                "—",
                "—",
                "—",
                "—",
                "—",
                empty_fig,
                empty_fig,
            )

    @app.callback(
        Output("evolution-status", "children"),
        Output("evolution-interval", "disabled"),
        Output("current-gen-display", "children"),
        Output("best-reward-display", "children"),
        Output("mean-reward-display", "children"),
        Output("diversity-display", "children"),
        Output("trades-display", "children"),
        Output("karl-qstar-display", "children"),
        Output("evolution-chart", "figure"),
        Output("diversity-chart", "figure"),
        Input("evolution-interval", "n_intervals"),
        State("gens-input", "value"),
        prevent_initial_call=True,
    )
    def poll_evolution(_n_intervals, gens):
        engine = getattr(get_engine_ref, "_engine", None)
        if engine is None:
            return _idle_status()
        hist = engine.stats_history
        current_gen = len(hist)
        progress = min(100, int(current_gen / max(1, int(gens)) * 100))
        if current_gen == 0:
            return (
                html.Span("Initializing..."),
                False,
                "0",
                "—",
                "—",
                "—",
                "—",
                "—",
                go.Figure().update_layout(template="plotly_dark", height=220),
                go.Figure().update_layout(template="plotly_dark", height=220),
            )
        latest = hist[-1]
        color = "success" if progress >= 100 else "info"
        # Build evolution chart
        fig = go.Figure()
        max_rw = [s.max_reward for s in hist]
        mean_rw = [s.mean_reward for s in hist]
        gens_nums = [s.generation for s in hist]
        fig.add_trace(
            go.Scatter(
                x=gens_nums,
                y=max_rw,
                mode="lines+markers",
                name="Best",
                line=dict(color="#00d4ff", width=2),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=gens_nums,
                y=mean_rw,
                mode="lines+markers",
                name="Mean",
                line=dict(color="#ffd600", dash="dot"),
            )
        )
        fig.update_layout(
            template="plotly_dark",
            height=220,
            margin=dict(l=40, r=20, t=20, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(
                title="Reward", showgrid=True, gridcolor="rgba(255,255,255,0.05)"
            ),
        )
        # Diversity chart
        div_fig = go.Figure()
        std_rw = [s.std_reward for s in hist]
        div_fig.add_trace(
            go.Bar(
                x=gens_nums,
                y=std_rw,
                name="Std Reward",
                marker_color="#ffd600",
                opacity=0.7,
            )
        )
        div_fig.update_layout(
            template="plotly_dark",
            height=220,
            margin=dict(l=40, r=20, t=20, b=30),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(
                title="Std Dev", showgrid=True, gridcolor="rgba(255,255,255,0.05)"
            ),
        )
        if progress >= 100:
            best = engine.get_best_strategy()
            best_id = best.id[:8] if best else "N/A"
            best_r = best.reward if best else 0.0
            best_sharpe = best.evaluation.sharpe if best and best.evaluation else 0.0
            trades = best.evaluation.trades if best and best.evaluation else 0
            status = html.Div(
                [
                    html.H6(
                        f"Complete! Best: {best_id}", className="text-success mb-1"
                    ),
                    dbc.Row(
                        [
                            dbc.Col(html.Span(f"Reward: {best_r:+.4f}")),
                            dbc.Col(html.Span(f"Sharpe: {best_sharpe:.3f}")),
                            dbc.Col(html.Span(f"Trades: {trades}")),
                        ]
                    ),
                ]
            )
            get_engine_ref._engine = None
            return (
                status,
                True,
                str(current_gen),
                f"{best_r:+.4f}",
                f"{latest.mean_reward:+.4f}",
                f"{latest.std_reward:.4f}",
                str(trades),
                f"{best_sharpe:.3f}",
                fig,
                div_fig,
            )
        else:
            karl_q = engine.agent.get_karl_state().get("current_q_star", 0.0)
            status = html.Div(
                [
                    html.Span(f"Gen {current_gen}/{gens}", className="fw-bold"),
                    html.Span(
                        f" | max: {latest.max_reward:+.4f} | mean: {latest.mean_reward:+.4f}"
                    ),
                    dbc.Progress(value=progress, color=color, className="mt-1"),
                ]
            )
            best_trades = (
                max(s.evaluation.trades for s in engine.agent.pool)
                if engine.agent.pool
                else 0
            )
            return (
                status,
                False,
                str(current_gen),
                f"{latest.max_reward:+.4f}",
                f"{latest.mean_reward:+.4f}",
                f"{latest.std_reward:.4f}",
                str(best_trades),
                f"{karl_q:+.3f}",
                fig,
                div_fig,
            )

    logger.debug("[DASH] Evolution callbacks registered")
