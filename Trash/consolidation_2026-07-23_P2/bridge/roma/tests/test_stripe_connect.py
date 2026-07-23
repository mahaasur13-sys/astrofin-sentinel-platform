#!/usr/bin/env python
"""Unit tests for Stripe Connect + Revenue-Share boundary cases"""
import sys

sys.path.insert(0, "/home/workspace/roma-execution-bridge")

from saas.webhooks.revenue_share import RevenueShareCalculator
from saas.webhooks.stripe_connect import calculate_application_fee

calc = RevenueShareCalculator()


def test_fee_boundaries():
    print("\n=== Fee boundary tests ===")
    # (gross, expected_rate) — tiers: $0-$1000→10%, $1001-$5000→15%, $5001+→20%
    cases = [
        (999.00, 0.10),  # below tier 2 threshold
        (1000.00, 0.10),  # top of tier 1 (boundary)
        (1001.00, 0.15),  # bottom of tier 2
        (5000.00, 0.15),  # top of tier 2 (boundary)
        (5001.00, 0.20),  # bottom of tier 3
        (0.01, 0.10),  # minimum positive
    ]
    all_passed = True
    for gross, expected_rate in cases:
        result = calc.calculate(gross, "partner_test")
        actual_rate = result["rate_used"]
        passed = actual_rate == expected_rate
        print(
            f"  [{'PASS' if passed else 'FAIL'}] ${gross:.2f} → {actual_rate*100:.0f}% (expected {expected_rate*100:.0f}%)"
        )
        if not passed:
            all_passed = False
    return all_passed


def test_negative_amounts():
    print("\n=== Negative amount rejection ===")
    try:
        calc.calculate(-100.00, "partner_test")
        print("  [FAIL] Negative amount was NOT rejected")
        return False
    except ValueError:
        print("  [PASS] Negative amount correctly rejected")
        return True


def test_zero_amount():
    print("\n=== Zero amount ===")
    result = calc.calculate(0.00, "partner_test")
    if result["romas_share"] == 0 and result["partner_payout"] == 0:
        print("  [PASS] Zero amount → zero payout (both sides)")
        return True
    print("  [FAIL] Zero amount handling incorrect")
    return False


def test_application_fee():
    print("\n=== Stripe Connect application fee ===")
    cases = [
        (50000, 15.0, 7500),
        (100000, 15.0, 15000),
        (100000, 10.0, 10000),
    ]
    all_passed = True
    for cents, pct, expected_fee in cases:
        result = calculate_application_fee(cents, pct)
        passed = result["application_fee_cents"] == expected_fee
        print(f"  [{'PASS' if passed else 'FAIL'}] {cents/100:.2f} @ {pct}% → fee={expected_fee/100:.2f}")
        if not passed:
            all_passed = False
    return all_passed


if __name__ == "__main__":
    results = [
        test_fee_boundaries(),
        test_negative_amounts(),
        test_zero_amount(),
        test_application_fee(),
    ]
    passed = sum(results)
    total = len(results)
    print(f"\n=== RESULTS: {passed}/{total} test groups PASSED ===")
    sys.exit(0 if all(results) else 1)
