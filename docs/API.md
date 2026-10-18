# API

## `reconcile(invoices, orders) -> Report`

Reconciles `invoices`, **in the order given**, against `orders`.

- `Invoice(vendor_id, invoice_number, po_number, currency, total, issue_date="")`. Build one with `Invoice.from_dict(d)` from the JSON shape in `fixtures/invoices.json`.
- `PurchaseOrder(po_number, vendor_id, currency, amount)`. Build one with `PurchaseOrder.from_dict(d)`.
- Amounts are `Decimal` with exactly two fractional digits (`reconcile.amount`), rounded half-even. Floats are refused.
- Currencies are compared upper-cased.

Each invoice gets one report line, in input order:

| `status` | Meaning | `difference` |
|---|---|---|
| `matched` | Vendor, currency and amount agree with the order; the order's open amount becomes `0.00` | `0.00` |
| `amount_mismatch` | The total differs from the amount still open on the order | total − open amount |
| `unknown_po` | No order has that number | `0.00` |
| `vendor_mismatch` | The order belongs to another vendor | `0.00` |
| `currency_mismatch` | The order is in another currency | `0.00` |

## Report (`Report.as_dict()`, and the CLI's output)

```json
{
  "lines": [
    {"invoice_number": "INV-2026-0042", "vendor_id": "DE811234567", "po_number": "PO-2026-0101",
     "status": "matched", "difference": "0.00"}
  ],
  "open_amounts": {"PO-2026-0101": "0.00"}
}
```

Amounts in the report are strings with two fractional digits. `open_amounts` is sorted by order number.

## CLI

`python -m reconcile INVOICES.json ORDERS.json` prints the report. Exit code 2 means wrong usage.
