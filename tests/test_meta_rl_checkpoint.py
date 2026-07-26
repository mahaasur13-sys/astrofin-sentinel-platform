"""Tests for Meta-RL checkpoint persistence (Sprint D/D1)."""
import pytest, tempfile, os, json
from pathlib import Path
from meta_rl.checkpoint import save_checkpoint, load_checkpoint, list_checkpoints, delete_checkpoint

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)

def test_save_and_load_checkpoint(temp_dir):
    weights = {'q_network': [0.1, 0.2], 'policy': {'lr': 0.001}}
    path = temp_dir / 'ckpt_001.json'
    save_checkpoint(weights, path)
    assert path.exists()
    loaded = load_checkpoint(path)
    assert loaded == weights

def test_load_nonexistent_returns_none(temp_dir):
    assert load_checkpoint(temp_dir / 'nonexistent.json') is None

def test_list_checkpoints(temp_dir):
    for name in ('ckpt_003.json', 'ckpt_001.json', 'ckpt_002.json'):
        save_checkpoint({}, temp_dir / name)
    ckpts = list_checkpoints(temp_dir)
    assert [p.name for p in ckpts] == ['ckpt_001.json', 'ckpt_002.json', 'ckpt_003.json']

def test_delete_checkpoint(temp_dir):
    p = temp_dir / 'ckpt_del.json'
    save_checkpoint({}, p)
    assert p.exists()
    delete_checkpoint(p)
    assert not p.exists()
