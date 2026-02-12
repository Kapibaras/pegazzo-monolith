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
    credit_payment_amounts: dict[str, Decimal]
    debit_payment_amounts: dict[str, Decimal]


@dataclass(frozen=True)
class PeriodMetrics:
    """Period metrics."""

    period: PeriodKey
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    transaction_count: int
    payment_method_breakdown: dict[str, Decimal]
    weekly_average_income: Decimal
    weekly_average_expense: Decimal
    income_expense_ratio: Decimal


@dataclass(frozen=True)
class PeriodComparison:
    """Period comparison."""

    current: PeriodMetrics
    previous: PeriodMetrics
    income_change_pct: Decimal
    expense_change_pct: Decimal
    balance_change_pct: Decimal
    transaction_count_delta: int


@dataclass(frozen=True)
class Page:
    """Page."""

    page: int
    limit: int
    offset: int
