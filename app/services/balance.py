from app.enum.balance import PaymentMethod, Type
from app.errors.balance import (
    InvalidDescriptionLengthException,
    InvalidPaymentMethodException,
    InvalidTransactionTypeException,
)
from app.models.balance import Transaction
from app.repositories.balance import BalanceRepository
from app.schemas.balance import TransactionResponseSchema, TransactionSchema
from app.utils.reference import generate_reference


class BalanceService:
    """Balance service class."""

    def __init__(self, repository: BalanceRepository):
        """Initialize the balance service with a repository."""
        self.repository = repository

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
            date=data.date,
            type=data.type,
            description=data.description,
            payment_method=data.payment_method,
        )
        return self.repository.create_transaction(transaction)
