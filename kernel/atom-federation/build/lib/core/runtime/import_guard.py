"""
import_guard.py — atom-federation-os v9.0+P0.4

Import-time execution firewall via sys.meta_path hook.

FAIL-CLOSED: any protected module imported outside ExecutionGateway
context is BLOCKED (raises ImportError).

Protected modules:
    mutation_executor.*, actuator.*, alignment.*, ledger.*,
    consensus.*, federation.*, cluster.node.node

Gateway context:
    Activated ONLY inside ExecutionGateway.execute().

Execution allowed <=> GATEWAY_CONTEXT["active"] == True
"""
from __future__ import annotations

import sys
import threading

# ── Gateway Context (global, process-wide) ──────────────────────────────────

class GatewayContext:
    """
    Process-wide execution context flag.
    
    Active ONLY during ExecutionGateway.execute() call.
    All other code runs with active=False.
    """
    _lock = threading.Lock()
    _active: bool = False
    _depth: int = 0  # recursion counter
    _origin: str | None = None

    @classmethod
    def activate(cls, origin: str = "execute") -> None:
        with cls._lock:
            cls._active = True
            cls._depth += 1
            cls._origin = origin

    @classmethod
    def deactivate(cls) -> None:
        with cls._lock:
            cls._depth = max(0, cls._depth - 1)
            if cls._depth == 0:
                cls._active = False
                cls._origin = None

    @classmethod
    def is_active(cls) -> bool:
        return cls._active

    @classmethod
    def assert_active(cls, module: str) -> None:
        if not cls._active:
            raise ImportError(
                f"ATOMFEDERATION-OS: import of '{module}' is BLOCKED outside "
                f"ExecutionGateway context. "
                f"Execution is only permitted inside ExecutionGateway.execute()."
            )


# ── Protected Module Patterns ──────────────────────────────────────────────────

_PROTECTED_PATTERNS = (
    "mutation_executor",
    "actuator",
    "alignment",
    "ledger",
    "consensus",
    "federation",
    "cluster.node.node",
)

_FORBIDDEN_ENTITIES = (
    "apply_mutation",
    "execute_mutation",
    "actuate",
    "CausalActuationEngine",
)


class _ImportFirewall:
    """
    sys.meta_path finder that blocks protected module imports
    when GatewayContext is not active.
    """

    def find_module(self, fullname: str, path=None):
        # Check if this module/package is protected
        if not self._is_protected(fullname):
            return None  # Not protected, allow normally

        # Protected module — check context
        if GatewayContext.is_active():
            return None  # Gateway active, allow

        # Outside gateway context — BLOCK
        raise ImportError(
            f"ATOMFEDERATION-OS IMPORT BLOCKED: '{fullname}' "
            f"is a protected execution module and cannot be imported "
            f"outside ExecutionGateway context. "
            f"Only ExecutionGateway.execute() may trigger mutations."
        )

    def _is_protected(self, fullname: str) -> bool:
        # Exact match
        if fullname in _PROTECTED_PATTERNS:
            return True
        # Package prefix match
        for pattern in _PROTECTED_PATTERNS:
            if fullname == pattern or fullname.startswith(pattern + "."):
                return True
        return False

    def find_spec(self, fullname: str, path, target=None):
        """Python 3.10+ meta_path hook."""
        if not self._is_protected(fullname):
            return None
        if GatewayContext.is_active():
            return None

        # Block by raising ImportError during spec resolution
        raise ImportError(
            f"ATOMFEDERATION-OS: protected module '{fullname}' "
            f"blocked outside ExecutionGateway"
        )


# ── Guard Installation ─────────────────────────────────────────────────────────

_guard = _ImportFirewall()
_installed = False
_lock = threading.Lock()


def install_firewall() -> None:
    """Install the import firewall into sys.meta_path. Idempotent."""
    global _installed
    with _lock:
        if _installed:
            return
        if _guard not in sys.meta_path:
            sys.meta_path.insert(0, _guard)
        _installed = True


def uninstall_firewall() -> None:
    """Remove the import firewall. Used only for testing."""
    global _installed
    with _lock:
        if _guard in sys.meta_path:
            sys.meta_path.remove(_guard)
        _installed = False


def is_installed() -> bool:
    return _installed


# ── Context Manager for Gateway ────────────────────────────────────────────────

class GatewayContextGuard:
    """
    Context manager that activates gateway context for a block of code.
    
    Usage inside ExecutionGateway.execute():
        with GatewayContextGuard("execute"):
            # gateway context is active here
    """
    def __init__(self, origin: str = "execute"):
        self.origin = origin

    def __enter__(self):
        GatewayContext.activate(self.origin)
        return self

    def __exit__(self, *args):
        GatewayContext.deactivate()
        return False
