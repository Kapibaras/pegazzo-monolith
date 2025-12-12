from app.errors.database import DBOperationError
from app.models.balance import Transaction
from app.utils.logging_config import logger

from .abstract import DBRepository


class BalanceRepository(DBRepository):
    """Balance repository class."""

    def create_transaction(self, transaction: Transaction):
        """Create a new transaction."""
        try:
            self.db.add(transaction)
            self.db.commit()
            self.db.refresh(transaction)
        except Exception as ex:
            self.db.rollback()
            logger.error(f"Error creating transaction {transaction.reference} due to: {ex}")
            raise DBOperationError(f"Failed to create transaction with reference {transaction.reference}") from ex

        return transaction

    def get_by_reference(self, reference: str):
        """Retrieve a transaction by their reference.

        Args: username (str): The username of the user to retrieve.
        """
        return self.db.query(Transaction).filter(Transaction.reference == reference).first()
