#!/usr/bin/env python3
"""ROMA Plugin API Specification — Lifecycle hooks, execution contract, sandbox."""

import hashlib
import json
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Protocol


class PluginPhase(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERING = "recovering"


class PluginCapability(Enum):
    GPU_ENABLED = "gpu_enabled"
    DISTRIBUTED = "distributed"
    STATEFUL = "stateful"
    SIDE_EFFECTS = "side_effects"
    NETWORK_ACCESS = "network_access"
    PERSISTENT_STORAGE = "persistent_storage"


class PluginPriority(Enum):
    CRITICAL = 0  # preemption-capable
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class IPlugin(ABC):
    """Plugin interface — all ROMA plugins must implement this contract."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def version(self) -> str: ...

    @property
    @abstractmethod
    def capabilities(self) -> list[PluginCapability]: ...

    @property
    @abstractmethod
    def priority(self) -> PluginPriority: ...

    @abstractmethod
    async def on_init(self, config: dict[str, Any]) -> None: ...

    @abstractmethod
    async def on_execute(self, task: "ROMATask", context: "ExecutionContext") -> "PluginResult": ...

    @abstractmethod
    async def on_validate(self, task: "ROMATask") -> "ValidationResult": ...

    @abstractmethod
    async def on_cleanup(self) -> None: ...


class IExecutionContext(Protocol):
    """Execution context injected by ROMA scheduler."""

    gpu_available: bool
    vram_gb: float
    cpu_cores: int
    ram_gb: int
    node_name: str
    tick: int


class ROMATask:
    """Immutable task object — plugin receives this."""

    def __init__(
        self,
        task_id: str,
        plugin_name: str,
        payload: dict[str, Any],
        metadata: dict[str, Any],
    ):
        self.task_id = task_id
        self.plugin_name = plugin_name
        self.payload = payload
        self.metadata = metadata
        self._created_at = time.time()
        self._hash = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

    @property
    def fingerprint(self) -> str:
        return self._hash


class PluginResult:
    """Immutable result — plugin returns this."""

    def __init__(self, success: bool, output: Any = None, error: str = None, metrics: dict = None):
        self.success = success
        self.output = output
        self.error = error
        self.metrics = metrics or {}
        self._timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metrics": self.metrics,
            "timestamp": self._timestamp,
        }


class ValidationResult:
    def __init__(self, valid: bool, errors: list[str] = None):
        self.valid = valid
        self.errors = errors or []


# =============================================================================
# Built-in Plugins (reference implementations)
# =============================================================================


class MLTrainingPlugin(IPlugin):
    """ML training workload plugin — reference implementation."""

    @property
    def name(self) -> str:
        return "ml_training"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> list[PluginCapability]:
        return [PluginCapability.GPU_ENABLED, PluginCapability.DISTRIBUTED]

    @property
    def priority(self) -> PluginPriority:
        return PluginPriority.HIGH

    async def on_init(self, config: dict[str, Any]) -> None:
        self.config = config

    async def on_execute(self, task: ROMATask, context: IExecutionContext) -> PluginResult:
        # Simulate GPU training execution
        batch_size = task.payload.get("batch_size", 8)
        epochs = task.payload.get("epochs", 10)
        gpu_mem = batch_size * 0.7  # ~700MB per batch
        duration = epochs * 2.5

        if context.gpu_available and context.vram_gb >= gpu_mem:
            return PluginResult(
                success=True,
                output={
                    "model_trained": True,
                    "epochs_completed": epochs,
                    "gpu_used": context.node_name,
                    "vram_gb": gpu_mem,
                },
                metrics={"vram_gb": gpu_mem, "duration_s": duration},
            )
        return PluginResult(success=False, error="Insufficient GPU resources")

    async def on_validate(self, task: ROMATask) -> ValidationResult:
        required = ["model_type", "dataset", "batch_size"]
        missing = [f for f in required if f not in task.payload]
        return ValidationResult(valid=not missing, errors=missing)

    async def on_cleanup(self) -> None:
        pass


class InferencePlugin(IPlugin):
    """Inference workload plugin."""

    @property
    def name(self) -> str:
        return "inference"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> list[PluginCapability]:
        return [PluginCapability.GPU_ENABLED]

    @property
    def priority(self) -> PluginPriority:
        return PluginPriority.CRITICAL

    async def on_execute(self, task: ROMATask, context: IExecutionContext) -> PluginResult:
        model = task.payload.get("model", "unknown")
        return PluginResult(
            success=True,
            output={
                "inference_id": task.task_id,
                "model": model,
                "node": context.node_name,
            },
        )

    async def on_init(self, config: dict[str, Any]) -> None:
        pass

    async def on_validate(self, task: ROMATask) -> ValidationResult:
        return ValidationResult(valid=True)

    async def on_cleanup(self) -> None:
        pass


class ETLPipelinePlugin(IPlugin):
    """ETL pipeline workload plugin."""

    @property
    def name(self) -> str:
        return "etl_pipeline"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> list[PluginCapability]:
        return [PluginCapability.STATEFUL, PluginCapability.PERSISTENT_STORAGE]

    @property
    def priority(self) -> PluginPriority:
        return PluginPriority.NORMAL

    async def on_execute(self, task: ROMATask, context: IExecutionContext) -> PluginResult:
        return PluginResult(success=True, output={"pipeline_id": task.task_id, "stage": "completed"})

    async def on_init(self, config: dict[str, Any]) -> None:
        pass

    async def on_validate(self, task: ROMATask) -> ValidationResult:
        return ValidationResult(valid=True)

    async def on_cleanup(self) -> None:
        pass


class SimulationPlugin(IPlugin):
    """Simulation workload plugin."""

    @property
    def name(self) -> str:
        return "simulation"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def capabilities(self) -> list[PluginCapability]:
        return [PluginCapability.GPU_ENABLED, PluginCapability.DISTRIBUTED]

    @property
    def priority(self) -> PluginPriority:
        return PluginPriority.LOW

    async def on_execute(self, task: ROMATask, context: IExecutionContext) -> PluginResult:
        return PluginResult(success=True, output={"sim_id": task.task_id})

    async def on_init(self, config: dict[str, Any]) -> None:
        pass

    async def on_validate(self, task: ROMATask) -> ValidationResult:
        return ValidationResult(valid=True)

    async def on_cleanup(self) -> None:
        pass


# Registry
PLUGIN_REGISTRY = {
    "ml_training": MLTrainingPlugin,
    "inference": InferencePlugin,
    "etl_pipeline": ETLPipelinePlugin,
    "simulation": SimulationPlugin,
}


def get_plugin(name: str) -> IPlugin:
    cls = PLUGIN_REGISTRY.get(name)
    if not cls:
        raise ValueError(f"Plugin '{name}' not registered")
    return cls()
