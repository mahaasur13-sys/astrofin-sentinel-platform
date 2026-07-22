#!/usr/bin/env python3
"""
Constraint Compiler — Parser
Transforms policy text into executable constraint DAG.
"""
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto

class ConstraintType(Enum):
    RESOURCE_LIMIT = auto()
    FORBIDDEN_ACTION = auto()
    REQUIRED_STATE = auto()
    TEMPORAL_BOUND = auto()
    CAUSAL_ORDER = auto()
    CAPACITY_LIMIT = auto()

@dataclass
class Constraint:
    id: str
    ctype: ConstraintType
    key: str
    operator: str  # >, <, ==, !=, in, not_in
    threshold: Any
    description: str = ""

    def evaluate(self, state: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        current = state.get(self.key)
        op = self.operator

        try:
            if op == ">":
                ok = current is not None and current > self.threshold
            elif op == "<":
                ok = current is not None and current < self.threshold
            elif op == "==":
                ok = current == self.threshold
            elif op == ">=":
                ok = current is not None and current >= self.threshold
            elif op == "<=":
                ok = current is not None and current <= self.threshold
            elif op == "!=":
                ok = current != self.threshold
            elif op == "in":
                ok = current in self.threshold
            elif op == "not_in":
                ok = current not in self.threshold
            else:
                return False, f"Unknown operator: {op}"

            if ok:
                return True, None
            return False, f"Constraint {self.id}: {self.key}={current} {op} {self.threshold}"
        except Exception as e:
            return False, f"Constraint {self.id} evaluation error: {e}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.ctype.name,
            "key": self.key,
            "operator": self.operator,
            "threshold": self.threshold,
            "description": self.description
        }

@dataclass
class ConstraintGroup:
    name: str
    constraints: List[Constraint] = field(default_factory=list)
    severity: str = "high"
    tags: List[str] = field(default_factory=list)

    def evaluate_all(self, state: Dict[str, Any]) -> List[str]:
        violations = []
        for c in self.constraints:
            ok, msg = c.evaluate(state)
            if not ok and msg:
                violations.append(msg)
        return violations

@dataclass
class PolicyBlock:
    action: str
    groups: List[ConstraintGroup] = field(default_factory=list)
    description: str = ""
    version: str = "1.0"

    def evaluate(self, state: Dict[str, Any]) -> List[str]:
        all_violations = []
        for group in self.groups:
            all_violations.extend(group.evaluate_all(state))
        return all_violations

class PolicyParser:
    def __init__(self):
        self.blocks: Dict[str, PolicyBlock] = {}

    def parse_text(self, text: str) -> Dict[str, PolicyBlock]:
        self.blocks.clear()
        current_block: Optional[PolicyBlock] = None
        current_group: Optional[ConstraintGroup] = None
        current_constraints: List[Constraint] = []

        for line in text.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("[POLICY ") and line.endswith("]"):
                if current_block:
                    if current_group:
                        current_block.groups.append(current_group)
                    self.blocks[current_block.action] = current_block
                action = line[8:-1].strip()
                current_block = PolicyBlock(action=action)
                current_group = None
                current_constraints = []
                continue

            if line.startswith("[GROUP ") and line.endswith("]"):
                if current_block and current_group:
                    cg = ConstraintGroup(name=current_group.name, constraints=current_constraints)
                    current_block.groups.append(cg)
                current_group_name = line[7:-1].strip()
                current_group = ConstraintGroup(name=current_group_name)
                current_constraints = []
                continue

            if line.startswith("[") and current_group:
                cg = ConstraintGroup(name=current_group.name, constraints=current_constraints)
                current_block.groups.append(cg)
                current_group = None
                current_constraints = []

            if ":" in line and current_group is not None:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()

                m = re.match(r"(\w+)\s*(>|<|>=|<=|==|!=|in|not_in)\s*(.+)", val)
                if m:
                    constraint = Constraint(
                        id=f"{current_group.name}_{key}",
                        ctype=ConstraintType.RESOURCE_LIMIT,
                        key=key,
                        operator=m.group(2),
                        threshold=self._parse_value(m.group(3)),
                        description=""
                    )
                    current_constraints.append(constraint)

        if current_block:
            if current_group:
                cg = ConstraintGroup(name=current_group.name, constraints=current_constraints)
                current_block.groups.append(cg)
            self.blocks[current_block.action] = current_block

        return self.blocks

    def _parse_value(self, val: str) -> Any:
        val = val.strip()
        if val.lower() == "null":
            return None
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        if val.startswith("[") and val.endswith("]"):
            return [v.strip() for v in val[1:-1].split(",")]
        try:
            if "." in val:
                return float(val)
            return int(val)
        except ValueError:
            return val.strip('"').strip("'")

    def get_block(self, action: str) -> Optional[PolicyBlock]:
        return self.blocks.get(action)

    def summary(self) -> Dict[str, Any]:
        return {
            "blocks": len(self.blocks),
            "actions": [b.action for b in self.blocks.values()],
            "total_constraints": sum(
                sum(len(g.constraints) for g in b.groups)
                for b in self.blocks.values()
            )
        }
