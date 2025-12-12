from unittest.mock import Mock

import pytest
from sqlalchemy.orm import Session

from app.errors.database import DBOperationError
from app.models.balance import Transaction
from app.repositories.balance import BalanceRepository


@pytest.fixture
def sample_transaction():
    """Create a sample transaction for testing."""
    tx = Transaction()
    tx.reference = "123456"
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
