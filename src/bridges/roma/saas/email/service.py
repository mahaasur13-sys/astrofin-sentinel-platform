"""saas.email.service — EmailService with template rendering + real sending."""

from __future__ import annotations

import smtplib
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any

try:
    import jinja2

    _HAS_JINJA2 = True
except ImportError:
    _HAS_JINJA2 = False


class EmailProvider(str, Enum):
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    RESEND = "resend"
    CONSOLE = "console"


class EmailConfig:
    provider: EmailProvider = EmailProvider.CONSOLE
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    from_email: str = "noreply@roma.ai"
    from_name: str = "ROMA Platform"
    sendgrid_api_key: str = ""
    resend_api_key: str = ""
    resend_domain: str = ""

    def __init__(
        self,
        provider: EmailProvider = EmailProvider.CONSOLE,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",
        smtp_password: str = "",
        from_email: str = "noreply@roma.ai",
        from_name: str = "ROMA Platform",
        sendgrid_api_key: str = "",
        resend_api_key: str = "",
        resend_domain: str = "",
    ) -> None:
        self.provider = provider
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email
        self.from_name = from_name
        self.sendgrid_api_key = sendgrid_api_key
        self.resend_api_key = resend_api_key
        self.resend_domain = resend_domain


TEMPLATES = {
    "welcome": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Welcome</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
<div style="background:{{ brand.get('primary_color','#6366f1') }};color:white;padding:24px;text-align:center;border-radius:8px 8px 0 0">
  <h1>{{ brand.get('app_name','ROMA') }}</h1>
</div>
<div style="background:#f8fafc;padding:32px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0">
  <h2 style="color:#1e293b;margin-top:0">Welcome, {{ tenant_name }}!</h2>
  <p style="color:#475569;line-height:1.6">Your white-label GPU cloud platform is ready.</p>
  <p style="color:#475569;line-height:1.6">API Key: <code style="background:#e2e8f0;padding:2px 8px;border-radius:4px;font-size:13px">{{ api_key }}</code></p>
  <a href="{{ dashboard_url }}" style="display:inline-block;background:{{ brand.get('primary_color','#6366f1') }};color:white;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;margin-top:16px">Open Dashboard</a>
</div>
<div style="text-align:center;color:#94a3b8;font-size:12px;margin-top:24px">Powered by <a href="https://roma.ai" style="color:#94a3b8">ROMA</a></div>
</body></html>""",
    "usage_alert": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Usage Alert</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
<div style="background:#fef3c7;border:1px solid #f59e0b;border-radius:8px;padding:20px;margin-bottom:24px">
  <strong style="color:#92400e">⚠️ {{ brand.get('app_name','ROMA') }} — Usage Alert</strong>
</div>
<div style="background:#f8fafc;padding:32px;border-radius:8px;border:1px solid #e2e8f0">
  <p>Tenant <strong>{{ tenant_name }}</strong> has used <strong>{{ percentage }}%</strong> of their monthly quota.</p>
  <div style="background:#e2e8f0;border-radius:4px;height:20px;width:100%;margin:16px 0">
    <div style="background:{{ brand.get('primary_color','#6366f1') }};height:20px;width:{{ percentage }}%;border-radius:4px"></div>
  </div>
  <p style="color:#475569;font-size:14px">Used: {{ used_gpus }} GPU-hours · Remaining: {{ remaining_gpus }} GPU-hours</p>
</div></body></html>""",
    "invoice": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Invoice {{ invoice_id }}</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
<div style="background:{{ brand.get('primary_color','#6366f1') }};color:white;padding:24px;text-align:center;border-radius:8px 8px 0 0">
  <h1>Invoice {{ invoice_id }}</h1>
</div>
<div style="background:#f8fafc;padding:32px;border-radius:0 0 8px 8px;border:1px solid #e2e8f0">
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:8px;color:#475569">Period</td><td style="padding:8px;text-align:right">{{ period }}</td></tr>
    <tr><td style="padding:8px;color:#475569">GPU Hours</td><td style="padding:8px;text-align:right">{{ gpu_hours }}</td></tr>
    <tr style="border-top:2px solid #e2e8f0"><td style="padding:12px;font-weight:bold">Subtotal</td><td style="padding:12px;text-align:right;font-weight:bold">${{ subtotal }}</td></tr>
    <tr><td style="padding:8px;color:#475569">ROMA Fee ({{ roma_fee }}%)</td><td style="padding:8px;text-align:right;color:#dc2626">-${{ roma_fee_amount }}</td></tr>
    <tr style="border-top:2px solid #6366f1">
      <td style="padding:12px;font-weight:bold;font-size:18px">Your Revenue</td>
      <td style="padding:12px;text-align:right;font-weight:bold;font-size:18px;color:#059669">${{ revenue }}</td>
    </tr>
  </table>
</div></body></html>""",
    "low_balance": """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Low Balance</title></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px">
<div style="background:#fee2e2;border:1px solid #ef4444;border-radius:8px;padding:20px;margin-bottom:24px">
  <strong style="color:#991b1b">🔴 {{ brand.get('app_name','ROMA') }} — Low Balance</strong>
</div>
<div style="background:#f8fafc;padding:32px;border-radius:8px;border:1px solid #e2e8f0">
  <p>Tenant <strong>{{ tenant_name }}</strong> has a balance of <strong style="color:#dc2626">${{ balance }}</strong>.</p>
  <p style="color:#475569">Top up at {{ dashboard_url }}</p>
</div></body></html>""",
}


class EmailService:
    def __init__(
        self,
        provider=EmailProvider.CONSOLE,
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        smtp_user="",
        smtp_password="",
        from_email="noreply@roma.ai",
        from_name="ROMA Platform",
        sendgrid_api_key="",
        resend_api_key="",
        resend_domain="",
    ):
        self.cfg = EmailConfig(
            provider=provider,
            smtp_host=smtp_host,
            smtp_port=smtp_port,
            smtp_user=smtp_user,
            smtp_password=smtp_password,
            from_email=from_email,
            from_name=from_name,
            sendgrid_api_key=sendgrid_api_key,
            resend_api_key=resend_api_key,
            resend_domain=resend_domain,
        )
        if _HAS_JINJA2:
            self._env = jinja2.Environment()
            self._templates = {name: self._env.from_string(src) for name, src in TEMPLATES.items()}
        else:
            self._env = None
            self._templates = {}

    def _render(self, template_name: str, **kwargs) -> str:
        if template_name not in self._templates:
            raise ValueError(f"Unknown template: {template_name}")
        return str(self._templates[template_name].render(**kwargs))

    def _build_smtp_message(self, to_email: str, subject: str, html_body: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.cfg.from_name} <{self.cfg.from_email}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html"))
        return msg

    def _send_smtp(self, to_email: str, msg: MIMEMultipart) -> bool:
        try:
            with smtplib.SMTP(self.cfg.smtp_host, self.cfg.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.cfg.smtp_user, self.cfg.smtp_password)
                server.sendmail(self.cfg.from_email, [to_email], msg.as_string())
            return True
        except Exception as e:  # noqa: BLE001
            print(f"[EmailService] SMTP error: {e}", file=sys.stderr)
            return False

    def _send_sendgrid(self, to_email: str, subject: str, html_body: str) -> bool:
        try:
            import requests

            resp = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={"Authorization": f"Bearer {self.cfg.sendgrid_api_key}", "Content-Type": "application/json"},
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": self.cfg.from_email, "name": self.cfg.from_name},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_body}],
                },
                timeout=10,
            )
            return resp.status_code in (200, 202)
        except Exception as e:  # noqa: BLE001
            print(f"[EmailService] SendGrid error: {e}", file=sys.stderr)
            return False

    def _send_resend(self, to_email: str, subject: str, html_body: str) -> bool:
        try:
            import requests

            resp = requests.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {self.cfg.resend_api_key}", "Content-Type": "application/json"},
                json={
                    "from": f"{self.cfg.from_name} <no-reply@{self.cfg.resend_domain}>",
                    "to": [to_email],
                    "subject": subject,
                    "html": html_body,
                },
                timeout=10,
            )
            return resp.status_code in (200, 201)
        except Exception as e:  # noqa: BLE001
            print(f"[EmailService] Resend error: {e}", file=sys.stderr)
            return False

    def send(self, to_email: str, subject: str, html_body: str) -> bool:
        if self.cfg.provider == EmailProvider.CONSOLE:
            print(
                f"\n{'=' * 60}\n[EmailService] CONSOLE — would send:\n  To: {to_email}\n  Subject: {subject}\n  Body: {html_body[:200]}...\n{'=' * 60}\n"
            )
            return True
        if self.cfg.provider == EmailProvider.SMTP:
            return self._send_smtp(to_email, self._build_smtp_message(to_email, subject, html_body))
        if self.cfg.provider == EmailProvider.SENDGRID:
            return self._send_sendgrid(to_email, subject, html_body)
        if self.cfg.provider == EmailProvider.RESEND:
            return self._send_resend(to_email, subject, html_body)
        return False

    def send_welcome(
        self,
        to_email: str,
        tenant_name: str,
        api_key: str,
        brand: dict[str, Any],
        dashboard_url: str = "https://dashboard.roma.ai",
    ) -> bool:
        html = self._render(
            "welcome", tenant_name=tenant_name, api_key=api_key, brand=brand, dashboard_url=dashboard_url
        )
        return self.send(to_email, f"Welcome to {brand.get('app_name', 'ROMA')}!", html)

    def send_usage_alert(
        self,
        to_email: str,
        tenant_name: str,
        percentage: float,
        used_gpus: float,
        remaining_gpus: float,
        brand: dict[str, Any],
    ) -> bool:
        html = self._render(
            "usage_alert",
            tenant_name=tenant_name,
            percentage=percentage,
            used_gpus=used_gpus,
            remaining_gpus=remaining_gpus,
            brand=brand,
        )
        return self.send(to_email, f"⚠️ Usage Alert — {percentage}% Quota Used", html)

    def send_invoice(
        self,
        to_email: str,
        invoice_id: str,
        period: str,
        gpu_hours: float,
        subtotal: float,
        roma_fee: float,
        roma_fee_amount: float,
        revenue: float,
        brand: dict[str, Any],
    ) -> bool:
        html = self._render(
            "invoice",
            invoice_id=invoice_id,
            period=period,
            gpu_hours=gpu_hours,
            subtotal=subtotal,
            roma_fee=roma_fee,
            roma_fee_amount=roma_fee_amount,
            revenue=revenue,
            brand=brand,
        )
        return self.send(to_email, f"Invoice {invoice_id} — Revenue Payment", html)

    def send_low_balance(
        self,
        to_email: str,
        tenant_name: str,
        balance: float,
        brand: dict[str, Any],
        dashboard_url: str = "https://dashboard.roma.ai",
    ) -> bool:
        html = self._render(
            "low_balance", tenant_name=tenant_name, balance=balance, brand=brand, dashboard_url=dashboard_url
        )
        return self.send(to_email, f"🔴 Low Balance — {brand.get('app_name', 'ROMA')}", html)


if __name__ == "__main__":
    svc = EmailService()
    brand = {"app_name": "VEGA Cloud", "primary_color": "#E53935"}
    r = svc.send_welcome("ops@vega.kz", "VEGA Cloud", "vk_live_abc123xyz", brand)
    print(f"Welcome email: {'OK' if r else 'FAILED'}")
