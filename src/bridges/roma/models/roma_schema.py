"""ROMA JSON Schema — input model validation."""

from typing import Literal, Optional
from pydantic import BaseModel, Field


class ResourceSpec(BaseModel):
    cpu_cores: int = 1
    memory_gb: int = 2
    gpu_required: bool = False
    vram_gb: Optional[float] = None
    gpu_model: Optional[str] = None  # e.g. "RTX3060"


class TaskStep(BaseModel):
    id: str
    type: Literal["data", "train", "validate", "inference", "build", "system"]
    command: str
    image: str
    depends_on: list[str] = Field(default_factory=list)
    resources: ResourceSpec = Field(default_factory=ResourceSpec)


class SecurityConfig(BaseModel):
    privileged: bool = False
    host_network: bool = False
    host_path_allowed: bool = False
    allow_root: bool = True


class ROMAInput(BaseModel):
    """Full ROMA JSON structure expected from Planner."""
    task_id: str
    analysis: dict
    dag: list[TaskStep]
    resources: ResourceSpec
    execution: dict
    security: SecurityConfig
    observability: dict
    notes: Optional[str] = None


def parse_roma_json(raw: dict) -> ROMAInput:
    """Parse and validate incoming ROMA JSON."""
    return ROMAInput(**raw)


def validate_structure(raw: dict) -> tuple[bool, str]:
    """Validate required top-level keys."""
    required = ["task_id", "analysis", "dag", "resources", "execution"]
    missing = [k for k in required if k not in raw]
    if missing:
        return False, f"Missing keys: {missing}"
    if not isinstance(raw.get("dag"), list):
        return False, "Field 'dag' must be a list"
    return True, "ok"
