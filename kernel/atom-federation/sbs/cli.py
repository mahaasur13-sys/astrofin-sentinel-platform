"""
sbs/cli.py — Typer-based CLI for SBS v1.
Rich output, auto-completion, --json, -v/-vv/--quiet.
"""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sbs import __version__
from sbs.cli_chaos import run_chaos
from sbs.cli_config import run_config
from sbs.cli_doctor import run_doctor
from sbs.cli_replay import run_replay
from sbs.cli_run import run_scenario
from sbs.version import BUILD, VERSION, VERSION_DATE

import logging
log = logging.getLogger(__name__)


# ── App ──────────────────────────────────────────────────────────────────────
app = typer.Typer(
    name="sbs",
    invoke_without_command=True,
    add_completion=False,
    help="""[bold cyan]SBS v1[/] — System Boundary Spec CLI

Cross-layer invariant verification for distributed OS stacks
(DRL · CCL · F2/F3/F8 · DESC).

Examples:
  sbs --version
  sbs verify --spec strict
  sbs status --json
  sbs doctor
  sbs config show
""",
)

console = Console(stderr=True)
out = Console()

# ── Global flags ──────────────────────────────────────────────────────────────
json_opt = typer.Option(False, "--json", help="Machine-readable JSON output")
quiet_opt = typer.Option(False, "--quiet", "-q", help="Suppress all output")
verbose_opt = typer.Option(0, "-v", "--verbose", count=True, help="Increase verbosity (-v, -vv, -vvv)")

# ── Callback: version + verbosity ──────────────────────────────────────────────
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="Show version and exit"),
    json_flag: bool = json_opt,
    quiet: bool = quiet_opt,
    verbose: int = verbose_opt,
):
    """Top-level handler — handles --version before any subcommand."""
    if version:
        info = {
            "name": "sbs",
            "version": __version__,
            "full_version": VERSION,
            "date": VERSION_DATE,
            "build": BUILD,
        }
        if json_flag:
            out.log.info(json.dumps(info, indent=2))
        else:
            out.log.info(f"[cyan]sbs[/] [bold]{__version__}[/] ({VERSION_DATE}, {BUILD})")
        raise typer.Exit(0)

    ctx.meta["json"] = json_flag
    ctx.meta["quiet"] = quiet
    ctx.meta["verbosity"] = verbose


# ── verify ────────────────────────────────────────────────────────────────────
@app.command("verify", help="Run SBS verification against all invariant contracts")
def verify(
    spec: str = typer.Option("strict", "--spec", "-s",
                              help="Spec mode: strict | relaxed | minimal"),
    json_out: bool = json_opt,
):
    """Verify system state against SBS contracts."""
    from sbs.cli_verify import run_verify

    try:
        ok, report = run_verify(spec)
    except Exception as e:
        if json_out:
            out.log.info(json.dumps({"ok": False, "error": str(e)}))
        else:
            out.log.info(f"[red]✗[/] Verification error: {e}", stderr=True)
        raise typer.Exit(1)

    if json_out:
        out.log.info(json.dumps(report, indent=2, default=str))
    else:
        _print_verify_report(report, spec)


# ── status ────────────────────────────────────────────────────────────────────
@app.command("status", help="Show current SBS runtime status")
def status(json_out: bool = json_opt):
    """Display SBS runtime status with all layer states."""
    from sbs.cli_status import run_status

    try:
        data = run_status()
    except Exception as e:
        if json_out:
            out.log.info(json.dumps({"ok": False, "error": str(e)}))
        else:
            out.log.info(f"[red]✗[/] Status error: {e}", stderr=True)
        raise typer.Exit(1)

    if json_out:
        out.log.info(json.dumps(data, indent=2, default=str))
    else:
        _print_status(data)


# ── inspect ───────────────────────────────────────────────────────────────────
@app.command("inspect", help="Deep-inspect a specific layer")
def inspect(
    layer: str | None = typer.Argument(None, help="Layer: drl | ccl | f2 | desc | sbs"),
    json_out: bool = json_opt,
):
    """Inspect a specific SBS layer."""
    from sbs.cli_inspect import run_inspect

    layers = ["drl", "ccl", "f2", "desc", "sbs"]
    if layer and layer not in layers:
        out.log.info(f"[red]Unknown layer: {layer}[/]. Valid: {', '.join(layers)}", stderr=True)
        raise typer.Exit(1)

    try:
        data = run_inspect(layer)
    except Exception as e:
        if json_out:
            out.log.info(json.dumps({"ok": False, "error": str(e)}))
        else:
            out.log.info(f"[red]✗[/] Inspect error: {e}", stderr=True)
        raise typer.Exit(1)

    if json_out:
        out.log.info(json.dumps(data, indent=2, default=str))
    else:
        _print_inspect(data, layer)


