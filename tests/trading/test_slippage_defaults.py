from decimal import Decimal

from trading.execution.slippage import DEFAULT_SLIPPAGE_BPS, SlippageModel
from trading.ledger.paper_broker import FixedBpsSlippage


def test_defaults_share_single_constant():
    assert SlippageModel().slippage_bps == DEFAULT_SLIPPAGE_BPS
    assert FixedBpsSlippage().slippage_bps == Decimal(str(DEFAULT_SLIPPAGE_BPS))


def test_gate_estimate_not_looser_than_paper_fill():
    spread = 2.5
    gate = SlippageModel(spread_bps=spread).calculate("buy", 1.0, 100.0).slippage_bps
    paper = float(FixedBpsSlippage().slippage_bps) + spread / 2
    assert gate >= paper
