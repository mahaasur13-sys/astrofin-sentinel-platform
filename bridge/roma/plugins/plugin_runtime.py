#!/usr/bin/env python3
"""ROMA Plugin Runtime Loader — Isolation, versioning, lifecycle management."""
import time
from pathlib import Path
from typing import Dict, List, Any, Type
from enum import Enum
from dataclasses import dataclass, field

class IsolationLevel(Enum):
    PROCESS = "process"
    CONTAINER = "container"
    SANDBOX = "sandbox"

class PluginVersion:
    def __init__(self, major: int, minor: int, patch: int):
        self.major, self.minor, self.patch = major, minor, patch
    def __str__(self) -> str: return f"{self.major}.{self.minor}.{self.patch}"
    def __lt__(self, other): return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

@dataclass
class PluginSpec:
    name: str
    version: PluginVersion
    entry_point: str
    isolation: IsolationLevel
    capabilities: List[str]
    priority: int
    config_schema: Dict[str, Any]
    checksum: str
    loaded_at: float = field(default_factory=time.time)

@dataclass
class PluginInstance:
    spec: PluginSpec
    plugin_class: Type
    instance: Any
    phase: str = "initializing"
    execution_count: int = 0
    error_count: int = 0

class PluginRuntime:
    def __init__(self, plugin_dir: str = "/home/workspace/roma-execution-bridge/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self._loaded: Dict[str, PluginInstance] = {}
        self._hooks: Dict[str, List] = {
            "on_load": [], "on_unload": [], "on_execute_before": [],
            "on_execute_after": [], "on_scheduler_tick": [],
        }

    def register_hook(self, hook_name: str, callback: callable) -> None:
        if hook_name not in self._hooks:
            raise ValueError(f"Unknown hook: {hook_name}")
        self._hooks[hook_name].append(callback)

    def load_from_class(self, plugin_class: Type, plugin_name: str, version: str = "1.0.0") -> PluginInstance:
        spec = PluginSpec(
            name=plugin_name,
            version=PluginVersion(*map(int, version.split("."))),
            entry_point=f"class:{plugin_class.__name__}",
            isolation=IsolationLevel.PROCESS,
            capabilities=getattr(plugin_class, 'capabilities', []),
            priority=getattr(plugin_class, 'priority', 2),
            config_schema={}, checksum="builtin"
        )
        instance_obj = plugin_class()
        plugin_inst = PluginInstance(spec=spec, plugin_class=plugin_class, instance=instance_obj)
        self._loaded[plugin_name] = plugin_inst
        for cb in self._hooks["on_load"]:
            cb(plugin_inst)
        print(f"  Loaded plugin: {plugin_name} v{version}")
        return plugin_inst

    def execute_plugin_sync(self, plugin_name: str, task: Any, context: Any) -> Dict:
        """Sync wrapper for plugin execution."""
        if plugin_name not in self._loaded:
            raise ValueError(f"Plugin not loaded: {plugin_name}")
        inst = self._loaded[plugin_name]
        for cb in self._hooks["on_execute_before"]:
            cb(inst, task)
        inst.instance.phase = "running"

        import asyncio
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(inst.instance.on_execute(task, context))
        loop.close()

        inst.execution_count += 1
        for cb in self._hooks["on_execute_after"]:
            cb(inst, task, result)
        return result.to_dict()

    def list_loaded(self) -> List[Dict]:
        return [{"name": k, "version": str(v.spec.version), "phase": v.phase,
                 "executions": v.execution_count, "errors": v.error_count}
                for k, v in self._loaded.items()]

def main():
    from plugin_api import PLUGIN_REGISTRY
    runtime = PluginRuntime()

    for name, cls in PLUGIN_REGISTRY.items():
        runtime.load_from_class(cls, name, "1.0.0")

    print("\nLoaded plugins:")
    for p in runtime.list_loaded():
        print(f"  {p['name']} v{p['version']} | phase={p['phase']} | executions={p['executions']}")

    class DemoTask:
        task_id = "task-001"
        plugin_name = "ml_training"
        payload = {"batch_size": 8, "epochs": 10}
        metadata = {}
        fingerprint = "abc123"

    class DemoContext:
        gpu_available = True
        vram_gb = 10.5
        cpu_cores = 8
        ram_gb = 32
        node_name = "gpu-node-1"
        tick = 1

    print("\nExecuting ml_training plugin:")
    result = runtime.execute_plugin_sync("ml_training", DemoTask(), DemoContext())
    print(f"  Result: {result}")

    print("\nExecuting inference plugin:")
    task2 = type('Task', (), {'task_id': 'task-002', 'plugin_name': 'inference',
                               'payload': {'model': 'llama3-8b'}, 'metadata': {}, 'fingerprint': 'x'})()
    result2 = runtime.execute_plugin_sync("inference", task2, DemoContext())
    print(f"  Result: {result2}")

    print("\nPlugin execution complete.")

if __name__ == "__main__":
    main()
