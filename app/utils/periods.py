from datetime import date, datetime, timedelta

from app.errors.transaction_metrics import TransactionMetricsPeriodError
from app.schemas.balance import (
    PaymentMethodBreakdownByTypeSchema,
    PaymentMethodBreakdownSchema,
    PeriodMetricsSchema,
)
from app.schemas.dto.periods import PeriodKey
from app.utils.dates import (
    count_iso_weeks_in_month,
    end_of_month,
    end_of_year,
    iso_weeks_in_year,
    start_of_month,
    start_of_year,
)


def get_affected_periods(dt: datetime) -> list[PeriodKey]:
    """Return affected week/month/year period keys for a datetime."""
    d = dt.date()
    iso = d.isocalendar()

    return [
        PeriodKey(period_type="week", year=iso.year, week=iso.week),
        PeriodKey(period_type="month", year=d.year, month=d.month),
        PeriodKey(period_type="year", year=d.year),
    ]


def get_period_date_range(key: PeriodKey) -> tuple[date, date]:
    """Return the start and end dates for a period."""
    if key.period_type == "week":
        if key.week is None:
            raise TransactionMetricsPeriodError.week_requires_week()
        start = date.fromisocalendar(key.year, key.week, 1)
        return start, start + timedelta(days=6)

    if key.period_type == "month":
        if key.month is None:
            raise TransactionMetricsPeriodError.month_requires_month()
        return (
            start_of_month(key.year, key.month),
            end_of_month(key.year, key.month),
        )

    if key.period_type == "year":
        return start_of_year(key.year), end_of_year(key.year)

    raise TransactionMetricsPeriodError.unknown_period_type(key.period_type)


def weeks_for_period(
    period_type: str,
    year: int,
    month: int | None,
) -> int:
    """Return the number of weeks in a period."""
    if period_type == "week":
        return 1
    if period_type == "month":
        return count_iso_weeks_in_month(year, month or 1)
    if period_type == "year":
        return iso_weeks_in_year(year)
    raise TransactionMetricsPeriodError.unknown_period_type(period_type)


def previous_period_key(key: PeriodKey) -> PeriodKey:
    """Return the immediately preceding period key."""
    match key.period_type:
        case "year":
            return PeriodKey(period_type="year", year=key.year - 1, month=None, week=None)

        case "month":
            if key.month is None:
                raise TransactionMetricsPeriodError.month_requires_month()

            year, month = (key.year - 1, 12) if key.month == 1 else (key.year, key.month - 1)
            return PeriodKey(period_type="month", year=year, month=month, week=None)

        case "week":
            if key.week is None:
                raise TransactionMetricsPeriodError.week_requires_week()

            prev_monday = date.fromisocalendar(key.year, key.week, 1) - timedelta(days=7)
            iso_year, iso_week, _ = prev_monday.isocalendar()
            return PeriodKey(period_type="week", year=iso_year, month=None, week=iso_week)

        case _:
            raise TransactionMetricsPeriodError.unknown_period_type(key.period_type)


def to_period_schema(row) -> PeriodMetricsSchema:
    """Convert repository row to PeriodMetricsSchema (or zeros)."""
    if not row:
        return PeriodMetricsSchema()
    return PeriodMetricsSchema(
        balance=float(row.balance or 0),
        total_income=float(row.total_income or 0),
        total_expense=float(row.total_expense or 0),
        transaction_count=int(row.transaction_count or 0),
    )


def payment_breakdown_schemas(row) -> PaymentMethodBreakdownByTypeSchema:
    """Build payment method breakdown schema from current row."""
    breakdown = dict(row.payment_method_breakdown) if row and row.payment_method_breakdown else {}

    credit = breakdown.get("credit", {})
    debit = breakdown.get("debit", {})

    return PaymentMethodBreakdownByTypeSchema(
        credit=PaymentMethodBreakdownSchema(
            amounts=credit.get("amounts", {}),
            percentages=credit.get("percentages", {}),
        ),
        debit=PaymentMethodBreakdownSchema(
            amounts=debit.get("amounts", {}),
            percentages=debit.get("percentages", {}),
        ),
    )


def weekly_averages_and_ratio(row) -> tuple[float, float, float]:
    """Get weekly averages and ratio from current row, defaulting to 0."""
    weekly_income = float(row.weekly_average_income) if row and row.weekly_average_income else 0.0
    weekly_expense = float(row.weekly_average_expense) if row and row.weekly_average_expense else 0.0
    ratio = float(row.income_expense_ratio) if row and row.income_expense_ratio else 0.0
    return weekly_income, weekly_expense, ratio
