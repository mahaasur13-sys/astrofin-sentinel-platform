from __future__ import annotations

# mas_factory/visualizer.py - ATOM-R-029: Topology Visualization
import json
from pathlib import Path

try:
    from .topology import Connection, NodeType, Role, SwitchAction, SwitchNode, Topology
except ImportError:
    from topology import Topology


class TopologyVisualizer:
    """Generates Mermaid and DOT visualizations from Topology"""

    NODE_COLORS = {
        "agent": "#4CAF50",  # Green for agents
        "switch": "#FF9800",  # Orange for switches
        "merge": "#9C27B0",  # Purple for merges
        "router": "#2196F3",  # Blue for router
        "adapter": "#607D8B",  # Gray for adapters
        "end": "#F44336",  # Red for end
    }

    def __init__(self, topology: Topology):
        self.topo = topology

    def to_mermaid(self) -> str:
        """Generate Mermaid flowchart from Topology"""
        lines = ["flowchart LR", "    %% AstroFin MAS Topology"]

        # Style definitions
        lines.append("    subgraph agents[")
        lines.append("        direction TB")

        # Add roles as nodes
        for role in self.topo.roles:
            self.NODE_COLORS.get("agent", "#4CAF50")
            lines.append(f'        {role.name}["{role.name}"]')

        lines.append("    ]")

        # Add switch nodes
        if self.topo.switch_nodes:
            lines.append("    subgraph switches[Switch Nodes]")
            for sw in self.topo.switch_nodes:
                self.NODE_COLORS.get("switch", "#FF9800")
                cond = sw.condition or "always"
                lines.append(f'        {sw.id}["{sw.id}\\n({cond})"]')
            lines.append("    ]")

        # Add connections
        for conn in self.topo.connections:
            adapter_label = f"[{conn.adapter.transform}]" if conn.adapter else ""
            lines.append(f"    {conn.from_node} -->{adapter_label} {conn.to_node}")

        # Entry/Exit points
        lines.append(f"    input((IN)) --> {self.topo.entry_point}")
        lines.append(f"    {self.topo.exit_point} --> output((OUT))")

        return "\n".join(lines)

    def to_dot(self) -> str:
        """Generate DOT graph for Graphviz"""
        lines = [
            "digraph MAS_Topology {",
            "    rankdir=LR;",
            '    node [shape=box, style="rounded,filled", fontname="DejaVu Sans Mono"];',
            '    edge [color="#666666", penwidth=1.5];',
            "",
            "    /* Entry/Exit */",
            '    input [shape=ellipse, label="INPUT", fillcolor="#E3F2FD", color="#1976D2"];',
            '    output [shape=ellipse, label="OUTPUT", fillcolor="#FFEBEE", color="#C62828"];',
        ]

        # Nodes
        for role in self.topo.roles:
            color = self.NODE_COLORS.get("agent", "#4CAF50")
            weight_str = f"\\nweight={role.weight}" if role.weight else ""
            lines.append(
                f'    {role.name} [label="{role.name}{weight_str}", fillcolor="{color}40", color="{color}"];'
            )

        for sw in self.topo.switch_nodes:
            sw_color = self.NODE_COLORS.get("switch", "#FF9800")
            cond = (sw.condition or "always")[:30]
            lines.append(
                f'    {sw.id} [label="{sw.id}\\n{cond}", shape=diamond, fillcolor="{sw_color}40", color="{sw_color}"];'
            )

        lines.append("")
        lines.append("    /* Connections */")

        for conn in self.topo.connections:
            adapter_label = (
                f' [label="{conn.adapter.transform}"]' if conn.adapter else ""
            )
            lines.append(f"    {conn.from_node} -> {conn.to_node}{adapter_label};")

        lines.append("")
        lines.append(
            f'    input -> {self.topo.entry_point} [style=dashed, color="#1976D2"];'
        )
        lines.append(
            f'    {self.topo.exit_point} -> output [style=dashed, color="#C62828"];'
        )

        # Legend
        lines.extend(
            [
                "",
                "    subgraph cluster_legend {",
                '        label="Legend"; fontsize=12;',
                '        style=dashed; color="#999999";',
                '        leg1 [shape=box, label="Agent", fillcolor="#4CAF5040"];',
                '        leg2 [shape=diamond, label="Switch", fillcolor="#FF980040"];',
                "    }",
                "}",
            ]
        )

        return "\n".join(lines)

    def to_ascii(self) -> str:
        """Generate ASCII art topology"""
        lines = [
            "=" * 60,
            f"  TOPOLOGY: {self.topo.intention}",
            f"  Symbol: {self.topo.symbol} | Timeframe: {self.topo.timeframe}",
            f"  Version: {self.topo.version} | Hash: {self.topo.hash}",
            "=" * 60,
            "",
            "  ENTRY -->",
        ]

        # Roles with weights
        role_colors = {
            "FundamentalAgent": "🟢",
            "QuantAgent": "🔵",
            "MacroAgent": "🟡",
            "TechnicalAgent": "🟠",
            "SentimentAgent": "🟣",
            "AstroCouncil": "⭐",
            "GroundingLoop": "🛡️",
            "Critic": "🔍",
            "ValidationLoop": "✅",
        }

        for i, role in enumerate(self.topo.roles):
            icon = role_colors.get(role.name, "⚙️")
            indent = "  " if i == 0 else "    "
            lines.append(f"{indent}{icon} {role.name} [{role.weight:.0%}]")
            if i < len(self.topo.roles) - 1:
                lines.append(f"{indent}  |")
                lines.append(f"{indent}  v")

        # Switch nodes
        if self.topo.switch_nodes:
            lines.append("")
            lines.append("  ┌─ SWITCHES ─┐")
            for sw in self.topo.switch_nodes:
                cond = sw.condition or "always"
                lines.append(f"  │ ◆ {sw.id}: {cond[:40]}")
                if sw.true_branch:
                    lines.append(f"  │   → {', '.join(sw.true_branch)}")
            lines.append("  └────────────┘")

        lines.append("")
        lines.append(f"  --> OUTPUT ({self.topo.exit_point})")
        lines.append("=" * 60)

        return "\n".join(lines)

    def to_json(self) -> dict:
        """Export topology as JSON"""
        return {
            "topology": self.topo.to_dict(),
            "mermaid": self.to_mermaid(),
            "dot": self.to_dot(),
            "ascii": self.to_ascii(),
            "summary": {
                "total_roles": len(self.topo.roles),
                "total_switches": len(self.topo.switch_nodes),
                "total_connections": len(self.topo.connections),
                "total_weight": sum(r.weight for r in self.topo.roles),
            },
        }

    def save_all(
        self, output_dir: str = "data/topology", session_id: str = None
    ) -> dict[str, str]:
        """Save all visualizations to files"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        prefix = f"{session_id}_" if session_id else ""
        hash_suffix = self.topo.hash[:8]

        files = {}

        # Save Mermaid
        mermaid_path = f"{output_dir}/{prefix}mermaid_{hash_suffix}.mmd"
        with open(mermaid_path, "w") as f:
            f.write(self.to_mermaid())
        files["mermaid"] = mermaid_path

        # Save DOT
        dot_path = f"{output_dir}/{prefix}dot_{hash_suffix}.dot"
        with open(dot_path, "w") as f:
            f.write(self.to_dot())
        files["dot"] = dot_path

        # Save ASCII
        ascii_path = f"{output_dir}/{prefix}ascii_{hash_suffix}.txt"
        with open(ascii_path, "w") as f:
            f.write(self.to_ascii())
        files["ascii"] = ascii_path

        # Save JSON
        json_path = f"{output_dir}/{prefix}topology_{hash_suffix}.json"
        with open(json_path, "w") as f:
            json.dump(self.to_json(), f, indent=2, default=str)
        files["json"] = json_path

        return files


def visualize_topology(
    topology: Topology, output_dir: str = "data/topology", session_id: str = None
) -> dict[str, str]:
    """Quick function to visualize a topology"""
    viz = TopologyVisualizer(topology)
    return viz.save_all(output_dir, session_id)


def print_topology_viz(topology: Topology):
    """Print all visualizations to console"""
    viz = TopologyVisualizer(topology)

    print(viz.to_ascii())
    print()
    print("=" * 60)
    print("MERMAID DIAGRAM:")
    print("=" * 60)
    print(viz.to_mermaid())
