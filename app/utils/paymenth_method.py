from decimal import Decimal
from typing import Any

from app.utils.decimal import calculate_percentage


def format_payment_method_breakdown(
    amounts: dict[str, Decimal],
) -> dict[str, Any]:
    """Format payment method breakdown."""
    total = sum(amounts.values(), Decimal("0.00"))
    return {
        "amounts": {k: float(v) for k, v in amounts.items()},
        "percentages": {k: float(calculate_percentage(v, total)) for k, v in amounts.items()},
    }
