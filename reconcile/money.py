"""Money as exact decimals with two fractional digits. Floats are refused: 0.1 + 0.2 is not money."""

from decimal import ROUND_HALF_EVEN, Decimal, InvalidOperation

CENT = Decimal("0.01")


def amount(value) -> Decimal:
    """An amount from a string or an int, rounded half-even to cents.

    >>> amount("1190.005")
    Decimal('1190.00')
    """
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise TypeError(f"amounts are strings or integers, not {type(value).__name__}")
    try:
        d = Decimal(str(value).strip().replace(",", ""))
    except InvalidOperation:
        raise ValueError(f"not an amount: {value!r}") from None
    if not d.is_finite():
        raise ValueError(f"not an amount: {value!r}")
    return d.quantize(CENT, rounding=ROUND_HALF_EVEN)


def text(d: Decimal) -> str:
    """An amount as the report states it: always two fractional digits."""
    return f"{d.quantize(CENT, rounding=ROUND_HALF_EVEN):f}"
