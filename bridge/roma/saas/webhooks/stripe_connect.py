#!/usr/bin/env python
"""Stripe Connect integration — white-label revenue-share"""
import json
import logging
import time

log = logging.getLogger(__name__)


CONFIG = {
    "mode": "stripe_connect_standard",
    "application_fee_percent": 15,
    "partner_payout_schedule": "monthly",
    "charge_type": "destination_charges",
    "webhook_events": [
        "invoice.paid",
        "invoice.payment_succeeded",
        "charge.succeeded",
        "account.updated",
        "account.charges_enabled",
    ],
}

def calculate_application_fee(amount_cents: int, fee_percent: float = 15.0) -> dict:
    gross = amount_cents / 100
    application_fee = int(amount_cents * fee_percent / 100)
    partner_payout = amount_cents - application_fee
    return {
        "gross_amount": gross,
        "application_fee_cents": application_fee,
        "partner_payout_cents": partner_payout,
        "fee_percent": fee_percent,
    }

class AsyncWebhookQueue:
    def __init__(self, queue_file="/tmp/roma_webhook_queue.json"):
        self._queue = []
        self._processed = set()
        self._queue_file = queue_file
        self._load()

    def _load(self):
        try:
            with open(self._queue_file) as f:
                self._queue = json.load(f)
        except Exception:
                pass

    def _save(self):
        with open(self._queue_file, 'w') as f:
            json.dump(self._queue, f)

    def enqueue(self, event_id: str, payload: dict):
        if event_id in self._processed:
            return "already_queued"
        self._queue.append({"event_id": event_id, "payload": payload, "enqueued_at": time.time()})
        self._save()
        return "queued"

    def process_all(self):
        processed = []
        for item in self._queue[:]:
            if item["event_id"] not in self._processed:
                self._processed.add(item["event_id"])
                processed.append(item["event_id"])
                self._queue.remove(item)
        self._save()
        return processed

if __name__ == "__main__":
    log.info("Stripe Connect: Ready for Standard/Custom accounts")
    log.info(f"Config: {CONFIG}")