# ── schema-check ──────────────────────────────────────────────────────────────
@app.command("schema-check", help="Validate state schema (file path or JSON string)")
def schema_check(
    data: str | None = typer.Argument(None, help="JSON string or @filepath"),
    file: str | None = typer.Option(None, "--file", "-f", help="Read from file"),
    json_out: bool = json_opt,
):
    """Validate SBS state schema."""
    from sbs.cli_schema import run_schema_check

    try:
        ok, result = run_schema_check(data, file)
    except Exception as e:
        if json_out:
            out.log.info(json.dumps({"ok": False, "error": str(e)}))
        else:
            out.log.info(f"[red]✗[/] Schema error: {e}", stderr=True)
        raise typer.Exit(1)

    if json_out:
        out.log.info(json.dumps({"ok": ok, **result}, indent=2))
    else:
        _print_schema(result, ok)


# ── doctor ────────────────────────────────────────────────────────────────────
@app.command("doctor", help="🩺 Diagnose environment, dependencies, SBS integrity")
def doctor(
    json_out: bool = json_opt,
    verbose: int = verbose_opt,
):
    """Run full system diagnostics."""
    try:
        report = run_doctor(verbose=verbose)
    except Exception as e:
        if json_out:
            out.log.info(json.dumps({"ok": False, "error": str(e)}))
        else:
            out.log.info(f"[red]✗[/] Doctor error: {e}", stderr=True)
        raise typer.Exit(1)

    if json_out:
        out.log.info(json.dumps(report, indent=2, default=str))
    else:
        _print_doctor(report)


# ── config ────────────────────────────────────────────────────────────────────
@app.command("config", help="⚙️ Show / edit SBS configuration")
def config(
    action: str = typer.Argument("show", help="Action: show | set | get | reset"),
    key: str | None = typer.Argument(None, help="Config key (for set/get)"),
    value: str | None = typer.Argument(None, help="Config value (for set)"),
):
    """Manage SBS configuration."""
    try:
        result = run_config(action, key, value)
    except Exception as e:
        out.log.info(f"[red]✗[/] Config error: {e}", stderr=True)
        raise typer.Exit(1)

    if result.get("json"):
        out.log.info(json.dumps(result, indent=2, default=str))
    else:
        _print_config(result)


# ── run ───────────────────────────────────────────────────────────────────────
@app.command("run", help="▶ Run a test scenario with custom state")

@app.command("chaos", help="💥 Run chaos experiment and save failures to replay")
def chaos_cmd(
    ctx: typer.Context,
    scenario: str | None = typer.Option(None, "--scenario", "-s", help="Chaos scenario name"),
    list_scenarios: bool = typer.Option(False, "--list-scenarios", help="Show available scenarios"),
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output"),
):
    run_chaos(scenario=scenario, list_scenarios=list_scenarios, json_output=json_output)

@app.command("replay", help="🔁 Replay recorded failure incidents")
def replay_cmd(
    ctx: typer.Context,
    list_ids: bool = typer.Option(False, "--list", help="List all recorded incident IDs"),
    incident_id: str | None = typer.Option(None, "--id", help="Replay specific incident by ID"),
    batch: bool = typer.Option(False, "--batch", help="Replay all incidents in batch"),
    json_output: bool = json_opt,
):
    """Replay recorded failure incidents."""
    run_replay(incident_id=incident_id, batch=batch, json_output=json_output)

def run(
    scenario: str = typer.Argument(..., help="Scenario name (list | run)"),
    state: str | None = typer.Option(None, "--state", help="JSON state override"),
    json_out: bool = json_opt,
):
    """Run predefined test scenarios."""
    try:
        report = run_scenario(scenario, state)
    except Exception as e:
        if json_out:
            out.log.info(json.dumps({"ok": False, "error": str(e)}))
        else:
            out.log.info(f"[red]✗[/] Run error: {e}", stderr=True)
        raise typer.Exit(1)

    if json_out:
        out.log.info(json.dumps(report, indent=2, default=str))
    else:
        _print_run(report)


# ── replay ────────────────────────────────────────────────────────────────────
@app.command("replay", help="🎭 Replay a saved failure scenario with recovery verification")
def replay(
    incident_id: str | None = typer.Argument(None, help="Incident ID to replay (or omit --list)"),
    list_scenarios: bool = typer.Option(False, "--list", "-l", help="List all saved scenarios"),
    json_out: bool = json_opt,
):
    """Replay a saved failure scenario through recovery loop.

    Examples:
      sbs replay --list
      sbs replay abc12345
      sbs replay abc12345 --json
    """
    from alignment.failure_replay import FailureRecorder

    try:
        recorder = FailureRecorder()
    except Exception as e:
        out.log.info(f"[red]✗[/] Failed to init FailureRecorder: {e}", stderr=True)
        raise typer.Exit(1)

    if list_scenarios or incident_id is None:
        scenarios = recorder.list_scenarios()
        if not scenarios:
            out.log.info("[yellow]No saved scenarios found[/]")
            return
        table = Table(title="📋 Saved Failure Scenarios", show_header=True, header_style="bold cyan")
        table.add_column("Filename", style="cyan")
        for s in scenarios:
            table.add_row(s)
        out.log.info(table)
        return

    try:
        result = recorder.replay_scenario(incident_id)
    except ValueError as e:
        out.log.info(f"[red]✗[/] {e}", stderr=True)
        raise typer.Exit(1)
    except Exception as e:
        out.log.info(f"[red]✗[/] Replay error: {e}", stderr=True)
        raise typer.Exit(1)

    if json_out:
        out.log.info(json.dumps(result, indent=2, default=str))
        return

    if result["success"]:
        icon = "[green]✅[/]"
        verdict = "[green]RECOVERY SUCCESSFUL[/]"
    else:
        icon = "[red]❌[/]"
        verdict = f"[red]RECOVERY FAILED[/] — {result.get('final_violations', [])}"

    out.log.info(Panel(
        f"{icon} Incident [cyan]{incident_id}[/cyan]\n"
        f"Status: {verdict}\n"
        f"Action: {result.get('action', {})}\n"
        f"Details: {result.get('details', 'N/A')}",
        title="🎭 Replay Result",
        border_style="cyan",
    ))


