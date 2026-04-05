from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.repositories.transaction_metrics import TransactionMetricsRepository
from app.schemas.dto.periods import PeriodRawMetrics
from app.utils.paymenth_method import compute_balance_breakdown, format_payment_method_breakdown
from app.utils.periods import get_affected_periods


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

        periods = get_affected_periods(dt)

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
        breakdown = format_payment_method_breakdown(
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
            credit_payment_amounts={"cash": Decimal("100.00")},
            debit_payment_amounts={"transfer": Decimal("300.00")},
        )

        fetch_mock = Mock(return_value=fake_metrics)
        monkeypatch.setattr(self.repository, "_fetch_period_metrics", fetch_mock)

        upsert_mock = Mock()
        monkeypatch.setattr(self.repository, "_upsert_metrics", upsert_mock)

        # Act
        self.repository.recalc_period(period_type="month", year=2026, month=1)

        # Assert
        fetch_mock.assert_called_once()

        # Assert
        args, kwargs = fetch_mock.call_args
        assert not kwargs
        assert len(args) == 1
        assert isinstance(args[0], (tuple, list))
        assert len(args[0]) >= 1

        # Assert
        upsert_mock.assert_called_once()

    def test_recalc_period_includes_balance_in_breakdown(self, monkeypatch):
        """Ensure recalc_period includes balance key in payment_method_breakdown."""

        fake_metrics = PeriodRawMetrics(
            total_income=Decimal("500.00"),
            total_expense=Decimal("200.00"),
            transaction_count=5,
            credit_payment_amounts={
                "cash": Decimal("300.00"),
                "transfer_personal_account": Decimal("200.00"),
            },
            debit_payment_amounts={
                "cash": Decimal("100.00"),
                "transfer_personal_account": Decimal("100.00"),
            },
        )

        fetch_mock = Mock(return_value=fake_metrics)
        monkeypatch.setattr(self.repository, "_fetch_period_metrics", fetch_mock)

        upsert_mock = Mock()
        monkeypatch.setattr(self.repository, "_upsert_metrics", upsert_mock)

        self.repository.recalc_period(period_type="month", year=2026, month=3)

        upsert_mock.assert_called_once()
        breakdown = upsert_mock.call_args.kwargs["payment_method_breakdown"]

        assert "credit" in breakdown
        assert "debit" in breakdown
        assert "balance" in breakdown

        assert breakdown["balance"]["amounts"]["cash"] == 200.0
        assert breakdown["balance"]["amounts"]["transfer_personal_account"] == 100.0

    def test_compute_balance_breakdown_basic(self):
        """Balance amounts = credit - debit per method."""
        credit = {"cash": Decimal("500.00"), "transfer": Decimal("300.00")}
        debit = {"cash": Decimal("200.00"), "transfer": Decimal("100.00")}

        result = compute_balance_breakdown(credit, debit)

        assert result["amounts"]["cash"] == 300.0
        assert result["amounts"]["transfer"] == 200.0
        assert result["percentages"]["cash"] == 60.0
        assert result["percentages"]["transfer"] == 40.0

    def test_compute_balance_breakdown_negative_balance(self):
        """A method can have negative balance (more debits than credits)."""
        credit = {"cash": Decimal("100.00")}
        debit = {"cash": Decimal("300.00")}

        result = compute_balance_breakdown(credit, debit)

        assert result["amounts"]["cash"] == -200.0
        assert result["percentages"]["cash"] == 100.0

    def test_compute_balance_breakdown_zero_total(self):
        """When total absolute balance is 0, all percentages should be 0."""
        credit = {"cash": Decimal("100.00")}
        debit = {"cash": Decimal("100.00")}

        result = compute_balance_breakdown(credit, debit)

        assert result["amounts"]["cash"] == 0.0
        assert result["percentages"]["cash"] == 0.0

    def test_compute_balance_breakdown_disjoint_methods(self):
        """Methods that exist only in credit or only in debit."""
        credit = {"cash": Decimal("500.00")}
        debit = {"transfer": Decimal("200.00")}

        result = compute_balance_breakdown(credit, debit)

        assert result["amounts"]["cash"] == 500.0
        assert result["amounts"]["transfer"] == -200.0

    def test_compute_balance_breakdown_empty(self):
        """Empty inputs produce empty output."""
        result = compute_balance_breakdown({}, {})

        assert result["amounts"] == {}
        assert result["percentages"] == {}
