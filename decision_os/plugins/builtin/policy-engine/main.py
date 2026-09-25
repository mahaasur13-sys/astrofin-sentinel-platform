"""
Policy Engine plugin — evaluates all permissions before any action.

Every action (payment, file send, wallet access) goes through:
1. Policy Engine check
2. Decision Gate
3. Audit Trail
"""
from __future__ import annotations


class Plugin:
    """Central policy evaluation engine."""

    def on_enable(self) -> None:
        pass

    def evaluate(self, action: str, context: dict) -> dict:
        """
        Evaluate whether an action is permitted.
        Returns {"allowed": bool, "reason": str}.
        """
        if action.startswith("dashbeam:wallet:share"):
            if context.get("wallet_type") == "spend_key":
                return {"allowed": False, "reason": "SPEND_KEYS_NEVER_SHARED"}
        return {"allowed": True, "reason": "policy passed"}
