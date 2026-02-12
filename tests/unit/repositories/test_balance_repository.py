from datetime import datetime, timezone
from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.enum.balance import PeriodType, SortOrder, TransactionSortBy
from app.errors.database import DBOperationError
from app.models.balance import Transaction
from app.models.transaction_metrics import TransactionMetrics
from app.repositories.balance import BalanceRepository
from app.utils.periods import PeriodKey


@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing."""
    tx = Transaction()
    tx.reference = "0054291019"
    tx.amount = 100
    tx.type = "debit"
    return tx


@pytest.fixture
def balance_repository_test_setup(request):
    """Fixture to set up BalanceRepository for class-based tests."""
    mock_db = Mock(spec=Session)
    repository = BalanceRepository(mock_db)

    request.cls.repository = repository
    request.cls.mock_db = mock_db


@pytest.mark.usefixtures("balance_repository_test_setup")
class TestBalanceRepository:
    """Tests for BalanceRepository."""

    def test_delete_transaction_success(self, sample_transaction):
        """Test successful transaction deletion."""
        # Act
        self.repository.delete_transaction(sample_transaction)

        # Assert
        self.mock_db.delete.assert_called_once_with(sample_transaction)
        self.mock_db.commit.assert_called_once()

    def test_delete_transaction_failure(self, sample_transaction):
        """Test deletion failure raises DBOperationError."""
        # Mock
        self.mock_db.delete.side_effect = Exception("Delete failed")

        # Act & Assert
        with pytest.raises(DBOperationError):
            self.repository.delete_transaction(sample_transaction)

        self.mock_db.rollback.assert_called_once()

    def test_create_transaction_success(self, sample_transaction):
        """Test successful creation of a transaction."""

        # Act
        result = self.repository.create_transaction(sample_transaction)

        # Assert
        self.mock_db.add.assert_called_once_with(sample_transaction)
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(sample_transaction)

        assert result == sample_transaction

    def test_create_transaction_failure(self, sample_transaction):
        """Test a failure during transaction creation raises DBOperationError."""

        self.mock_db.add.side_effect = Exception("DB Error")

        with pytest.raises(DBOperationError):
            self.repository.create_transaction(sample_transaction)

        self.mock_db.rollback.assert_called_once()

    def test_get_by_reference_found(self, sample_transaction):
        """Should return a transaction when found."""

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = sample_transaction

        # Act
        result = self.repository.get_by_reference("123456")

        # Assert
        self.mock_db.query.assert_called_once_with(Transaction)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

        assert result == sample_transaction

    def test_get_by_reference_not_found(self):
        """Should return None when transaction does not exist."""

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # Act
        result = self.repository.get_by_reference("NOT_EXISTS")

        # Assert
        assert result is None

    def test_update_transaction_success(self, sample_transaction):
        """Test successful transaction update."""

        # Mock
        self.repository.get_by_reference = Mock(return_value=sample_transaction)

        result = self.repository.update_transaction(sample_transaction)

        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once_with(sample_transaction)

        assert result == sample_transaction

    def test_update_transaction_failure(self, sample_transaction):
        """Test update failure raises DBOperationError."""

        self.mock_db.commit.side_effect = Exception("Commit failed")

        with pytest.raises(DBOperationError):
            self.repository.update_transaction(sample_transaction)

        self.mock_db.rollback.assert_called_once()

    def test_get_month_year_metrics_found(self):
        """Should return metrics when month and year exist."""

        metrics = TransactionMetrics()
        metrics.month = 1
        metrics.year = 2025

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = metrics

        # Act
        result = self.repository.get_month_year_metrics(month=1, year=2025)

        # Assert
        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

        assert result == metrics

    def test_get_month_year_metrics_not_found(self):
        """Should return None when metrics do not exist."""

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        # Act
        result = self.repository.get_month_year_metrics(month=12, year=2030)

        # Assert
        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

        assert result is None

    def test_get_period_metrics_year_found(self):
        metrics = TransactionMetrics()
        metrics.period_type = "year"
        metrics.year = 2026

        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = metrics

        result = self.repository.get_period_metrics(period_type="year", year=2026, month=None, week=None)

        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

        assert result == metrics

    def test_get_period_metrics_month_found(self):
        metrics = TransactionMetrics()
        metrics.period_type = "month"
        metrics.year = 2026
        metrics.month = 1

        mock_query = self.mock_db.query.return_value

        # 1er filter: period_type + year
        mock_q1 = mock_query.filter.return_value
        # 2do filter: month
        mock_q2 = mock_q1.filter.return_value

        mock_q2.first.return_value = metrics

        result = self.repository.get_period_metrics(period_type="month", year=2026, month=1, week=None)

        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        mock_query.filter.assert_called_once()
        mock_q1.filter.assert_called_once()
        mock_q2.first.assert_called_once()

        assert result == metrics

    def test_get_period_metrics_week_found(self):
        metrics = TransactionMetrics()
        metrics.period_type = "week"
        metrics.year = 2026
        metrics.week = 5

        mock_query = self.mock_db.query.return_value

        # 1er filter: period_type + year
        mock_q1 = mock_query.filter.return_value
        # 2do filter: week
        mock_q2 = mock_q1.filter.return_value

        mock_q2.first.return_value = metrics

        result = self.repository.get_period_metrics(period_type="week", year=2026, month=None, week=5)

        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        mock_query.filter.assert_called_once()
        mock_q1.filter.assert_called_once()
        mock_q2.first.assert_called_once()

        assert result == metrics

    def test_get_period_metrics_not_found(self):
        mock_query = self.mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = self.repository.get_period_metrics(period_type=PeriodType.YEAR.value, year=2099, month=None, week=None)

        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        mock_query.filter.assert_called_once()
        mock_filter.first.assert_called_once()

        assert result is None

    def test_get_metrics_for_keys_year_success(self):
        metrics_2025 = TransactionMetrics()
        metrics_2025.period_type = "year"
        metrics_2025.year = 2025

        metrics_2026 = TransactionMetrics()
        metrics_2026.period_type = "year"
        metrics_2026.year = 2026

        keys = [
            PeriodKey(period_type=PeriodType.YEAR, year=2025, month=None, week=None),
            PeriodKey(period_type=PeriodType.YEAR, year=2026, month=None, week=None),
        ]

        mock_query = self.mock_db.query.return_value
        mock_q1 = mock_query.filter.return_value
        mock_q2 = mock_q1.filter.return_value
        mock_q2.all.return_value = [metrics_2025, metrics_2026]

        result = self.repository.get_metrics_for_keys(period_type=PeriodType.YEAR, keys=keys)

        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        assert mock_query.filter.call_count == 1
        assert mock_q1.filter.call_count == 1
        mock_q2.all.assert_called_once()

        assert result == [metrics_2025, metrics_2026]

    def test_get_metrics_for_keys_month_success(self):
        metrics = TransactionMetrics()
        metrics.period_type = "month"
        metrics.year = 2026
        metrics.month = 1

        keys = [
            PeriodKey(period_type=PeriodType.MONTH, year=2026, month=1, week=None),
            PeriodKey(period_type=PeriodType.MONTH, year=2026, month=2, week=None),
        ]

        mock_query = self.mock_db.query.return_value
        mock_q1 = mock_query.filter.return_value
        mock_q2 = mock_q1.filter.return_value
        mock_q2.all.return_value = [metrics]

        result = self.repository.get_metrics_for_keys(period_type=PeriodType.MONTH, keys=keys)

        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        assert mock_query.filter.call_count == 1
        assert mock_q1.filter.call_count == 1
        mock_q2.all.assert_called_once()

        assert result == [metrics]

    def test_get_metrics_for_keys_month_all_missing_month_returns_empty(self):
        """If all keys have month=None for month period, pairs becomes empty -> [] without querying .all()."""
        keys = [
            PeriodKey(period_type=PeriodType.MONTH, year=2026, month=None, week=None),
            PeriodKey(period_type=PeriodType.MONTH, year=2025, month=None, week=None),
        ]

        mock_query = self.mock_db.query.return_value
        mock_q1 = mock_query.filter.return_value

        result = self.repository.get_metrics_for_keys(period_type=PeriodType.MONTH, keys=keys)

        assert result == []
        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        mock_query.filter.assert_called_once()
        mock_q1.filter.assert_not_called()

    def test_get_metrics_for_keys_week_success(self):
        metrics = TransactionMetrics()
        metrics.period_type = "week"
        metrics.year = 2026
        metrics.month = 1
        metrics.week = 5

        keys = [
            PeriodKey(period_type=PeriodType.WEEK, year=2026, month=1, week=5),
            PeriodKey(period_type=PeriodType.WEEK, year=2026, month=1, week=6),
        ]

        mock_query = self.mock_db.query.return_value
        mock_q1 = mock_query.filter.return_value
        mock_q2 = mock_q1.filter.return_value
        mock_q2.all.return_value = [metrics]

        result = self.repository.get_metrics_for_keys(period_type=PeriodType.WEEK, keys=keys)

        self.mock_db.query.assert_called_once_with(TransactionMetrics)
        assert mock_query.filter.call_count == 1
        assert mock_q1.filter.call_count == 1
        mock_q2.all.assert_called_once()

        assert result == [metrics]

    def test_count_transactions_in_range_success(self):
        start_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        mock_query = self.mock_db.query.return_value
        mock_q1 = mock_query.filter.return_value
        mock_q1.count.return_value = 45

        result = self.repository.count_transactions_in_range(start_dt=start_dt, end_dt=end_dt)

        self.mock_db.query.assert_called_once_with(Transaction)
        mock_query.filter.assert_called_once()
        mock_q1.count.assert_called_once()

        args, kwargs = mock_query.filter.call_args
        assert kwargs == {}
        assert len(args) == 2
        assert ">=" in str(args[0])
        assert "<=" in str(args[1])

        assert result == 45

    @pytest.mark.parametrize(
        ("sort_by", "sort_order"),
        [
            (TransactionSortBy.DATE, SortOrder.DESC),
            (TransactionSortBy.DATE, SortOrder.ASC),
            (TransactionSortBy.AMOUNT, SortOrder.DESC),
            (TransactionSortBy.AMOUNT, SortOrder.ASC),
            (TransactionSortBy.REFERENCE, SortOrder.DESC),
            (TransactionSortBy.REFERENCE, SortOrder.ASC),
        ],
    )
    def test_list_transactions_in_range_success(self, sort_by, sort_order):
        start_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        limit = 10
        offset = 20

        mock_query = self.mock_db.query.return_value
        mock_q1 = mock_query.filter.return_value
        mock_q2 = mock_q1.order_by.return_value
        mock_q3 = mock_q2.offset.return_value
        mock_q4 = mock_q3.limit.return_value

        tx1 = Transaction()
        tx1.reference = "A"
        tx2 = Transaction()
        tx2.reference = "B"
        mock_q4.all.return_value = [tx1, tx2]

        result = self.repository.list_transactions_in_range(
            start_dt=start_dt,
            end_dt=end_dt,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        self.mock_db.query.assert_called_once_with(Transaction)

        mock_query.filter.assert_called_once()
        f_args, f_kwargs = mock_query.filter.call_args
        assert f_kwargs == {}
        assert len(f_args) == 2
        assert ">=" in str(f_args[0])
        assert "<=" in str(f_args[1])

        mock_q1.order_by.assert_called_once()

        mock_q2.offset.assert_called_once_with(offset)
        mock_q3.limit.assert_called_once_with(limit)
        mock_q4.all.assert_called_once()

        assert result == [tx1, tx2]

    def test_list_transactions_in_range_default_sort_fallback(self):
        start_dt = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end_dt = datetime(2026, 1, 31, 23, 59, 59, tzinfo=timezone.utc)

        mock_query = self.mock_db.query.return_value
        mock_q1 = mock_query.filter.return_value
        mock_q2 = mock_q1.order_by.return_value
        mock_q3 = mock_q2.offset.return_value
        mock_q4 = mock_q3.limit.return_value
        mock_q4.all.return_value = []

        result = self.repository.list_transactions_in_range(
            start_dt=start_dt,
            end_dt=end_dt,
            limit=10,
            offset=0,
            sort_by="bad",
            sort_order=SortOrder.DESC,
        )

        self.mock_db.query.assert_called_once_with(Transaction)
        mock_query.filter.assert_called_once()
        mock_q1.order_by.assert_called_once()
        mock_q2.offset.assert_called_once_with(0)
        mock_q3.limit.assert_called_once_with(10)
        mock_q4.all.assert_called_once()

        assert result == []
