"""trading/execution/vwap.py — ATOM-STEP-10: VWAP Execution Strategy"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from .order_book import OrderBookSimulator
from .slippage import AdaptiveSlippageModel


@dataclass
class VWAPSlice:
    slice_num: int
    scheduled_time: float
    target_qty: float
    actual_qty: float
    exec_price: float
    slippage_bps: float
    slippage_cost: float
    market_volume: float
    participation_rate: float
    filled: bool
    order_id: str = ""


@dataclass
class VWAPExecutionReport:
    strategy: str = "VWAP"
    symbol: str = ""
    side: str = ""
    total_qty: float = 0.0
    num_slices: int = 0
    start_time: float = 0.0
    end_time: float = 0.0
    duration_minutes: float = 0.0
    avg_price: float = 0.0
    vwap: float = 0.0
    avg_slippage_bps: float = 0.0
    total_slippage_cost: float = 0.0
    total_commission: float = 0.0
    total_cost: float = 0.0
    price_start: float = 0.0
    price_end: float = 0.0
    price_impact_bps: float = 0.0
    filled_qty: float = 0.0
    remaining_qty: float = 0.0
    avg_participation_rate: float = 0.0
    participation_violations: int = 0
    execution_prices: list[float] = field(default_factory=list)
    volume_profile: list[float] = field(default_factory=list)
    slices: list[VWAPSlice] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"VWAP {self.symbol} {self.side.upper()} | "
            f"qty={self.filled_qty:.4f} | "
            f"avg=${self.avg_price:.2f} | "
            f"slip={self.avg_slippage_bps:.1f}bps | "
            f"cost=${self.total_cost:.2f} | "
            f"vwap=${self.vwap:.2f} | "
            f"participation={self.avg_participation_rate:.1f}%"
        )


@dataclass
class VWAPConfig:
    """VWAP execution configuration."""

    num_slices: int = 10
    slice_duration_seconds: int = 30
    participation_rate: float = 0.10  # target % of market volume per slice
    max_participation_rate: float = 0.25  # hard cap on participation
    use_volume_curve: bool = True  # weight slices by typical volume distribution
    volume_curve_type: str = "default"  # "default", "morning", "afternoon", "intraday"
    max_price_slippage_bps: float = 50.0
    commission_bps: float = 2.0
    # Volume curve (24 hourly weights summing to 1.0)
    # Default: U-shaped distribution (low at open/close, high mid-day)
    volume_weights: list[float] = field(default_factory=list)

    def __post_init__(self):
        if not self.volume_weights:
            # Default U-shaped volume curve
            self.volume_weights = self._default_curve()

    def _default_curve(self) -> list[float]:
        """Default intraday volume curve (24 hourly weights).

        Based on typical equity market patterns.
        Market open (9-10am) and close (3-4pm) are highest volume.
        Lunch (12-1pm) is lowest.
        """
        hours = [
            0.5,
            0.3,
            0.2,
            0.2,
            0.3,
            0.5,  # 0-5am
            1.0,
            2.5,
            4.0,
            3.5,
            3.0,
            2.0,  # 6-11am
            2.0,
            2.5,
            3.0,
            3.5,
            4.0,
            4.5,  # 12-17pm
            3.5,
            2.5,
            1.5,
            1.0,
            0.7,
            0.5,  # 18-23pm
        ]
        total = sum(hours)
        return [h / total for h in hours]

    def get_slice_weight(self, slice_num: int) -> float:
        """Get volume weight for a given slice number."""
        if not self.use_volume_curve:
            return 1.0 / self.num_slices
        if slice_num < len(self.volume_weights):
            hour_idx = int(slice_num * 24 / self.num_slices)
            return self.volume_weights[min(hour_idx, 23)]
        return 1.0 / self.num_slices


class VWAPExecutor:
    """Volume-Weighted Average Price execution strategy.

    Executes orders proportional to expected market volume,
    targeting VWAP as the benchmark. Respects volume distribution
    throughout the trading day.

    Usage:
        executor = VWAPExecutor(broker=broker)
        config = VWAPConfig(num_slices=20, participation_rate=0.10)
        report = executor.execute("BTC/USDT", "buy", qty=1.0, config=config)
    """

    def __init__(
        self,
        order_book_sim: OrderBookSimulator | None = None,
        slippage_model: AdaptiveSlippageModel | None = None,
        commission_bps: float = 2.0,
    ):
        self.ob_sim = order_book_sim or OrderBookSimulator()
        self.slippage = slippage_model or AdaptiveSlippageModel()
        self.commission_bps = commission_bps

    def _simulate_market_volume(self, slice_num: int, cfg: VWAPConfig) -> float:
        """Simulate market volume for a given slice (in base currency units).

        Uses configured volume curve to distribute volume.
        """
        base_volume = self.ob_sim.adv / 390  # per 5-min bar on average
        weight = cfg.get_slice_weight(slice_num)
        num_slices_per_hour = 3600 / cfg.slice_duration_seconds
        # Volume varies by time of day
        volume = base_volume * weight * num_slices_per_hour
        # Add some randomness
        noise = 0.8 + 0.4 * ((hash((time.time(), slice_num)) % 1000) / 1000)
        return volume * noise

    def execute(
        self,
        symbol: str,
        side: str,
        qty: float,
        config: VWAPConfig | None = None,
        current_price: float = 0.0,
        get_market_price_fn=None,
    ) -> VWAPExecutionReport:
        """Execute a VWAP order.

        Args:
            symbol: Trading pair
            side: "buy" or "sell"
            qty: Total quantity to execute
            config: VWAP configuration
            current_price: Reference price
            get_market_price_fn: Optional live price function

        Returns:
            VWAPExecutionReport with detailed execution breakdown
        """
        cfg = config or VWAPConfig()
        price = current_price or self.ob_sim.mid_price

        report = VWAPExecutionReport(
            strategy="VWAP",
            symbol=symbol,
            side=side,
            total_qty=qty,
            num_slices=cfg.num_slices,
            start_time=time.time(),
            price_start=price,
        )

        total_cost = 0.0
        total_slippage_cost = 0.0
        total_commission = 0.0
        exec_prices = []
        volumes = []
        now = time.time()
        filled_qty_total = 0.0
        participation_sum = 0.0
        participation_violations = 0

        for i in range(cfg.num_slices):
            slice_price = price

            # Simulate price drift
            price_drift = 0.0003 * ((hash((now, i)) % 1000) - 500) / 500
            slice_price = slice_price * (1 + price_drift)

            # Target quantity based on volume curve
            raw_target = qty * cfg.get_slice_weight(i)
            target_qty = raw_target

            # Market volume simulation
            market_vol = self._simulate_market_volume(i, cfg)
            volumes.append(market_vol)

            # Participation rate check
            participation = market_vol * cfg.participation_rate if market_vol > 0 else 0
            target_qty = min(target_qty, market_vol * cfg.max_participation_rate)

            if participation > 0 and target_qty / participation > cfg.max_participation_rate:
                participation_violations += 1

            participation_rate = (target_qty / market_vol * 100) if market_vol > 0 else 0
            participation_sum += participation_rate

            # Market impact
            impact = self.ob_sim.estimate_market_impact(side, target_qty, num_slices=1, base_price=slice_price)

            # Slippage
            slip = self.slippage.calculate(
                side,
                target_qty,
                slice_price,
                volatility_bps=impact.slippage_bps * 100,
                spread_bps=self.ob_sim.spread_bps,
                adv=self.ob_sim.adv,
                market_regime="normal",
                orderbook_depth=self.ob_sim.depth_per_level,
            )

            if slip.slippage_bps > cfg.max_price_slippage_bps:
                report.slices.append(
                    VWAPSlice(
                        slice_num=i + 1,
                        scheduled_time=now + i * cfg.slice_duration_seconds,
                        target_qty=raw_target,
                        actual_qty=0,
                        exec_price=0,
                        slippage_bps=slip.slippage_bps,
                        slippage_cost=0,
                        market_volume=market_vol,
                        participation_rate=participation_rate,
                        filled=False,
                        order_id="ABORTED",
                    )
                )
                continue

            exec_price = slip.exec_price
            exec_prices.append(exec_price)
            commission = target_qty * exec_price * cfg.commission_bps / 10000
            slice_cost = slip.slippage_cost + impact.market_impact_cost + commission

            total_cost += slice_cost
            total_slippage_cost += slip.slippage_cost
            total_commission += commission
            filled_qty_total += target_qty

            report.slices.append(
                VWAPSlice(
                    slice_num=i + 1,
                    scheduled_time=now + i * cfg.slice_duration_seconds,
                    target_qty=raw_target,
                    actual_qty=target_qty,
                    exec_price=exec_price,
                    slippage_bps=slip.slippage_bps,
                    slippage_cost=slip.slippage_cost,
                    market_volume=market_vol,
                    participation_rate=participation_rate,
                    filled=True,
                    order_id=f"VWAP-{int(now * 1000)}-{i}",
                )
            )

            time.sleep(0.01)

        report.end_time = time.time()
        report.duration_minutes = (report.end_time - report.start_time) / 60
        report.filled_qty = filled_qty_total
        report.remaining_qty = qty - filled_qty_total

        filled = [s for s in report.slices if s.filled]
        report.avg_price = (
            sum(s.exec_price * s.actual_qty for s in filled) / filled_qty_total if filled_qty_total > 0 else 0
        )
        report.vwap = report.avg_price

        # VWAP benchmark: sum(price * volume) / sum(volume) for filled slices
        vwap_numerator = sum(s.exec_price * s.market_volume for s in filled)
        vwap_denominator = sum(s.market_volume for s in filled)
        if vwap_denominator > 0:
            report.vwap = vwap_numerator / vwap_denominator

        report.avg_slippage_bps = sum(s.slippage_bps for s in filled) / len(filled) if filled else 0
        report.total_slippage_cost = total_slippage_cost
        report.total_commission = total_commission
        report.total_cost = total_cost
        report.price_end = exec_prices[-1] if exec_prices else price
        report.execution_prices = exec_prices
        report.volume_profile = volumes
        report.avg_participation_rate = participation_sum / cfg.num_slices
        report.participation_violations = participation_violations

        if report.price_start > 0:
            report.price_impact_bps = abs(report.avg_price - report.price_start) / report.price_start * 10000

        return report

    def __repr__(self) -> str:
        return f"VWAPExecutor(num_slices={self.ob_sim.num_levels}, commission={self.commission_bps}bps)"


if __name__ == "__main__":
    print("=== VWAP Execution ===")
    executor = VWAPExecutor()
    cfg = VWAPConfig(num_slices=5, slice_duration_seconds=10)
    report = executor.execute("BTC/USDT", "buy", qty=1.0, current_price=50000, config=cfg)
    print(f"  {report.summary()}")
    for s in report.slices:
        status = "FILLED" if s.filled else "ABORTED"
        print(
            f"    Slice {s.slice_num}: {status} | "
            f"qty={s.actual_qty:.4f} | "
            f"@${s.exec_price:.2f} | "
            f"mkt_vol={s.market_volume:.2f} | "
            f"participation={s.participation_rate:.1f}%"
        )
    print(f"  VWAP benchmark: ${report.vwap:.2f}")
    print(f"  Participation violations: {report.participation_violations}")
