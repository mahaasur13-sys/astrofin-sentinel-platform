#!/usr/bin/env python3
"""ROMA Operator SDK — Plugin → Declarative Controller Framework."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class CRDSpec:
    apiVersion: str
    kind: str
    version: str
    plural: str
    schema: Dict[str, Any]
    validation_rules: List[str]
    defaults: Dict[str, Any]

class RomaOperator(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def version(self) -> str: ...
    @abstractmethod
    def define_crd(self) -> CRDSpec: ...
    @abstractmethod
    def reconcile(self, desired_state: Dict, current_state: Dict) -> Dict: ...
    def watch_events(self) -> List[str]:
        return ["ADD", "UPDATE", "DELETE"]
    def default_policy(self) -> Dict[str, Any]:
        return {}

def plugin_to_crd(plugin_class) -> CRDSpec:
    """Auto-generate CRD spec from plugin capabilities."""
    name = plugin_class.__name__.replace("Plugin", "").lower()
    kind = plugin_class.__name__.replace("Plugin", "")
    caps = list(plugin_class().capabilities) if hasattr(plugin_class, 'capabilities') else []
    resources = plugin_class().get_resource_requirements({}) if hasattr(plugin_class, 'get_resource_requirements') else {}
    gpu = any("GPU" in str(c) for c in caps)
    schema = {
        "gpu_required": {"type": "boolean", "default": gpu},
        "memory": {"type": "string", "default": resources.get("memory", "8Gi")},
        "cpu": {"type": "string", "default": resources.get("cpu", "2")},
    }
    return CRDSpec(
        apiVersion="roma.io/v1",
        kind=kind,
        version="v1",
        plural=f"{name.lower()}s",
        schema=schema,
        validation_rules=["gpu_required must be boolean"],
        defaults={"priority": "NORMAL"},
    )

def generate_controller_code(operator_class, name: str) -> str:
    return f"""\
# Auto-generated controller: {name}
class {name}Reconciler:
    operator = "{name}"
    def reconcile(self, desired, current):
        return {{"status": "reconciled"}}
    def desired_state(self, spec):
        return spec
"""

def generate_crd_yaml(crd: CRDSpec) -> str:
    schema_lines = []
    for k, v in crd.schema.items():
        schema_lines.append(f"            {k}:")
        schema_lines.append(f"              type: {v.get('type', 'string')}")
    return f"""\
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: {crd.plural}.roma.io
spec:
  group: roma.io
  names:
    kind: {crd.kind}
    plural: {crd.plural}
  scope: Namespaced
  versions:
    - name: {crd.version}
      served: true
      storage: true
  schema:
    openAPIV3Schema:
      type: object
      properties:
        spec:
          type: object
          properties:
{chr(10).join(schema_lines)}
"""
