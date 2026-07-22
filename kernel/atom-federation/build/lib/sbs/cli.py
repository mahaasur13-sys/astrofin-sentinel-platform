"""
sbs/cli.py — Command-line interface for SBS v1.

Commands:
    sbs --version
    sbs verify [--spec strict|relaxed]
    sbs status
    sbs inspect [--layer drl|ccl|f2|desc]
    sbs schema-check [--file PATH] [JSON]

For pretty output install rich:
    pip install atom-federation-os[cli]
"""

import argparse
import json
import sys

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    _RICH = True
except ImportError:
    _RICH = False

from sbs import GlobalInvariantEngine, SystemBoundarySpec, __version__, schema_validate_state


def _out(msg: str, style: str | None = None) -> None:
    if _RICH:
        from rich import print as rprint
        rprint(f"[{style}]{msg}[/{style}]" if style else msg)
    else:
        print(msg)


def _run_verify(spec_mode: str) -> int:
    """Run SBS invariant verification against test cases."""
    modes = {"strict": False, "relaxed": True}
    spec = SystemBoundarySpec(allow_event_reorder=modes.get(spec_mode, False))
    engine = GlobalInvariantEngine(spec)

    cases = [
        {
            "name": "nominal",
            "drl": {"leader": "n1", "term": 1, "partitions": 0, "quorum_ratio": 0.9},
            "ccl": {"leader": "n1", "term": 1, "stale_reads": 0},
            "f2": {"leader": "n1", "term": 1, "quorum_ratio": 0.9, "commit_index": 10},
            "desc": {"leader": "n1", "term": 1, "commit_index": 10},
            "expect": "pass",
        },
        {
            "name": "split-brain",
            "drl": {"leader": "n1", "term": 1, "partitions": 2, "quorum_ratio": 0.9},
            "ccl": {"leader": "n2", "term": 2, "stale_reads": 0},
            "f2": {"leader": "n1", "term": 1, "quorum_ratio": 0.6, "commit_index": 5},
            "desc": {"leader": "n1", "term": 1, "commit_index": 5},
            "expect": "violation",
        },
        {
            "name": "stale-read",
            "drl": {"leader": "n1", "term": 2, "partitions": 1, "quorum_ratio": 0.9},
            "ccl": {"leader": "n1", "term": 1, "stale_reads": 5},
            "f2": {"leader": "n1", "term": 1, "quorum_ratio": 0.9, "commit_index": 10},
            "desc": {"leader": "n1", "term": 1, "commit_index": 10},
            "expect": "violation",
        },
    ]

    table = Table(title="SBS Verification Results", show_header=True, header_style="bold cyan")
    table.add_column("Test Case", style="bold")
    table.add_column("Result", justify="center")
    table.add_column("Details", style="dim")

    all_pass = True
    for tc in cases:
        name = tc["name"]
        expect = tc["expect"]
        result = engine.evaluate(
            drl_state=tc["drl"],
            ccl_state=tc["ccl"],
            f2_state=tc["f2"],
            desc_state=tc["desc"],
        )

        if result:  # bool — no violation
            status = "✅ PASS" if expect == "pass" else "❌ FAIL (expected violation)"
            details = "No violation"
            if expect == "violation":
                all_pass = False
        else:  # violation detected
            status = "✅ CORRECTLY DETECTED" if expect == "violation" else "❌ FAIL"
            details = "invariant violation detected"
            if expect == "pass":
                all_pass = False

        table.add_row(tc["name"], status, details)

    if _RICH:
        Console().print(table)
    else:
        for tc in cases:
            print(f"  {tc['name']}: {'PASS' if engine.evaluate(
                **{k: v for k, v in tc.items() if k != 'expect'}).is_ok else 'FAIL'}")

    _out(f"\nOverall: {'✅ ALL PASS' if all_pass else '❌ FAILURES DETECTED'}",
         "green" if all_pass else "red")
    return 0 if all_pass else 1


def _run_status() -> int:
    """Show SBS system status and configuration."""
    spec = SystemBoundarySpec()
    info = {
        "version": __version__,
        "allow_split_brain": spec.allow_split_brain,
        "allow_event_reorder": spec.allow_event_reorder,
        "allow_uncommitted_read": spec.allow_uncommitted_read,
        "quorum_threshold": spec.quorum_threshold,
        "max_partitions": spec.max_partitions,
        "clock_skew_threshold_ms": spec.clock_skew_threshold_ms,
    }

    if _RICH:
        Console().print(Panel(
            "\n".join(f"  [bold]{k}:[/bold] [cyan]{v}[/cyan]" for k, v in info.items()),
            title="[bold]SBS v1 — System Status[/bold]",
            border_style="blue",
        ))
    else:
        print("SBS v1 — System Status")
        for k, v in info.items():
            print(f"  {k}: {v}")
    return 0


