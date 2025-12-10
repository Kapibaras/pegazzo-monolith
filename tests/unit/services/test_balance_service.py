from unittest.mock import Mock, patch

import pytest
from pydantic import ValidationError

from app.enum.balance import PaymentMethod, Type
from app.errors.balance import (
    InvalidDescriptionLengthException,
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

    def test_create_transaction_success(self):
        """Test successful creation of a transaction."""

        schema = TransactionSchema(
            amount=1200,
            reference="IGNORED",
            date="2025-01-01T10:00:00",
            type=Type.DEBIT,
            description="Pago de material",
            payment_method=PaymentMethod.CASH,
        )

        # Mock
        self.mock_repo.create_transaction.side_effect = lambda t: t

        with patch("app.services.balance.generate_reference") as mock_ref:
            mock_ref.return_value = "REF12345"

            result = self.service.create_transaction(schema)

        self.mock_repo.create_transaction.assert_called_once()
        assert isinstance(result, Transaction)
        assert result.amount == 1200
        assert result.reference == "REF12345"

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
