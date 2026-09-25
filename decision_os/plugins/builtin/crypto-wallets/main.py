"""
Crypto Wallets plugin — Monero view-only + subaddresses.
SPEND KEYS NEVER LEAVE THIS PLUGIN.
"""
from __future__ import annotations


class Plugin:
    def on_enable(self) -> None:
        pass

    def get_view_only_wallet(self, wallet_id: str) -> dict:
        """
        Returns ONLY view-key data. Spend keys are NEVER serialized.
        """
        return {
            "wallet_id": wallet_id,
            "primary_address": "4...",
            "view_key": "0...",
            "subaddresses": [],
        }
