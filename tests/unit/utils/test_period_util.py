from datetime import datetime, timezone

import pytest

from app.enum.balance import PeriodType
from app.errors.transaction_metrics import TransactionMetricsPeriodError
from app.schemas.dto.periods import PeriodKey
from app.utils.metrics import percent_change
from app.utils.periods import current_period_key, period_bounds_utc, previous_period_key


class TestPeriodsUtils:
    """Test cases for period utility functions."""

    def test_previous_year(self):
        key = PeriodKey(period_type="year", year=2026)
        prev = previous_period_key(key)
        assert prev.year == 2025
        assert prev.period_type == "year"

    def test_previous_month_regular(self):
        key = PeriodKey(period_type="month", year=2026, month=5)
        prev = previous_period_key(key)
        assert prev.year == 2026
        assert prev.month == 4

    def test_previous_month_january_boundary(self):
        key = PeriodKey(period_type="month", year=2026, month=1)
        prev = previous_period_key(key)
        assert prev.year == 2025
        assert prev.month == 12

    def test_previous_week_iso(self):
        key = PeriodKey(period_type="week", year=2026, week=1)
        prev = previous_period_key(key)
        assert prev.period_type == "week"
        assert prev.year in (2025, 2026)
        assert 1 <= prev.week <= 53

    def test_percent_change_previous_zero(self):
        assert percent_change(current=10, previous=0) == 0

    def test_percent_change_basic(self):
        assert float(percent_change(current=200, previous=100)) == 100.0

    def test_current_period_key_year(self):
        now = datetime(2026, 2, 3, 10, 0, 0, tzinfo=timezone.utc)
        key = current_period_key(period_type=PeriodType.YEAR, now=now)

        assert key.period_type == "year"
        assert key.year == 2026
        assert key.month is None
        assert key.week is None

    def test_current_period_key_month(self):
        now = datetime(2026, 2, 3, 10, 0, 0, tzinfo=timezone.utc)
        key = current_period_key(period_type=PeriodType.MONTH, now=now)

        assert key.period_type == "month"
        assert key.year == 2026
        assert key.month == 2
        assert key.week is None

    def test_current_period_key_week_uses_iso_week_and_month_of_week_start(self):
        now = datetime(2026, 1, 7, 10, 0, 0, tzinfo=timezone.utc)
        key = current_period_key(period_type=PeriodType.WEEK, now=now)

        iso_year, iso_week, _ = now.isocalendar()
        week_start = datetime.fromisocalendar(iso_year, iso_week, 1).date()

        assert key.period_type == "week"
        assert key.year == iso_year
        assert key.week == iso_week
        assert key.month == week_start.month

    def test_period_bounds_utc_year(self):
        key = PeriodKey(period_type="year", year=2026)

        start_dt, end_dt = period_bounds_utc(key)

        assert start_dt == datetime(2026, 1, 1, tzinfo=timezone.utc)
        assert end_dt == datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    def test_period_bounds_utc_month_regular(self):
        key = PeriodKey(period_type="month", year=2026, month=2)

        start_dt, end_dt = period_bounds_utc(key)

        assert start_dt == datetime(2026, 2, 1, tzinfo=timezone.utc)
        assert end_dt == datetime(2026, 2, 28, 23, 59, 59, tzinfo=timezone.utc)

    def test_period_bounds_utc_month_leap_year(self):
        key = PeriodKey(period_type="month", year=2024, month=2)

        start_dt, end_dt = period_bounds_utc(key)

        assert start_dt == datetime(2024, 2, 1, tzinfo=timezone.utc)
        assert end_dt == datetime(2024, 2, 29, 23, 59, 59, tzinfo=timezone.utc)

    def test_period_bounds_utc_month_requires_month(self):
        key = PeriodKey(period_type="month", year=2026, month=None)

        with pytest.raises(TransactionMetricsPeriodError) as ex:
            period_bounds_utc(key)

        assert "month" in str(ex.value).lower()

    def test_period_bounds_utc_week(self):
        key = PeriodKey(period_type="week", year=2026, month=1, week=5)

        start_dt, end_dt = period_bounds_utc(key)

        assert start_dt.weekday() == 0
        assert start_dt.tzinfo == timezone.utc

        assert end_dt.weekday() == 6
        assert end_dt.hour == 23
        assert end_dt.minute == 59
        assert end_dt.second == 59
        assert end_dt.tzinfo == timezone.utc

        assert (end_dt.date() - start_dt.date()).days == 6

    def test_period_bounds_utc_week_requires_week(self):
        key = PeriodKey(period_type="week", year=2026, month=1, week=None)

        with pytest.raises(TransactionMetricsPeriodError) as ex:
            period_bounds_utc(key)

        assert "week" in str(ex.value).lower()

    def test_period_bounds_utc_unknown_period_type(self):
        key = PeriodKey(period_type="quarter", year=2026)

        with pytest.raises(TransactionMetricsPeriodError) as ex:
            period_bounds_utc(key)

        assert "unknown" in str(ex.value).lower()
