"""Callbacks package — decomposed from the monolithic web/callbacks.py (Wave 2 P1-3).

The former 1032-line god-object is split into domain modules:

    routing.py      → register_routing_callbacks(app)
    evolution.py    → register_evolution_callbacks(app, engine_ref)
    live.py         → register_live_callbacks(app)
    strategy.py     → register_strategy_callbacks(app)
    sessions.py     → register_session_callbacks(app)

``register_all_callbacks(app, engine_ref)`` aggregates every domain registrar
and is the single entry point used by web/app.py.

Note: the header clock (``update_clock`` → ``header-time``) is registered inline
by web/app.py, so it is intentionally not duplicated here.
"""

from __future__ import annotations

import logging

from web.callbacks.evolution import register_evolution_callbacks
from web.callbacks.live import register_live_callbacks, render_live_status
from web.callbacks.routing import register_routing_callbacks
from web.callbacks.sessions import register_session_callbacks
from web.callbacks.strategy import register_strategy_callbacks

logger = logging.getLogger(__name__)


def register_all_callbacks(app, get_engine_ref):
    """Register every domain's callbacks on the Dash ``app``.

    Args:
        app: the Dash application instance.
        get_engine_ref: shared engine-reference object used by the evolution
            callbacks to persist the running EvolutionEngine between polls.
    """
    register_routing_callbacks(app)
    register_evolution_callbacks(app, get_engine_ref)
    register_live_callbacks(app)
    register_strategy_callbacks(app)
    register_session_callbacks(app)
    logger.info("[DASH] All callbacks registered (Wave 2 P1-3 modular split)")


__all__ = [
    "register_all_callbacks",
    "register_routing_callbacks",
    "register_evolution_callbacks",
    "register_live_callbacks",
    "register_strategy_callbacks",
    "register_session_callbacks",
    "render_live_status",
]
