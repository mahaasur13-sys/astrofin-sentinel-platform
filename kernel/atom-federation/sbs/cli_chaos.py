"""sbs/cli_chaos.py — final cleaned version with good replay behavior"""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def run_chaos(
    list_scenarios: bool = False,
    scenario: str | None = None,
    json_output: bool = False,
) -> None:
    try:
        from alignment.adlr import FailureReplay
        from chaos.harness import ChaosHarness
        from chaos.scenarios import SCENARIO_REGISTRY
        from chaos.validator import Verdict
    except ImportError as e:
        console.print(f"[red]Import error: {e}[/]")
        return

    if list_scenarios:
        table = Table(title="Available Chaos Scenarios")
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="dim")
        for name, s in SCENARIO_REGISTRY.items():
            desc = getattr(s, "description", "No description")[:80]
            table.add_row(name, desc)
        console.print(table)
        return

    if not scenario or scenario not in SCENARIO_REGISTRY:
        console.print("[red]Unknown scenario. Use --list-scenarios.[/]")
        return

    scenario_obj = SCENARIO_REGISTRY[scenario]
    mock_ctx = {"nodes": ["node-a", "node-b", "node-c"]}

    console.print(f"[cyan]Running chaos scenario:[/] {scenario}")
    harness = ChaosHarness(scenario=scenario_obj, cluster_ctx=mock_ctx)
    result = harness.run()

    # Replay-friendly record
    saved_path = None
    try:
        fr = FailureReplay()
        verdict = result.verdict.value

        # Use stages that match the orchestrator's default behavior better
        if verdict == "PASS":
            stage_sequence = ["ATTEMPT", "TERMINAL"]
        else:
            stage_sequence = ["VALIDATION", "TERMINAL"]

        record = fr.record(
            action_sequence=[f"chaos_{verdict.lower()}"],
            stage_sequence=stage_sequence,
            oscillation_scores=[int(result.duration_s)],
            byzantine_risk=False,
            k=2,
            t=2,
            final_stage="TERMINAL",
            final_action=f"chaos_{verdict.lower()}",
            metadata={
                "chaos_scenario": result.scenario_name,
                "verdict": verdict,
                "duration_s": round(result.duration_s, 2),
            },
        )
        saved_path = fr.save(record.incident_id)
        if not json_output:
            console.print(f"[green]✅ Saved to replay:[/] {saved_path}")
    except Exception as e:
        console.print(f"[red]Failed to save: {e}[/]")

    color = "green" if verdict == "PASS" else "red"
    panel = Panel(
        f"[cyan]Scenario:[/] {result.scenario_name}\n"
        f"[cyan]Verdict:[/] {verdict}\n"
        f"[cyan]Duration:[/] {result.duration_s:.1f}s\n"
        f"[cyan]Saved to replay:[/] {saved_path or 'none'}",
        title="🔥 Chaos Experiment Result",
        border_style=color,
    )
    console.print(panel)

if __name__ == "__main__":
    typer.run(run_chaos)
