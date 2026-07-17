"""sbs/cli_replay.py — sbs replay CLI command."""

from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from alignment.adlr import FailureReplay

console = Console()


def run_replay(
    incident_id: str | None = None,
    batch: bool = False,
    json_output: bool = False,
) -> None:
    """Replay recorded failure incidents."""
    fr = FailureReplay()

    if json_output:
        result = _run_replay_json(fr, incident_id, batch)
        console.print(json.dumps(result, indent=2))
        return

    if batch:
        results = fr.replay_all()
        table = Table(title=f"Batch Replay — {len(results)} incidents")
        table.add_column("ID", style="cyan")
        table.add_column("Status", style="yellow")
        table.add_column("Summary", style="dim")
        for r in results:
            table.add_row(r.incident_id, r.status, r.summary())
        console.print(table)
        return

    if incident_id:
        result = fr.replay(incident_id)
        panel = Panel(
            f"[cyan]ID:[/] {result.incident_id}\n"
            f"[cyan]Status:[/] {result.status}\n"
            f"[cyan]Original final:[/] {result.original_final_stage}\n"
            f"[cyan]Replay final:[/] {result.replay_final_stage}\n"
            f"[cyan]Steps:[/] {result.replay_steps}\n"
            f"[cyan]Divergence:[/] {result.divergence_score:.2f}\n"
            f"[dim]{result.summary()}[/]",
            title="🔁 Replay Result",
            border_style="green" if result.is_match() else "red",
        )
        console.print(panel)
        return

    # --list or no args — show all saved incidents
    ids = fr.list_saved()
    if not ids:
        console.print("[yellow]No incidents to replay[/]")
        return
    table = Table(title=f"Saved Incidents ({len(ids)})")
    table.add_column("ID", style="cyan")
    table.add_column("File", style="dim")
    for fid in ids:
        table.add_row(fid, f"{fr.storage_dir}/{fid}")
    console.print(table)


def _run_replay_json(fr, incident_id, batch):
    if batch:
        results = fr.replay_all()
        return {
            "mode": "batch",
            "count": len(results),
            "results": [
                {
                    "incident_id": r.incident_id,
                    "status": r.status,
                    "is_match": r.is_match(),
                    "replay_steps": r.replay_steps,
                    "divergence_score": r.divergence_score,
                    "summary": r.summary(),
                }
                for r in results
            ],
        }
    if incident_id:
        result = fr.replay(incident_id)
        return {
            "incident_id": result.incident_id,
            "status": result.status,
            "is_match": result.is_match(),
            "original_final_stage": result.original_final_stage,
            "replay_final_stage": result.replay_final_stage,
            "replay_steps": result.replay_steps,
            "diverged_at_step": result.diverged_at_step,
            "divergence_reason": result.divergence_reason,
            "divergence_score": result.divergence_score,
            "summary": result.summary(),
        }
    ids = fr.list_saved()
    return {"saved_incidents": ids}
