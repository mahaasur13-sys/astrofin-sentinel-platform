"""Revenue Share Calculator — tiered, per partner, per month"""


class RevenueShareCalculator:
    # Tier thresholds: (max_gross_INCLUSIVE, rate)
    # $0-$1000 → 10%, $1001-$5000 → 15%, $5001+ → 20%
    TIERS = [
        (1000.0, 0.10),  # $0 - $1000 inclusive
        (5000.0, 0.15),  # $1001 - $5000 inclusive
        (float("inf"), 0.20),
    ]

    def __init__(self):
        self._store = {}

    def calculate(self, gross_amount: float, partner_id: str) -> dict:
        if gross_amount < 0:
            raise ValueError("gross_amount cannot be negative")
        if gross_amount == 0:
            return {"romas_share": 0.0, "partner_payout": 0.0, "rate_used": 0.0}
        rate = self._get_tier_rate(gross_amount)
        roma_share = round(gross_amount * rate, 6)
        partner_payout = round(gross_amount - roma_share, 6)
        return {
            "gross_amount": gross_amount,
            "romas_share": roma_share,
            "partner_payout": partner_payout,
            "rate_used": rate,
            "partner_id": partner_id,
        }

    def _get_tier_rate(self, gross_amount: float) -> float:
        for threshold, rate in self.TIERS:
            if gross_amount <= threshold:
                return rate
        return 0.20

    def record_revenue(self, partner_id: str, amount: float, invoice_id: str, period: str) -> int:
        key = (partner_id, period)
        if key not in self._store:
            self._store[key] = {"total": 0.0, "invoices": []}
        self._store[key]["total"] += amount
        self._store[key]["invoices"].append({"invoice_id": invoice_id, "amount": amount})
        return len(self._store[key]["invoices"])

    def get_partner_monthly_revenue(self, partner_id: str, period: str) -> dict:
        entry = self._store.get((partner_id, period), {"total": 0.0, "invoices": []})
        return {"partner_id": partner_id, "period": period, "total": entry["total"]}


if __name__ == "__main__":
    calc = RevenueShareCalculator()
    for amt in [999, 1000, 1001, 5000, 5001, 0.01]:
        r = calc.calculate(amt, "test")
        print(f"${amt}: ROMA {r['rate_used']*100:.0f}% = ${r['romas_share']:.2f}")
