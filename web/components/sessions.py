"""web/components/sessions.py — Sessions tab (ATOM-META-RL-004)"""

from __future__ import annotations
import dash_bootstrap_components as dbc
from dash import dcc, html


def sessions_tab() -> html.Div:
    return html.Div(
        [
            dbc.Row(
                [
                    dbc.Col(
                        html.H4("📋 Evolution Sessions", className="mb-0 text-light"),
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
                className="mb-4 align-items-center",
            ),
            dbc.Card(
                [
                    dbc.CardHeader(
                        [
                            html.Span("Sessions", className="fw-bold"),
                            dbc.Button(
                                "↻ Refresh",
                                id="refresh-sessions-btn",
                                color="outline-secondary",
                                size="sm",
                                className="float-end",
                            ),
                        ]
                    ),
                    dbc.CardBody(
                        [
                            html.Div(
                                id="sessions-table-container",
                                children=html.Div(
                                    "Click Refresh to load sessions",
                                    className="text-muted p-3",
                                ),
                                style={"maxHeight": "320px", "overflowY": "auto"},
                            ),
                        ]
                    ),
                ],
                color="dark",
                outline=True,
                className="mb-4",
            ),
            dbc.Card(
                [
                    dbc.CardHeader(
                        html.Span(
                            "Session Comparison (select 2+ sessions above)",
                            className="fw-bold",
                        )
                    ),
                    dbc.CardBody(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dcc.Graph(
                                                id="comparison-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "300px"},
                                            ),
                                        ],
                                        width=7,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Div(id="comparison-table-container"),
                                        ],
                                        width=5,
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                "Session for Convergence Chart",
                                                size="sm",
                                            ),
                                            dcc.Dropdown(
                                                id="convergence-session-select",
                                                options=[],
                                                value=None,
                                                placeholder="Select session...",
                                            ),
                                        ],
                                        width=4,
                                    ),
                                ],
                                className="mt-3",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dcc.Graph(
                                                id="convergence-chart",
                                                config={
                                                    "displayModeBar": False,
                                                    "responsive": True,
                                                },
                                                style={"height": "250px"},
                                            ),
                                        ],
                                        width=12,
                                    ),
                                ]
                            ),
                        ]
                    ),
                ],
                color="dark",
                outline=True,
            ),
            dcc.Store(id="sessions-store", data=[]),
        ],
        className="p-3",
    )
