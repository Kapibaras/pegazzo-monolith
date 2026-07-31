from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from app.errors.transaction_metrics import TransactionMetricsPeriodError
from app.schemas.dto.periods import PeriodKey
from app.utils.metrics import percent_change
from app.utils.periods import (
    get_period_date_range,
    period_bounds_utc,
    previous_period_key,
    weeks_for_period,
)


class TestPeriodsUtils:
    """Test cases for period utility functions."""

    def test_previous_year(self):
        key = PeriodKey(period_type="year", year=2026)
        prev = previous_period_key(key)
        assert prev.period_type == "year"
        assert prev.year == 2025
        assert prev.month is None
        assert prev.week is None

    def test_previous_month_regular(self):
        key = PeriodKey(period_type="month", year=2026, month=5)
        prev = previous_period_key(key)
        assert prev.period_type == "month"
        assert prev.year == 2026
        assert prev.month == 4
        assert prev.week is None

    def test_previous_month_january_boundary(self):
        key = PeriodKey(period_type="month", year=2026, month=1)
        prev = previous_period_key(key)
        assert prev.period_type == "month"
        assert prev.year == 2025
        assert prev.month == 12
        assert prev.week is None

    def test_previous_week_iso_is_exactly_7_days_before(self):
        key = PeriodKey(period_type="week", year=2026, week=5)
        prev = previous_period_key(key)

        assert prev.period_type == "week"
        assert prev.month is None

        cur_monday = date.fromisocalendar(2026, 5, 1)
        prev_monday = date.fromisocalendar(prev.year, prev.week, 1)
        assert prev_monday == cur_monday - timedelta(days=7)

    def test_previous_period_key_invalid_period_type_raises(self):
        key = PeriodKey(period_type="INVALID", year=2026)
        with pytest.raises(TransactionMetricsPeriodError):
            previous_period_key(key)

    def test_previous_period_key_week_requires_week(self):
        key = PeriodKey(period_type="week", year=2026, week=None)
        with pytest.raises(TransactionMetricsPeriodError):
            previous_period_key(key)

    def test_previous_period_key_month_requires_month(self):
        key = PeriodKey(period_type="month", year=2026, month=None)
        with pytest.raises(TransactionMetricsPeriodError):
            previous_period_key(key)

    def test_percent_change_previous_zero(self):
        assert percent_change(current=10, previous=0) == Decimal("0.00")

    def test_percent_change_basic(self):
        assert percent_change(current=200, previous=100) == Decimal("100.00")

    def test_percent_change_quantizes_two_decimals(self):
        assert percent_change(current=2, previous=1) == Decimal("100.00")
        assert percent_change(current=110, previous=100) == Decimal("10.00")
        assert percent_change(current=1, previous=3) == Decimal("-66.67")

    # --- get_period_date_range ---

    def test_get_period_date_range_week(self):
        key = PeriodKey(period_type="week", year=2026, week=1)
        start, end = get_period_date_range(key)
        assert start == date.fromisocalendar(2026, 1, 1)
        assert end == start + timedelta(days=6)

    def test_get_period_date_range_month(self):
        key = PeriodKey(period_type="month", year=2026, month=3)
        start, end = get_period_date_range(key)
        assert start == date(2026, 3, 1)
        assert end == date(2026, 3, 31)

    def test_get_period_date_range_year(self):
        key = PeriodKey(period_type="year", year=2026)
        start, end = get_period_date_range(key)
        assert start == date(2026, 1, 1)
        assert end == date(2026, 12, 31)

    def test_get_period_date_range_week_missing_week_raises(self):
        key = PeriodKey(period_type="week", year=2026, week=None)
        with pytest.raises(TransactionMetricsPeriodError):
            get_period_date_range(key)

    def test_get_period_date_range_month_missing_month_raises(self):
        key = PeriodKey(period_type="month", year=2026, month=None)
        with pytest.raises(TransactionMetricsPeriodError):
            get_period_date_range(key)

    def test_get_period_date_range_unknown_type_raises(self):
        key = PeriodKey(period_type="INVALID", year=2026)
        with pytest.raises(TransactionMetricsPeriodError):
            get_period_date_range(key)

    # --- weeks_for_period ---

    def test_weeks_for_period_week_always_one(self):
        assert weeks_for_period("week", 2026, None) == 1

    def test_weeks_for_period_month(self):
        result = weeks_for_period("month", 2026, 1)
        assert isinstance(result, int)
        assert result >= 4

    def test_weeks_for_period_year(self):
        result = weeks_for_period("year", 2026, None)
        assert result in (52, 53)

    def test_weeks_for_period_unknown_type_raises(self):
        with pytest.raises(TransactionMetricsPeriodError):
            weeks_for_period("INVALID", 2026, None)

    # --- period_bounds_utc ---

    def test_period_bounds_utc_year(self):
        key = PeriodKey(period_type="year", year=2026)
        start, end = period_bounds_utc(key)
        assert start == datetime(2026, 1, 1, tzinfo=UTC)
        assert end == datetime(2026, 12, 31, 23, 59, 59, tzinfo=UTC)

    def test_period_bounds_utc_month(self):
        key = PeriodKey(period_type="month", year=2026, month=2)
        start, end = period_bounds_utc(key)
        assert start == datetime(2026, 2, 1, tzinfo=UTC)
        assert end == datetime(2026, 2, 28, 23, 59, 59, tzinfo=UTC)

    def test_period_bounds_utc_month_missing_month_raises(self):
        key = PeriodKey(period_type="month", year=2026, month=None)
        with pytest.raises(TransactionMetricsPeriodError):
            period_bounds_utc(key)

    def test_period_bounds_utc_week(self):
        key = PeriodKey(period_type="week", year=2026, week=1)
        start, end = period_bounds_utc(key)
        expected_start = datetime.fromisocalendar(2026, 1, 1).replace(tzinfo=UTC)
        assert start == expected_start
        assert end == expected_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

    def test_period_bounds_utc_week_missing_week_raises(self):
        key = PeriodKey(period_type="week", year=2026, week=None)
        with pytest.raises(TransactionMetricsPeriodError):
            period_bounds_utc(key)

    def test_period_bounds_utc_unknown_type_raises(self):
        key = PeriodKey(period_type="INVALID", year=2026)
        with pytest.raises(TransactionMetricsPeriodError):
            period_bounds_utc(key)
