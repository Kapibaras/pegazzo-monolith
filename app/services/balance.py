from datetime import datetime, timezone

from app.enum.balance import PaymentMethod, Type
from app.errors.balance import (
    InvalidDescriptionLengthException,
    InvalidPaymentMethodException,
    InvalidTransactionTypeException,
    TransactionNotFoundException,
)
from app.models.balance import Transaction
from app.repositories.balance import BalanceRepository
from app.schemas.balance import BalanceMetricsSimpleResponseSchema, TransactionResponseSchema, TransactionSchema
from app.utils.reference import generate_reference


class BalanceService:
    """Balance service class."""

    def __init__(self, repository: BalanceRepository):
        """Initialize the balance service with a repository."""
        self.repository = repository

    def get_transaction(self, reference: str) -> TransactionResponseSchema:
        """Get a transaction by reference."""

        transaction = self.repository.get_by_reference(reference)
        if not transaction:
            raise TransactionNotFoundException(reference)
        return transaction

    def create_transaction(self, data: TransactionSchema) -> TransactionResponseSchema:
        """Create a new transaction."""

        if data.type not in Type:
            raise InvalidTransactionTypeException

        if data.payment_method not in PaymentMethod:
            raise InvalidPaymentMethodException

        if data.description and len(data.description) > 255:
            raise InvalidDescriptionLengthException

        transaction = Transaction(
            amount=data.amount,
            reference=generate_reference(data.type, data.payment_method),
            date=data.date if data.date else datetime.now(timezone.utc),
            type=data.type,
            description=data.description,
            payment_method=data.payment_method,
        )
        return self.repository.create_transaction(transaction)

    def delete_transaction(self, reference: str):
        """Delete a transaction."""

        transaction = self.repository.get_by_reference(reference)
        if not transaction:
            raise TransactionNotFoundException(reference)

        self.repository.delete_transaction(transaction)

    def update_transaction(self, reference: str, data: TransactionSchema) -> TransactionResponseSchema:
        """Update a transaction."""

        transaction = self.repository.get_by_reference(reference)
        if not transaction:
            raise TransactionNotFoundException(reference)

        if data.amount is not None:
            transaction.amount = data.amount

        if data.description is not None:
            if len(data.description) > 255:
                raise InvalidDescriptionLengthException
            transaction.description = data.description

        if data.payment_method is not None:
            if data.payment_method not in PaymentMethod:
                raise InvalidPaymentMethodException
            transaction.payment_method = data.payment_method

        return self.repository.update_transaction(transaction)

    def get_metrics(self, month: int | None = None, year: int | None = None) -> BalanceMetricsSimpleResponseSchema:
        """Get metrics."""
        if month is None and year is None:
            now = datetime.now(timezone.utc)
            month = now.month
            year = now.year

        metrics = self.repository.get_month_year_metrics(month=month, year=year)
        if not metrics:
            return {
                "balance": 0,
                "total_income": 0,
                "total_expense": 0,
                "transaction_count": 0,
                "period": {"month": month, "year": year},
            }

        return {
            "balance": metrics.balance,
            "total_income": metrics.total_income,
            "total_expense": metrics.total_expense,
            "transaction_count": metrics.transaction_count,
            "period": {"month": month, "year": year},
        }
