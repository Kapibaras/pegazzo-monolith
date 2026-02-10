from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.errors.transaction_metrics import TransactionMetricsPeriodError
from app.schemas.dto.periods import PeriodKey
from app.utils.metrics import percent_change
from app.utils.periods import current_period_key, period_bounds_utc, previous_period_key


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
