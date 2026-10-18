"""Invoices and purchase orders, as the reconciliation reads them."""

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

from .money import amount

_DIGITS = re.compile(r"\d+")
_ASCII_DIGITS = frozenset("0123456789")
_SEPARATORS = frozenset("-/._\u2212")  # plus whitespace and every Unicode dash (category Pd)


def _is_separator(c: str) -> bool:
    return c.isspace() or c in _SEPARATORS or unicodedata.category(c) == "Pd"


def _strip_zeros(m: re.Match) -> str:
    digits = "".join(str(unicodedata.decimal(c)) for c in m.group())
    return digits.lstrip("0") or "0"


def normalize_invoice_number(number: str) -> str:
    """The form in which two invoice numbers are compared to find duplicates.

    Unicode NFKC, case-folded; whitespace, `-` `/` `.` `_` and every Unicode dash are not
    significant; leading zeros of each number inside it are not significant. A separator
    between two numbers still ends the first number, so `INV-2026-0042`, `inv 2026 42` and
    `ＩＮＶ–2026–0042` are the same invoice, but `INV-20-2642` is not.

    >>> normalize_invoice_number("INV–2026–0042")
    'inv2026 42'
    """
    s = unicodedata.normalize("NFKC", unicodedata.normalize("NFKC", number).casefold())
    segments, current = [], []
    for c in s:
        if _is_separator(c):
            if current:
                segments.append("".join(current))
                current = []
        else:
            current.append(c)
    if current:
        segments.append("".join(current))
    out = ""
    for seg in (_DIGITS.sub(_strip_zeros, seg) for seg in segments):
        # Only a boundary between two numbers is kept; elsewhere separators vanish.
        if out and out[-1] in _ASCII_DIGITS and seg[0] in _ASCII_DIGITS:
            out += " "
        out += seg
    return out


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
