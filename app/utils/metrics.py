from decimal import Decimal

from app.utils.decimal import DEC_2, ROUND_HALF_UP


def calculate_weekly_averages(
    *,
    total_income: Decimal,
    total_expense: Decimal,
    weeks: int,
) -> tuple[Decimal, Decimal]:
    """Calculate weekly averages."""
    w = Decimal(max(1, weeks))
    return (
        (total_income / w).quantize(DEC_2, rounding=ROUND_HALF_UP),
        (total_expense / w).quantize(DEC_2, rounding=ROUND_HALF_UP),
    )


def calculate_income_expense_ratio(
    total_income: Decimal,
    total_expense: Decimal,
) -> Decimal:
    """Calculate income expense ratio."""
    if total_expense == 0:
        return Decimal("0.00")
    return (total_income / total_expense).quantize(
        DEC_2,
        rounding=ROUND_HALF_UP,
    )
