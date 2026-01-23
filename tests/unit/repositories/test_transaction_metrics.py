from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.repositories.dto import PeriodRawMetrics
from app.repositories.transaction_metrics import TransactionMetricsRepository


@pytest.fixture
def transaction_metrics_repository_setup(request):
    """Fixture to set up TransactionMetricsRepository with a mocked session."""
    mock_session = Mock(spec=Session)
    repository = TransactionMetricsRepository(mock_session)

    request.cls.repository = repository
    request.cls.mock_session = mock_session


@pytest.mark.usefixtures("transaction_metrics_repository_setup")
class TestTransactionMetricsRepository:
    """Unit tests for TransactionMetricsRepository."""

    def test_get_affected_periods(self):
        dt = datetime(2026, 1, 31, 12, 0, tzinfo=timezone.utc)

        periods = self.repository.get_affected_periods(dt)

        assert len(periods) == 3

        period_types = {p.period_type for p in periods}
        assert period_types == {"week", "month", "year"}

        week = next(p for p in periods if p.period_type == "week")
        month = next(p for p in periods if p.period_type == "month")
        year = next(p for p in periods if p.period_type == "year")

        assert week.year == 2026
        assert month.month == 1
        assert year.year == 2026

    def test_format_payment_method_breakdown(self):
        breakdown = self.repository.format_payment_method_breakdown(
            {
                "cash": Decimal("100.00"),
                "transfer": Decimal("300.00"),
            },
        )

        assert breakdown["amounts"]["cash"] == 100.0
        assert breakdown["amounts"]["transfer"] == 300.0

        assert breakdown["percentages"]["cash"] == 25.0
        assert breakdown["percentages"]["transfer"] == 75.0

    def test_recalc_period_orchestration(self, monkeypatch):
        """Ensure recalc_period orchestrates internal calls correctly."""

        fake_metrics = PeriodRawMetrics(
            total_income=Decimal("200.00"),
            total_expense=Decimal("50.00"),
            transaction_count=3,
            payment_amounts={"cash": Decimal("250.00")},
        )

        # Mock internal metric fetch
        monkeypatch.setattr(
            self.repository,
            "_fetch_period_metrics",
            Mock(return_value=fake_metrics),
        )

        # Mock upsert to avoid DB interaction
        upsert_mock = Mock()
        monkeypatch.setattr(
            self.repository,
            "_upsert_metrics",
            upsert_mock,
        )

        # Act
        self.repository.recalc_period(
            period_type="month",
            year=2026,
            month=1,
        )

        # Assert
        upsert_mock.assert_called_once()
