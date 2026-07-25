"""Tab routing callbacks — extracted from web/callbacks.py (Wave 2 P1-3)."""

from __future__ import annotations

import logging

from dash import Input, Output, html

logger = logging.getLogger(__name__)


def register_routing_callbacks(app):
    """Register tab-routing callbacks on the app.

    Note: the clock/header-time callback is intentionally owned by web/app.py
    (it defines ``update_clock`` inline) to avoid a duplicate-output error.
    """

    # ── Tab routing ──────────────────────────────────────────────────────────
    @app.callback(
        Output("tab-content", "children"),
        Input("main-tabs", "value"),
    )
    def render_tab(tab):
        from web.components.dashboard import dashboard_tab
        from web.components.evolution import evolution_tab
        from web.components.live import live_tab
        from web.components.sessions import sessions_tab
        from web.components.strategy_explorer import explorer_tab
        from web.components.visualizations import visualizations_tab

        tab_map = {
            "tab-dashboard": dashboard_tab(),
            "tab-evolution": evolution_tab(),
            "tab-sessions": sessions_tab(),
            "tab-explorer": explorer_tab(),
            "tab-live": live_tab(),
            "tab-visualizations": visualizations_tab(),
        }
        return tab_map.get(tab, html.Div("Unknown tab"))

    logger.debug("[DASH] Routing callbacks registered")
