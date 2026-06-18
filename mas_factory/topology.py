"""mas_factory/topology.py - ATOM-R-028: Dynamic SwitchNode + Topology Updater"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class NodeType(Enum):
    AGENT = "agent"
    SWITCH = "switch"
    MERGE = "merge"
    ROUTER = "router"
    ADAPTER = "adapter"
    END = "end"


class SwitchStrategy(Enum):
    THOMPSON = "thompson"
    GREEDY = "greedy"
    ROUND_ROBIN = "round_robin"
    CONFIDENCE_WEIGHTED = "confidence_weighted"


class SwitchAction(Enum):
    ADD_ROLE = "add_role"
    REMOVE_ROLE = "remove_role"
    CHANGE_WEIGHT = "change_weight"
    ADD_LOOP = "add_loop"
    TIGHTEN_POLICY = "tighten_policy"
    REORDER_ROLES = "reorder_roles"


class ConditionEvaluator:
    SAFE_NAMES = {
        "uncertainty_total",
        "oos_fail_rate",
        "confidence",
        "bias_detected",
        "regime",
        "entropy_avg",
        "ttc_depth",
    }

    @classmethod
    def evaluate(cls, condition: str, context: dict[str, Any]) -> bool:
        if not condition:
            return True
        try:
            ns = {k: v for k, v in context.items() if k in cls.SAFE_NAMES or k.startswith("_")}
            ns["true"] = True
            ns["false"] = False
            return bool(eval(condition, {"__builtins__": {}}, ns))
        except Exception:
            return False


@dataclass
class SwitchNode:
    id: str
    strategy: SwitchStrategy = SwitchStrategy.THOMPSON
    condition: str | None = None
    candidates: list[str] = field(default_factory=list)
    k: int = 3
    weights: dict[str, float] | None = None
    true_branch: list[str] | None = None
    false_branch: list[str] | None = None
    action: SwitchAction | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def evaluate_condition(self, context: dict[str, Any]) -> bool:
        return ConditionEvaluator.evaluate(self.condition, context)

    def decide(self, context: dict[str, Any]) -> list[str]:
        if self.strategy == SwitchStrategy.THOMPSON:
            import random

            scores = {a: random.random() * (self.weights or {}).get(a, 1.0) for a in self.candidates}
            return [a for a, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)[: self.k]]
        return self.candidates[: self.k]


@dataclass
class Adapter:
    source: str
    target: str
    transform: str = "passthrough"
    field_mapping: dict[str, str] = field(default_factory=dict)

    def apply(self, data: Any) -> Any:
        if self.transform == "passthrough":
            return data
        elif self.transform == "extract_signal" and isinstance(data, dict):
            return {k: data.get(k) for k in ["signal", "confidence", "reasoning"]}
        elif self.transform == "merge_confidences" and isinstance(data, list):
            signals = [d.get("signal", "NEUTRAL") for d in data if isinstance(d, dict)]
            confs = [d.get("confidence", 50) for d in data if isinstance(d, dict)]
            return {
                "signal": signals[0] if signals else "NEUTRAL",
                "confidence": sum(confs) / len(confs) if confs else 50,
            }
        return data


@dataclass
class Role:
    name: str
    agent_type: str
    weight: float = 0.1
    constraints: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    timeout_ms: int = 30000


@dataclass
class Connection:
    from_node: str
    to_node: str
    adapter: Adapter | None = None
    condition: str | None = None


@dataclass
class Message:
    from_node: str
    to_node: str
    payload: Any
    timestamp: str


@dataclass
class TopologyChange:
    change_id: str
    timestamp: str
    reason: str
    triggered_by: str
    action: SwitchAction
    target: str
    before: dict[str, Any]
    after: dict[str, Any]
    rollback_stack: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        action: SwitchAction,
        target: str,
        before: dict,
        after: dict,
        reason: str,
        triggered_by: str,
    ) -> "TopologyChange":
        return cls(
            change_id=f"chg_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            timestamp=datetime.now().isoformat(),
            reason=reason,
            triggered_by=triggered_by,
            action=action,
            target=target,
            before=before,
            after=after,
            rollback_stack=[before],
        )


@dataclass
class TopologyVersion:
    version: str
    timestamp: str
    topology: "Topology"
    changes: list[TopologyChange] = field(default_factory=list)
    parent_version: str | None = None


@dataclass
class Topology:
    intention: str
    symbol: str
    timeframe: str
    version: str = "1.0"
    roles: list[Role] = field(default_factory=list)
    connections: list[Connection] = field(default_factory=list)
    switch_nodes: list[SwitchNode] = field(default_factory=list)
    entry_point: str = "router"
    exit_point: str = "synthesis"
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_role(self, name: str) -> Role | None:
        for r in self.roles:
            if r.name == name:
                return r
        return None

    def get_outgoing(self, node: str) -> list[Connection]:
        return [c for c in self.connections if c.from_node == node]

    @property
    def hash(self) -> str:
        return self.compute_hash()

    def validate(self) -> list[str]:
        errors = []
        node_ids = {r.name for r in self.roles} | {s.id for s in self.switch_nodes}
        special = {"input", "end"}
        for c in self.connections:
            if c.from_node not in node_ids and c.from_node not in special:
                errors.append(f"Unknown from_node: {c.from_node}")
            if c.to_node not in node_ids and c.to_node not in special:
                errors.append(f"Unknown to_node: {c.to_node}")
        return errors

    def compute_hash(self) -> str:
        data = json.dumps(
            {
                "intention": self.intention,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "roles": sorted([r.name for r in self.roles]),
                "version": self.version,
            },
            sort_keys=True,
        )
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["_hash"] = self.compute_hash()
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Topology":
        data.pop("_hash", None)
        return cls(**data)


class TopologyUpdater:
    def __init__(self, topology: Topology):
        self.current_topology = topology
        self.versions: list[TopologyVersion] = []
        self.change_history: list[TopologyChange] = []
        self._version_counter = 0
        self._init_version()

    def _init_version(self):
        self.versions.append(
            TopologyVersion(
                version=f"v{self._version_counter}",
                timestamp=datetime.now().isoformat(),
                topology=self.current_topology,
                changes=[],
            )
        )

    def _bump_version(self) -> str:
        self._version_counter += 1
        return f"v{self._version_counter}"

    def apply_change(self, change: TopologyChange) -> Topology:
        try:
            new_topo = self._apply_change_internal(change)
            print(f"    [DEBUG] new_topo id={id(new_topo)}, roles={[r.name for r in new_topo.roles]}")
            self.versions.append(
                TopologyVersion(
                    version=self._bump_version(),
                    timestamp=datetime.now().isoformat(),
                    topology=new_topo,
                    changes=[change],
                    parent_version=self.versions[-1].version if self.versions else None,
                )
            )
            self.change_history.append(change)
            print(
                f"    [DEBUG] current_topology id={id(self.current_topology)}, roles={[r.name for r in self.current_topology.roles]}"
            )
            self.current_topology = new_topo
            return new_topo
        except Exception as e:
            self._rollback_last()
            raise RuntimeError(f"Topology change failed: {e}") from e

    def _apply_change_internal(self, change: TopologyChange) -> Topology:
        old = self.current_topology
        topo = Topology(
            intention=old.intention,
            symbol=old.symbol,
            timeframe=old.timeframe,
            version=old.version,
            roles=[
                Role(
                    name=r.name,
                    agent_type=r.agent_type,
                    weight=r.weight,
                    constraints=dict(r.constraints),
                    capabilities=list(r.capabilities),
                    inputs=list(r.inputs),
                    outputs=list(r.outputs),
                    timeout_ms=r.timeout_ms,
                )
                for r in old.roles
            ],
            connections=[
                Connection(
                    from_node=c.from_node,
                    to_node=c.to_node,
                    adapter=c.adapter,
                    condition=c.condition,
                )
                for c in old.connections
            ],
            switch_nodes=list(old.switch_nodes),
            entry_point=old.entry_point,
            exit_point=old.exit_point,
            metadata=dict(old.metadata),
        )
        if change.action in (SwitchAction.ADD_ROLE, SwitchAction.ADD_LOOP):
            role_data = change.after.get("added_role")
            if not role_data:
                role_data = {
                    "name": change.target or "NewLoopRole",
                    "agent_type": change.target or "NewLoopRole",
                    "weight": 0.1,
                }
            topo.roles.append(Role(**role_data))
        elif change.action == SwitchAction.REMOVE_ROLE:
            topo.roles = [r for r in topo.roles if r.name != change.target]
        elif change.action == SwitchAction.CHANGE_WEIGHT:
            new_weight = change.after.get("weight")
            if new_weight:
                for role in topo.roles:
                    if role.name == change.target:
                        role.weight = new_weight
                        break
        elif change.action == SwitchAction.TIGHTEN_POLICY:
            factor = change.after.get("factor", 0.5)
            for role in topo.roles:
                role.weight *= factor
        elif change.action == SwitchAction.REORDER_ROLES:
            new_order = change.after.get("order", [])
            role_map = {r.name: r for r in topo.roles}
            topo.roles = [role_map[n] for n in new_order if n in role_map]
        return topo

    def _rollback_last(self):
        if len(self.versions) > 1:
            self.versions.pop()
            self.change_history.pop()
            self.current_topology = self.versions[-1].topology

    def get_change_summary(self) -> dict[str, Any]:
        if not self.change_history:
            return {"total_changes": 0, "current_version": "v0"}
        return {
            "total_changes": len(self.change_history),
            "current_version": self.versions[-1].version if self.versions else "v0",
            "last_change": {
                "id": self.change_history[-1].change_id,
                "action": self.change_history[-1].action.value,
                "reason": self.change_history[-1].reason,
            }
            if self.change_history
            else None,
        }


class UncertaintySwitch(SwitchNode):
    def __init__(self, id: str = "uncertainty_switch"):
        super().__init__(
            id=id,
            strategy=SwitchStrategy.GREEDY,
            condition="uncertainty_total > 0.6",
            candidates=["GroundingLoop"],
            true_branch=["GroundingLoop"],
            action=SwitchAction.ADD_LOOP,
            metadata={
                "threshold": 0.6,
                "description": "Adds grounding when uncertainty > 0.6",
            },
        )


class BiasSwitch(SwitchNode):
    def __init__(self, id: str = "bias_switch"):
        super().__init__(
            id=id,
            strategy=SwitchStrategy.GREEDY,
            condition="bias_detected == True",
            candidates=["Critic"],
            true_branch=["Critic"],
            action=SwitchAction.ADD_ROLE,
            metadata={
                "threshold": True,
                "description": "Adds Critic when bias detected",
            },
        )


class RegimeSwitch(SwitchNode):
    def __init__(self, id: str = "regime_switch"):
        super().__init__(
            id=id,
            strategy=SwitchStrategy.GREEDY,
            condition="regime in ['HIGH', 'EXTREME']",
            candidates=["HighVolatilityAgent"],
            true_branch=["HighVolatilityAgent"],
            action=SwitchAction.REORDER_ROLES,
            metadata={
                "regimes": ["HIGH", "EXTREME"],
                "description": "Prioritizes stability in HIGH/EXTREME regimes",
            },
        )


class OOSFailSwitch(SwitchNode):
    def __init__(self, id: str = "oos_fail_switch"):
        super().__init__(
            id=id,
            strategy=SwitchStrategy.GREEDY,
            condition="oos_fail_rate > 0.4",
            candidates=[],
            action=SwitchAction.TIGHTEN_POLICY,
            metadata={
                "threshold": 0.4,
                "factor": 0.5,
                "description": "Tightens policy when OOS fail > 0.4",
            },
        )


class LowConfidenceSwitch(SwitchNode):
    def __init__(self, id: str = "low_confidence_switch"):
        super().__init__(
            id=id,
            strategy=SwitchStrategy.GREEDY,
            condition="confidence < 40",
            candidates=["ValidationLoop"],
            true_branch=["ValidationLoop"],
            action=SwitchAction.ADD_LOOP,
            metadata={
                "threshold": 40,
                "description": "Adds validation when confidence < 40",
            },
        )
