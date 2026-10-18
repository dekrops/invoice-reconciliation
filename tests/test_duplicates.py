"""Duplicate invoices: same vendor, same invoice number after normalization (issue #1)."""

import json
import pathlib
import unittest
from decimal import Decimal

from reconcile import Invoice, PurchaseOrder, reconcile
from reconcile.model import normalize_invoice_number

ROOT = pathlib.Path(__file__).resolve().parents[1]


def inv(number, po="PO-1", total="100.00", vendor="V1", currency="EUR"):
    return Invoice.from_dict({"vendor_id": vendor, "invoice_number": number, "po_number": po,
                              "currency": currency, "total": total})


def order(po="PO-1", vendor="V1", amount="100.00", currency="EUR"):
    return PurchaseOrder.from_dict({"po_number": po, "vendor_id": vendor, "currency": currency,
                                    "amount": amount})


ORDERS = [order()]


class Normalization(unittest.TestCase):
    def same(self, a, b):
        self.assertEqual(normalize_invoice_number(a), normalize_invoice_number(b), (a, b))

    def different(self, a, b):
        self.assertNotEqual(normalize_invoice_number(a), normalize_invoice_number(b), (a, b))

    def test_issue_examples_are_one_invoice(self):
        for other in ["inv 2026 42", "INV–2026–0042", "ＩＮＶ-2026-0042",
                      "INV-2026-42"]:
            self.same("INV-2026-0042", other)

    def test_nfkc_and_case(self):
        self.same("ｉｎｖ－２０２６－００４２",
                  "INV-2026-42")  # full-width letters, digits and hyphen
        self.same("Inv-2026-0042", "iNV-2026-0042")
        self.same("RECHNUNG-STRASSE-1", "rechnung-straße-1")  # case folding

    def test_separators_and_whitespace(self):
        for sep in ["-", "/", ".", "_", " ", "\t", "  ", "　",
                    "‐", "‑", "‒", "–", "—", "―", "−"]:
            self.same("INV-2026-0042", f"INV{sep}2026{sep}0042")
        self.same("INV-2026-0042", " INV - 2026 - 0042 ")
        self.same("INV-2026-0042", "INV2026-42")
        self.same("F2026/311", "F-2026-311")
        self.same("AB-CD-1", "ABCD1")

    def test_leading_zeros(self):
        self.same("INV-2026-0042", "INV-02026-00042")
        self.same("R-0", "R-000")
        self.same("A7", "A007")
        self.different("A7", "A70")
        self.different("A-0", "A")

    def test_numbers_are_not_merged_across_separators(self):
        self.different("INV-2026-42", "INV-20-2642")
        self.different("INV-2026-0043", "INV-2026-0042")

    def test_letters_stay_significant(self):
        self.different("INV-2026-0042", "CRN-2026-0042")
        self.different("INV-2026-0042", "INV-2026-0042A")


