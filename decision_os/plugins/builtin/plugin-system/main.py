"""Plugin System plugin — manages plugin lifecycle, marketplace, discovery."""
from __future__ import annotations


class Plugin:
    def on_enable(self) -> None:
        pass
