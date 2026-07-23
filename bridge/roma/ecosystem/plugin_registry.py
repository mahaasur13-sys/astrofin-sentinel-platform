"""ROMA Plugin Registry — Discovery, versioning, dependency resolution."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


@dataclass
class PluginMetadata:
    name: str
    version: str
    capabilities: list[str]
    resource_requirements: dict[str, any]
    dependencies: list[str] = field(default_factory=list)
    hash_sha256: str = ""
    published_at: float = 0.0


class PluginRegistry:
    def __init__(self):
        self.plugins: dict[str, dict[str, PluginMetadata]] = {}
        self.index: dict[str, set[str]] = {}

    def register(self, meta: PluginMetadata):
        if meta.name not in self.plugins:
            self.plugins[meta.name] = {}
        self.plugins[meta.name][meta.version] = meta
        for cap in meta.capabilities:
            if cap not in self.index:
                self.index[cap] = set()
            self.index[cap].add(meta.name)

    def get_latest_version(self, name: str) -> str | None:
        if name not in self.plugins:
            return None
        versions = sorted(self.plugins[name].keys())
        return versions[-1] if versions else None

    def search(self, query: str) -> list[str]:
        q = query.lower()
        return [p for p in self.plugins if q in p.lower()]

    def resolve_dependencies(self, name: str, version: str = "latest") -> list[str]:
        if version == "latest":
            version = self.get_latest_version(name) or ""
        if name not in self.plugins or version not in self.plugins[name]:
            return []
        meta = self.plugins[name][version]
        resolved = []
        for dep in meta.dependencies:
            dep_ver = self.get_latest_version(dep)
            resolved.append(f"{dep}@{dep_ver}" if dep_ver else dep)
        return resolved


if __name__ == "__main__":
    reg = PluginRegistry()
    reg.register(
        PluginMetadata(
            name="ml_training",
            version="1.0.0",
            capabilities=["GPU_ENABLED", "DISTRIBUTED"],
            resource_requirements={"gpu": True, "vram": "8GB"},
            dependencies=[],
        )
    )
    reg.register(
        PluginMetadata(
            name="inference",
            version="1.0.0",
            capabilities=["GPU_ENABLED"],
            resource_requirements={"gpu": True, "vram": "4GB"},
            dependencies=["ml_training"],
        )
    )
    print("Registry size:", len(reg.plugins))
    print("Latest versions:", {n: reg.get_latest_version(n) for n in reg.plugins})
    print("Search ml:", reg.search("ml"))
    print("GPU plugins:", list(reg.index.get("GPU_ENABLED", set())))
    print("Dependencies inference:", reg.resolve_dependencies("inference"))
