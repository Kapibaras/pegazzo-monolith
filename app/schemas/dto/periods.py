from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class PeriodKey:
    """Period key."""

    period_type: str
    year: int
    month: Optional[int] = None
    week: Optional[int] = None


@dataclass(frozen=True)
class PeriodRawMetrics:
    """Period raw metrics."""

    total_income: Decimal
    total_expense: Decimal
    transaction_count: int
    payment_amounts: dict[str, Decimal]
