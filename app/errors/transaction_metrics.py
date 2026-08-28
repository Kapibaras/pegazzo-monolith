from __future__ import annotations

from fastapi import status

from app.errors import PegazzoException


class TransactionMetricsPeriodError(ValueError):
    """Raised when a PeriodKey is invalid or incomplete."""

    @classmethod
    def week_requires_week(cls) -> TransactionMetricsPeriodError:
        return cls("Week period requires 'week'.")

    @classmethod
    def month_requires_month(cls) -> TransactionMetricsPeriodError:
        return cls("Month period requires 'month'.")

    @classmethod
    def unknown_period_type(cls, period_type: str) -> TransactionMetricsPeriodError:
        return cls(f"Unknown period_type: {period_type}.")


class InvalidMetricsPeriodException(PegazzoException):
    """Invalid month/year combination for metrics."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid metrics period or missing required parameters. "
                "Valid periods are 'week', 'month', or 'year', with their corresponding parameters."
            ),
        )
