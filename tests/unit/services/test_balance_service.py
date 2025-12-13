from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.enum.balance import PaymentMethod, Type
from app.errors.balance import (
    InvalidDescriptionLengthException,
    TransactionNotFoundException,
)
from app.models.balance import Transaction
from app.repositories.balance import BalanceRepository
from app.schemas.balance import TransactionSchema
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
