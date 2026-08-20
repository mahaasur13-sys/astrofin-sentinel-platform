"""Settings plugin — manage plugins, keys, tiers."""
from __future__ import annotations


class Plugin:
    def on_enable(self) -> None:
        pass

    def get_settings_sections(self) -> list[dict]:
        return [
            {"id": "plugins", "label": "Plugins", "icon": "puzzle"},
            {"id": "api-keys", "label": "API Keys", "icon": "key"},
            {"id": "tiers", "label": "Tiers", "icon": "layers"},
            {"id": "account", "label": "Account", "icon": "user"},
        ]
