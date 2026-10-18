"""Invoices and purchase orders, as the reconciliation reads them."""

from dataclasses import dataclass
from decimal import Decimal

from .money import amount


@dataclass(frozen=True)
class Invoice:
    vendor_id: str
    invoice_number: str
    po_number: str
    currency: str
    total: Decimal
    issue_date: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Invoice":
        return cls(
            vendor_id=d["vendor_id"],
            invoice_number=d["invoice_number"],
            po_number=d["po_number"],
            currency=d["currency"].upper(),
            total=amount(d["total"]),
            issue_date=d.get("issue_date", ""),
        )


@dataclass(frozen=True)
class PurchaseOrder:
    po_number: str
    vendor_id: str
    currency: str
    amount: Decimal

    @classmethod
    def from_dict(cls, d: dict) -> "PurchaseOrder":
        return cls(
            po_number=d["po_number"],
            vendor_id=d["vendor_id"],
            currency=d["currency"].upper(),
            amount=amount(d["amount"]),
        )
