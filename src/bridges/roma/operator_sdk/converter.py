#!/usr/bin/env python3
"""ROMA Operator SDK — Plugin → CRD → Controller transformation."""

import sys

sys.path.insert(0, "/home/workspace/roma-execution-bridge")
from operator_sdk.operator_base import (
    plugin_to_crd,
    generate_controller_code,
    generate_crd_yaml,
)


class PluginToOperatorConverter:
    def __init__(self):
        self._converted = {}

    def convert(self, plugin_class) -> dict:
        name = plugin_class.__name__.replace("Plugin", "")
        crd = plugin_to_crd(plugin_class)
        yaml = generate_crd_yaml(crd)
        code = generate_controller_code(plugin_class, name)
        self._converted[name] = {
            "crd_yaml": yaml,
            "controller_code": code,
            "schema": crd.schema,
        }
        return self._converted[name]


if __name__ == "__main__":
    from plugins.ml_training import MLTrainingPlugin

    conv = PluginToOperatorConverter()
    result = conv.convert(MLTrainingPlugin)
    print("=== Generated CRD YAML ===")
    print(result["crd_yaml"][:800])
    print("\n=== Controller Code ===")
    print(result["controller_code"][:600])
    print("\n✅ Plugin → Operator transformation complete")
