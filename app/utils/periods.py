from datetime import date, datetime, timedelta

from app.errors.transaction_metrics import TransactionMetricsPeriodError
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
