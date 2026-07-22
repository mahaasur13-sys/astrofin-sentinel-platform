#!/usr/bin/env python3
"""
Constraint Compiler — DSL → executable constraints.
Input: YAML DSL → AST → lambda(state) → bool.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Any
import re


@dataclass
class CompiledConstraint:
    name: str
    description: str
    severity: str  # "hard" | "soft"
    fn: Callable[[dict], tuple[bool, str]]  # (passes, message)


class ConstraintCompiler:
    """
    Compiles DSL constraints into executable Python functions.
    
    DSL examples:
        latency_guard:     "p99_latency < 200"
        cpu_guard:          "cpu_util < 0.95"
        failure_rate:       "failure_rate < 0.05"
        queue_depth:        "queue_depth < 1000"
    """

    OPS = {
        "<":  lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">":  lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    def compile(self, constraint_yaml: dict) -> CompiledConstraint:
        name = constraint_yaml["name"]
        expr = constraint_yaml["expr"]
        severity = constraint_yaml.get("severity", "hard")

        # Parse: "metric OP threshold"
        pattern = r"(\w+(?:\.\w+)*)\s*(<=|>=|==|!=|<|>)\s*(\S+)"
        m = re.match(pattern, expr)
        if not m:
            raise ValueError(f"Invalid constraint expr: {expr}")

        metric_path, op_str, threshold_str = m.groups()
        op_fn = self.OPS[op_str]
        threshold = self._parse_value(threshold_str)

        def fn(state: dict) -> tuple[bool, str]:
            value = self._get_nested(state, metric_path)
            if value is None:
                return False, f"metric {metric_path} not found in state"
            passes = op_fn(value, threshold)
            msg = f"{name}: {metric_path}={value} {op_str} {threshold} → {'PASS' if passes else 'FAIL'}"
            return passes, msg

        return CompiledConstraint(
            name=name,
            description=constraint_yaml.get("description", ""),
            severity=severity,
            fn=fn,
        )

    def _get_nested(self, state: dict, path: str) -> Any:
        keys = path.split(".")
        val = state
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                return None
            if val is None:
                return None
        return val

    def _parse_value(self, s: str) -> float:
        s = s.strip()
        if s.endswith("ms"):
            return float(s[:-2])
        if s.endswith("%"):
            return float(s[:-1]) / 100.0
        if s.endswith("s"):
            return float(s[:-1])
        return float(s)

    def build_registry(self, constraints_yaml: list[dict]) -> dict[str, CompiledConstraint]:
        return {c["name"]: self.compile(c) for c in constraints_yaml}


class ConstraintRegistry:
    """
    Runtime registry of active compiled constraints.
    Validates decisions against all active constraints.
    """

    def __init__(self):
        self._constraints: dict[str, CompiledConstraint] = {}

    def register(self, constraint: CompiledConstraint) -> None:
        self._constraints[constraint.name] = constraint

    def validate(self, decision: dict, context) -> list[str]:
        state = self._build_state(decision, context)
        violations = []
        for name, c in self._constraints.items():
            passes, _ = c.fn(state)
            if not passes:
                violations.append(name)
        return violations

    def _build_state(self, decision: dict, context) -> dict:
        # Merge decision + context into flat state dict for constraint eval
        state = {}
        state.update(decision)
        state.update(context.cluster_state if hasattr(context, "cluster_state") else {})
        return state

    def list_constraints(self) -> list[str]:
        return list(self._constraints.keys())
