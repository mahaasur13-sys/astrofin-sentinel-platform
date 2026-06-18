"""web/sessions_callbacks.py — Sessions tab callbacks (ATOM-META-RL-004)"""

from __future__ import annotations
import logging

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import ALL, Input, Output, State, ctx, html

logger = logging.getLogger(__name__)


def register_sessions_callbacks(app):
    """Register all Sessions tab callbacks."""

    @app.callback(
        Output("sessions-table-container", "children"),
        Input("refresh-sessions-btn", "n_clicks"),
    )
    def refresh_sessions_table(_):
        from meta_rl.persistence import get_persistence

        p = get_persistence()
        sessions = p.list_sessions()
        sessions = sessions[-30:][::-1]

        if not sessions:
            return html.Div("No sessions found", className="text-muted p-3 text-center")

        rows = []
        for sid in sessions:
            meta = p.load_session_metadata(sid) or {}
            best = meta.get("best_reward", 0.0)
            n_strat = meta.get("n_strategies", "?")
            badge = "bg-success" if best > 0.7 else "bg-warning text-dark" if best > 0.4 else "bg-secondary"
            rows.append(
                html.Tr(
                    [
                        html.Td(
                            dbc.Checkbox(
                                id={"type": "session-check", "index": sid},
                                value=False,
                            )
                        ),
                        html.Td(html.Code(sid[:24], className="text-info small")),
                        html.Td(f"{best:+.4f}"),
                        html.Td(str(n_strat)),
                        html.Td(
                            html.Span(
                                className=f"badge {badge}",
                                children="🟢" if best > 0.7 else "⚪",
                            )
                        ),
                    ]
                )
            )

        return dbc.Table(
            [
                html.Thead(
                    html.Tr(
                        [
                            html.Th(""),
                            html.Th("Session ID"),
                            html.Th("Best Reward"),
                            html.Th("Strategies"),
                            html.Th("Status"),
                        ]
                    )
                )
            ]
            + [html.Tbody(rows)],
            bordered=True,
            hover=True,
            responsive=True,
            color="dark",
            size="sm",
        )

    @app.callback(
        Output("comparison-chart", "figure"),
        Input({"type": "session-check", "index": ALL}, "value"),
        State({"type": "session-check", "index": ALL}, "id"),
        prevent_initial_call=True,
    )
    def update_comparison(checks, ids):
        from web.utils.comparison import build_comparison_chart

        checked = [ctx.triggered_id["index"] for c, i in zip(checks, ids, strict=False) if c]
        if len(checked) < 2:
            return go.Figure().to_dict()

        from meta_rl.persistence import get_persistence

        p = get_persistence()
        records_by_session = {}
        for sid in checked:
            recs = p.load_scored_strategies(sid)
            if recs:
                records_by_session[sid] = recs
        if not records_by_session:
            return go.Figure().to_dict()
        return build_comparison_chart(records_by_session)

    @app.callback(
        Output("comparison-table-container", "children"),
        Input({"type": "session-check", "index": ALL}, "value"),
        State({"type": "session-check", "index": ALL}, "id"),
        prevent_initial_call=True,
    )
    def update_comparison_table(checks, ids):
        from web.utils.comparison import build_comparison_table

        checked = [ctx.triggered_id["index"] for c, i in zip(checks, ids, strict=False) if c]
        if len(checked) < 2:
            return html.Div("Select 2+ sessions above to compare", className="text-muted p-3")

        from meta_rl.persistence import get_persistence

        p = get_persistence()
        all_records = []
        for sid in checked:
            all_records.extend(p.load_scored_strategies(sid))
        all_records.sort(key=lambda r: r.get("reward", 0), reverse=True)
        table_html = build_comparison_table(all_records[:10])
        return html.Div(dangerously_set_inner_HTML=table_html)

    @app.callback(
        Output("convergence-session-select", "options"),
        Output("convergence-session-select", "value"),
        Input("refresh-sessions-btn", "n_clicks"),
    )
    def populate_convergence_select(_):
        from meta_rl.persistence import get_persistence

        p = get_persistence()
        sessions = p.list_sessions()
        opts = [{"label": s, "value": s} for s in sessions[-20:]]
        return opts, (opts[-1]["value"] if opts else None)

    @app.callback(
        Output("convergence-chart", "figure"),
        Input("convergence-session-select", "value"),
        prevent_initial_call=True,
    )
    def update_convergence_chart(session_id):
        if not session_id:
            return go.Figure().to_dict()
        from meta_rl.persistence import get_persistence
        from web.utils.comparison import build_convergence_chart

        p = get_persistence()
        meta = p.load_session_metadata(session_id) or {}
        gen_stats = meta.get("generation_stats", [])
        return build_convergence_chart(gen_stats)

    logger.info("[DASH] Sessions callbacks registered")
