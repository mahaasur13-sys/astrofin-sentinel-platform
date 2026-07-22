#!/usr/bin/env python3
"""
L9 EBL — Policy Compiler
Transforms policy (YAML/text) into executable constraint graphs.
"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import yaml

@dataclass
class ConstraintNode:
    id: str
    constraint_type: str  # resource_limit | forbidden_action | required_state
    params: Dict[str, Any]
    description: str = ""

    def validate(self, params: Dict[str, Any]) -> List[str]:
        violations = []
        if self.constraint_type == "resource_limit":
            key = self.params.get("key")
            limit = self.params.get("limit")
            if key in params and params[key] > limit:
                violations.append(f"{key}={params[key]} exceeds limit={limit}")
        elif self.constraint_type == "forbidden_action":
            action = self.params.get("action")
            if params.get("action") == action:
                violations.append(f"Action {action} is forbidden")
        elif self.constraint_type == "required_state":
            key = self.params.get("key")
            required = self.params.get("value")
            if key not in params or params[key] != required:
                violations.append(f"Required {key}={required}, got {params.get(key)}")
        return violations

@dataclass
class GuardRule:
    action: str
    constraints: List[ConstraintNode]
    severity: str = "high"
    tags: List[str] = field(default_factory=list)

    def validate(self, params: Dict[str, Any]) -> List[str]:
        violations = []
        for c in self.constraints:
            violations.extend(c.validate(params))
        return violations

class PolicyCompiler:
    def __init__(self):
        self.rules: Dict[str, GuardRule] = {}
        self._compiled = False

    def load_policy(self, policy_text: str) -> None:
        data = yaml.safe_load(policy_text)
        self.rules.clear()
        for rule_name, rule_data in data.get("rules", {}).items():
            guard = GuardRule(
                action=rule_data["action"],
                constraints=[
                    ConstraintNode(
                        id=c.get("id", ""),
                        constraint_type=c["type"],
                        params=c.get("params", {}),
                        description=c.get("description", "")
                    ) for c in rule_data.get("constraints", [])
                ],
                severity=rule_data.get("severity", "high"),
                tags=rule_data.get("tags", [])
            )
            self.rules[rule_name] = guard
        self._compiled = True

    def get_guard(self, action: str) -> Optional[GuardRule]:
        for rule in self.rules.values():
            if rule.action == action:
                return rule
        return None

    def compile_summary(self) -> Dict[str, Any]:
        return {
            "rules_count": len(self.rules),
            "actions": [r.action for r in self.rules.values()],
            "compiled": self._compiled
        }