def _run_inspect(layer: str | None) -> int:
    """Inspect layer details or full system contract."""
    from sbs.system_contract import SYSTEM_CONTRACT, InvariantType

    layer_info = {
        "drl": "Distributed Reality Layer — network partitions, clock skew, leader term",
        "ccl": "Consensus Contract Layer — semantic contracts, stale reads, leader leases",
        "f2": "Quorum Kernel — F2/F3/F8 commit safety, leader uniqueness",
        "desc": "Distributed Event Sourcing Component — immutable append-only audit trail",
    }

    if layer:
        layer = layer.lower()
        if layer not in layer_info:
            print(f"Unknown layer: {layer}. Choose: drl, ccl, f2, desc", file=sys.stderr)
            return 1
        if _RICH:
            Console().print(Panel(
                layer_info[layer],
                title=f"[bold]{layer.upper()} Layer[/bold]",
                border_style="cyan",
            ))
        else:
            print(f"{layer.upper()} — {layer_info[layer]}")
    else:
        if _RICH:
            Console().print(Panel(
                "\n".join(
                    f"[bold]{inv.name}[/bold]\n" +
                    "\n".join(f"  • {r.description} [dim](w={r.weight})[/dim]"
                              for r in [rr for rr in SYSTEM_CONTRACT if rr.type == inv])
                    + "\n"
                    for inv in InvariantType
                ),
                title="[bold]SBS v1 — SYSTEM CONTRACT[/bold]",
                border_style="green",
            ))
        else:
            print("SBS v1 — SYSTEM CONTRACT")
            for inv in InvariantType:
                rules = [r for r in SYSTEM_CONTRACT if r.type == inv]
                if rules:
                    print(f"\n{inv.name}")
                    for r in rules:
                        print(f"  • {r.description} (w={r.weight})")
    return 0


def _run_schema_check(state_arg: str | None, file_path: str | None) -> int:
    """Validate state JSON against required schema."""
    if file_path:
        try:
            with open(file_path) as f:
                state_arg = f.read()
        except OSError as e:
            print(f"Cannot read {file_path}: {e}", file=sys.stderr)
            return 1

    if not state_arg:
        print("Provide state JSON as argument or via --file", file=sys.stderr)
        return 1

    try:
        state = json.loads(state_arg)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}", file=sys.stderr)
        return 1

    try:
        schema_validate_state(state)
        _out("✅ State schema valid", "green")
        return 0
    except Exception as e:
        _out(f"❌ Schema validation failed: {e}", "red")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="sbs",
        description="SBS v1 — System Boundary Spec CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  sbs --version
  sbs verify
  sbs verify --spec relaxed
  sbs status
  sbs inspect
  sbs inspect --layer drl
  sbs schema-check '{"drl":{},"ccl":{},"f2":{},"desc":{}}'
  sbs schema-check --file state.json

Install rich for pretty output: pip install atom-federation-os[cli]
        """,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output, show only result")
    subs = parser.add_subparsers(dest="command", required=True)

    p_ver = subs.add_parser("verify", help="run SBS invariant verification")
    p_ver.add_argument("--spec", choices=["strict", "relaxed"], default="strict")

    subs.add_parser("status", help="show SBS system status")

    p_ins = subs.add_parser("inspect", help="inspect layer or system contract")
    p_ins.add_argument("--layer", choices=["drl", "ccl", "f2", "desc"])

    p_sc = subs.add_parser("schema-check", help="validate state JSON against schema")
    p_sc.add_argument("state", nargs="?", default=None)
    p_sc.add_argument("--file", default=None)

    args = parser.parse_args()

    if args.command == "verify":
        sys.exit(_run_verify(args.spec))
    elif args.command == "status":
        sys.exit(_run_status())
    elif args.command == "inspect":
        sys.exit(_run_inspect(args.layer))
    elif args.command == "schema-check":
        sys.exit(_run_schema_check(args.state, args.file))


if __name__ == "__main__":
    main()
