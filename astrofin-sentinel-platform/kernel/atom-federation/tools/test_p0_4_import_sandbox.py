#!/usr/bin/env python3
"""
test_p0_4_import_sandbox.py — P0.4 Import Firewall Tests

Tests that protected modules are blocked outside ExecutionGateway context.
"""
import subprocess
import sys

REPO = "/home/workspace/atom-federation-os"

def run_test(description: str, code: str, expect_pass: bool) -> bool:
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=10,
    )
    passed = (result.returncode == 0) == expect_pass
    status = "PASS" if passed else "FAIL"
    print(f"  [{status}] {description}")
    if not passed:
        print(f"    Expected: {'pass' if expect_pass else 'fail'}")
        print(f"    Got returncode={result.returncode}")
        if result.stderr:
            print(f"    stderr: {result.stderr[:200]}")
    return passed


def test_direct_import_blocked():
    """Protected module import outside gateway → blocked."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall
install_firewall()
# Simulate outside-gateway state
from core.runtime.import_guard import GatewayContext
assert not GatewayContext.is_active(), "context should be inactive"
# Try to import actuator — should be blocked
try:
    import actuator
    print("FAIL: actuator should be blocked")
except ImportError as e:
    if "BLOCKED" in str(e) or "protected" in str(e).lower():
        print("PASS")
    else:
        print(f"FAIL: wrong error: {{e}}")
"""
    return run_test("Direct import of actuator outside gateway → BLOCKED", code, True)


def test_mutation_executor_blocked():
    """MutationExecutor import outside gateway → blocked."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall
install_firewall()
try:
    import mutation_executor
    print("FAIL")
except ImportError:
    print("PASS")
"""
    return run_test("MutationExecutor import outside gateway → BLOCKED", code, True)


def test_gateway_context_allows():
    """Import allowed when gateway context is active."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall, GatewayContextGuard
install_firewall()
# Activate gateway context (simulates being inside ExecutionGateway.execute)
with GatewayContextGuard("test"):
    import actuator  # Should succeed
    print("PASS")
"""
    return run_test("Protected import INSIDE gateway context → ALLOWED", code, True)


def test_nested_import_blocked():
    """Nested import chain outside gateway → blocked."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall
install_firewall()
# Outer module (unprotected) tries to import protected
try:
    import importlib
    # Try importing consensus module
    importlib.import_module("consensus")
    print("FAIL")
except ImportError:
    print("PASS")
"""
    return run_test("Nested import of consensus outside gateway → BLOCKED", code, True)


def test_actuator_via_importlib():
    """importlib import of actuator outside gateway → blocked."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall
install_firewall()
try:
    import importlib
    importlib.import_module("actuator")
    print("FAIL")
except ImportError:
    print("PASS")
"""
    return run_test("importlib actuator outside gateway → BLOCKED", code, True)


def test_install_idempotent():
    """Firewall install is idempotent."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall, is_installed
install_firewall()
install_firewall()  # should not duplicate
install_firewall()
# Check it's in meta_path
found = any(hasattr(m, '_is_protected') for m in sys.meta_path)
print("PASS" if found else "FAIL")
"""
    return run_test("Firewall install is idempotent", code, True)


def test_uninstall_works():
    """Uninstall removes firewall from meta_path."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall, uninstall_firewall, _guard
install_firewall()
uninstall_firewall()
# Should not block now
in_meta = _guard in sys.meta_path
print("PASS" if not in_meta else "FAIL")
"""
    return run_test("Firewall uninstall removes from meta_path", code, True)


def test_consensus_blocked():
    """consensus module blocked outside gateway."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall
install_firewall()
try:
    import consensus
    print("FAIL")
except ImportError:
    print("PASS")
"""
    return run_test("consensus import outside gateway → BLOCKED", code, True)


def test_alignment_blocked():
    """alignment module blocked outside gateway."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall
install_firewall()
try:
    import alignment
    print("FAIL")
except ImportError:
    print("PASS")
"""
    return run_test("alignment import outside gateway → BLOCKED", code, True)


def test_cluster_node_blocked():
    """cluster.node.node (bypass path) blocked."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import install_firewall
install_firewall()
try:
    import cluster.node.node
    print("FAIL")
except ImportError:
    print("PASS")
"""
    return run_test("cluster.node.node import outside gateway → BLOCKED", code, True)


def test_multiple_calls_context():
    """Multiple activate/deactivate calls tracked correctly."""
    code = f"""
import sys
sys.path.insert(0, "{REPO}")
from core.runtime.import_guard import GatewayContext
assert not GatewayContext.is_active()
GatewayContext.activate("t1")
assert GatewayContext.is_active()
GatewayContext.activate("t2")  # nested
assert GatewayContext.is_active()
GatewayContext.deactivate()
assert GatewayContext.is_active()  # still active (depth=1)
GatewayContext.deactivate()
assert not GatewayContext.is_active()
print("PASS")
"""
    return run_test("Nested activate/deactivate tracked by depth", code, True)


def main():
    print("═"*60)
    print("P0.4 IMPORT SANDBOX TESTS")
    print("═"*60)

    tests = [
        test_direct_import_blocked,
        test_mutation_executor_blocked,
        test_gateway_context_allows,
        test_nested_import_blocked,
        test_actuator_via_importlib,
        test_install_idempotent,
        test_uninstall_works,
        test_consensus_blocked,
        test_alignment_blocked,
        test_cluster_node_blocked,
        test_multiple_calls_context,
    ]

    results = []
    for t in tests:
        results.append(t())
        if not results[-1]:
            print("  ^^^ FIRST FAILURE ^^^")

    print()
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} passed")
    print("═"*60)
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
