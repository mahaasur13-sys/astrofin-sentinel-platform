#!/usr/bin/env python3
"""ROMA Usage Aggregator — GPU-second aggregation from billing events."""
from billing.models.billing_events import BillingEvent, BillingEventStore, BillingEventType
import time

class UsageAggregator:
    def __init__(self, event_store: BillingEventStore):
        self._store = event_store

    def aggregate_gpu_seconds(self, tenant_id: str, start: float, end: float) -> float:
        events = self._store.get_in_range(tenant_id, start, end)
        total_gpu_sec = 0.0
        for e in events:
            total_gpu_sec += e.gpu_seconds
        return total_gpu_sec

    def aggregate_by_type(self, tenant_id: str, start: float, end: float) -> dict:
        events = self._store.get_in_range(tenant_id, start, end)
        by_type = {}
        for e in events:
            key = e.event_type.value
            by_type[key] = by_type.get(key, 0.0) + e.gpu_seconds
        return by_type

    def monthly_summary(self, tenant_id: str, month_ts: float) -> dict:
        # Approximate month from timestamp
        import datetime
        dt = datetime.datetime.fromtimestamp(month_ts)
        start = datetime.datetime(dt.year, dt.month, 1).timestamp()
        if dt.month == 12:
            end = datetime.datetime(dt.year + 1, 1, 1).timestamp()
        else:
            end = datetime.datetime(dt.year, dt.month + 1, 1).timestamp()
        gpu = self.aggregate_gpu_seconds(tenant_id, start, end)
        by_type = self.aggregate_by_type(tenant_id, start, end)
        return {"period_start": start, "period_end": end, "gpu_seconds": gpu, "by_type": by_type}

def simulate_usage(aggregator: UsageAggregator) -> None:
    store = aggregator._store
    now = time.time()
    for i in range(1, 11):
        store.append(BillingEvent(
            event_id=f"evt-{i:03d}", tenant_id="tenant-abc",
            event_type=BillingEventType.JOB_STARTED if i % 2 == 0 else BillingEventType.GPU_ALLOCATED,
            timestamp=now - (10 - i) * 3600,
            gpu_seconds=3600.0 + i * 120,  # 1h + 2min increments
            gpu_node=f"gpu-node-{i % 3}"
        ))
    total = aggregator.aggregate_gpu_seconds("tenant-abc", now - 10 * 3600, now)
    summary = aggregator.monthly_summary("tenant-abc", now)
    print(f"Aggregated GPU-seconds (10h window): {total:.1f}s = {total/3600:.2f}h")
    print(f"Monthly summary: {summary['gpu_seconds']:.1f}s = {summary['gpu_seconds']/3600:.2f}h")
