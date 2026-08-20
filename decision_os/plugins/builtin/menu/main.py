"""Menu plugin — renders left sidebar from active plugins."""
from __future__ import annotations


class Plugin:
    def on_enable(self) -> None:
        pass

    def get_menu_items(self) -> list[dict]:
        return [
            {"id": "dashboard", "label": "Dashboard", "icon": "layout-dashboard", "route": "/"},
            {"id": "analytics", "label": "Analytics", "icon": "chart-bar", "route": "/analytics"},
            {"id": "support", "label": "Support", "icon": "headset", "route": "/support"},
            {"id": "settings", "label": "Settings", "icon": "settings", "route": "/settings"},
        ]
