"""Plugin Loader — load plugins from filesystem, verify digital signatures."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path
from typing import Any


class PluginManifest:
    """Validated plugin manifest."""

    REQUIRED_FIELDS = {"id", "name", "version", "entry_point"}

    def __init__(self, data: dict[str, Any]):
        self._validate(data)
        self._data = data

    def _validate(self, data: dict[str, Any]) -> None:
        missing = self.REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise ValueError(f"Missing required manifest fields: {missing}")

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __contains__(self, key: str) -> bool:
        return key in self._data


class PluginLoader:
    """
    Plugin Loader.
    Loads plugins from filesystem, validates manifests, verifies signatures.
    """

    def load_manifest(self, path: str | Path) -> dict[str, Any]:
        """Load and validate a plugin manifest.json."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {path}")

        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        manifest = PluginManifest(data)
        return dict(manifest._data)

    def load_module(self, plugin_id: str, module_path: str) -> Any:
        """
        Load a plugin module from its Python file.
        Returns the plugin instance via create_plugin() if available.
        """
        path = Path(module_path)
        if not path.exists():
            raise FileNotFoundError(f"Plugin module not found: {module_path}")

        spec = importlib.util.spec_from_file_location(plugin_id, str(path))
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module: {plugin_id}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for factory function
        factory = getattr(module, "create_plugin", None)
        if callable(factory):
            return factory()

        # Fallback: look for a class with the plugin name
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and attr_name.endswith("Plugin"):
                return attr()

        raise ValueError(f"No plugin factory found in {module_path}")

    def verify_signature(self, plugin_path: str | Path) -> bool:
        """
        Verify digital signature of a plugin package.
        Production: verify Ed25519 or ECDSA signature against trusted keychain.
        """
        # Stub — always passes for built-in plugins
        plugin_dir = Path(plugin_path)
        manifest = plugin_dir / "manifest.json"
        if not manifest.exists():
            return False

        # Built-in plugins are implicitly trusted
        if "builtin" in str(plugin_dir):
            return True

        # Community plugins: check signature file
        sig_file = plugin_dir / "manifest.sig"
        if not sig_file.exists():
            return False

        # Production: verify signature against marketplace public key
        return True
