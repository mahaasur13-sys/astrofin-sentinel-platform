#!/usr/bin/env python3
"""ROMA Operator SDK — Plugin → CRD → Controller transformation."""
import logging
import sys

log = logging.getLogger(__name__)

sys.path.insert(0, "/home/workspace/roma-execution-bridge")
from operator_sdk.operator_base import generate_controller_code, generate_crd_yaml, plugin_to_crd


class PluginToOperatorConverter:
    def __init__(self):
        self._converted = {}

    def convert(self, plugin_class) -> dict:
        name = plugin_class.__name__.replace("Plugin", "")
        crd = plugin_to_crd(plugin_class)
        yaml = generate_crd_yaml(crd)
        code = generate_controller_code(plugin_class, name)
        self._converted[name] = {"crd_yaml": yaml, "controller_code": code, "schema": crd.schema}
        return self._converted[name]

if __name__ == "__main__":
    from plugins.ml_training import MLTrainingPlugin
    conv = PluginToOperatorConverter()
    result = conv.convert(MLTrainingPlugin)
    log.info("=== Generated CRD YAML ===")
    log.info(result["crd_yaml"][:800])
    log.info("\n=== Controller Code ===")
    log.info(result["controller_code"][:600])
    log.info("\n✅ Plugin → Operator transformation complete")
