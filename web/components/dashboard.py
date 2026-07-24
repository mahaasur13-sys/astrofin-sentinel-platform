"""web/components/dashboard.py — Dashboard overview (ATOM-META-RL-004)"""

from __future__ import annotations
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import dcc, html


def dashboard_tab():
    from meta_rl.persistence import get_persistence

    p = get_persistence()
    summary = p.get_sessions_summary()
    total = summary.get("total_sessions", 0)
    strategies = summary.get("total_strategies", 0)
    best = summary.get("max_reward", 0.0)
    mean = summary.get("mean_reward", 0.0)

    return html.Div(
        [
            dbc.Row(
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
                        width=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3(
                                        f"{strategies}", className="mb-0 text-warning"
                                    ),
                                    html.Small("Strategies Evolved"),
                                ]
                            )
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3(
                                        f"{best:+.4f}", className="mb-0 text-success"
                                    ),
                                    html.Small("Best Reward"),
                                ]
                            )
                        ),
                        width=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.H3(
                                        f"{mean:+.4f}", className="mb-0 text-secondary"
                                    ),
                                    html.Small("Mean Reward"),
                                ]
                            )
                        ),
                        width=3,
                    ),
                ],
                className="mb-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("System Status"),
                                    dbc.CardBody(
                                        [
                                            html.Div(id="system-status-display"),
                                            dcc.Interval(
                                                id="status-interval",
                                                interval=10000,
                                                n_intervals=0,
                                            ),
                                        ]
                                    ),
                                ],
                                color="dark",
                                outline=True,
                            ),
                        ],
                        width=12,
                    ),
                ],
                className="mb-4",
            ),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Small(
                                f"AstroFinSentinelV5 • Meta-RL Dashboard • "
                                f"Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                className="text-muted",
                            )
                        ],
                        width=12,
                    ),
                ]
            ),
        ]
    )
