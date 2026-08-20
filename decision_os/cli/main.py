"""DecisionOS CLI tool."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))


def cmd_list(args):
    from decision_os.core import PluginManager as PM
    pm = PM(tenant_tier=args.tier or "Start")
    pm.discover()
    for pid in sorted(pm.registry.list_all()):
        entry = pm.registry.get(pid)
        print(f"  {pid:25s}  v{entry.manifest.version:8s}  {entry.state.value}")


def cmd_install(args):
    from decision_os.core import PluginManager as PM
    pm = PM(tenant_tier=args.tier or "Start")
    manifests = pm.discover()
    if args.plugin_id not in manifests:
        print(f"Plugin '{args.plugin_id}' not found")
        return 1
    pm.install(manifests[args.plugin_id])
    pm.load(args.plugin_id)
    pm.enable(args.plugin_id)
    print(f"Plugin '{args.plugin_id}' installed and enabled")
    return 0


def cmd_bootstrap(args):
    from decision_os.core import PluginManager as PM
    pm = PM(tenant_tier=args.tier or "Start")
    manifests = pm.discover()
    for mid, mf in manifests.items():
        pm.install(mf)
        pm.load(mid)
        pm.enable(mid)
        print(f"  ✓ {mid} v{mf.version}")
    print("All plugins bootstrapped")
    return 0


def main():
    parser = argparse.ArgumentParser(description="DecisionOS CLI")
    parser.add_argument("--tier", help="Tenant tier (Start, Pro, Enterprise)")

    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all plugins")
    sp_install = sub.add_parser("install", help="Install a plugin")
    sp_install.add_argument("plugin_id")
    sub.add_parser("bootstrap", help="Bootstrap all built-in plugins")

    args = parser.parse_args()
    if args.command == "list":
        return cmd_list(args)
    elif args.command == "install":
        return cmd_install(args)
    elif args.command == "bootstrap":
        return cmd_bootstrap(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
