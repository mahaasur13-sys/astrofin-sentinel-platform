"""web/components/live.py — Live monitoring tab (ATOM-META-RL-003)"""

import dash_bootstrap_components as dbc
from dash import dcc, html


def live_tab():
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(html.H4("Live Monitoring")),
                    dbc.Col(
                        dbc.Checklist(
                            id="live-enabled-toggle",
                            options=[{"label": " Live Mode", "value": 1}],
                            value=[],
                            switch=True,
                        ),
                        width="auto",
                    ),
                ],
                className="mb-3 align-items-center",
            ),
            # Live KPIs
            html.Div(id="live-metrics", className="mb-3"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Market Data Stream"),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="live-price-display"),
                                            html.Hr(),
                                            html.Div(id="live-regime-display"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Current Best Strategy"),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="live-best-strategy"),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("System Status"),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="live-status"),
                                            html.Hr(),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Span("Sessions: "),
                                                        width="auto",
                                                    ),
                                                    dbc.Col(
                                                        html.Span(
                                                            id="live-sessions-count",
                                                            children="—",
                                                        ),
                                                        width="auto",
                                                    ),
                                                ]
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Span("Strategies: "),
                                                        width="auto",
                                                    ),
                                                    dbc.Col(
                                                        html.Span(
                                                            id="live-strategies-count",
                                                            children="—",
                                                        ),
                                                        width="auto",
                                                    ),
                                                ]
                                            ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        html.Span("Last update: "),
                                                        width="auto",
                                                    ),
                                                    dbc.Col(
                                                        html.Span(
                                                            id="live-last-update",
                                                            children="—",
                                                        ),
                                                        width="auto",
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        width=4,
                    ),
                ],
                className="mb-3",
            ),
            dbc.Row(
                [
                    dbc.Col([dcc.Graph(id="live-equity-chart")], width=8),
                    dbc.Col([dcc.Graph(id="live-diversity-chart")], width=4),
                ]
            ),
            dcc.Interval(id="live-interval", interval=10000, n_intervals=0),
        ]
    )
