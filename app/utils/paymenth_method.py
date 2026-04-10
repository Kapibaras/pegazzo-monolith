from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.utils.decimal import DEC_2, calculate_percentage


def format_payment_method_breakdown(
    amounts: dict[str, Decimal],
) -> dict[str, Any]:
    """Format payment method breakdown."""
    total = sum(amounts.values(), Decimal("0.00"))
    return {
        "amounts": {k: float(v) for k, v in amounts.items()},
        "percentages": {k: float(calculate_percentage(v, total)) for k, v in amounts.items()},
    }


def compute_balance_breakdown(
    credit_amounts: dict[str, Decimal],
    debit_amounts: dict[str, Decimal],
) -> dict[str, Any]:
    """Compute balance (credit - debit) per payment method with percentages."""
    all_methods = set(credit_amounts) | set(debit_amounts)

    balance_amounts: dict[str, Decimal] = {}
    for method in all_methods:
        credit = credit_amounts.get(method, Decimal("0.00"))
        debit = debit_amounts.get(method, Decimal("0.00"))
        balance_amounts[method] = (credit - debit).quantize(DEC_2, rounding=ROUND_HALF_UP)

    total_abs = sum(abs(v) for v in balance_amounts.values())

    percentages: dict[str, Decimal] = {}
    for method, value in balance_amounts.items():
        if total_abs == 0:
            percentages[method] = Decimal("0.00")
        else:
            percentages[method] = (abs(value) * Decimal("100") / total_abs).quantize(
                DEC_2, rounding=ROUND_HALF_UP,
            )

    return {
        "amounts": {k: float(v) for k, v in balance_amounts.items()},
        "percentages": {k: float(v) for k, v in percentages.items()},
    }
