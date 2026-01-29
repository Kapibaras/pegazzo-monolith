from app.schemas.balance import (
    BalanceMetricsDetailedResponseSchema,
    ComparisonSchema,
    PaymentMethodBreakdownByTypeSchema,
    PaymentMethodBreakdownSchema,
    PeriodMetricsSchema,
    WeeklyAveragesSchema,
)


def zero_period_metrics() -> PeriodMetricsSchema:
    """Return zero-filled period metrics."""
    return PeriodMetricsSchema(
        balance=0.0,
        total_income=0.0,
        total_expense=0.0,
        transaction_count=0,
    )


def zero_breakdown_by_type() -> PaymentMethodBreakdownByTypeSchema:
    """Return zero-filled payment method breakdown by type."""
    return PaymentMethodBreakdownByTypeSchema(
        credit=PaymentMethodBreakdownSchema(amounts={}, percentages={}),
        debit=PaymentMethodBreakdownSchema(amounts={}, percentages={}),
    )


def zero_response() -> BalanceMetricsDetailedResponseSchema:
    """Return zero-filled detailed metrics response."""
    return BalanceMetricsDetailedResponseSchema(
        current_period=zero_period_metrics(),
        previous_period=zero_period_metrics(),
        comparison=ComparisonSchema(
            balance_change_percent=0.0,
            income_change_percent=0.0,
            expense_change_percent=0.0,
            transaction_change=0,
        ),
        payment_method_breakdown=zero_breakdown_by_type(),
        weekly_averages=WeeklyAveragesSchema(income=0.0, expense=0.0),
        income_expense_ratio=0.0,
    )
