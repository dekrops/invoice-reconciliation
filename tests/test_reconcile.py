import unittest
from decimal import Decimal

from reconcile import Invoice, PurchaseOrder, reconcile
from reconcile.reconcile import normalize_number


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

    def test_resent_copies_are_duplicates_however_they_are_written(self):
        first = inv("INV-2026-0042", total="100.10")
        copies = [inv("inv 2026 42"), inv("INV\u20132026\u20130042"), inv("\uff29\uff2e\uff36-2026-0042")]
        lines = reconcile([first] + copies, ORDERS).lines
        self.assertEqual([line.status for line in lines],
                         ["amount_mismatch", "duplicate", "duplicate", "duplicate"])
        self.assertEqual([line.duplicate_of for line in lines[1:]], ["INV-2026-0042"] * 3)
        self.assertEqual(lines[1].as_dict()["difference"], "0.00")
        self.assertEqual(lines[1].as_dict()["duplicate_of"], "INV-2026-0042")

    def test_a_duplicate_does_not_close_or_change_the_order(self):
        report = reconcile([inv("A-1", total="99.00"), inv("A-1")], ORDERS)
        self.assertEqual([line.status for line in report.lines], ["amount_mismatch", "duplicate"])
        self.assertEqual(report.open_amounts["PO-1"], Decimal("100.00"))

    def test_the_first_copy_of_a_duplicate_pair_is_reconciled(self):
        self.assertEqual(self.status([inv("A-1"), inv("A-1")]), ["matched", "duplicate"])

    def test_different_vendors_are_never_duplicates(self):
        orders = ORDERS + [PurchaseOrder.from_dict({"po_number": "PO-2", "vendor_id": "V2",
                                                    "currency": "EUR", "amount": "100.00"})]
        self.assertEqual(self.status([inv("A-1"), inv("A-1", po="PO-2", vendor="V2")], orders),
                         ["matched", "matched"])

    def test_different_numbers_are_not_duplicates(self):
        self.assertEqual(self.status([inv("INV-2026-0042"), inv("INV-2026-0043")]),
                         ["matched", "amount_mismatch"])

    def test_normalization(self):
        same = ["INV-2026-0042", "inv 2026 42", "INV\u20132026\u20130042", "INV/2026.42", "INV_2026_0042"]
        self.assertEqual({normalize_number(n) for n in same}, {"inv202642"})
        self.assertNotEqual(normalize_number("A-10"), normalize_number("A-1"))


if __name__ == "__main__":
    unittest.main()
