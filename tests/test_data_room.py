"""Data Room CI contract test."""
from __future__ import annotations
from dataclasses import fields
import pytest
from data_room.resolvers import RESOLVER_REGISTRY
from data_room.blueprint import PriceTick

def test_data_room_inventory_flag():
    """Validate data room resolvers + blueprint contract."""
    assert len(RESOLVER_REGISTRY) >= 3, "Need at least 3 resolvers"
    assert all(hasattr(r, "name") for r in RESOLVER_REGISTRY)
    field_names = {f.name for f in fields(PriceTick)}
    assert "symbol" in field_names
    assert "price" in field_names
    assert "source_id" in field_names
    assert "quality_score" in field_names
