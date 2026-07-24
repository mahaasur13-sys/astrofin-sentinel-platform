"""web/components/evolution.py — Evolution tab (ATOM-META-RL-004)

Enhanced with real-time polling, live stats, progress tracking and professional quant UI.
"""

from __future__ import annotations
import dash_bootstrap_components as dbc
from dash import dcc, html


def evolution_tab() -> html.Div:
    return html.Div(
        [
            # ── Header ──
            dbc.Row(
                [
                    dbc.Col(
                        html.H4("▶ Evolution Control", className="mb-0 text-light"),
                        width=8,
                    ),
                    dbc.Col(
                        html.Span(
                            "ATOM-META-RL-004",
                            className="badge bg-warning text-dark float-end",
                            style={"fontSize": "0.75rem"},
                        ),
                        width=4,
                    ),
                ],
                className="mb-3 align-items-center",
            ),
            # ── Configuration Card ──
            dbc.Card(
                [
                    dbc.CardHeader(html.Span("Configuration", className="fw-bold")),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    # Symbol
                                    dbc.Col(
                                        [
                                            dbc.Label("Symbol", size="sm"),
                                            dbc.Select(
                                                id="symbol-input",
                                                options=[
                                                    {
                                                        "label": "BTC/USDT",
                                                        "value": "BTC/USDT",
                                                    },
                                                    {
                                                        "label": "ETH/USDT",
                                                        "value": "ETH/USDT",
                                                    },
                                                    {
                                                        "label": "SOL/USDT",
                                                        "value": "SOL/USDT",
                                                    },
                                                ],
                                                value="BTC/USDT",
                                            ),
                                        ],
                                        width=3,
                                    ),
                                    # Timeframe
                                    dbc.Col(
                                        [
                                            dbc.Label("Timeframe", size="sm"),
                                            dbc.Select(
                                                id="timeframe-input",
                                                options=[
                                                    {"label": "1 Hour", "value": "1h"},
                                                    {"label": "4 Hours", "value": "4h"},
                                                    {"label": "1 Day", "value": "1d"},
                                                ],
                                                value="1h",
                                            ),
                                        ],
                                        width=3,
                                    ),
                                    # Generations
                                    dbc.Col(
                                        [
                                            dbc.Label("Generations", size="sm"),
                                            dbc.Input(
                                                id="gens-input",
                                                value=8,
                                                type="number",
                                                min=1,
                                                max=100,
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    # Population
                                    dbc.Col(
                                        [
                                            dbc.Label("Population", size="sm"),
                                            dbc.Input(
                                                id="pop-input",
                                                value=20,
                                                type="number",
                                                min=5,
                                                max=200,
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    # Walk-Forward
                                    dbc.Col(
                                        [
                                            dbc.Label("Walk-Forward", size="sm"),
                                            dbc.Checklist(
                                                id="walk-forward-toggle",
                                                options=[
                                                    {"label": " Enabled", "value": 1}
                                                ],
                                                value=[1],
                                                switch=True,
                                                inline=True,
                                            ),
                                        ],
                                        width=2,
                                    ),
                                ],
                                className="align-items-end g-3",
                            ),
                            # Action Buttons
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            "▶ Start Evolution",
                                            id="start-evolution-btn",
                                            color="primary",
                                            size="lg",
                                            className="w-100",
                                            n_clicks=0,
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "⟳ Reset",
                                            id="reset-evolution-btn",
                                            color="outline-secondary",
                                            className="w-100",
                                            n_clicks=0,
                                        ),
                                        width=2,
                                    ),
                                ],
                                className="mt-4",
                            ),
                        ]
                    ),
                ],
                color="dark",
                outline=True,
                className="mb-4",
            ),
            # ── Progress & Live Stats Card ──
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.Span("Evolution Progress", className="fw-bold me-2"),
                            html.Span(id="evolution-spinner", className="ms-2"),
                            html.Span(
                                id="evolution-status",
                                children="Idle",
                                className="ms-3 text-info fw-bold",
                            ),
                        ]
                    ),
                    dbc.CardBody(
                        [
                            # Progress Bar
                            dbc.Progress(
                                id="progress-bar",
                                value=0,
                                color="info",
                                style={"height": "12px"},
                                className="mb-3",
                                animated=True,
                                striped=True,
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Small(
                                                "Progress", className="text-muted"
                                            ),
                                            html.Br(),
                                            html.Span(
                                                id="progress-pct",
                                                children="0%",
                                                className="fw-bold fs-5",
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                "Generation", className="text-muted"
                                            ),
                                            html.Br(),
                                            html.Span(
                                                id="current-gen-display",
                                                children="—",
                                                className="fw-bold text-info fs-5",
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                "Best Reward", className="text-muted"
                                            ),
                                            html.Br(),
                                            html.Span(
                                                id="best-reward-display",
                                                children="—",
                                                className="fw-bold text-success fs-5",
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                "Δ Best", className="text-muted"
                                            ),
                                            html.Br(),
                                            html.Span(
                                                id="delta-best-display",
                                                children="—",
                                                className="fw-bold",
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                "Mean ± Std", className="text-muted"
                                            ),
                                            html.Br(),
                                            html.Span(
                                                id="mean-std-display",
                                                children="—",
                                                className="fw-bold",
                                            ),
                                        ],
                                        width=2,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                "KARL Q*", className="text-muted"
                                            ),
                                            html.Br(),
                                            html.Span(
                                                id="karl-qstar-display",
                                                children="—",
                                                className="fw-bold text-info",
                                            ),
                                        ],
                                        width=1,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Small(
                                                "Diversity", className="text-muted"
                                            ),
                                            html.Br(),
                                            html.Span(
                                                id="diversity-display",
                                                children="—",
                                                className="fw-bold text-warning",
                                            ),
                                        ],
                                        width=1,
                                    ),
                                ],
                                className="text-center",
                            ),
                        ]
                    ),
                ],
                color="dark",
                outline=True,
                className="mb-4",
            ),
            # ── Live Charts Row ──
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Reward Convergence"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="evolution-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "320px"},
                                            )
                                        ]
                                    ),
                                ],
                                color="dark",
                                outline=True,
                            )
                        ],
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Population Diversity"),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="diversity-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "320px"},
                                            )
                                        ]
                                    ),
                                ],
                                color="dark",
                                outline=True,
                            )
                        ],
                        width=4,
                    ),
                ]
            ),
            # ── Hidden Stores & Interval ──
            dcc.Store(
                id="evolution-store",
                data={
                    "running": False,
                    "session_id": None,
                    "prev_best": None,
                    "history": [],
                },
            ),
            dcc.Interval(
                id="evolution-interval", interval=3000, disabled=True, n_intervals=0
            ),
        ],
        className="p-3",
    )
