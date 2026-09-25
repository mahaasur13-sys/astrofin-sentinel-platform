"""Dashboard plugin — main metrics and status view."""
from __future__ import annotations


class Plugin:
    def on_enable(self) -> None:
        pass

    def get_dashboard_data(self, manager) -> dict:
        plugins = manager.list_all()
        return {
            "total_plugins": len(plugins),
            "active_plugins": sum(1 for p in plugins if p["status"] == "active"),
            "system_health": "healthy",
            "uptime_seconds": 0,
        }
