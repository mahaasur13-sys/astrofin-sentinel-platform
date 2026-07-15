"""web/components/__init__.py"""

from web.components.dashboard import dashboard_tab
from web.components.evolution import evolution_tab
from web.components.live import live_tab
from web.components.sessions import sessions_tab
from web.components.strategy_explorer import explorer_tab

__all__ = [
    "dashboard_tab",
    "evolution_tab",
    "sessions_tab",
    "explorer_tab",
    "live_tab",
]
