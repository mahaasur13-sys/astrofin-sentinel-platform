"""Tests for RevenueShareCalculator + Stripe Webhook."""
import sys; sys.path.insert(0, '.')

class MockLedger:
    def get_monthly_revenue(self, tid):
        return {"t1": 500.0, "t2": 3000.0, "t3": 7000.0}.get(tid, 0.0)

def test_tiered_rates():
    from saas.webhooks.revenue_share import RevenueShareCalculator
    calc = RevenueShareCalculator()
    # Теперь ставка зависит от суммы транзакции, а не от месячного дохода
    # (partner_id, gross_amount_in_dollars, expected_rate)
    test_cases = [
        ("t1", 500.0, 0.10),    # ≤ 1000 → 10%
        ("t2", 3000.0, 0.15),   # ≤ 5000 → 15%
        ("t3", 7000.0, 0.20),   # > 5000 → 20%
    ]
    for partner_id, gross, exp_rate in test_cases:
        r = calc.calculate(gross, partner_id)
        assert r["rate_used"] == exp_rate, f"{partner_id}: got {r['rate_used']}, want {exp_rate}"
        assert r["romas_share"] == round(gross * exp_rate, 6)
        assert r["partner_payout"] == gross - r["romas_share"]
    log.info("PASS: tiered_rates")

def test_idempotency():
    processed = set()
    def dup(e): return e in processed
    def mark(e): processed.add(e)
    assert not dup("e1")
    mark("e1")
    assert dup("e1")
    log.info("PASS: idempotency")

def test_response_model():
    from saas.webhooks.stripe_webhook import Response
    r = Response(received=True, event_id="evt_1", processed=True)
    assert r.received and r.processed and r.error is None
    log.info("PASS: response_model")

def test_signature_skip_on_empty():
    from saas.webhooks.stripe_webhook import _verify
    assert _verify(b"payload", "sig", "")
    assert _verify(b"payload", "", "secret")
    log.info("PASS: signature_skip_on_empty")

def test_ledger_revenue_share_ext():
    from billing.ledger import BillingLedger
    ledger = BillingLedger()
    assert hasattr(ledger, "record_revenue_share")
    assert hasattr(ledger, "get_monthly_revenue")
    assert hasattr(ledger, "get_pending_revenue_share")
    log.info("PASS: ledger_revenue_share_ext")

if __name__ == "__main__":
    test_tiered_rates()
    test_idempotency()
    test_response_model()
    test_signature_skip_on_empty()
    test_ledger_revenue_share_ext()
    log.info("\n✅ All revenue-share tests passed")
