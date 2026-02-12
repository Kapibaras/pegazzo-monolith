from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.enum.balance import PaymentMethod, PeriodType, SortOrder, TransactionSortBy, Type
from app.errors.balance import (
    InvalidDescriptionLengthException,
    TransactionNotFoundException,
)
from app.errors.transaction_metrics import InvalidMetricsPeriodException, TransactionMetricsPeriodError
from app.models.balance import Transaction
from app.repositories.balance import BalanceRepository
from app.schemas.balance import (
    BalanceMetricsDetailedResponseSchema,
    BalanceTransactionsResponseSchema,
    BalanceTrendResponseSchema,
    TransactionPatchSchema,
    TransactionSchema,
)
from app.services.balance import BalanceService


@pytest.fixture
def balance_service_test_setup(request):
    """Fixture to prepare BalanceRepository for tests."""
    mock_repo = Mock(spec=BalanceRepository)
    service = BalanceService(mock_repo)
    request.cls.service = service
    request.cls.mock_repo = mock_repo


@pytest.mark.usefixtures("balance_service_test_setup")
class TestBalanceService:
    """Tests for BalanceService."""

    def setup_method(self):
        self.mock_repo = Mock()
        self.service = BalanceService(repository=self.mock_repo)

    def test_delete_transaction_success(self):
        """Test deleting a transaction by reference."""
        # Arrange
        mock_transaction = Mock()
        self.mock_repo.get_by_reference.return_value = mock_transaction

        # Act
        self.service.delete_transaction("ABC123")

        # Assert
        self.mock_repo.get_by_reference.assert_called_once_with("ABC123")
        self.mock_repo.delete_transaction.assert_called_once_with(mock_transaction)

    def test_delete_transaction_not_found(self):
        """Test error when deleting non-existent transaction."""
        # Arrange
        self.mock_repo.get_by_reference.return_value = None

        # Act & Assert
        with pytest.raises(TransactionNotFoundException):
            self.service.delete_transaction("NOEXIST")

    def test_get_transaction_success(self):
        """Test returning a transaction by reference."""
        fake_tx = Mock()
        self.mock_repo.get_by_reference.return_value = fake_tx

        result = self.service.get_transaction("REF123")
        self.mock_repo.get_by_reference.assert_called_once_with("REF123")
        assert result == fake_tx

    def test_get_transaction_not_found(self):
        """Should raise exception when reference doesn't exist."""
        self.mock_repo.get_by_reference.return_value = None

        with pytest.raises(TransactionNotFoundException):
            self.service.get_transaction("NOEXISTS")

    def test_create_transaction_success(self):
        """Test successful creation of a transaction."""

        schema = TransactionSchema(
            amount=1200,
            date="2025-01-01T10:00:00",
            type=Type.DEBIT,
            description="Pago de material",
            payment_method=PaymentMethod.CASH,
        )

        # Mock
        self.mock_repo.create_transaction.side_effect = lambda t: t

        with patch("app.services.balance.generate_reference") as mock_ref:
            mock_ref.return_value = "0054291019"
            result = self.service.create_transaction(schema)

        self.mock_repo.create_transaction.assert_called_once()
        assert isinstance(result, Transaction)
        assert result.amount == 1200
        assert result.reference == "0054291019"

    @pytest.mark.parametrize(
        "invalid_type",
        ["xyz", None, 123, object()],
    )
    def test_create_transaction_invalid_type(self, invalid_type):
        """Pydantic must validate enum before service."""
        with pytest.raises(ValidationError):
            TransactionSchema(
                amount=100,
                reference="IGNORED",
                date="2025-01-01T10:00:00",
                type=invalid_type,
                description="Test",
                payment_method=PaymentMethod.CASH,
            )

    @pytest.mark.parametrize(
        "invalid_method",
        ["xxx", None, 500, {}, []],
    )
    def test_create_transaction_invalid_payment_method_schema(self, invalid_method):
        """Pydantic should reject invalid payment_method before service is called."""
        with pytest.raises(ValidationError):
            TransactionSchema(
                amount=50,
                reference="IGNORED",
                date="2025-01-01T10:00:00",
                type=Type.DEBIT,
                description="Test",
                payment_method=invalid_method,
            )

    def test_create_transaction_invalid_description_length(self):
        """Test error for description > 255 chars."""

        long_desc = "x" * 256

        schema = TransactionSchema(
            amount=100,
            reference="IGNORED",
            date="2025-01-01T10:00:00",
            type=Type.DEBIT,
            description=long_desc,
            payment_method=PaymentMethod.CASH,
        )

        with pytest.raises(InvalidDescriptionLengthException):
            self.service.create_transaction(schema)

    def test_update_transaction_success(self):
        """Test updating a transaction successfully."""

        existing_tx = Transaction(
            reference="REF123",
            amount=100,
            description="Old description",
            payment_method=PaymentMethod.CASH,
        )

        self.mock_repo.get_by_reference.return_value = existing_tx
        self.mock_repo.update_transaction.side_effect = lambda t: t

        update_schema = TransactionPatchSchema(
            amount=500,
            description="Updated description",
            payment_method=PaymentMethod.CASH,
        )

        result = self.service.update_transaction("REF123", update_schema)

        self.mock_repo.get_by_reference.assert_called_once_with("REF123")
        self.mock_repo.update_transaction.assert_called_once_with(existing_tx)

        assert result.amount == 500
        assert result.description == "Updated description"
        assert result.payment_method == PaymentMethod.CASH

    def test_update_transaction_partial(self):
        """Test partial update of a transaction."""

        existing_tx = Transaction(
            reference="REF123",
            amount=100,
            description="Original",
            payment_method=PaymentMethod.CASH,
        )

        self.mock_repo.get_by_reference.return_value = existing_tx
        self.mock_repo.update_transaction.side_effect = lambda t: t

        update_schema = TransactionPatchSchema(
            amount=None,
            description="Only description updated",
            payment_method=None,
        )

        result = self.service.update_transaction("REF123", update_schema)

        assert result.amount == 100
        assert result.description == "Only description updated"
        assert result.payment_method == PaymentMethod.CASH

    def test_update_transaction_not_found(self):
        """Test error when updating non-existent transaction."""

        self.mock_repo.get_by_reference.return_value = None

        update_schema = TransactionPatchSchema(
            amount=200,
            description="Update",
            payment_method=PaymentMethod.CASH,
        )

        with pytest.raises(TransactionNotFoundException):
            self.service.update_transaction("NOEXIST", update_schema)

    def test_update_transaction_invalid_description_length(self):
        """Test error when updating transaction with long description."""

        long_desc = "x" * 256

        existing_tx = Transaction(
            reference="REF123",
            amount=100,
            description="Old",
            payment_method=PaymentMethod.CASH,
        )

        self.mock_repo.get_by_reference.return_value = existing_tx

        update_schema = TransactionPatchSchema(
            amount=None,
            description=long_desc,
            payment_method=None,
        )

        with pytest.raises(InvalidDescriptionLengthException):
            self.service.update_transaction("REF123", update_schema)

    def test_get_month_year_metrics_returns_zero_when_no_data(self):
        # Arrange
        self.mock_repo.get_month_year_metrics.return_value = None

        # Act
        result = self.service.get_metrics(month=5, year=2025)

        # Assert
        self.mock_repo.get_month_year_metrics.assert_called_once_with(
            month=5,
            year=2025,
        )

        assert result == {
            "balance": 0,
            "total_income": 0,
            "total_expense": 0,
            "transaction_count": 0,
            "period": {
                "month": 5,
                "year": 2025,
            },
        }

    def test_get_month_year_metrics_returns_repo_data(self):
        # Arrange
        repo_result = SimpleNamespace(
            balance=1500,
            total_income=3000,
            total_expense=1500,
            transaction_count=12,
        )

        self.mock_repo.get_month_year_metrics.return_value = repo_result

        # Act
        result = self.service.get_metrics(month=5, year=2025)

        # Assert
        self.mock_repo.get_month_year_metrics.assert_called_once_with(
            month=5,
            year=2025,
        )

        assert result == {
            "balance": 1500,
            "total_income": 3000,
            "total_expense": 1500,
            "transaction_count": 12,
            "period": {
                "month": 5,
                "year": 2025,
            },
        }

    def test_get_month_year_metrics_propagates_unexpected_error(self):
        # Arrange
        self.mock_repo.get_month_year_metrics.side_effect = RuntimeError("DB exploded")

        # Act / Assert
        with pytest.raises(RuntimeError, match="DB exploded"):
            self.service.get_metrics(month=5, year=2025)

    def test_service_does_not_mutate_repo_result(self):
        # Arrange
        repo_result = SimpleNamespace(
            balance=100,
            total_income=200,
            total_expense=100,
            transaction_count=2,
        )

        self.mock_repo.get_month_year_metrics.return_value = repo_result

        # Act
        result = self.service.get_metrics(month=1, year=2025)

        # Assert
        assert result == {
            "balance": 100,
            "total_income": 200,
            "total_expense": 100,
            "transaction_count": 2,
            "period": {
                "month": 1,
                "year": 2025,
            },
        }

        assert result is not repo_result

    def test_service_does_not_modify_repo_result(self):
        # Arrange
        repo_result = SimpleNamespace(
            balance=100,
            total_income=200,
            total_expense=100,
            transaction_count=2,
        )

        original_state = repo_result.__dict__.copy()
        self.mock_repo.get_month_year_metrics.return_value = repo_result

        # Act
        self.service.get_metrics(month=1, year=2025)

        # Assert
        assert repo_result.__dict__ == original_state

    def test_get_management_metrics_invalid_period_raises(self):
        with pytest.raises(TransactionMetricsPeriodError):
            self.service.get_management_metrics(period="INVALID", year=2026)

    def test_get_management_metrics_week_missing_params_raises(self):
        with pytest.raises(TransactionMetricsPeriodError):
            self.service.get_management_metrics(period="week", year=2026, week=None, month=1)

    def test_get_management_metrics_month_missing_params_raises(self):
        with pytest.raises(TransactionMetricsPeriodError):
            self.service.get_management_metrics(period="month", year=2026, month=None)

    def test_get_management_metrics_year_missing_params_raises(self):
        with pytest.raises(TypeError):
            self.service.get_management_metrics(period="year", year=None)

    def test_get_management_metrics_returns_zero_when_no_rows(self):
        """If both current and previous are None, should return BalanceMetricsDetailedResponseSchema()."""
        self.mock_repo.get_period_metrics.return_value = None

        result = self.service.get_management_metrics(period="year", year=2026)

        assert BalanceMetricsDetailedResponseSchema.model_validate(result)
        assert self.mock_repo.get_period_metrics.call_count == 2

        assert result.current_period.balance == 0.0
        assert result.previous_period.balance == 0.0
        assert result.comparison.balance_change_percent == 0.0

    def test_get_management_metrics_calls_repo_with_current_and_previous_year(self):
        """year=2026 should query current (2026) and previous (2025)."""
        current = SimpleNamespace(
            balance=Decimal("100.00"),
            total_income=Decimal("200.00"),
            total_expense=Decimal("100.00"),
            transaction_count=5,
            payment_method_breakdown={},
            weekly_average_income=Decimal("50.00"),
            weekly_average_expense=Decimal("25.00"),
            income_expense_ratio=Decimal("2.00"),
        )
        prev = None

        self.mock_repo.get_period_metrics.side_effect = [current, prev]

        result = self.service.get_management_metrics(period="year", year=2026)

        assert BalanceMetricsDetailedResponseSchema.model_validate(result)

        calls = self.mock_repo.get_period_metrics.call_args_list
        assert calls[0].kwargs == {"period_type": "year", "year": 2026, "month": None, "week": None}
        assert calls[1].kwargs == {"period_type": "year", "year": 2025, "month": None, "week": None}

        assert result.current_period.total_income == 200.0
        assert result.previous_period.total_income == 0.0
        assert result.comparison.transaction_change == 5

    def test_get_management_metrics_percent_change_div_by_zero_is_zero(self):
        """If previous is 0, percentage changes should be 0 (per percent_change behavior)."""
        current = SimpleNamespace(
            balance=Decimal("100.00"),
            total_income=Decimal("100.00"),
            total_expense=Decimal("0.00"),
            transaction_count=2,
            payment_method_breakdown={},
            weekly_average_income=Decimal("0.00"),
            weekly_average_expense=Decimal("0.00"),
            income_expense_ratio=Decimal("0.00"),
        )
        previous = SimpleNamespace(
            balance=Decimal("0.00"),
            total_income=Decimal("0.00"),
            total_expense=Decimal("0.00"),
            transaction_count=0,
            payment_method_breakdown={},
            weekly_average_income=Decimal("0.00"),
            weekly_average_expense=Decimal("0.00"),
            income_expense_ratio=Decimal("0.00"),
        )

        self.mock_repo.get_period_metrics.side_effect = [current, previous]

        result = self.service.get_management_metrics(period="year", year=2026)

        assert result.comparison.balance_change_percent == 0.0
        assert result.comparison.income_change_percent == 0.0
        assert result.comparison.expense_change_percent == 0.0
        assert result.comparison.transaction_change == 2

    def test_get_historical_requires_valid_limit_by_contract(self):
        """Validation is handled at the API layer (query schema / route)."""
        self.mock_repo.get_metrics_for_keys.return_value = []

        with patch("app.services.balance.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 7, 12, 0, 0, tzinfo=timezone.utc)
            result = self.service.get_historical(period=PeriodType.MONTH, limit=3)

        assert BalanceTrendResponseSchema.model_validate(result)
        self.mock_repo.get_metrics_for_keys.assert_called_once()

    def test_get_historical_returns_zeros_when_no_rows(self):
        """If repo returns no rows, all periods should be present with 0 totals."""
        self.mock_repo.get_metrics_for_keys.return_value = []

        with patch("app.services.balance.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 7, 12, 0, 0, tzinfo=timezone.utc)

            result = self.service.get_historical(period=PeriodType.MONTH, limit=3)

        assert BalanceTrendResponseSchema.model_validate(result)
        assert result.period_type == "month"
        assert len(result.data) == 3

        assert all(d.total_income == 0.0 for d in result.data)
        assert all(d.total_expense == 0.0 for d in result.data)

        starts = [d.period_start for d in result.data]
        assert starts == sorted(starts)

    def test_get_historical_fills_missing_periods_with_zeros_and_keeps_real_values(self):
        """If some periods exist in transaction_metrics and others don't, missing ones must be zero-filled."""
        with patch("app.services.balance.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 7, 12, 0, 0, tzinfo=timezone.utc)

            december_row = SimpleNamespace(
                period_type="month",
                year=2025,
                month=12,
                week=None,
                total_income=Decimal("4500.00"),
                total_expense=Decimal("2200.00"),
            )
            self.mock_repo.get_metrics_for_keys.return_value = [december_row]

            result = self.service.get_historical(period=PeriodType.MONTH, limit=3)

        assert BalanceTrendResponseSchema.model_validate(result)
        assert result.period_type == "month"
        assert len(result.data) == 3

        starts = [d.period_start for d in result.data]
        assert starts == sorted(starts)

        non_zero = [d for d in result.data if d.total_income > 0 or d.total_expense > 0]
        zero = [d for d in result.data if d.total_income == 0.0 and d.total_expense == 0.0]

        assert len(non_zero) == 1
        assert len(zero) == 2

        assert non_zero[0].total_income == 4500.0
        assert non_zero[0].total_expense == 2200.0

    def test_get_historical_week_uses_iso_week_and_is_chronological(self):
        """Week trend should return N points and be chronological."""
        self.mock_repo.get_metrics_for_keys.return_value = []

        with patch("app.services.balance.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 2, 3, 12, 0, 0, tzinfo=timezone.utc)

            result = self.service.get_historical(period=PeriodType.WEEK, limit=8)

        assert BalanceTrendResponseSchema.model_validate(result)
        assert result.period_type == "week"
        assert len(result.data) == 8

        starts = [d.period_start for d in result.data]
        assert starts == sorted(starts)
        assert all(d.period_start.weekday() == 0 for d in result.data)

    def test_get_historical_year_is_chronological_and_length_matches_limit(self):
        self.mock_repo.get_metrics_for_keys.return_value = []

        with patch("app.services.balance.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 1, 7, 12, 0, 0, tzinfo=timezone.utc)

            result = self.service.get_historical(period=PeriodType.YEAR, limit=3)

        assert BalanceTrendResponseSchema.model_validate(result)
        assert result.period_type == "year"
        assert len(result.data) == 3

        starts = [d.period_start for d in result.data]
        assert starts == sorted(starts)
        assert all(d.period_start.month == 1 and d.period_start.day == 1 for d in result.data)
        assert all(d.period_end.month == 12 and d.period_end.day == 31 for d in result.data)

    def test_get_transactions_calls_repo_with_bounds_and_pagination(self):
        """Service should compute offset and call repo with start/end, limit/offset, sort params."""
        # Arrange
        start_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        self.mock_repo.count_transactions_in_range.return_value = 45
        self.mock_repo.list_transactions_in_range.return_value = []

        # Act
        with patch("app.services.balance.period_bounds_utc", return_value=(start_dt, end_dt)) as mock_bounds:
            result = self.service.get_transactions(
                period=PeriodType.MONTH,
                year=2026,
                month=1,
                week=None,
                page=2,
                limit=10,
                sort_by=TransactionSortBy.DATE,
                sort_order=SortOrder.DESC,
            )

        # Assert
        assert BalanceTransactionsResponseSchema.model_validate(result)

        mock_bounds.assert_called_once()
        key_arg = mock_bounds.call_args.args[0]
        assert key_arg.period_type == PeriodType.MONTH
        assert key_arg.year == 2026
        assert key_arg.month == 1
        assert key_arg.week is None

        self.mock_repo.count_transactions_in_range.assert_called_once_with(start_dt=start_dt, end_dt=end_dt)
        self.mock_repo.list_transactions_in_range.assert_called_once_with(
            start_dt=start_dt,
            end_dt=end_dt,
            limit=10,
            offset=10,
            sort_by=TransactionSortBy.DATE,
            sort_order=SortOrder.DESC,
        )

        assert result.pagination.page == 2
        assert result.pagination.limit == 10
        assert result.pagination.total == 45
        assert result.pagination.total_pages == 5

    def test_get_transactions_total_zero_returns_zero_pages(self):
        """If total=0, total_pages must be 0 and transactions come from repo (likely empty)."""
        start_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

        self.mock_repo.count_transactions_in_range.return_value = 0
        self.mock_repo.list_transactions_in_range.return_value = []

        with patch("app.services.balance.period_bounds_utc", return_value=(start_dt, end_dt)):
            result = self.service.get_transactions(
                period=PeriodType.YEAR,
                year=2026,
                page=1,
                limit=10,
                sort_by=TransactionSortBy.DATE,
                sort_order=SortOrder.DESC,
            )

        assert BalanceTransactionsResponseSchema.model_validate(result)
        assert result.transactions == []
        assert result.pagination.total == 0
        assert result.pagination.total_pages == 0

    @pytest.mark.parametrize(
        ("total", "limit", "expected_pages"),
        [
            (1, 10, 1),
            (10, 10, 1),
            (11, 10, 2),
            (99, 10, 10),
            (100, 10, 10),
        ],
    )
    def test_get_transactions_total_pages_uses_ceil(self, total, limit, expected_pages):
        """total_pages must be ceil(total/limit) when total>0."""
        start_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        self.mock_repo.count_transactions_in_range.return_value = total
        self.mock_repo.list_transactions_in_range.return_value = []

        with patch("app.services.balance.period_bounds_utc", return_value=(start_dt, end_dt)):
            result = self.service.get_transactions(
                period=PeriodType.MONTH,
                year=2026,
                month=1,
                page=1,
                limit=limit,
                sort_by=TransactionSortBy.DATE,
                sort_order=SortOrder.DESC,
            )

        assert BalanceTransactionsResponseSchema.model_validate(result)
        assert result.pagination.total == total
        assert result.pagination.total_pages == expected_pages

    def test_get_transactions_returns_repo_rows_in_response(self):
        """Service should return repo rows in `transactions`."""
        start_dt = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        end_dt = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        tx1 = Transaction(reference="TRX-001", amount=100, date=start_dt, type="debit", description="A", payment_method="cash")
        tx2 = Transaction(reference="TRX-002", amount=200, date=end_dt, type="debit", description="B", payment_method="cash")

        self.mock_repo.count_transactions_in_range.return_value = 2
        self.mock_repo.list_transactions_in_range.return_value = [tx1, tx2]

        with patch("app.services.balance.period_bounds_utc", return_value=(start_dt, end_dt)):
            result = self.service.get_transactions(
                period=PeriodType.MONTH,
                year=2026,
                month=1,
                page=1,
                limit=10,
                sort_by=TransactionSortBy.AMOUNT,
                sort_order=SortOrder.ASC,
            )

        assert BalanceTransactionsResponseSchema.model_validate(result)
        assert len(result.transactions) == 2
        assert result.transactions[0].reference == "TRX-001"
        assert result.transactions[1].reference == "TRX-002"

        self.mock_repo.list_transactions_in_range.assert_called_once_with(
            start_dt=start_dt,
            end_dt=end_dt,
            limit=10,
            offset=0,
            sort_by=TransactionSortBy.AMOUNT,
            sort_order=SortOrder.ASC,
        )
