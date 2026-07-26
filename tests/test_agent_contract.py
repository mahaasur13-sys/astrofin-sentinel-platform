"""Tests for Agent contract validation (Sprint D/D2)."""
import pytest
from core.agent_contract import AgentOutput

def test_valid_agent_output():
    out = AgentOutput(signal='LONG', confidence=85, reasoning='Strong uptrend')
    assert out.signal == 'LONG'
    assert out.confidence == 85

def test_signal_rejects_invalid_value():
    with pytest.raises(ValueError):
        AgentOutput(signal='NONSENSE', confidence=50, reasoning='test')

def test_confidence_below_0_rejected():
    with pytest.raises(ValueError):
        AgentOutput(signal='HOLD', confidence=-1, reasoning='test')

def test_confidence_above_100_rejected():
    with pytest.raises(ValueError):
        AgentOutput(signal='HOLD', confidence=101, reasoning='test')

def test_metadata_optional():
    out = AgentOutput(signal='SHORT', confidence=60, reasoning='Bearish divergence')
    assert out.metadata == {}

def test_metadata_preserved():
    out = AgentOutput(signal='LONG', confidence=90, reasoning='test', metadata={'source': 'gann'})
    assert out.metadata == {'source': 'gann'}
