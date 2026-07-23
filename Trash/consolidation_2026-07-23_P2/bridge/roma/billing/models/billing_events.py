#!/usr/bin/env python3
"""ROMA Billing Events — Core billing event definitions for GPU usage."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class BillingEventType(Enum):
    JOB_SUBMITTED = "job.submitted"
    JOB_STARTED = "job.started"
    GPU_ALLOCATED = "gpu.allocated"
    GPU_RELEASED = "gpu.released"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    PLUGIN_EXECUTED = "plugin.executed"
    QUOTA_EXCEEDED = "quota.exceeded"
    INVOICE_FINALIZED = "invoice.finalized"
    PAYMENT_SUCCEEDED = "payment.succeeded"
    PAYMENT_FAILED = "payment.failed"


@dataclass
class BillingEvent:
    event_id: str
    tenant_id: str
    event_type: BillingEventType
    timestamp: float
    job_id: str | None = None
    plugin_id: str | None = None
    gpu_seconds: float = 0.0
    cpu_seconds: float = 0.0
    memory_gb_seconds: float = 0.0
    gpu_node: str | None = None
    plan: str = "FREE"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_stripe_record(self) -> dict:
        return {
            "name": self.event_type.value,
            "value": self.gpu_seconds,
            "timestamp": self.timestamp,
            "tenant_id": self.tenant_id,
        }


class BillingEventStore:
    def __init__(self):
        self._events: list[BillingEvent] = []
        self._by_tenant: dict[str, list[BillingEvent]] = {}

    def append(self, event: BillingEvent) -> None:
        self._events.append(event)
        if event.tenant_id not in self._by_tenant:
            self._by_tenant[event.tenant_id] = []
        self._by_tenant[event.tenant_id].append(event)

    def get_for_tenant(self, tenant_id: str) -> list[BillingEvent]:
        return self._by_tenant.get(tenant_id, [])

    def get_in_range(self, tenant_id: str, start: float, end: float) -> list[BillingEvent]:
        return [e for e in self.get_for_tenant(tenant_id) if start <= e.timestamp <= end]

    def last_event(self, tenant_id: str) -> BillingEvent | None:
        tenant_events = self.get_for_tenant(tenant_id)
        return tenant_events[-1] if tenant_events else None


@dataclass
class Invoice:
    invoice_id: str
    tenant_id: str
    period_start: float
    period_end: float
    gpu_seconds: float
    cpu_seconds: float
    memory_gb_seconds: float
    line_items: list[dict]
    subtotal: float
    discount: float
    tax: float
    total: float
    currency: str = "USD"
    status: str = "DRAFT"
    stripe_invoice_id: str | None = None
    created_at: float = field(default_factory=lambda: __import__("time").time())
    finalized_at: float | None = None
    paid_at: float | None = None
    stripe_webhook_received: bool = False

    def to_dict(self) -> dict:
        return {
            "invoice_id": self.invoice_id,
            "tenant_id": self.tenant_id,
            "status": self.status,
            "total": self.total,
            "currency": self.currency,
            "period": f"{self.period_start}→{self.period_end}",
        }
