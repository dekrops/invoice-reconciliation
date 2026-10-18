"""Matching invoices against purchase orders.

Each invoice is matched to the purchase order it names. The result says whether vendor, currency
and amount agree; the amount still open on each order is what was ordered minus what matched
invoices billed. See docs/API.md for the report format.
"""

from dataclasses import dataclass, field
from decimal import Decimal

from .model import Invoice, PurchaseOrder, normalize_invoice_number
from .money import text


@dataclass
class Line:
    invoice_number: str
    vendor_id: str
    po_number: str
    status: str
    difference: Decimal = Decimal("0.00")
    duplicate_of: str | None = None

    def as_dict(self) -> dict:
        d = {
            "invoice_number": self.invoice_number,
            "vendor_id": self.vendor_id,
            "po_number": self.po_number,
            "status": self.status,
            "difference": text(self.difference),
        }
        if self.duplicate_of is not None:
            d["duplicate_of"] = self.duplicate_of
        return d


@dataclass
class Report:
    lines: list[Line] = field(default_factory=list)
    open_amounts: dict[str, Decimal] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "lines": [line.as_dict() for line in self.lines],
            "open_amounts": {po: text(a) for po, a in sorted(self.open_amounts.items())},
        }


def reconcile(invoices: list[Invoice], orders: list[PurchaseOrder]) -> Report:
    """Reconcile `invoices` in the order given against `orders`.

    Statuses: `matched`, `unknown_po`, `vendor_mismatch`, `currency_mismatch`,
    `amount_mismatch` (with `difference` = invoice total minus the amount still open) and
    `duplicate`: an invoice of the same vendor whose number equals an earlier one's after
    `normalize_invoice_number`. A duplicate is not reconciled again; its line names the first
    invoice's number as written in `duplicate_of`.
    """
    by_number = {o.po_number: o for o in orders}
    report = Report(open_amounts={o.po_number: o.amount for o in orders})
    first_seen: dict[tuple[str, str], str] = {}
    for inv in invoices:
        key = (inv.vendor_id, normalize_invoice_number(inv.invoice_number))
        if key in first_seen:
            report.lines.append(Line(inv.invoice_number, inv.vendor_id, inv.po_number,
                                     "duplicate", Decimal("0.00"), first_seen[key]))
            continue
        first_seen[key] = inv.invoice_number
        order = by_number.get(inv.po_number)
        if order is None:
            status, diff = "unknown_po", Decimal("0.00")
        elif order.vendor_id != inv.vendor_id:
            status, diff = "vendor_mismatch", Decimal("0.00")
        elif order.currency != inv.currency:
            status, diff = "currency_mismatch", Decimal("0.00")
        else:
            remaining = report.open_amounts[order.po_number]
            diff = inv.total - remaining
            status = "matched" if diff == 0 else "amount_mismatch"
            if status == "matched":
                report.open_amounts[order.po_number] = Decimal("0.00")
        report.lines.append(Line(inv.invoice_number, inv.vendor_id, inv.po_number, status, diff))
    return report