# ─────────────────────────────────────────────────────────────────────────────
# Pretty-printers (fallback when rich unavailable — unit tests / minimal env)
# ─────────────────────────────────────────────────────────────────────────────

def _print_verify_report(report: dict, spec: str):
    table = Table(title=f"SBS Verification — {spec}", show_header=True, header_style="bold cyan")
    table.add_column("Layer", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details")

    layers = report.get("layers", {})
    all_ok = True
    for name, info in layers.items():
        ok = info.get("ok", False)
        status = "[green]✓[/]" if ok else "[red]✗[/]"
        details = info.get("message", "")
        table.add_row(name, status, details)
        if not ok:
            all_ok = False

    out.log.info(table)
    summary = report.get("summary", {})
    verdict = "[green]✅ ALL PASS[/]" if all_ok else "[red]❌ FAILURES DETECTED[/]"
    out.log.info(f"\n{verdict}  ({summary.get('passed', 0)}/{summary.get('total', 0)} layers)")


def _print_status(data: dict):
    panel = Panel(
        f"[cyan]Version:[/] {data.get('version', '?')}\n"
        f"[cyan]Mode:[/]    {data.get('mode', '?')}\n"
        f"[cyan]Engine:[/]  {data.get('engine', '?')}",
        title="SBS Runtime Status",
        border_style="cyan",
    )
    out.log.info(panel)

    layers = data.get("layers", {})
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Layer")
    table.add_column("State")
    table.add_column("Health")
    for name, info in layers.items():
        table.add_row(name, str(info.get("state", "-")), str(info.get("health", "-")))
    out.log.info(table)


def _print_inspect(data: dict, layer: str | None):
    if layer:
        info = data.get(layer, data)
    else:
        info = data
    out.log.info(Panel(str(info), title=f"Layer: {layer or 'all'}", border_style="cyan"))


def _print_schema(result: dict, ok: bool):
    status = "[green]✅ State schema valid[/]" if ok else "[red]❌ State schema invalid[/]"
    out.log.info(status)
    if result.get("missing"):
        out.log.info(f"  Missing layers: {', '.join(result['missing'])}")
    if result.get("version"):
        out.log.info(f"  Version: {result['version']}")


def _print_doctor(report: dict):
    overall = report.get("overall", "unknown")
    color = "green" if overall == "pass" else "red" if overall == "fail" else "yellow"

    table = Table(title="🩺 SBS Doctor Report", show_header=False)
    table.add_column("Check", style="cyan")
    table.add_column("Result")
    table.add_column("Details")

    for check in report.get("checks", []):
        status_icon = {"pass": "✅", "fail": "❌", "warn": "⚠️"}.get(check.get("status", ""), "⏳")
        status_color = {"pass": "green", "fail": "red", "warn": "yellow"}.get(check.get("status", ""), "")
        status_str = f"[{status_color}]{status_icon} {check.get('name','')}[/{status_color}]"
        table.add_row(status_str, check.get("status", ""), check.get("message", ""))

    out.log.info(table)
    out.log.info(f"\nOverall: [{color}]{overall.upper()}[/{color}]")


def _print_config(result: dict):
    action = result.get("action", "show")
    if action == "show":
        table = Table(title="⚙️ SBS Configuration", show_header=True, header_style="cyan")
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        for key, val in result.get("config", {}).items():
            table.add_row(key, str(val))
        out.log.info(table)
    else:
        out.log.info(f"[cyan]Config:[/] {result.get('message', 'ok')}")


def _print_run(report: dict):
    ok = report.get("ok", False)
    status = "[green]✅ Scenario PASSED[/]" if ok else "[red]❌ Scenario FAILED[/]"
    out.log.info(status)
    if report.get("duration"):
        out.log.info(f"  Duration: {report['duration']:.2f}s")
    if report.get("output"):
        out.log.info(f"  Output: {report['output']}")
