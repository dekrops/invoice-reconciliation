import unittest
from decimal import Decimal

from reconcile.money import amount, text


class Money(unittest.TestCase):
    def test_amounts_are_exact_cents(self):
        self.assertEqual(amount("1190"), Decimal("1190.00"))
        self.assertEqual(amount("1,190.10"), Decimal("1190.10"))
        self.assertEqual(amount(12), Decimal("12.00"))

    def test_half_even_rounding(self):
        self.assertEqual(amount("0.125"), Decimal("0.12"))
        self.assertEqual(amount("0.135"), Decimal("0.14"))

    def test_floats_and_garbage_are_refused(self):
        with self.assertRaises(TypeError):
            amount(0.1)
        with self.assertRaises(ValueError):
            amount("twelve")
        with self.assertRaises(ValueError):
            amount("NaN")

    def test_text_has_two_digits(self):
        self.assertEqual(text(Decimal("5")), "5.00")


if __name__ == "__main__":
    unittest.main()
