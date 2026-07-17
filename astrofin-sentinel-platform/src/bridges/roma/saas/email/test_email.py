#!/usr/bin/env python3
"""Tests for saas.email.service."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from saas.email.service import EmailService, EmailProvider


def _brand():
    return {"app_name": "VEGA Cloud", "primary_color": "#E53935"}


def test_console_welcome():
    svc = EmailService(provider=EmailProvider.CONSOLE)
    r = svc.send_welcome("ops@vega.kz", "VEGA Cloud", "vk_live_abc123", _brand())
    assert r, f"send_welcome returned {r!r}"
    print("PASS: console_welcome")


def test_console_all_types():
    svc = EmailService(provider=EmailProvider.CONSOLE)
    assert svc.send_usage_alert(
        "ops@vega.kz", "VEGA Cloud", 75.0, 15.0, 5.0, _brand()
    ), "usage_alert"
    assert svc.send_invoice(
        "ops@vega.kz", "INV-001", "April 2026", 20.0, 10.00, 15.0, 1.50, 8.50, _brand()
    ), "invoice"
    assert svc.send_low_balance(
        "ops@vega.kz", "VEGA Cloud", 2.50, _brand()
    ), "low_balance"
    print("PASS: all_email_types")


def test_no_cross_contamination():
    svc1 = EmailService(provider=EmailProvider.CONSOLE)
    svc2 = EmailService(provider=EmailProvider.CONSOLE)
    b1 = {"app_name": "Alpha", "primary_color": "#111111"}
    b2 = {"app_name": "Beta", "primary_color": "#222222"}
    html1 = svc1._render(
        "welcome",
        tenant_name="Alpha",
        api_key="key1",
        brand=b1,
        dashboard_url="https://a.com",
    )
    html2 = svc2._render(
        "welcome",
        tenant_name="Beta",
        api_key="key2",
        brand=b2,
        dashboard_url="https://b.com",
    )
    assert "Alpha" in html1 and "Beta" not in html1, "cross-contamination: Alpha/Beta"
    assert "key1" in html1 and "key2" not in html1, "cross-contamination: key1/key2"
    assert "#111111" in html1 and "#222222" not in html1, "cross-contamination: colors"
    print("PASS: no_cross_contamination")


def test_templates_render():
    svc = EmailService(provider=EmailProvider.CONSOLE)
    brand = {"app_name": "Test", "primary_color": "#000000"}
    html = svc._render(
        "welcome",
        tenant_name="Test",
        api_key="key123",
        brand=brand,
        dashboard_url="https://x.ai",
    )
    assert "Test" in html
    assert "key123" in html
    assert "#000000" in html
    print("PASS: templates_render")


if __name__ == "__main__":
    test_console_welcome()
    test_console_all_types()
    test_no_cross_contamination()
    test_templates_render()
    print("\n=== All email tests PASSED ===")
