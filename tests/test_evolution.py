from __future__ import annotations

import pytest
@pytest.mark.unit
def test_engine_imports():
    from meta_rl.evolution import EvolutionEngine

    assert EvolutionEngine is not None
