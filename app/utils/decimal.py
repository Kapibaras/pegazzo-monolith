from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any

DEC_2 = Decimal("0.01")


def round_to_2_decimals(value: Any) -> Decimal:
    """Round to 2 decimals."""
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(DEC_2, rounding=ROUND_HALF_UP)
    return Decimal(str(value)).quantize(DEC_2, rounding=ROUND_HALF_UP)


def calculate_percentage(value: Decimal, total: Decimal) -> Decimal:
    """Calculate percentage with 2 decimals."""
    if total == 0:
        return Decimal("0.00")
    return (value * Decimal("100") / total).quantize(DEC_2, rounding=ROUND_HALF_UP)
