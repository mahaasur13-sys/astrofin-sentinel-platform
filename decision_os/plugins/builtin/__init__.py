"""Built-in DecisionOS plugins.

Each subdirectory is a plugin with manifest.json + main.py.
The Plugin class in main.py follows the PluginBase interface contract
(loaded dynamically, not via import chain).
"""

BUILTIN_PLUGINS = [
    "policy-engine",
    "decision-gate",
    "crypto-payments",
    "crypto-wallets",
    "support-chat",
    "plugin-system",
    "menu",
    "dashboard",
    "settings",
]
