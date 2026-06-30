"""
runtime_dfa_extractor.py — Extract transitions from ExecutionGateway code.
"""

from __future__ import annotations

import ast
import pathlib
import sys


class TransitionExtractor(ast.NodeVisitor):
    """Extract DFA transitions from ExecutionGateway source."""

    GATES = ["G1_ADV","G2_POL","G3_ALN","G4_GOV","G5_CB","G6_PRE","G7_ACT","G8_INV","G9_LED","G10_RB"]
    GATE_NEXT = {
        "G1_ADV":"G2_POL","G2_POL":"G3_ALN","G3_ALN":"G4_GOV",
        "G4_GOV":"G5_CB","G5_CB":"G6_PRE","G6_PRE":"G7_ACT",
        "G7_ACT":"G8_INV","G8_INV":"G9_LED","G9_LED":"G10_RB","G10_RB":"ACCEPT",
    }

    def __init__(self, src_path: pathlib.Path):
        self.src_path = src_path
        self.transitions: set[tuple[str,str,str]] = set()
        self.entry_points: list[dict] = []
        self._in_execute = False

    def extract(self) -> dict:
        """Run extraction and return structured result."""
        text = self.src_path.read_text(errors="ignore")
        tree = ast.parse(text, filename=str(self.src_path))
        self.visit(tree)
        return self.as_spec()

    def as_spec(self) -> dict:
        """Return as formal DFA specification dict."""
        return {
            "type": "runtime_dfa",
            "source": str(self.src_path),
            "transitions": sorted(self._fmt(t) for t in self.transitions),
            "entry_points": self.entry_points,
        }

    def _fmt(self, t: tuple[str,str,str]) -> str:
        return f"{t[0]},{t[1]},{t[2]}"

    # ── find execute() methods ─────────────────────────────────────────────

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        is_execute = node.name in ("execute","_execute","execute_with_sbs")
        was = self._in_execute
        if is_execute:
            self._in_execute = True
        self.generic_visit(node)
        if is_execute:
            self._in_execute = was
            self.entry_points.append({
                "method": node.name,
                "file": str(self.src_path.relative_to(self.src_path.parent.parent)),
                "line": node.lineno,
            })

    # ── detect transition sequences from trace logging ────────────────────

    def visit_Call(self, node: ast.Call) -> None:
        if not self._in_execute:
            self.generic_visit(node)
            return
        # pattern: state.trace.append(f"{gate}:{status.value}")
        if isinstance(node.func, ast.Attribute):
            method = node.func.attr
            if method == "trace" and len(node.args) >= 1:
                arg = node.args[0]
                # f-string: f"X:{Y}" where X is gate, Y is status
                if isinstance(arg, ast.JoinedStr):
                    parts = self._parse_fstring(arg)
                    gate, status = parts[0], parts[1] if len(parts) > 1 else ""
                    if gate in self.GATES or gate == "ACT":
                        if status == "pass":
                            next_state = self.GATE_NEXT.get(gate, "ACCEPT")
                            self.transitions.add((gate, "G_PASS", next_state))
                        elif status == "block":
                            self.transitions.add((gate, "G_BLOCK", "REJECT"))
        self.generic_visit(node)

    def _parse_fstring(self, node: ast.JoinedStr) -> list[str]:
        parts = []
        for val in node.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str):
                parts.append(val.value.strip(":"))
        return parts


def extract_from_file(path: pathlib.Path) -> dict:
    ext = TransitionExtractor(path)
    return ext.extract()


if __name__ == "__main__":
    import json
    if len(sys.argv) > 1:
        path = pathlib.Path(sys.argv[1])
        spec = extract_from_file(path)
        print(json.dumps(spec, indent=2))
    else:
        print("Usage: python runtime_dfa_extractor.py <gateway.py>")
