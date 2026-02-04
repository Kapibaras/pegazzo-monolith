import calendar
from datetime import date, datetime, timedelta, timezone

from app.enum.balance import PeriodType
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


def previous_period_key(key: PeriodKey) -> PeriodKey:
    """Return the immediately preceding period key.

    - week: ISO week (uses date.fromisocalendar)
    - month: handle Jan -> Dec boundary
    - year: year - 1
    """
    if key.period_type == "year":
        return PeriodKey(period_type="year", year=key.year - 1, month=None, week=None)

    if key.period_type == "month":
        if key.month is None:
            raise TransactionMetricsPeriodError.month_requires_month()
        if key.month == 1:
            return PeriodKey(period_type="month", year=key.year - 1, month=12, week=None)
        return PeriodKey(period_type="month", year=key.year, month=key.month - 1, week=None)

    if key.period_type == "week":
        if key.week is None:
            raise TransactionMetricsPeriodError.week_requires_week()
        monday = date.fromisocalendar(key.year, key.week, 1)
        prev_monday = monday - timedelta(days=7)
        iso_year, iso_week, _ = prev_monday.isocalendar()
        return PeriodKey(period_type="week", year=iso_year, month=None, week=iso_week)

    raise TransactionMetricsPeriodError.unknown_period_type(key.period_type)


def current_period_key(period_type: PeriodType, now: datetime) -> PeriodKey:
    """Build PeriodKey for 'current' period based on now (UTC)."""

    if period_type == PeriodType.YEAR:
        return PeriodKey(period_type="year", year=now.year)

    if period_type == PeriodType.MONTH:
        return PeriodKey(period_type="month", year=now.year, month=now.month)

    iso_year, iso_week, _iso_weekday = now.isocalendar()
    week_start = datetime.fromisocalendar(iso_year, iso_week, 1).date()
    return PeriodKey(period_type="week", year=iso_year, month=week_start.month, week=iso_week)


def period_bounds_utc(key: PeriodKey) -> tuple[datetime, datetime]:
    """Return (start_dt, end_dt) for a PeriodKey in UTC. End is inclusive at 23:59:59 UTC to match typical API expectations."""

    if key.period_type == "year":
        start_date = datetime(key.year, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(key.year, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        return start_date, end_date

    if key.period_type == "month":
        if key.month is None:
            raise TransactionMetricsPeriodError.month_requires_month()
        last_day = calendar.monthrange(key.year, key.month)[1]
        start_date = datetime(key.year, key.month, 1, tzinfo=timezone.utc)
        end_date = datetime(key.year, key.month, last_day, 23, 59, 59, tzinfo=timezone.utc)
        return start_date, end_date

    if key.period_type == "week":
        if key.week is None:
            raise TransactionMetricsPeriodError.week_requires_week()

        start = datetime.fromisocalendar(key.year, key.week, 1).replace(tzinfo=timezone.utc)
        end = (start + timedelta(days=6)).replace(hour=23, minute=59, second=59)
        return start, end

    raise TransactionMetricsPeriodError.unknown_period_type(key.period_type)
