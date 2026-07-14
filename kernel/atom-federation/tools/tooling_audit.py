#!/usr/bin/env python
"""
tooling_audit.py — atom-federation-os v9.0 Tooling Readiness Audit

SYSTEM READY = Zo(12/12) AND API_KEYS(4/4) AND audit == PASS
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

print("=" * 60)
print("LAYER 1 — ZO COMPUTER NATIVE TOOLS")
print("=" * 60)

ZO_NATIVE = [
    ("google_drive", "Google Drive"),
    ("dropbox", "Dropbox"),
    ("gmail", "Gmail"),
    ("spotify", "Spotify"),
    ("linear", "Linear"),
    ("notion", "Notion"),
    ("google_calendar", "Google Calendar"),
    ("google_tasks", "Google Tasks"),
    ("airtable_oauth", "Airtable"),
    ("microsoft_onedrive", "OneDrive"),
    ("microsoft_outlook", "Outlook"),
    ("x", "X/Twitter"),
]

import importlib

zo_ok = 0
for slug, name in ZO_NATIVE:
    try:
        m = importlib.import_module(f"zo.apps.{slug}")
        tools = getattr(m, "TOOLS", None)
        ready = bool(tools)
    except Exception:
        ready = False
    status = "CONNECTED" if ready else "NOT CONNECTED"
    print(f"  {name:<22} {'OK' if ready else 'MISSING'}")
    if ready:
        zo_ok += 1

print(f"\nZo Native: {zo_ok}/{len(ZO_NATIVE)} ready")

print("\n" + "=" * 60)
print("LAYER 2 — AABS GATEWAY (EXTERNAL APIs)")
print("=" * 60)

AABS_KEYS = {
    "FIRECRAWL_API_KEY": "Firecrawl",
    "INSTANTLY_API_KEY": "Instantly",
    "COMPOSIO_API_KEY": "Composio",
    "AGENTMAIL_API_KEY": "AgentMail",
}

aabs_ok = 0
for env_var, name in AABS_KEYS.items():
    present = bool(os.environ.get(env_var))
    print(f"  {name:<22} {'READY' if present else 'MISSING'}")
    if present:
        aabs_ok += 1

print(f"\nAABS Keys: {aabs_ok}/{len(AABS_KEYS)} ready")

print("\n" + "=" * 60)
print("LAYER 3 — AGENT BROWSER")
print("=" * 60)

try:
    r = subprocess.run(
        ["/root/agent-browser/bin/agent-browser-linux-x64", "--version"],
        capture_output=True, timeout=5
    )
    version = r.stdout.strip() or "installed"
    print(f"  agent-browser  OK ({version})")
    agent_browser_ok = True
except Exception:
    print("  agent-browser  MISSING")
    agent_browser_ok = False

print("\n" + "=" * 60)
print("LAYER 4 — ATOMFEDERATION-OS INTEGRATED TOOLS")
print("=" * 60)

IN_REPO = [
    ("orchestration.ExecutionGateway.execution_gateway", "ExecutionGateway"),
    ("core.proof.proof_verifier", "ProofVerifier"),
    ("core.runtime.runtime_guard", "RuntimeGuard"),
    ("core.federation.federated_gateway", "FederatedGateway"),
    ("core.economics.stake_registry", "StakeRegistry"),
    ("core.economics.slashing_engine", "SlashingEngine"),
    ("formal.dfa_gateway", "DFAExecutionGuard"),
    ("formal.model_checker", "ASTSnapshot"),
    ("atomos_pkg.atomos.aabs.aabs_gateway", "AABSGateway"),
]

in_repo_ok = 0
for module_path, name in IN_REPO:
    try:
        parts = module_path.rsplit(".", 1)
        if len(parts) == 2:
            mod = importlib.import_module(f"{parts[0]}.{parts[1]}")
        else:
            mod = importlib.import_module(parts[0])
        print(f"  {name:<22} OK")
        in_repo_ok += 1
    except Exception:
        print(f"  {name:<22} MISSING")

print(f"\nIn-repo: {in_repo_ok}/{len(IN_REPO)} ready")

print("\n" + "=" * 60)
print("AUDIT SUMMARY")
print("=" * 60)

blockers = []
if zo_ok < len(ZO_NATIVE):
    blockers.append(f"Zo Native: {len(ZO_NATIVE) - zo_ok} missing")
if aabs_ok < len(AABS_KEYS):
    blockers.append(f"AABS Keys: {len(AABS_KEYS) - aabs_ok} missing")
if not agent_browser_ok:
    blockers.append("Agent Browser: not installed")
if in_repo_ok < len(IN_REPO):
    blockers.append(f"In-repo: {len(IN_REPO) - in_repo_ok} missing")

if not blockers:
    print("  SYSTEM READY — ZERO BLOCKERS")
    sys.exit(0)
else:
    print("  SYSTEM NOT READY:")
    for b in blockers:
        print(f"    - {b}")
    print()
    print("NEXT ACTIONS:")
    print("  1. Connect Zo apps: Settings > Integrations")
    print("  2. Add API keys: Settings > Advanced")
    for env_var, name in AABS_KEYS.items():
        if not os.environ.get(env_var):
            print(f"     - {name}: set {env_var}")
    print("  3. Re-run: python3 tools/tooling_audit.py")
    sys.exit(1)
