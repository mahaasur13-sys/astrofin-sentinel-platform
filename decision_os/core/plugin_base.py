"""DecisionOS PluginBase — abstract base for all plugins."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .plugin_manager import HookSystem, PluginRegistry, Sandbox


class PluginBase:
    plugin_id: str = ""
    manifest: dict = {}
    hook_system: "HookSystem" | None = None
    registry: "PluginRegistry" | None = None
    sandbox: "Sandbox" | None = None

    def on_enable(self) -> None:
        pass

    def on_disable(self) -> None:
        pass

    def on_unload(self) -> None:
        pass