class Duplicates(unittest.TestCase):
    def test_second_copy_is_a_duplicate_and_leaves_open_amounts(self):
        report = reconcile([inv("INV-2026-0042"), inv("inv 2026 42")], ORDERS)
        self.assertEqual([l.status for l in report.lines], ["matched", "duplicate"])
        self.assertEqual(report.open_amounts, {"PO-1": Decimal("0.00")})
        self.assertEqual(report.as_dict()["lines"][1], {
            "invoice_number": "inv 2026 42", "vendor_id": "V1", "po_number": "PO-1",
            "status": "duplicate", "difference": "0.00", "duplicate_of": "INV-2026-0042"})

    def test_duplicate_of_a_mismatch_does_not_close_the_order(self):
        report = reconcile([inv("INV-2026-0042", total="90.00"),
                            inv("INV–2026–0042", total="100.00")], ORDERS)
        self.assertEqual([l.status for l in report.lines], ["amount_mismatch", "duplicate"])
        self.assertEqual(report.lines[1].difference, Decimal("0.00"))
        self.assertIsInstance(report.lines[1].difference, Decimal)
        self.assertEqual(report.open_amounts["PO-1"], Decimal("100.00"))

    def test_duplicate_of_names_the_first_invoice_as_written(self):
        first = "ＩＮＶ-2026-0042"
        report = reconcile([inv(first), inv("INV-2026-42"), inv("inv/2026/0042")], ORDERS)
        self.assertEqual([l.status for l in report.lines], ["matched", "duplicate", "duplicate"])
        self.assertEqual([l.duplicate_of for l in report.lines], [None, first, first])

    def test_duplicates_with_other_po_or_amount_are_still_duplicates(self):
        orders = ORDERS + [order("PO-2", amount="50.00")]
        report = reconcile([inv("A-1"), inv("A-01", po="PO-2", total="50.00")], orders)
        self.assertEqual([l.status for l in report.lines], ["matched", "duplicate"])
        self.assertEqual(report.as_dict()["lines"][1]["po_number"], "PO-2")
        self.assertEqual(report.open_amounts["PO-2"], Decimal("50.00"))

    def test_first_copy_is_reconciled_as_today_whatever_its_status(self):
        report = reconcile([inv("A-1", po="PO-9"), inv("A-1")], ORDERS)
        self.assertEqual([l.status for l in report.lines], ["unknown_po", "duplicate"])
        self.assertEqual(report.open_amounts["PO-1"], Decimal("100.00"))

    def test_different_vendors_are_never_duplicates(self):
        orders = [order(), order("PO-2", vendor="V2")]
        report = reconcile([inv("INV-2026-0042"), inv("INV-2026-0042", po="PO-2", vendor="V2")],
                           orders)
        self.assertEqual([l.status for l in report.lines], ["matched", "matched"])
        self.assertNotIn("duplicate_of", report.as_dict()["lines"][1])

    def test_distinct_invoices_of_one_vendor_are_not_duplicates(self):
        orders = [order(), order("PO-2")]
        report = reconcile([inv("INV-2026-0042"), inv("INV-2026-0043", po="PO-2")], orders)
        self.assertEqual([l.status for l in report.lines], ["matched", "matched"])

    def test_other_lines_keep_their_keys(self):
        report = reconcile([inv("A-1"), inv("a 1"), inv("B-1", total="1.00")], ORDERS)
        keys = [set(line) for line in report.as_dict()["lines"]]
        base = {"invoice_number", "vendor_id", "po_number", "status", "difference"}
        self.assertEqual(keys, [base, base | {"duplicate_of"}, base])

    def test_fixture_report_is_unchanged(self):
        invoices = [Invoice.from_dict(d)
                    for d in json.loads((ROOT / "fixtures" / "invoices.json").read_text())]
        orders = [PurchaseOrder.from_dict(d)
                  for d in json.loads((ROOT / "fixtures" / "orders.json").read_text())]
        expected = json.loads((ROOT / "fixtures" / "expected-report.json").read_text())
        self.assertEqual(reconcile(invoices, orders).as_dict(), expected)

    def test_resent_copy_of_a_fixture_invoice_is_a_duplicate(self):
        invoices = [Invoice.from_dict(d)
                    for d in json.loads((ROOT / "fixtures" / "invoices.json").read_text())]
        orders = [PurchaseOrder.from_dict(d)
                  for d in json.loads((ROOT / "fixtures" / "orders.json").read_text())]
        first = invoices[0]
        copy = Invoice(first.vendor_id, "INV—2026—0042", first.po_number,
                       first.currency, first.total)
        expected = json.loads((ROOT / "fixtures" / "expected-report.json").read_text())
        got = reconcile(invoices + [copy], orders).as_dict()
        self.assertEqual(got["lines"][:-1], expected["lines"])
        self.assertEqual(got["open_amounts"], expected["open_amounts"])
        self.assertEqual(got["lines"][-1]["duplicate_of"], "INV-2026-0042")


if __name__ == "__main__":
    unittest.main()
