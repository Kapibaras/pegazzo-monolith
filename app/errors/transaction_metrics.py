from __future__ import annotations


class TransactionMetricsPeriodError(ValueError):
    """Raised when a PeriodKey is invalid or incomplete."""

    @classmethod
    def week_requires_week(cls) -> "TransactionMetricsPeriodError":
        """Build an error for missing week number in week period."""
        return cls("Week period requires 'week'.")

    @classmethod
    def month_requires_month(cls) -> "TransactionMetricsPeriodError":
        """Build an error for missing month number in month period."""
        return cls("Month period requires 'month'.")

    @classmethod
    def unknown_period_type(cls, period_type: str) -> "TransactionMetricsPeriodError":
        """Build an error for unknown period type."""
        return cls(f"Unknown period_type: {period_type}.")
