"""Live tab callbacks — extracted from web/callbacks.py (Wave 2 P1-3).

Real-time metrics polling and system-status panel, plus the live-data status
badge helper (``render_live_status``, ATOM-META-RL-007).
"""

from __future__ import annotations

import logging

import dash_bootstrap_components as dbc
from dash import Input, Output, html

logger = logging.getLogger(__name__)


def register_live_callbacks(app):
    """Register live-metrics and system-status callbacks on the app."""

    @app.callback(
        Output("live-metrics", "children"),
        Input("live-interval", "n_intervals"),
    )
    def poll_live_metrics(n):
        from meta_rl.persistence import get_persistence

        p = get_persistence()
        summary = p.get_sessions_summary()
        best = summary.get("max_reward", 0.0)
        total = summary.get("total_sessions", 0)
        strategies = summary.get("total_strategies", 0)
        return dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3(f"{total}", className="mb-0 text-info"),
                                html.Small("Total Sessions"),
                            ]
                        )
                    ),
                    width=4,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3(f"{strategies}", className="mb-0 text-warning"),
                                html.Small("Strategies Evolved"),
                            ]
                        )
                    ),
                    width=4,
                ),
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H3(f"{best:+.4f}", className="mb-0 text-success"),
                                html.Small("Best Reward"),
                            ]
                        )
                    ),
                    width=4,
                ),
            ]
        )

    @app.callback(
        Output("system-status-display", "children"),
        Input("status-interval", "n_intervals"),
    )
    def update_system_status(n):
        from meta_rl.config import (
            LIVE_DATA_ENABLED,
            META_RL_ENABLED,
            WALK_FORWARD_ENABLED,
        )
        from meta_rl.persistence import get_persistence

        p = get_persistence()
        summary = p.get_sessions_summary()
        rows = [
            html.Tr(
                [
                    html.Td("Meta-RL"),
                    html.Td("🟢 Active" if META_RL_ENABLED else "🔴 Disabled"),
                ]
            ),
            html.Tr(
                [
                    html.Td("Live Data"),
                    html.Td("🟢 Connected" if LIVE_DATA_ENABLED else "⚪ Sandbox"),
                ]
            ),
            html.Tr(
                [
                    html.Td("Walk-Forward"),
                    html.Td("🟢 Enabled" if WALK_FORWARD_ENABLED else "⚪ Disabled"),
                ]
            ),
            html.Tr(
                [html.Td("Sessions"), html.Td(f"{summary.get('total_sessions', 0)}")]
            ),
            html.Tr(
                [
                    html.Td("Strategies"),
                    html.Td(f"{summary.get('total_strategies', 0)}"),
                ]
            ),
            html.Tr(
                [
                    html.Td("Best Reward"),
                    html.Td(
                        f"{summary.get('max_reward', 0):+.4f}", className="text-success"
                    ),
                ]
            ),
        ]
        return dbc.Table(
            [html.Thead(html.Tr([html.Th("Component"), html.Th("Status")]))]
            + [html.Tbody(rows)],
            bordered=False,
            size="sm",
            color=None,
            style={"background": "transparent"},
        )

    logger.debug("[DASH] Live callbacks registered")


# ── ATOM-META-RL-007: Live Data Status ──────────────────────────────────────
def render_live_status() -> html.Div:
    """Live data status panel for the dashboard header or Live tab."""
    try:
        from meta_rl.live_data import create_live_provider

        provider = create_live_provider("BTC/USDT")
        hc = provider.health_check()
        bundle = provider.get_latest_bars("BTC/USDT", "1h", 1)
        price = hc.get("last_price") or 0
        regime = bundle.get("regime", "UNKNOWN")
        regime_color = {
            "BULL": "success",
            "BEAR": "danger",
            "NEUTRAL": "secondary",
            "VOLATILE": "warning",
        }.get(regime, "secondary")
        return html.Div(
            [
                dbc.Badge(f"REGIME: {regime}", color=regime_color, className="me-2"),
                dbc.Badge(
                    f"MODE: {hc.get('mode', 'sandbox').upper()}",
                    color="info",
                    className="me-2",
                ),
                dbc.Badge(f"BTC: ${price:,.2f}", color="light", className="me-2"),
                dbc.Badge(
                    f"HALTH: {hc.get('status', 'OK')}",
                    color="success" if hc.get("status") == "OK" else "danger",
                ),
            ],
            className="d-flex align-items-center",
        )
    except Exception as e:
        return html.Div(dbc.Badge(f"Live Data Error: {e}", color="danger"))
