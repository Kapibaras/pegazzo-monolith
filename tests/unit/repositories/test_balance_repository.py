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

        # Result
        assert result == sample_transaction

    def test_create_transaction_failure(self, sample_transaction):
        """Test a failure during transaction creation raises DBOperationError."""

        # Mock
        self.mock_db.add.side_effect = Exception("DB Error")

        # Act & Assert
        with pytest.raises(DBOperationError):
            self.repository.create_transaction(sample_transaction)

        # Must roll back on error
        self.mock_db.rollback.assert_called_once()
