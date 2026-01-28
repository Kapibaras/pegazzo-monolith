from types import SimpleNamespace
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
from app.schemas.balance import TransactionPatchSchema, TransactionSchema
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
