"""web/components/strategy_explorer.py — Strategy Explorer (ATOM-META-RL-005)

Enhanced with Deploy to KARL, Paper Test, Signal Example, Alpha Decay Badge,
Export JSON/Python, Backtest buttons.
"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def _alpha_badge(risk_adj_pnl, sharpe, trades):
    """Color-coded alpha decay / out-of-sample health badge."""
    score = 0.0
    if sharpe > 1.5:
        score += 2
    elif sharpe > 1.0:
        score += 1
    if trades >= 10:
        score += 1
    if risk_adj_pnl and risk_adj_pnl > 0:
        score += 1
    if score >= 4:
        color, label = "success", "Healthy Alpha"
    elif score >= 2:
        color, label = "warning", "Mild Decay"
    else:
        color, label = "danger", "Alpha Decay"
    return dbc.Badge(label, color=color, pill=True, className="mt-1")


def explorer_tab() -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H4("\U0001f9ac Strategy Explorer", className="mb-0 text-light"),
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Span(
                                "\U0001f680 Deploy to KARL",
                                className="badge bg-success me-1 p-1",
                                style={"fontSize": "0.7rem"},
                            ),
                            html.Span(
                                "Paper Test",
                                className="badge bg-info me-1 p-1",
                                style={"fontSize": "0.7rem"},
                            ),
                            html.Span(
                                "Export",
                                className="badge bg-secondary p-1",
                                style={"fontSize": "0.7rem"},
                            ),
                        ],
                        width=6,
                        className="text-end",
                    ),
                ],
                className="mb-3 align-items-center",
            ),
            # Session + Strategy selectors
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Session", size="sm"),
                            dcc.Dropdown(
                                id="session-selector",
                                options=[{"label": "Loading...", "value": ""}],
                                value=None,
                                placeholder="Select session...",
                                clearable=True,
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Strategy", size="sm"),
                            dcc.Dropdown(
                                id="strategy-selector",
                                options=[{"label": "Select session first", "value": ""}],
                                value=None,
                                placeholder="Select strategy...",
                                clearable=True,
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Alpha Health", size="sm"),
                            html.Div(
                                id="alpha-badge",
                                children=dbc.Badge("—", color="secondary", pill=True),
                            ),
                        ],
                        width=1,
                    ),
                    dbc.Col(
                        [
                            dbc.Label("Actions", size="sm"),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button(
                                        "\U0001f680 Deploy",
                                        id="deploy-karl-btn",
                                        color="success",
                                        size="sm",
                                        disabled=True,
                                    ),
                                    dbc.Button(
                                        "\U0001f4b8 Paper",
                                        id="paper-test-btn",
                                        color="info",
                                        size="sm",
                                        outline=True,
                                        disabled=True,
                                    ),
                                    dbc.Button(
                                        "\u2b07 JSON",
                                        id="export-json-btn",
                                        color="secondary",
                                        size="sm",
                                        outline=True,
                                        disabled=True,
                                    ),
                                    dbc.Button(
                                        "\u2b07 Py",
                                        id="export-py-btn",
                                        color="secondary",
                                        size="sm",
                                        outline=True,
                                        disabled=True,
                                    ),
                                ],
                                size="sm",
                            ),
                        ],
                        width=3,
                    ),
                ],
                className="mb-3 align-items-end",
            ),
            # Strategy ID bar
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div(
                                id="strategy-id-display",
                                children=html.Span("No strategy selected", className="text-muted small"),
                            ),
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                "\U0001f3af Backtest Strategy",
                                id="backtest-btn",
                                color="warning",
                                size="sm",
                                outline=True,
                                disabled=True,
                                className="float-end",
                            ),
                        ],
                        width=8,
                        className="text-end",
                    ),
                ],
                className="mb-2",
            ),
            # Main content: 2-column
            dbc.Row(
                [
                    # Left: Chromosome
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Span(
                                            "\U0001f9ec Chromosome Parameters",
                                            className="fw-bold",
                                        )
                                    ),
                                    dbc.CardBody(
                                        id="strategy-chromosome-display",
                                        children=html.Div(
                                            "Select session + strategy to load",
                                            className="text-muted p-3 text-center",
                                        ),
                                    ),
                                ]
                            ),
                        ],
                        width=4,
                    ),
                    # Right: Charts grid
                    dbc.Col(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Card(
                                                [
                                                    dbc.CardHeader(
                                                        html.Span(
                                                            "\U0001f4ca Radar \u2014 Strategy Profile",
                                                            className="fw-bold",
                                                        )
                                                    ),
                                                    dbc.CardBody(
                                                        [
                                                            dcc.Graph(
                                                                id="radar-chart",
                                                                config={
                                                                    "displayModeBar": False,
                                                                    "responsive": True,
                                                                },
                                                                style={"height": "230px"},
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ],
                                        width=7,
                                    ),
                                    dbc.Col(
                                        [
                                            # Top KPIs
                                            dbc.Card(
                                                [
                                                    dbc.CardBody(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            html.Small("Reward"),
                                                                            html.Br(),
                                                                            html.Span(
                                                                                id="kpi-reward",
                                                                                children="\u2014",
                                                                                className="fs-5 fw-bold text-success",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            html.Small("Sharpe"),
                                                                            html.Br(),
                                                                            html.Span(
                                                                                id="kpi-sharpe",
                                                                                children="\u2014",
                                                                                className="fs-5 fw-bold text-info",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ],
                                                                className="mb-2",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            html.Small("Risk PnL"),
                                                                            html.Br(),
                                                                            html.Span(
                                                                                id="kpi-risk-pnl",
                                                                                children="\u2014",
                                                                                className="fs-5 fw-bold",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            html.Small("Trades"),
                                                                            html.Br(),
                                                                            html.Span(
                                                                                id="kpi-trades",
                                                                                children="\u2014",
                                                                                className="fs-5 fw-bold text-warning",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ],
                                                                className="mb-2",
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        [
                                                                            html.Small("Win Rate"),
                                                                            html.Br(),
                                                                            html.Span(
                                                                                id="kpi-winrate",
                                                                                children="\u2014",
                                                                                className="fs-5 fw-bold",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        [
                                                                            html.Small("Max DD"),
                                                                            html.Br(),
                                                                            html.Span(
                                                                                id="kpi-dd",
                                                                                children="\u2014",
                                                                                className="fs-5 fw-bold text-danger",
                                                                            ),
                                                                        ],
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                        ]
                                                    ),
                                                ],
                                                className="mb-2",
                                            ),
                                            # KARL Q* card
                                            dbc.Card(
                                                [
                                                    dbc.CardBody(
                                                        [
                                                            html.Small("KARL Q*"),
                                                            html.Br(),
                                                            html.Span(
                                                                id="kpi-karl-qstar",
                                                                children="\u2014",
                                                                className="fs-5 fw-bold text-info",
                                                            ),
                                                        ]
                                                    ),
                                                ]
                                            ),
                                        ],
                                        width=5,
                                    ),
                                ]
                            ),
                        ],
                        width=8,
                    ),
                ],
                className="mb-3",
            ),
            # Second row: Equity + Drawdown + Signals
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Span(
                                            "\U0001f4c8 Equity Curve + Drawdown Area",
                                            className="fw-bold",
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="strategy-equity-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "220px"},
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=7,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Span(
                                            "\U0001f4ca Signal Example (last 50 bars)",
                                            className="fw-bold",
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="signal-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "220px"},
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=5,
                    ),
                ],
                className="mb-3",
            ),
            # Third row: Reward History + Drawdown Analysis
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Span(
                                            "\U0001f501 Reward History Across Generations",
                                            className="fw-bold",
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="reward-history-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "200px"},
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader(
                                        html.Span(
                                            "\U0001f4c9 Drawdown Analysis",
                                            className="fw-bold",
                                        )
                                    ),
                                    dbc.CardBody(
                                        [
                                            dcc.Graph(
                                                id="drawdown-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "200px"},
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                        ],
                        width=6,
                    ),
                ]
            ),
            # Strategy data store (invisible)
            dcc.Store(id="selected-strategy-store", data={}),
            dcc.Store(id="explorer-store", data={}),
        ],
        className="p-3",
    )
