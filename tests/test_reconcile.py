import unittest
from decimal import Decimal

from reconcile import Invoice, PurchaseOrder, reconcile


def inv(number, po="PO-1", total="100.00", vendor="V1", currency="EUR"):
    return Invoice.from_dict({"vendor_id": vendor, "invoice_number": number, "po_number": po,
                              "currency": currency, "total": total})


ORDERS = [PurchaseOrder.from_dict({"po_number": "PO-1", "vendor_id": "V1", "currency": "EUR",
                                   "amount": "100.00"})]


class Reconcile(unittest.TestCase):
    def status(self, invoices, orders=ORDERS):
        return [line.status for line in reconcile(invoices, orders).lines]

    def test_a_matching_invoice_closes_its_order(self):
        report = reconcile([inv("A-1")], ORDERS)
        self.assertEqual(self.status([inv("A-1")]), ["matched"])
        self.assertEqual(report.open_amounts["PO-1"], Decimal("0.00"))

    def test_amount_mismatch_states_the_difference(self):
        line = reconcile([inv("A-1", total="100.10")], ORDERS).lines[0]
        self.assertEqual((line.status, line.difference), ("amount_mismatch", Decimal("0.10")))

    def test_unknown_po_vendor_and_currency(self):
        self.assertEqual(self.status([inv("A-1", po="PO-9")]), ["unknown_po"])
        self.assertEqual(self.status([inv("A-1", vendor="V2")]), ["vendor_mismatch"])
        self.assertEqual(self.status([inv("A-1", currency="USD")]), ["currency_mismatch"])

    def test_report_format(self):
        d = reconcile([inv("A-1")], ORDERS).as_dict()
        self.assertEqual(d["lines"][0], {"invoice_number": "A-1", "vendor_id": "V1",
                                         "po_number": "PO-1", "status": "matched",
                                         "difference": "0.00"})
        self.assertEqual(d["open_amounts"], {"PO-1": "0.00"})


if __name__ == "__main__":
    unittest.main()
