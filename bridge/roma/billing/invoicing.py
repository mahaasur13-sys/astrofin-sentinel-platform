"""ROMA Invoicing — Invoice generation, payment tracking."""
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List

log = logging.getLogger(__name__)


@dataclass
class Invoice:
    invoice_id: str
    tenant_id: str
    period_start: float
    period_end: float
    line_items: List[Dict]
    subtotal: float
    tax: float
    total: float
    status: str = "draft"  # draft | issued | paid | overdue

class InvoicingEngine:
    def __init__(self, tax_rate: float = 0.0):
        self.tax_rate = tax_rate
        self.invoices: Dict[str, Invoice] = {}

    def generate(self, tenant_id: str, items: List[Dict], period_start: float,
                period_end: float) -> Invoice:
        subtotal = sum(i["cost"] for i in items)
        tax = subtotal * self.tax_rate
        inv = Invoice(
            invoice_id=f"INV-{uuid.uuid4().hex[:8].upper()}",
            tenant_id=tenant_id, period_start=period_start, period_end=period_end,
            line_items=items, subtotal=subtotal, tax=tax, total=subtotal + tax
        )
        self.invoices[inv.invoice_id] = inv
        return inv

    def issue(self, invoice_id: str) -> Invoice:
        inv = self.invoices[invoice_id]
        inv.status = "issued"
        inv.issued_at = time.time()
        return inv

if __name__ == "__main__":
    ie = InvoicingEngine(tax_rate=0.0)
    inv = ie.generate("tenant-abc",
        [{"desc": "GPU compute (5000s @ $0.00001)", "cost": 0.05},
         {"desc": "Plugin executions (10x)", "cost": 0.01}],
        period_start=time.time() - 86400, period_end=time.time())
    ie.issue(inv.invoice_id)
    log.info(f"Invoice {inv.invoice_id}: ${inv.total:.4f} [{inv.status}]")
