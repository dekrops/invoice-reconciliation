"""python -m reconcile INVOICES.json ORDERS.json: prints the reconciliation report as JSON."""

import json
import sys

from .model import Invoice, PurchaseOrder
from .reconcile import reconcile


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python -m reconcile INVOICES.json ORDERS.json", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as f:
        invoices = [Invoice.from_dict(d) for d in json.load(f)]
    with open(argv[1], encoding="utf-8") as f:
        orders = [PurchaseOrder.from_dict(d) for d in json.load(f)]
    json.dump(reconcile(invoices, orders).as_dict(), sys.stdout, indent=2, ensure_ascii=False)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
