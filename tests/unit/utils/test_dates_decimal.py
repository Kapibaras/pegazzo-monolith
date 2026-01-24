from __future__ import annotations

from decimal import Decimal

from app.utils.dates import count_iso_weeks_in_month, iso_weeks_in_year
from app.utils.decimal import calculate_percentage, round_to_2_decimals


def test_dates_utils_basic():
    assert iso_weeks_in_year(2026) in (52, 53)
    assert count_iso_weeks_in_month(2026, 1) >= 4


def test_decimal_utils_basic():
    assert round_to_2_decimals(None) == Decimal("0.00")
    assert round_to_2_decimals("10") == Decimal("10.00")
    assert calculate_percentage(Decimal("1.00"), Decimal("0.00")) == Decimal("0.00")
    assert calculate_percentage(Decimal("1.00"), Decimal("4.00")) == Decimal("25.00")
