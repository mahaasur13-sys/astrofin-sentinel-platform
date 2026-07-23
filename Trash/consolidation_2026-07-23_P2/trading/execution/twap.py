"""trading/execution/twap.py — ATOM-STEP-10: TWAP Execution Strategy"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .order_book import OrderBookSimulator
from .slippage import AdaptiveSlippageModel


@dataclass
class TWAPSlice:
    slice_num: int
    scheduled_time: float
    qty: float
    exec_price: float
    slippage_bps: float
    slippage_cost: float
    filled: bool
    order_id: str = ""


@dataclass
class TWAPExecutionReport:
    strategy: str = "TWAP"
    symbol: str = ""
    side: str = ""
    total_qty: float = 0.0
    num_slices: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    duration_minutes: float = 0.0
    avg_price: float = 0.0
    avg_slippage_bps: float = 0.0
    total_slippage_cost: float = 0.0
    total_commission: float = 0.0
    total_cost: float = 0.0
    price_start: float = 0.0
    price_end: float = 0.0
    price_impact_bps: float = 0.0
    vwap: float = 0.0
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    execution_prices: list[float] = field(default_factory=list)
    slices: list[TWAPSlice] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"TWAP {self.symbol} {self.side.upper()} | "
            f"qty={self.filled_qty:.4f} | "
            f"avg=${self.avg_price:.2f} | "
            f"slip={self.avg_slippage_bps:.1f}bps | "
            f"cost=${self.total_cost:.2f} | "
            f"vwap=${self.vwap:.2f}"
        )


@dataclass
class TWAPConfig:
    num_slices: int = 10
    slice_duration_seconds: int = 30
    schedule_variance: float = 0.1
    execution_start_hour: int = 9
    execution_end_hour: int = 16
    max_price_slippage_bps: float = 50.0
    order_book_depth_threshold: float = 0.3
    use_adaptive_sizing: bool = True
    commission_bps: float = 2.0


class TWAPExecutor:
    def __init__(
        self,
        order_book_sim: OrderBookSimulator | None = None,
        slippage_model: AdaptiveSlippageModel | None = None,
        commission_bps: float = 2.0,
    ):
        self.ob_sim = order_book_sim or OrderBookSimulator()
        self.slippage = slippage_model or AdaptiveSlippageModel()
        self.commission_bps = commission_bps

    def execute(
        self,
        symbol: str,
        side: str,
        qty: float,
        config: TWAPConfig | None = None,
        current_price: float = 0.0,
        get_market_price_fn=None,
    ) -> TWAPExecutionReport:
        cfg = config or TWAPConfig()
        price = current_price or self.ob_sim.mid_price

        report = TWAPExecutionReport(
            strategy="TWAP",
            symbol=symbol,
            side=side,
            total_qty=qty,
            num_slices=cfg.num_slices,
            start_time=time.time(),
            price_start=price,
        )

        slice_qty = qty / cfg.num_slices
        total_cost = 0.0
        total_slippage_cost = 0.0
        total_commission = 0.0
        exec_prices = []
        now = time.time()

        for i in range(cfg.num_slices):
            slice_price = price * (1 + 0.0005 * ((hash((now, i)) % 1000) - 500) / 500)

            impact = self.ob_sim.estimate_market_impact(side, slice_qty, num_slices=1, base_price=slice_price)

            slip = self.slippage.calculate(
                side,
                slice_qty,
                slice_price,
                volatility_bps=impact.slippage_bps * 100,
                spread_bps=self.ob_sim.spread_bps,
                adv=self.ob_sim.adv,
                market_regime="normal",
                orderbook_depth=self.ob_sim.depth_per_level,
            )

            if slip.slippage_bps > cfg.max_price_slippage_bps:
                report.slices.append(
                    TWAPSlice(
                        slice_num=i + 1,
                        scheduled_time=now + i * cfg.slice_duration_seconds,
                        qty=slice_qty,
                        exec_price=0,
                        slippage_bps=slip.slippage_bps,
                        slippage_cost=0,
                        filled=False,
                        order_id="ABORTED",
                    )
                )
                continue

            exec_price = slip.exec_price
            exec_prices.append(exec_price)
            commission = slice_qty * exec_price * cfg.commission_bps / 10000
            slip_cost = slip.slippage_cost
            impact_cost = impact.market_impact_cost
            slice_cost = slip_cost + impact_cost + commission

            total_cost += slice_cost
            total_slippage_cost += slip_cost
            total_commission += commission

            report.slices.append(
                TWAPSlice(
                    slice_num=i + 1,
                    scheduled_time=now + i * cfg.slice_duration_seconds,
                    qty=slice_qty,
                    exec_price=exec_price,
                    slippage_bps=slip.slippage_bps,
                    slippage_cost=slip_cost,
                    filled=True,
                    order_id=f"TWAP-{int(now * 1000)}-{i}",
                )
            )

            time.sleep(0.01)

        report.end_time = time.time()
        report.duration_minutes = (report.end_time - report.start_time) / 60

        filled = [s for s in report.slices if s.filled]
        report.filled_qty = sum(s.qty for s in filled)
        report.remaining_qty = qty - report.filled_qty
        report.avg_price = sum(s.exec_price * s.qty for s in filled) / report.filled_qty if report.filled_qty > 0 else 0
        report.vwap = report.avg_price
        report.avg_slippage_bps = sum(s.slippage_bps for s in filled) / len(filled) if filled else 0
        report.total_slippage_cost = total_slippage_cost
        report.total_commission = total_commission
        report.total_cost = total_cost
        report.price_end = exec_prices[-1] if exec_prices else price
        report.execution_prices = exec_prices

        if report.price_start > 0:
            report.price_impact_bps = abs(report.avg_price - report.price_start) / report.price_start * 10000

        return report

    def __repr__(self) -> str:
        return f"TWAPExecutor(num_slices={self.ob_sim.num_levels}, commission={self.commission_bps}bps)"


if __name__ == "__main__":
    print("=== TWAP Execution ===")
    executor = TWAPExecutor()
    cfg = TWAPConfig(num_slices=5, slice_duration_seconds=10)
    report = executor.execute("BTC/USDT", "buy", qty=1.0, current_price=50000, config=cfg)
    print(f"  {report.summary()}")
    for s in report.slices:
        status = "FILLED" if s.filled else "ABORTED"
        print(
            f"    Slice {s.slice_num}: {status} @ ${s.exec_price:.2f}, slip={s.slippage_bps:.2f}bps, cost=${s.slippage_cost:.2f}"
        )
    print(f"  Total cost: ${report.total_cost:.2f} (commissions ${report.total_commission:.2f})")
