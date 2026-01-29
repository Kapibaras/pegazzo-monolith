from app.schemas.dto.periods import PeriodKey
from app.utils.metrics import percent_change
from app.utils.periods import previous_period_key


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
